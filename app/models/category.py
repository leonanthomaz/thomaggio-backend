from datetime import datetime, timezone
from typing import Optional, List
from sqlmodel import Field, Relationship, SQLModel

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.product import Product

class Category(SQLModel, table=True):
    __tablename__ = "tb_category"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True) 
    description: Optional[str] = None 
    
    is_active: bool = Field(default=True)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = Field(default=None)
    deleted_at: Optional[datetime] = Field(default=None)

    products: List["Product"] = Relationship(back_populates="category")

    class Config:
        from_attributes = True
