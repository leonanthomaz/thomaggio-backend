from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from sqlmodel import JSON, Column, SQLModel, Field, Relationship

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.cart import Cart
    from app.models.product import Product

class CartItem(SQLModel, table=True):
    __tablename__ = "tb_cart_item"

    id: Optional[int] = Field(default=None, primary_key=True)
    cart_id: int = Field(foreign_key="tb_cart.id")
    product_id: int = Field(foreign_key="tb_product.id")
    size: Optional[str] = Field(default=None, index=True)
    
    observation: Optional[str] = Field(default=None, max_length=255)

    selected_flavors: Optional[List[Dict[str, Any]]] = Field(default=None, sa_column=Column(JSON))
    options: Optional[Dict[str, float]] = Field(default_factory=dict, sa_column=Column(JSON))
    
    min_flavors: Optional[int] = Field(default=None, description="Minimo de sabores a escolher")
    max_flavors: Optional[int] = Field(default=None, description="Maximo de sabores a escolher")

    flavors_required: bool = Field(default=False, description="Obrigatoriedade de sabores")
    options_required: bool = Field(default=False, description="Obrigatoriedade de opções")
    
    quantity: int = Field(default=1, ge=1)
    unit_price: float = Field(default=0.0, ge=0)

    cart: Optional["Cart"] = Relationship(back_populates="items")
    product: Optional["Product"] = Relationship()

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def subtotal(self) -> float:
        options_total = sum(self.options.values()) if self.options else 0.0
        total_unit_price = self.unit_price + options_total
        return self.quantity * total_unit_price
