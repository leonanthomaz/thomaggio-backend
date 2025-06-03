from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlmodel import JSON, Column, Field, Relationship, SQLModel

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.product import Product

class OrderItem(SQLModel, table=True):
    __tablename__ = "tb_order_item"

    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="tb_order.id")
    product_id: int = Field(foreign_key="tb_product.id")
    quantity: int = Field(default=1)
    unit_price: float = Field(default=0.0)
    total_price: float = Field(default=0.0)
    
    size: Optional[str] = None
    observation: Optional[str] = None
    
    selected_flavors: Optional[List[Dict[str, Any]]] = Field(default=None, sa_column=Column(JSON(none_as_null=True)))
    options: Optional[Dict[str, float]] = Field(default_factory=dict, sa_column=Column(JSON))

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = Field(default=None)
    deleted_at: Optional[datetime] = Field(default=None)

    order: "Order" = Relationship(back_populates="items")
    product: Optional["Product"] = Relationship()

    class Config:
        from_attributes = True
