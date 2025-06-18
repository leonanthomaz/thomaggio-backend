from datetime import datetime
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
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
from fastapi.responses import PlainTextResponse


ORDER_STATUS_PT = {
    "pending": "PENDENTE",
    "preparing": "PREPARANDO",
    "ready": "PRONTO",
    "delivered": "ENTREGUE",
    "canceled": "CANCELADO"
}

Configuration()
db_session = get_session
get_current_user = AuthRouter().get_current_user

class OrderRouter(APIRouter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logo = "https://pub-60387806396445c199b61c92e7c5ab5e.r2.dev/thomaggio-logo.png"
        self.add_api_route("/orders/", self.get_all_orders, methods=["GET"], response_model=List[OrderRead])
        self.add_api_route("/orders/", self.create_order, methods=["POST"], response_model=OrderRead)
        self.add_api_route("/orders/search/", self.search_orders, methods=["GET"], response_model=List[OrderRead])
        self.add_api_route("/orders/{code}", self.get_order_by_code, methods=["GET"], response_model=OrderRead)
        self.add_api_route("/orders/{order_id}", self.update_order_by_id, methods=["PUT"], response_model=OrderRead)
        self.add_api_route("/orders/{order_id}", self.delete_order, methods=["DELETE"], response_model=dict)
        self.add_api_route("/orders/{order_id}/status", self.update_order_status_by_id, methods=["PATCH"])
        self.add_api_route("/orders/{order_id}/print",self.print_order_by_id,methods=["GET"], response_class=PlainTextResponse)

    def get_all_orders(self, current_user: User = Depends(get_current_user), session: Session = Depends(db_session)):
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
                else:
                    # Atualiza nome se mudou
                    if user.name != order_request.customer.name:
                        user.name = order_request.customer.name
                        session.add(user)
                        session.commit()

                # 2. Gerenciar endereço - pegar o primeiro endereço existente ou criar um novo
                address = session.exec(
                    select(Address)
                    .where(Address.user_id == user.id)
                    .where(Address.is_company_address == False)
                    .order_by(Address.id)  # Ordena por ID para pegar o mais antigo primeiro
                ).first()

                if address:
                    # Atualiza o endereço existente com os novos dados
                    address.street = order_request.address.street
                    address.number = order_request.address.number
                    address.complement = order_request.address.complement
                    address.neighborhood = order_request.address.neighborhood
                    address.city = order_request.address.city
                    address.state = order_request.address.state
                    address.zip_code = order_request.address.zip_code
                    address.reference = order_request.address.reference
                    session.add(address)
                else:
                    # Cria um novo endereço se não existir nenhum
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

                # Restante do código permanece igual...
                # 3. Validar cupom promocional (se veio do carrinho, já foi validado)
                discount_value = order_request.discount_value or 0.0
                promo_code = order_request.promo_code.upper() if order_request.promo_code else None

                if promo_code:
                    # Verifica se o cupom existe e está ativo (mas não recalcula o desconto)
                    promo = session.exec(
                        select(PromoCode).where(PromoCode.code == promo_code)
                    ).first()

                    if promo:
                        # Atualiza contagem de usos do cupom
                        promo.current_uses += 1
                        session.add(promo)
                        session.commit()

                if order_request.payment_method == "dinheiro" and order_request.cash_change_for:
                    # O total a pagar deve incluir o valor com desconto MAIS a taxa de entrega
                    total_a_pagar = (order_request.total_amount_with_discount 
                                     if order_request.promo_code 
                                     else order_request.total_amount) + (order_request.delivery_fee or 0)
                    
                    cash_change_total = order_request.cash_change_for - total_a_pagar
                else:
                    cash_change_total = None


                # 4. Criar pedido com os valores já calculados
                order = Order(
                    user_id=user.id,
                    customer_name=user.name,
                    phone=user.phone,
                    delivery_address_id=address.id,
                    payment_method=order_request.payment_method,
                    delivery_fee=order_request.delivery_fee,
                    total_amount=order_request.total_amount,
                    total_amount_with_discount=order_request.total_amount_with_discount,
                    discount_code=promo_code,
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

                # 5. Criar itens do pedido
                for item in order_request.items:
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

                # 6. Atualizar status do carrinho, se houver
                if order_request.cart_code:
                    cart = session.exec(select(Cart).where(Cart.code == order_request.cart_code)).first()
                    if cart:
                        cart.status = CartStatus.COMPLETED
                        session.add(cart)

                session.commit()

                # 7. Popular dados para resposta
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

    async def get_order_by_code(self, code: str, session: Session = Depends(db_session)):
        order = session.exec(select(Order).where(Order.code == code)).first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado")

        order.items = session.exec(select(OrderItem).where(OrderItem.order_id == order.id)).all()
        
        return order

    async def update_order_by_id(
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

    def update_order_status_by_id(
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

    async def print_order_by_id(
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

            # Carrega relacionamentos
            product_ids = [item.product_id for item in order.items]
            products = session.exec(select(Product).where(Product.id.in_(product_ids))).all()
            produtos_dict = {p.id: p for p in products}
            
            if order.delivery_address_id:
                order.delivery_address = session.get(Address, order.delivery_address_id)

            # Cabeçalho
            lines = []
            lines.append("=" * 24)
            lines.append(f"{'COMANDA Nº ' + order.code:^24}")
            lines.append("=" * 24)
            lines.append(f"Data: {format_brazilian_date(order.created_at)}")
            status_pt = ORDER_STATUS_PT.get(order.status.value.lower(), order.status.value.upper())
            lines.append(f"Status: {status_pt}")
            lines.append("-" * 24)
            
            # Cliente
            lines.append(f"CLIENTE: {order.customer_name or 'Não informado'}")
            lines.append(f"TEL: {order.phone or 'Não informado'}")
            
            # Endereço (se entrega)
            if order.delivery_address:
                addr = order.delivery_address
                lines.append("-" * 24)
                lines.append("ENTREGA:")
                lines.append(f"{addr.street}, {addr.number}")
                if addr.complement:
                    lines.append(f"Comp: {addr.complement}")
                lines.append(f"{addr.neighborhood}")
                lines.append(f"{addr.city}/{addr.state}")
                if addr.reference:
                    lines.append(f"Ref: {addr.reference}")
            
            lines.append("=" * 24)
            lines.append(f"{'ITENS DO PEDIDO':^24}")
            lines.append("=" * 24)
            
            # Itens do pedido
            for item in order.items:
                prod = produtos_dict.get(item.product_id)
                if not prod:
                    continue
                    
                # Nome e quantidade
                lines.append(f"{item.quantity}x {prod.name[:28]}")
                
                # Tamanho
                if item.size:
                    size_display = {
                        'U': 'Único',
                        'P': 'P',
                        'M': 'M',
                        'G': 'G',
                        'GG': 'GG'
                    }.get(item.size, item.size)
                    lines.append(f"Tam: {size_display}")
                
                # Sabores
                if item.selected_flavors:
                    lines.append("Sabores:")
                    for flavor in item.selected_flavors:
                        lines.append(f"- {flavor.get('name')} ({flavor.get('quantity', 1)}x)")
                
                # Opcionais
                if item.options:
                    lines.append("Adicionais:")
                    for option, price in item.options.items():
                        if price > 0:
                            lines.append(f"+ {option} (+{format_currency(price)})")
                
                # Observação
                if item.observation:
                    lines.append(f"Obs: {item.observation[:28]}")
                
                # Preço do item
                lines.append(f"R$ {format_currency(item.total_price)}")
                lines.append("-" * 24)
            
            # Resumo de valores
            # O subtotal deve ser o valor dos itens sem desconto
            subtotal_itens = order.total_amount

            # Aplica desconto se houver
            if order.discount_value and order.discount_value > 0:
                valor_com_desconto = subtotal_itens - order.discount_value
            else:
                valor_com_desconto = subtotal_itens

            # Taxa de entrega (se aplicável)
            taxa_entrega = order.delivery_fee if order.delivery_fee else 0

            # Total geral (itens com desconto + entrega)
            total_geral = valor_com_desconto + taxa_entrega

            # Atualizar as linhas de exibição
            lines.append(f"Subtotal: R$ {format_currency(subtotal_itens)}")

            if order.discount_value and order.discount_value > 0:
                lines.append(f"Desconto: -R$ {format_currency(order.discount_value)}")
                lines.append(f"Cupom: {order.discount_code or 'Aplicado'}")
                lines.append(f"Total c/ desc: R$ {format_currency(valor_com_desconto)}")

            if order.delivery_fee and order.delivery_fee > 0:
                lines.append(f"Entrega: +R$ {format_currency(order.delivery_fee)}")

            lines.append("=" * 24)
            lines.append(f"TOTAL GERAL: R$ {format_currency(total_geral)}")
                        
            # Pagamento
            payment_methods = {
                'pix': 'PIX',
                'dinheiro': 'DINHEIRO',
                'cartao': 'CARTÃO',
                'debito': 'CARTÃO DÉBITO',
                'credito': 'CARTÃO CRÉDITO'
            }
            lines.append(f"Pagamento: {payment_methods.get(order.payment_method, order.payment_method.upper())}")
            
            if order.payment_method == 'dinheiro' and order.cash_change_for:
                lines.append(f"Troco p/: R$ {format_currency(order.cash_change_for)}")
                if order.cash_change and order.cash_change > 0:
                    lines.append(f"Troco: R$ {format_currency(order.cash_change)}")
            
            # Rodapé
            lines.append("=" * 24)
            lines.append(f"{'OBRIGADO PELA PREFERÊNCIA!':^24}")
            lines.append("=" * 24)
            
            content = "\n".join(lines)
            return PlainTextResponse(content)