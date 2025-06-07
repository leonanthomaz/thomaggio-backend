import logging
from typing import List
from app.configuration.settings import Configuration
from app.enums.cart import CartStatus
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.product import Product
from app.auth.auth import AuthRouter
from app.database.connection import get_session
from app.schemas.cart import CartCreate, CartUpdate, CartRead, CartList
from app.schemas.cart_item import CartItemCreate, CartItemUpdate, CartItemRead

Configuration()
db_session = get_session
get_current_user = AuthRouter().get_current_user


class CartRouter(APIRouter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_api_route("/cart/", self.create_cart, methods=["POST"], response_model=CartRead)
        self.add_api_route("/cart/", self.list_carts, methods=["GET"], response_model=List[CartList])
        self.add_api_route("/cart/{cart_code}", self.get_cart_by_code, methods=["GET"], response_model=CartRead)
        self.add_api_route("/cart/{cart_code}", self.update_cart_by_code, methods=["PUT"], response_model=CartRead)
        self.add_api_route("/cart/{cart_code}", self.delete_cart_by_code, methods=["DELETE"], response_model=dict)
        self.add_api_route("/cart/{cart_code}/items/", self.add_item_by_code, methods=["POST"], response_model=CartItemRead)
        self.add_api_route("/cart/{cart_code}/items/{item_id}", self.update_item_by_code, methods=["PATCH"], response_model=CartItemRead)
        self.add_api_route("/cart/{cart_code}/items/{item_id}/size/{size}", self.remove_item_by_code, methods=["DELETE"], response_model=dict)
        self.add_api_route("/cart/{cart_code}/items/", self.clear_items_by_code, methods=["DELETE"], response_model=dict)

    def create_cart(self, cart_data: CartCreate, session: Session = Depends(db_session)):
        cart = Cart(status=CartStatus.ACTIVE)

        if cart_data.whatsapp_id:
            cart.whatsapp_id = cart_data.whatsapp_id

        session.add(cart)
        session.commit()
        session.refresh(cart)
        return cart

    def list_carts(self, session: Session = Depends(db_session)):
        carts = session.exec(select(Cart)).all()
        return carts

    def get_cart_by_code(self, cart_code: str, session: Session = Depends(db_session)):
        cart = session.exec(select(Cart).where(Cart.code == cart_code)).first()
        if not cart:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Carrinho não encontrado")
        return cart

    def update_cart_by_code(self, cart_code: str, cart_update: CartUpdate, session: Session = Depends(db_session)):
        cart = session.exec(select(Cart).where(Cart.code == cart_code)).first()
        if not cart:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Carrinho não encontrado")

        for key, value in cart_update.dict(exclude_unset=True).items():
            setattr(cart, key, value)

        session.commit()
        session.refresh(cart)
        return cart

    def delete_cart_by_code(self, cart_code: str, session: Session = Depends(db_session)):
        cart = session.exec(select(Cart).where(Cart.code == cart_code)).first()
        if not cart:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Carrinho não encontrado")

        session.delete(cart)
        cart.status = CartStatus.EXPIRED
        session.commit()
        return {"message": "Carrinho deletado com sucesso"}

    def add_item_by_code(self, cart_code: str, item_data: CartItemCreate, session: Session = Depends(db_session)):
        logging.info(f"DADOS VINDOS DO FRONTEND -> ITEM DATA: {item_data}")
        cart = session.exec(select(Cart).where(Cart.code == cart_code)).first()
        if not cart:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Carrinho não encontrado")

        product = session.get(Product, item_data.product_id)
        if not product or not product.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto inválido ou inativo")

        # Valida tamanho
        if item_data.size not in product.prices_by_size:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tamanho inválido para este produto")

        unit_price = product.prices_by_size[item_data.size]

        # Verifica se já existe um item igual
        existing_item = session.exec(
            select(CartItem).where(
                CartItem.cart_id == cart.id,
                CartItem.product_id == item_data.product_id,
                CartItem.size == item_data.size,
            )
        ).first()

        if existing_item:
            existing_item.quantity += item_data.quantity
            session.commit()
            session.refresh(existing_item)
            return existing_item
                            
        if item_data.selected_flavors:
            for flavor in item_data.selected_flavors:
                if flavor['name'] not in product.selected_flavors:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Sabor '{flavor['name']}' inválido para este produto"
                    )


        new_item = CartItem(
            cart_id=cart.id,
            product_id=item_data.product_id,
            quantity=item_data.quantity,
            size=item_data.size,
            selected_flavors=item_data.selected_flavors,
            unit_price=unit_price,
            observation=item_data.observation,
            options=item_data.options
        )
        session.add(new_item)
        
        # Atualiza status se ainda estiver ACTIVE
        if cart.status == CartStatus.ACTIVE or cart.status == CartStatus.CLEARED:
            cart.status = CartStatus.PROCESSING
        
        session.commit()
        session.refresh(new_item)
        
        logging.info(f"Item adicionado ao carrinho {cart_code}: {new_item.id} - {new_item.product_id} - {new_item.size} - {new_item.quantity} >>> {new_item.observation}")
        return new_item

    def update_item_by_code(self, cart_code: str, item_id: int, update_data: CartItemUpdate, session: Session = Depends(db_session)):
        cart = session.exec(select(Cart).where(Cart.code == cart_code)).first()
        if not cart:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Carrinho não encontrado")

        item = session.exec(
            select(CartItem).where(
                CartItem.id == item_id,
                CartItem.cart_id == cart.id
            )
        ).first()

        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item não encontrado no carrinho")

        if update_data.size is not None:
            item.size = update_data.size

        if update_data.selected_flavors is not None:
            item.selected_flavors = update_data.selected_flavors

        if update_data.observation is not None:
            item.observation = update_data.observation
            
        if update_data.options is not None:
            item.options = update_data.options
    
        item.quantity = update_data.quantity
        session.commit()
        session.refresh(item)
        return item

    def remove_item_by_code(
        self,
        cart_code: str,
        item_id: int,
        size: str,
        session: Session = Depends(db_session)
    ):
        cart = session.exec(select(Cart).where(Cart.code == cart_code)).first()
        if not cart:
            raise HTTPException(status_code=404, detail="Carrinho não encontrado")

        # Verifica se o item pertence ao carrinho
        item = session.exec(
            select(CartItem).where(
                CartItem.id == item_id,
                CartItem.cart_id == cart.id,
                CartItem.size == size
            )
        ).first()

        if not item:
            raise HTTPException(status_code=404, detail="Item não encontrado no carrinho")

        session.delete(item)
        session.commit()
        return {"message": "Item removido com sucesso"}

    def clear_items_by_code(self, cart_code: str, session: Session = Depends(db_session)):
        cart = session.exec(select(Cart).where(Cart.code == cart_code)).first()
        if not cart:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Carrinho não encontrado")

        items = session.exec(select(CartItem).where(CartItem.cart_id == cart.id)).all()
        for item in items:
            session.delete(item)
        
        if items:  # só marca como cancelado se tinha itens
            cart.status = CartStatus.CLEARED
        
        session.commit()
      
        return {"message": "Todos os itens foram removidos do carrinho"}
    
