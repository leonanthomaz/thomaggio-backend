from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from sqlmodel import JSON, Column, SQLModel, Field, Relationship

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.cart.cart import Cart
    from app.models.product.product import Product

class CartItem(SQLModel, table=True):
    __tablename__ = "tb_cart_item"

    id: Optional[int] = Field(default=None, primary_key=True)
    cart_id: int = Field(foreign_key="tb_cart.id")
    product_id: int = Field(foreign_key="tb_product.id")
    size: Optional[str] = Field(default=None, index=True)
    
    observation: Optional[str] = Field(default=None, max_length=255)

    selected_flavors: Optional[List[Dict[str, Any]]] = Field(default=None, sa_column=Column(JSON))
    options: Optional[Dict[str, float]] = Field(default_factory=dict, sa_column=Column(JSON))
    
    quantity: int = Field(default=1, ge=1)
    unit_price: float = Field(default=0.0, ge=0)

    cart: Optional["Cart"] = Relationship(back_populates="items")
    product: Optional["Product"] = Relationship()

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    @property
    def subtotal(self) -> float:
        options_total = sum(self.options.values()) if self.options else 0.0
        total_unit_price = self.unit_price + options_total
        return self.quantity * total_unit_price
