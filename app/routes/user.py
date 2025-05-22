from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database.connection import get_session
from app.models.user import User
from app.models.address import Address
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.schemas.address import AddressCreate

class UserRouter(APIRouter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_api_route("/users/", self.get_all_users, methods=["GET"], response_model=List[UserResponse])
        self.add_api_route("/users/", self.create_user, methods=["POST"], response_model=UserResponse)
        self.add_api_route("/users/{user_id}", self.get_user, methods=["GET"], response_model=UserResponse)
        self.add_api_route("/users/{user_id}", self.update_user, methods=["PUT"], response_model=UserResponse)

    def get_all_users(self, session: Session = Depends(get_session)):
        users = session.exec(select(User)).all()
        return users
    
    def create_user(self, user_data: UserCreate, session: Session = Depends(get_session)):
        # Verifica se usuário já existe
        existing = session.exec(select(User).where(User.phone == user_data.phone)).first()
        if existing:
            raise HTTPException(status_code=400, detail="Usuário com esse telefone já existe.")

        # Cria o usuário
        user = User(
            name=user_data.name,
            username=user_data.username,
            password_hash=user_data.password,  # Nota: Você deve hashear a senha!
            email=user_data.email,
            phone=user_data.phone,
            company_id=user_data.company_id,
            role="customer",
            is_admin=False,
            is_active=True
        )

        # Adiciona endereços
        if user_data.addresses:
            for addr_data in user_data.addresses:
                # Valida os dados do endereço usando o schema
                address_data = AddressCreate(**addr_data.dict())
                address = Address(
                    street=address_data.street,
                    number=address_data.number,
                    neighborhood=address_data.neighborhood,
                    zip_code=address_data.zip_code,
                    complement=address_data.complement,
                    city=address_data.city,
                    state=address_data.state,
                    reference=address_data.reference,
                    user_id=None,  # Será definido automaticamente pelo relacionamento
                    is_company_address=False
                )
                user.addresses.append(address)

        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    def get_user(self, user_id: int, session: Session = Depends(get_session)):
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")
        return user

    def update_user(self, user_id: int, user_data: UserUpdate, session: Session = Depends(get_session)):
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")

        # Atualiza campos básicos
        if user_data.name is not None:
            user.name = user_data.name
        if user_data.phone is not None:
            user.phone = user_data.phone
        if user_data.email is not None:
            user.email = user_data.email

        # Atualiza endereços
        if user_data.addresses is not None:
            # Remove endereços existentes
            for address in user.addresses:
                session.delete(address)
            
            # Adiciona os novos endereços
            for addr_data in user_data.addresses:
                address = Address(
                    street=addr_data.street,
                    number=addr_data.number,
                    neighborhood=addr_data.neighborhood,
                    zip_code=addr_data.zip_code,
                    complement=addr_data.complement,
                    city=addr_data.city,
                    state=addr_data.state,
                    reference=addr_data.reference,
                    user_id=user_id,
                    is_company_address=False
                )
                session.add(address)

        session.add(user)
        session.commit()
        session.refresh(user)
        return user