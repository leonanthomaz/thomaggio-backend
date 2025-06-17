from typing import Optional, List
from datetime import datetime, timezone
from app.enums.cart import CartStatus
from sqlmodel import SQLModel, Field, Relationship
import uuid

from app.core.utils.hash_utils import generate_hash

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.cart.cart_item import CartItem

CART_CODE_HASH_LENGTH = 10

def generate_cart_code() -> str:
    timestamp = datetime.now(timezone.utc).isoformat()
    raw = f"{timestamp}-{uuid.uuid4()}"
    return generate_hash(raw)[:CART_CODE_HASH_LENGTH]

class Cart(SQLModel, table=True):
    __tablename__ = "tb_cart"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(default_factory=generate_cart_code, index=True, unique=True)
    whatsapp_id: Optional[str] = Field(default=None, index=True)
    
    status: CartStatus = Field(default=CartStatus.ACTIVE)

    items: List["CartItem"] = Relationship(back_populates="cart")
    
    promo_code: Optional[str] = Field(default=None)
    promo_discount_percentage: Optional[float] = Field(default=None)
    promo_discount_value: Optional[float] = Field(default=None)
    promo_applied_at: Optional[datetime] = Field(default=None)
        
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    
    delivery_fee: Optional[float] = None
    delivery_neighborhood: Optional[str] = None
    
    
    @property
    def total(self) -> float:
        return sum(item.subtotal for item in self.items or [])
    
    @property
    def total_with_discount(self) -> float:
        discount = self.promo_discount_value or 0
        return max(self.total - discount, 0)

    @property
    def total_items(self) -> int:
        return sum(item.quantity for item in self.items or [])
