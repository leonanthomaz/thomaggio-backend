from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database.connection import get_session
from app.auth.auth import AuthRouter
from app.models.user import User
from app.models.delivery_config import DeliveryConfig
from app.models.delivery_zone import DeliveryZone
from app.schemas.delivery_config import DeliveryConfigCreate, DeliveryConfigRead, DeliveryConfigUpdate
from app.schemas.delivery_zone import DeliveryZoneCreate, DeliveryZoneRead, DeliveryZoneUpdate

db_session = get_session
get_current_user = AuthRouter().get_current_user

class DeliveryRouter(APIRouter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_api_route("/delivery/config", self.create_config, methods=["POST"], response_model=DeliveryConfigRead)
        self.add_api_route("/delivery/config", self.get_config, methods=["GET"], response_model=DeliveryConfigRead)
        self.add_api_route("/delivery/config", self.update_config, methods=["PUT"], response_model=DeliveryConfigRead)

        self.add_api_route("/delivery/zones", self.create_zone, methods=["POST"], response_model=DeliveryZoneRead)
        self.add_api_route("/delivery/zones", self.get_zones, methods=["GET"], response_model=list[DeliveryZoneRead])
        self.add_api_route("/delivery/zones/{zone_id}", self.update_zone, methods=["PUT"], response_model=DeliveryZoneRead)
        self.add_api_route("/delivery/zones/{zone_id}", self.delete_zone, methods=["DELETE"])

    def create_config(self, data: DeliveryConfigCreate, current_user: User = Depends(get_current_user), session: Session = Depends(db_session)):
        config = session.exec(select(DeliveryConfig)).first()
        if config:
            raise HTTPException(status_code=400, detail="Configuração de entrega já existe.")
        new_config = DeliveryConfig(**data.dict())
        session.add(new_config)
        session.commit()
        session.refresh(new_config)
        return new_config

    def get_config(self, session: Session = Depends(db_session)):
        config = session.exec(select(DeliveryConfig)).first()        
        if not config:
            raise HTTPException(status_code=404, detail="Configuração não encontrada.")
        return config

    def update_config(self, data: DeliveryConfigUpdate, current_user: User = Depends(get_current_user), session: Session = Depends(db_session)):
        config = session.exec(select(DeliveryConfig)).first() 
        if not config:
            raise HTTPException(status_code=404, detail="Configuração não encontrada.")

        for key, value in data.dict(exclude_unset=True).items():
            setattr(config, key, value)

        session.add(config)
        session.commit()
        session.refresh(config)
        return config

    def create_zone(self, data: DeliveryZoneCreate, current_user: User = Depends(get_current_user), session: Session = Depends(db_session)):
        zone = DeliveryZone(**data.dict())
        session.add(zone)
        session.commit()
        session.refresh(zone)
        return zone

    def get_zones(self, session: Session = Depends(db_session)):
        config = session.exec(select(DeliveryConfig)).first() 
        if not config:
            raise HTTPException(status_code=404, detail="Configuração não encontrada.")
        return config.zones

    def update_zone(self, zone_id: int, data: DeliveryZoneUpdate, current_user: User = Depends(get_current_user), session: Session = Depends(db_session)):
        zone = session.get(DeliveryZone, zone_id)
        for key, value in data.dict(exclude_unset=True).items():
            setattr(zone, key, value)
        session.add(zone)
        session.commit()
        session.refresh(zone)
        return zone

    def delete_zone(self, zone_id: int, session: Session = Depends(db_session)):
        zone = session.get(DeliveryZone, zone_id)
        session.delete(zone)
        session.commit()
        return {"detail": "Zona deletada com sucesso."}
            
