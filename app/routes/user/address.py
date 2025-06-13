from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.core.middlewares.users import is_admin
from app.models.user.address import Address
from app.models.user.user import User
from app.auth.auth import AuthRouter
from app.database.connection import get_session
from app.schemas.company.address import AddressUpdate

db_session = get_session
get_current_user = AuthRouter().get_current_user

class AddressRouter(APIRouter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_api_route("/address/", self.get_all_addresses, methods=["GET"], response_model=List[Address])
        self.add_api_route("/address/{address_id}", self.get_address_by_id, methods=["GET"], response_model=Address)
        self.add_api_route("/address/{address_id}", self.update_address_by_id, methods=["PUT"], response_model=Address)
        self.add_api_route("/address/{address_id}", self.delete_address_by_id, methods=["DELETE"])

    def get_all_addresses(self, session: Session = Depends(db_session)):
        addresses = session.query(Address).all()
        return addresses
    
    def get_address_by_id(self, address_id: int, session: Session = Depends(db_session)):
        address = session.get(Address, address_id)
        if not address:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Endereço não encontrado")
        return address

    def update_address_by_id(self, address_id: int, updated_address: AddressUpdate, session: Session = Depends(db_session)):
        address = session.get(Address, address_id)
        if not address:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Endereço não encontrado")

        for key, value in updated_address.dict(exclude_unset=True).items():
            setattr(address, key, value)

        address.updated_at = datetime.now(timezone.utc)
        session.add(address)

        session.commit()
        session.refresh(address)
        return address

    def delete_address_by_id(self, address_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(db_session)):
        is_admin(current_user)
        address = session.get(Address, address_id)
        if not address:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Endereço não encontrado")
        
        session.delete(address)
        session.commit()
        return {"message": "Endereço deletado com sucesso!"}
