from datetime import datetime
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlmodel import Session, or_, select
from app.configuration.settings import Configuration
from app.enums.cart import CartStatus
from app.enums.order_status import OrderStatus
from app.helpers.order.formatters import format_brazilian_date, format_currency
from app.models.cart.cart import Cart
from app.models.order.order import Order
from app.models.order.order_item import OrderItem
from app.models.product.product import Product
from app.models.user.address import Address
from app.models.company.promocode import PromoCode
from app.schemas.order.order import OrderCreate, OrderUpdate, OrderRead, StatusUpdateRequest
from app.models.user.user import User
from app.auth.auth import AuthRouter
from app.database.connection import get_session
from app.tasks.websockets.ws_manager import order_ws_manager
from escpos.printer import Serial
from serial.tools import list_ports
from fastapi.responses import PlainTextResponse

Configuration()
db_session = get_session
get_current_user = AuthRouter().get_current_user

class OrderRouter(APIRouter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_api_route("/orders/", self.list_orders, methods=["GET"], response_model=List[OrderRead])
        self.add_api_route("/orders/", self.create_order, methods=["POST"], response_model=OrderRead)
        self.add_api_route("/orders/search/", self.search_orders, methods=["GET"], response_model=List[OrderRead])
        self.add_api_route("/orders/{code}", self.get_order, methods=["GET"], response_model=OrderRead)
        self.add_api_route("/orders/{order_id}", self.update_order, methods=["PUT"], response_model=OrderRead)
        self.add_api_route("/orders/{order_id}", self.delete_order, methods=["DELETE"], response_model=dict)
        self.add_api_route("/orders/{order_id}/status", self.update_order_status, methods=["PATCH"])
        self.add_api_route("/orders/{order_id}/print",self.print_order,methods=["GET"], response_class=PlainTextResponse)

    def list_orders(self, current_user: User = Depends(get_current_user), session: Session = Depends(db_session)):
        orders = session.exec(select(Order)).all()
        for order in orders:
            order.items = session.exec(select(OrderItem).where(OrderItem.order_id == order.id)).all()
            order.delivery_address = session.get(Address, order.delivery_address_id)
        return orders
    
    def search_orders(
        self,
        query: str = Query(..., min_length=2),
        current_user: User = Depends(get_current_user),
        session: Session = Depends(db_session)
    ):
        logging.info(f"QUERY >>> {query}")
        try:
            stmt = select(Order).where(
                or_(
                    Order.customer_name.contains(query),
                    Order.phone.contains(query),
                )
            ).order_by(Order.id.desc())

            orders = session.exec(stmt).all()

            for order in orders:
                order.items = session.exec(select(OrderItem).where(OrderItem.order_id == order.id)).all()
                order.delivery_address = session.get(Address, order.delivery_address_id)

            return orders
        except Exception as e:
            raise HTTPException(status_code=404, detail="Pedido não encontrado")

    async def create_order(self, order_request: OrderCreate, session: Session = Depends(db_session)):
        try:
            # 1. Criar ou recuperar usuário
            user = session.exec(
                select(User).where(User.phone == order_request.customer.phone)
            ).first()
            
            if not user:
                user = User(
                    name=order_request.customer.name,
                    phone=order_request.customer.phone,
                    role="customer",
                    is_active=True
                )
                session.add(user)
                session.commit()
                session.refresh(user)

            # 2. Criar endereço
            address = Address(
                street=order_request.address.street,
                number=order_request.address.number,
                complement=order_request.address.complement,
                neighborhood=order_request.address.neighborhood,
                city=order_request.address.city,
                state=order_request.address.state,
                zip_code=order_request.address.zip_code,
                reference=order_request.address.reference,
                user_id=user.id,
                is_company_address=False
            )
            session.add(address)
            session.commit()
            session.refresh(address)

            # --- VALIDAÇÃO DO PROMOCODE AQUI ---
            discount_value = 0.0
            promo_code_upper = order_request.promo_code.upper() if order_request.promo_code else None

            if promo_code_upper:
                promo = session.exec(
                    select(PromoCode).where(PromoCode.code == promo_code_upper)
                ).first()

                if not promo:
                    raise HTTPException(status_code=400, detail="Código promocional inválido")

                now = datetime.now()
                if not promo.is_active or promo.valid_from > now or promo.valid_until < now:
                    raise HTTPException(status_code=400, detail="Código promocional não está ativo")

                if promo.max_uses and promo.current_uses >= promo.max_uses:
                    raise HTTPException(status_code=400, detail="Código promocional atingiu o limite de uso")

                if promo.min_order_value and order_request.total_amount < promo.min_order_value:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Valor mínimo para usar esse cupom é {promo.min_order_value}"
                    )

                # Calcula desconto
                discount_value = order_request.total_amount * (promo.discount_percentage / 100)

                # Atualiza contador de uso
                promo.current_uses += 1
                session.add(promo)
                session.commit()

            # Calcula o total final com desconto aplicado (não deixa negativo)
            total_after_discount = max(order_request.total_amount - discount_value, 0)

            cash_change_total = 0.0
            if order_request.payment_method == "dinheiro" and order_request.cash_change_for:
                cash_change_total = order_request.cash_change_for - order_request.total_amount
            else:
                cash_change_total = None

            # 3. Criar pedido
            order = Order(
                user_id=user.id,
                customer_name=user.name,
                phone=user.phone,
                delivery_address_id=address.id,
                payment_method=order_request.payment_method,
                delivery_fee=order_request.delivery_fee,
                total_amount=total_after_discount,
                discount_code=promo_code_upper,
                discount_value=discount_value,
                whatsapp_id=order_request.whatsapp_id,
                status=OrderStatus.PENDING,
                cash_change_for=order_request.cash_change_for,
                cash_change=cash_change_total,
                is_whatsapp=order_request.is_whatsapp,
                privacy_policy_version=order_request.privacy_policy_version,
                privacy_policy_accepted_at=order_request.privacy_policy_accepted_at
            )
            session.add(order)
            session.commit()
            session.refresh(order)

            # 4. Criar itens do pedido
            for item in order_request.items:
                flavors = item.selected_flavors
                if flavors is not None and not isinstance(flavors, list):
                    raise ValueError("selected_flavors deve ser uma lista ou None")
                
                order_item = OrderItem(
                    product_id=item.product_id,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    total_price=item.total_price,
                    size=item.size,
                    observation=item.observation,
                    selected_flavors=item.selected_flavors,
                    order_id=order.id
                )
                session.add(order_item)

            # Atualiza status do carrinho, se houver
            if order_request.cart_code:
                cart = session.exec(select(Cart).where(Cart.code == order_request.cart_code)).first()
                if cart:
                    cart.status = CartStatus.COMPLETED

            session.commit()

            # Carregar relacionamentos para resposta
            order.items = session.exec(select(OrderItem).where(OrderItem.order_id == order.id)).all()
            order.delivery_address = address
            
            await order_ws_manager.broadcast({
                "type": "new_order",
                "order": OrderRead.model_validate(order).model_dump(mode="json")
            })
            
            return OrderRead.model_validate(order)

        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    async def get_order(self, code: str, session: Session = Depends(db_session)):
        order = session.exec(select(Order).where(Order.code == code)).first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado")

        order.items = session.exec(select(OrderItem).where(OrderItem.order_id == order.id)).all()
        
        return order

    async def update_order(
        self,
        order_id: int,
        updated_order: OrderUpdate,
        current_user: User = Depends(get_current_user),
        session: Session = Depends(db_session)
    ):
        order = session.get(Order, order_id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado")

        # Atualiza campos fornecidos
        update_data = updated_order.dict(exclude_unset=True)

        for field, value in update_data.items():
            setattr(order, field, value)

        session.add(order)
        session.commit()
        session.refresh(order)

        order.items = session.exec(select(OrderItem).where(OrderItem.order_id == order.id)).all()
        order.delivery_address = session.get(Address, order.delivery_address_id)
        
        await order_ws_manager.broadcast({
            "type": "new_order",
            "order": OrderRead.model_validate(order).model_dump(mode="json")
        })


        return OrderRead.model_validate(order)

    def delete_order(self, order_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(db_session)):
        order = session.get(Order, order_id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado")

        # Deleta itens associados
        session.exec(select(OrderItem).where(OrderItem.order_id == order_id)).delete()

        # Deleta pedido
        session.delete(order)
        session.commit()
        return {"message": "Pedido deletado com sucesso"}

    def update_order_status(
        self,
        order_id: int,
        status_data: StatusUpdateRequest,
        current_user: User = Depends(get_current_user),
        session: Session = Depends(db_session)
    ):
        order = session.get(Order, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Pedido não encontrado")

        order.status = status_data.status
        session.commit()
        session.refresh(order)
        return {"message": "Status atualizado com sucesso", "status": order.status}


    async def print_order(
        self,
        order_id: int,
        session: Session = Depends(db_session),
        current_user=Depends(get_current_user),
    ):
        order = session.get(Order, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Pedido não encontrado")

        order.items = session.exec(
            select(OrderItem).where(OrderItem.order_id == order.id)
        ).all()

        if not order.items:
            raise HTTPException(status_code=400, detail="Pedido sem itens")

        # Produtos relacionados
        product_ids = [item.product_id for item in order.items]
        products = session.exec(
            select(Product).where(Product.id.in_(product_ids))
        ).all()
        produtos_dict = {p.id: p for p in products}

        lines = []
        lines.append(f"Comanda #{order.code}")
        lines.append(format_brazilian_date(order.created_at))
        lines.append("")

        for item in order.items:
            prod = produtos_dict.get(item.product_id)
            if not prod:
                continue
            name = prod.name[:20].ljust(20)
            qty = str(item.quantity)
            price = format_currency(item.total_price)
            lines.append(f"{name}{qty} x {price}")

        lines.append("")

        total = order.total_amount + (order.delivery_fee or 0.0)
        lines.append(f"TOTAL: {format_currency(total)}")

        if order.payment_method:
            lines.append(f"Pagamento: {order.payment_method.capitalize()}")

        if order.cash_change_for:
            lines.append(f"Troco para: {format_currency(order.cash_change_for)}")

        content = "\n".join(lines)
        return PlainTextResponse(content)