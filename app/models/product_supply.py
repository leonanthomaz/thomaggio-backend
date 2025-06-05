from typing import Optional
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime, timezone

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.supply import Supply

class ProductSupply(SQLModel, table=True):
    __tablename__ = "tb_product_supply"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    product_id: int = Field(foreign_key="tb_product.id")
    supply_id: int = Field(foreign_key="tb_supply.id")

    quantity: float 
    unit: str  

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = Field(default=None)
    deleted_at: Optional[datetime] = Field(default=None)

    product: Optional["Product"] = Relationship(back_populates="supplies_used")
    supply: Optional["Supply"] = Relationship()
