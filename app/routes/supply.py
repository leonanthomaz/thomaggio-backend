from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.models.supply import Supply
from app.schemas.supply import SupplyCreate, SupplyUpdate, SupplyRead
from app.database.connection import get_session

# Instância do session maker
db_session = get_session

class SupplyRouter(APIRouter):
    """
    Roteador para operações relacionadas a insumos (Supply).
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_api_route("/supply", self.create_supply, methods=["POST"], response_model=SupplyRead)
        self.add_api_route("/supply/{supply_id}", self.get_supply, methods=["GET"], response_model=SupplyRead)
        self.add_api_route("/supply/{supply_id}", self.update_supply, methods=["PUT"], response_model=SupplyRead)
        self.add_api_route("/supply/{supply_id}", self.delete_supply, methods=["DELETE"])
        self.add_api_route("/supplies", self.list_supplies, methods=["GET"], response_model=list[SupplyRead])

    def create_supply(self, supply: SupplyCreate, session: Session = Depends(db_session)):
        new_supply = Supply(**supply.dict())
        session.add(new_supply)
        session.commit()
        session.refresh(new_supply)
        return new_supply

    def get_supply(self, supply_id: int, session: Session = Depends(db_session)):
        supply = session.get(Supply, supply_id)
        if not supply:
            raise HTTPException(status_code=404, detail="Insumo não encontrado.")
        return supply

    def update_supply(self, supply_id: int, supply_data: SupplyUpdate, session: Session = Depends(db_session)):
        supply = session.get(Supply, supply_id)
        if not supply:
            raise HTTPException(status_code=404, detail="Insumo não encontrado.")

        for key, value in supply_data.dict(exclude_unset=True).items():
            setattr(supply, key, value)

        supply.updated_at = datetime.now(timezone.utc)

        session.add(supply)
        session.commit()
        session.refresh(supply)

        return supply

    def delete_supply(self, supply_id: int, session: Session = Depends(db_session)):
        supply = session.get(Supply, supply_id)
        if not supply:
            raise HTTPException(status_code=404, detail="Insumo não encontrado.")

        supply.is_active = False
        supply.updated_at = datetime.now(timezone.utc)
        session.add(supply)
        session.commit()
        return {"detail": "Insumo desativado com sucesso."}

    def list_supplies(self, session: Session = Depends(db_session)):
        supplies = session.exec(select(Supply).where(Supply.is_active == True)).all()
        return supplies
