from datetime import datetime
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.auth.auth import AuthRouter
from app.configuration.settings import Configuration
from app.core.middlewares.users import is_admin
from app.database.connection import get_session
from app.models.cart.cart import Cart
from app.models.company.promocode import PromoCode
from app.models.user.user import User
from app.schemas.company.promocode import PromoCodeCreate, PromoCodeResponse, PromoCodeUpdate

Configuration()
db_session = get_session
get_current_user = AuthRouter().get_current_user

class PromoCodeRouter(APIRouter):
    def __init__(self, *args, **kwargs):
        super().__init__(
            prefix="/promocode",
            tags=["PromoCode"],
            *args, **kwargs
        )
        self.add_api_route("/", self.get_all_promocodes, methods=["GET"], response_model=List[PromoCode])
        self.add_api_route("/", self.create_promocode, methods=["POST"], response_model=PromoCodeResponse)

        self.add_api_route("/{promo_id}", self.get_promocode_by_id, methods=["GET"], response_model=PromoCode)
        self.add_api_route("/{promo_id}", self.update_promocode_by_id, methods=["PUT"], response_model=PromoCode)
        self.add_api_route("/{promo_id}", self.delete_promocode_by_id, methods=["DELETE"], response_model=dict)

        self.add_api_route("/apply/{promo_code}/{cart_code}", self.apply_promocode, methods=["POST"])
        self.add_api_route("/remove/{cart_code}", self.remove_promocode, methods=["DELETE"])

    async def get_all_promocodes(self, current_user: User = Depends(get_current_user), session: Session = Depends(db_session)):
        is_admin(current_user)
        promo_codes = session.exec(select(PromoCode)).all()
        return promo_codes

    async def get_promocode_by_id(self, promo_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(db_session)):
        is_admin(current_user)
        promo = session.get(PromoCode, promo_id)
        if not promo:
            raise HTTPException(status_code=404, detail="PromoCode não encontrado")
        return promo

    async def create_promocode(
        self, 
        promocode: PromoCodeCreate, 
        current_user: User = Depends(get_current_user), 
        session: Session = Depends(db_session)
    ):
        logging.info(f"DADOS PROMOCIONAIS VINDOS DO FRONTEND : {promocode}")
        
        db_promo = PromoCode(**promocode.dict())
        
        session.add(db_promo)
        session.commit()
        session.refresh(db_promo)
        return db_promo

    async def update_promocode_by_id(
        self, 
        promo_id: int, 
        promocode_data: PromoCodeUpdate, 
        current_user: User = Depends(get_current_user), 
        session: Session = Depends(db_session)
    ):
        is_admin(current_user)
        db_promo = session.get(PromoCode, promo_id)
        if not db_promo:
            raise HTTPException(status_code=404, detail="PromoCode não encontrado")

        for key, value in promocode_data.dict(exclude_unset=True).items():
            setattr(db_promo, key, value)

        db_promo.updated_at = datetime.now()
        session.add(db_promo)
        session.commit()
        session.refresh(db_promo)
        return db_promo

    async def delete_promocode_by_id(self, promo_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(db_session)):
        is_admin(current_user)
        db_promo = session.get(PromoCode, promo_id)
        if not db_promo:
            raise HTTPException(status_code=404, detail="PromoCode não encontrado")
        session.delete(db_promo)
        session.commit()
        return {"detail": "PromoCode deletado com sucesso"}
    
    async def apply_promocode(
        self, 
        promo_code: str, 
        cart_code: str, 
        session: Session = Depends(db_session)
    ):
        """Aplica um código promocional ao carrinho e calcula o desconto"""
        
        # 1. Busca o carrinho
        cart = session.exec(select(Cart).where(Cart.code == cart_code)).first()
        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Carrinho não encontrado"
            )
        
        # 2. Busca o código promocional (case insensitive)
        promo_code_upper = promo_code.upper()
        promo = session.exec(
            select(PromoCode).where(PromoCode.code == promo_code_upper)
        ).first()
        
        if not promo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código promocional inválido"
            )
        
        # 3. Validações do código promocional
        now = datetime.now()
        
        if not promo.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código promocional inativo"
            )
        
        if now < promo.valid_from:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Código promocional válido apenas a partir de {promo.valid_from}"
            )
        
        if now > promo.valid_until:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código promocional expirado"
            )
        
        if promo.max_uses is not None and promo.current_uses >= promo.max_uses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código promocional atingiu o limite de usos"
            )
        
        if promo.min_order_value is not None and cart.total < promo.min_order_value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Valor mínimo do pedido para este cupom é R$ {promo.min_order_value:.2f}"
            )
        
        # 4. Calcula o desconto
        discount_value = cart.total * (promo.discount_percentage / 100)
        total_with_discount = max(cart.total - discount_value, 0)
        
        cart.promo_code = promo.code
        cart.promo_discount_percentage = promo.discount_percentage
        cart.promo_discount_value = discount_value
        cart.promo_applied_at = datetime.now()
        promo.current_uses += 1
        
        session.add_all([cart, promo])
        session.commit()
        
        # 6. Retorna os dados do desconto aplicado
        return {
            "original_total": cart.total,
            "discount_percentage": promo.discount_percentage,
            "discount_value": discount_value,
            "total_with_discount": total_with_discount,
            "promo_code": promo.code,
            "promo_description": promo.description
        }
        
    async def remove_promocode(
        self, 
        cart_code: str, 
        session: Session = Depends(db_session)
    ):
        """Remove um código promocional aplicado ao carrinho, revertendo para o valor original"""
        
        cart = session.exec(select(Cart).where(Cart.code == cart_code)).first()
        if not cart:
            raise HTTPException(status_code=404, detail="Carrinho não encontrado")

        cart.promo_code = None
        cart.promo_discount_percentage = 0
        cart.promo_discount_value = 0
        cart.promo_applied_at = None

        session.add(cart)
        session.commit()

        return {
            "success": True,
            "message": "Código promocional removido com sucesso",
            "original_total": cart.total,
            "current_total": cart.total,
            "discount_applied": 0,
            "promo_code": None
        }