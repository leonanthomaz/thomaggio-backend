from datetime import datetime
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.auth.auth import AuthRouter
from app.configuration.settings import Configuration
from app.database.connection import get_session
from app.models.promocode import PromoCode
from app.models.user import User
from app.schemas.promocode import PromoCodeCreate, PromoCodeResponse, PromoCodeUpdate

Configuration()
db_session = get_session
get_current_user = AuthRouter().get_current_user

class PromoCodeRouter(APIRouter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_api_route("/promocode/", self.list_promocodes, methods=["GET"], response_model=List[PromoCode])
        self.add_api_route("/promocode/", self.create_promocode, methods=["POST"], response_model=PromoCodeResponse)

        self.add_api_route("/promocode/{promo_id}", self.get_promocode, methods=["GET"], response_model=PromoCode)
        self.add_api_route("/promocode/{promo_id}", self.update_promocode, methods=["PUT"], response_model=PromoCode)
        self.add_api_route("/promocode/{promo_id}", self.delete_promocode, methods=["DELETE"], response_model=dict)

    async def list_promocodes(self, session: Session = Depends(db_session)):
        promo_codes = session.exec(select(PromoCode)).all()
        return promo_codes

    async def get_promocode(self, promo_id: int, session: Session = Depends(db_session)):
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

    async def update_promocode(
        self, 
        promo_id: int, 
        promocode_data: PromoCodeUpdate, 
        current_user: User = Depends(get_current_user), 
        session: Session = Depends(db_session)
    ):
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

    async def delete_promocode(self, promo_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(db_session)):
        db_promo = session.get(PromoCode, promo_id)
        if not db_promo:
            raise HTTPException(status_code=404, detail="PromoCode não encontrado")
        session.delete(db_promo)
        session.commit()
        return {"detail": "PromoCode deletado com sucesso"}