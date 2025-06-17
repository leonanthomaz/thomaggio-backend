from typing import Optional, List
from datetime import datetime
from app.enums.cart import CartStatus
from pydantic import BaseModel

from app.schemas.cart.cart_item import CartItemRead


class CartBase(BaseModel):
    whatsapp_id: Optional[str] = None


class CartCreate(CartBase):
    pass


class CartUpdate(CartBase):
    status: Optional[CartStatus] = None
    delivery_fee: Optional[float] = None

class CartRead(CartBase):
    id: int
    code: str
    total: float
    total_items: int
    total_with_discount: float
    delivery_fee: Optional[float]
    promo_code: Optional[str]
    promo_discount_percentage: Optional[float]
    promo_discount_value: Optional[float]
    promo_applied_at: Optional[datetime]
    created_at: datetime
    items: List[CartItemRead] = []
    status: str
    
    class Config:
        orm_mode = True


class CartList(BaseModel):
    id: int
    code: str
    total: float
    total_items: int
    created_at: datetime
    status: str
    
    class Config:
        orm_mode = True
