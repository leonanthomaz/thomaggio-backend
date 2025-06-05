from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Relationship, Field

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.company import Company

class Supply(SQLModel, table=True):
    __tablename__ = "tb_supply"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None 
    quantity: float = 0
    unit: str
    type: str
    min_quantity: Optional[float] = 0 
    unit_price: Optional[float] = 0.0 

    company_id: int = Field(foreign_key="tb_company.id")
    company: Optional["Company"] = Relationship(back_populates="supply")

    is_active: bool = Field(default=True) 
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = Field(default=None)
    deleted_at: Optional[datetime] = Field(default=None)

    class Config:
        from_attributes = True
