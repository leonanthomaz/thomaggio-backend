from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database.connection import get_session
from app.models.user.user import User
from app.models.user.address import Address
from app.schemas.user.user import UserCreate, UserUpdate, UserResponse

class UserRouter(APIRouter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_api_route("/users/", self.create_user, methods=["POST"], response_model=UserResponse)
        self.add_api_route("/users/{user_id}", self.get_user, methods=["GET"], response_model=UserResponse)
        self.add_api_route("/users/{user_id}", self.update_user, methods=["PUT"], response_model=UserResponse)
    
    def create_user(self, user_data: UserCreate, session: Session = Depends(get_session)):
        # Verifica se usuário já existe
        existing = session.exec(select(User).where(User.phone == user_data.phone)).first()
        if existing:
            raise HTTPException(status_code=400, detail="Usuário com esse telefone já existe.")

        # Cria o usuário
        user = User(
            name=user_data.name,
            username=user_data.username,
            password_hash=user_data.password,
            email=user_data.email,
            phone=user_data.phone,
            company_id=user_data.company_id,
            role="customer",
            is_admin=False,
            is_active=True
        )

        # Adiciona endereços
        if user_data.addresses:
            for address_data in user_data.addresses:
                already_exists = False
                for existing_address in existing.addresses:
                    if self.is_same_address(existing_address, address_data):
                        already_exists = True
                        break

                if not already_exists:
                    db_address = Address(
                        user_id=existing.id,
                        street=address_data.street,
                        number=address_data.number,
                        city=address_data.city,
                        state=address_data.state,
                        zip_code=address_data.zip_code,
                        neighborhood=address_data.neighborhood,
                        complement=address_data.complement,
                        reference=address_data.reference,
                        is_company_address=address_data.is_company_address,
                    )
                    existing.addresses.append(db_address)

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
    
    def is_same_address(self, addr1, addr2):
            if hasattr(addr2, "dict"):
                addr2 = addr2.dict()
            return (
                addr1.street == addr2.get("street") and
                addr1.number == addr2.get("number") and
                addr1.city == addr2.get("city") and
                addr1.state == addr2.get("state") and
                addr1.zip_code == addr2.get("zip_code") and
                addr1.neighborhood == addr2.get("neighborhood") and
                (addr1.complement or "") == (addr2.get("complement") or "") and
                (addr1.reference or "") == (addr2.get("reference") or "") and
                addr1.is_company_address == addr2.get("is_company_address")
            )