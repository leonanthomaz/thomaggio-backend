from datetime import datetime, timezone
import logging
from typing import List
from zoneinfo import ZoneInfo
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

# Definir o fuso horário de São Paulo
SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo")

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

    def convert_local_to_utc(self, dt: datetime) -> datetime:
        """Recebe datetime sem timezone e converte para UTC"""
        if dt.tzinfo is None:
            # Assume que a data está no fuso horário local (SP) e converte para UTC
            return dt.replace(tzinfo=SAO_PAULO_TZ).astimezone(timezone.utc)
        # Se já tem timezone, converte para UTC
        return dt.astimezone(timezone.utc)
    
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
        is_admin(current_user)
        logging.info(f"DADOS PROMOCIONAIS VINDOS DO FRONTEND : {promocode}")

        promo_dict = promocode.dict()

        for key in ["valid_from", "valid_until"]:
            dt = promo_dict.get(key)
            if dt:
                dt = datetime.fromisoformat(dt) if isinstance(dt, str) else dt
                # REMOVE timezone, força naive (local sem fuso explícito)
                promo_dict[key] = self.convert_local_to_utc(dt)


                db_promo = PromoCode(**promo_dict)

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

        update_data = promocode_data.dict(exclude_unset=True)

        for key in ["valid_from", "valid_until"]:
            dt = update_data.get(key)
            if dt:
                dt = datetime.fromisoformat(dt) if isinstance(dt, str) else dt
                update_data[key] = self.convert_local_to_utc(dt)


                for key, value in update_data.items():
                    setattr(db_promo, key, value)

                db_promo.updated_at = datetime.now(timezone.utc)
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
        now = datetime.now(SAO_PAULO_TZ)

        valid_from_local = promo.valid_from.astimezone(SAO_PAULO_TZ) if promo.valid_from else None
        valid_until_local = promo.valid_until.astimezone(SAO_PAULO_TZ) if promo.valid_until else None

        if not promo.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código promocional inativo"
            )

        if valid_from_local and now < valid_from_local:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Código promocional válido apenas a partir de {valid_from_local.strftime('%d/%m/%Y %H:%M')}"
            )

        if valid_until_local and now > valid_until_local:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Código promocional expirado em {valid_until_local.strftime('%d/%m/%Y %H:%M')}"
            )

        # 4. Calcula o desconto
        subtotal = cart.total  # Somente os produtos
        discount_value = subtotal * (promo.discount_percentage / 100)

        cart.promo_code = promo.code
        cart.promo_discount_percentage = promo.discount_percentage
        cart.promo_discount_value = discount_value
        cart.promo_applied_at = datetime.now(timezone.utc)
        promo.current_uses += 1

        session.add_all([cart, promo])
        session.commit()

        return {
            "subtotal": subtotal,
            "discount_percentage": promo.discount_percentage,
            "discount_value": discount_value,
            "total_with_discount": max(subtotal - discount_value, 0),
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