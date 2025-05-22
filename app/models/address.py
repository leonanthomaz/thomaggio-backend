from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.company import Company

class Address(SQLModel, table=True):
    __tablename__ = "tb_address"

    id: Optional[int] = Field(default=None, primary_key=True)

    street: str  # Obrigatório
    number: str  # Obrigatório
    complement: str
    neighborhood: str
    zip_code: str
    city: Optional[str] = None
    state: Optional[str] = None
    reference: Optional[str] = None

    is_company_address: bool = Field(default=False)

    user_id: Optional[int] = Field(default=None, foreign_key="tb_user.id")
    user: Optional["User"] = Relationship(back_populates="addresses")

    company_id: Optional[int] = Field(default=None, foreign_key="tb_company.id")
    company: Optional["Company"] = Relationship(back_populates="addresses")

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        orm_mode = True
