from datetime import datetime, timezone
from typing import List, Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.company.company import Company
    from app.models.user.address import Address
    from app.models.order.order import Order

class User(SQLModel, table=True):
    __tablename__ = "tb_user"

    id: Optional[int] = Field(default=None, primary_key=True)

    name: Optional[str] = Field(default=None)
    username: Optional[str] = Field(default=None)
    password_hash: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)
    phone: Optional[str] = Field(default=None)

    role: str = Field(default="customer")
    
    is_admin: bool = Field(default=False)
    is_active: bool = Field(default=True)
    last_login: Optional[datetime] = None
    token_password_reset: Optional[str] = Field(default=None)

    company_id: Optional[int] = Field(default=None, foreign_key="tb_company.id")
    company: Optional["Company"] = Relationship(back_populates="users")

    orders: List["Order"] = Relationship(back_populates="user")
    addresses: List["Address"] = Relationship(back_populates="user")

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = Field(default=None)

    class Config:
        orm_mode = True
