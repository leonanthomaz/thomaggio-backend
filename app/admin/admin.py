from datetime import datetime, timedelta, timezone
import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Dict, Any

from app.core.middlewares.users import is_admin
from app.models.user.address import Address
from app.models.user.user import User
from app.schemas.user.user import UserCreate, UserResponse, UserUpdate
from app.auth.auth import AuthRouter
from app.database.connection import get_session

get_current_user = AuthRouter().get_current_user

class AdminRouter(APIRouter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_api_route("/admin/users", self.get_all_users, methods=["GET"], response_model=List[UserResponse])
        self.add_api_route("/admin/users", self.create_user, methods=["POST"], response_model=UserResponse)
        self.add_api_route("/admin/recent-users", self.get_recent_users, methods=["GET"], response_model=Dict[str, List[UserResponse]])
        self.add_api_route("/admin/users/{user_id}", self.update_user_by_id, methods=["PUT"], response_model=UserResponse)
        self.add_api_route("/admin/users/{user_id}", self.delete_user_by_id, methods=["DELETE"], response_model=Dict[str, Any])

    async def get_all_users(self, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
        is_admin(current_user)
        users = session.exec(select(User).where(User.deleted_at == None)).all()
        return [UserResponse.from_orm(user) for user in users]

    async def create_user(self, user_data: UserCreate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
        is_admin(current_user)

        hashed_password = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt())

        db_user = User(
            name=user_data.name,
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_password.decode('utf-8'),
            phone=user_data.phone,
            role=user_data.role or "customer",
            is_admin=user_data.is_admin or False,
        )

        if user_data.addresses:
            for address_data in user_data.addresses:
                already_exists = False
                for existing_address in db_user.addresses:
                    if self.is_same_address(existing_address, address_data):
                        already_exists = True
                        break

                if not already_exists:
                    db_address = Address(
                        user_id=db_user.id,
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
                    db_user.addresses.append(db_address)

        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return UserResponse.from_orm(db_user)

    async def update_user_by_id(self, user_id: int, user_data: UserUpdate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
        is_admin(current_user)
        db_user = session.get(User, user_id)
        if not db_user or db_user.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")

        if user_data.password:
            hashed_password = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt())
            db_user.password_hash = hashed_password.decode('utf-8')

        for key, value in user_data.dict(exclude_unset=True, exclude={"password", "addresses"}).items():
            setattr(db_user, key, value)

        for address_data in user_data.addresses:
            if address_data.id:
                existing_address = next((a for a in db_user.addresses if a.id == address_data.id), None)
                if existing_address:
                    for field, value in address_data.dict(exclude_unset=True).items():
                        setattr(existing_address, field, value)
                else:
                    # endereço com id mas não encontrado — ignora ou adiciona
                    pass
            else:
                new_address = Address(**address_data.dict())
                db_user.addresses.append(new_address)


        db_user.updated_at = datetime.now(timezone.utc)

        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return UserResponse.from_orm(db_user)

    async def delete_user_by_id(self, user_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
        is_admin(current_user)
        db_user = session.get(User, user_id)
        if not db_user or db_user.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")

        db_user.deleted_at = datetime.now(timezone.utc)
        session.add(db_user)
        session.commit()
        return {"ok": True, "message": "Usuário deletado com sucesso"}

    async def get_recent_users(self, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
        is_admin(current_user)
        now = datetime.now(timezone.utc)
        start_of_week = now - timedelta(days=now.weekday())
        start_of_month = now.replace(day=1)

        recent_users_week = session.exec(
            select(User).where(User.created_at >= start_of_week, User.deleted_at == None)
        ).all()
        recent_users_month = session.exec(
            select(User).where(User.created_at >= start_of_month, User.deleted_at == None)
        ).all()

        return {
            "week": [UserResponse.from_orm(user) for user in recent_users_week],
            "month": [UserResponse.from_orm(user) for user in recent_users_month],
        }

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
