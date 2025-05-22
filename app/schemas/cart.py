from typing import Optional, List
from datetime import datetime
from app.enums.cart import CartStatus
from pydantic import BaseModel

from app.schemas.cart_item import CartItemRead


class CartBase(BaseModel):
    whatsapp_id: Optional[str] = None


class CartCreate(CartBase):
    pass


class CartUpdate(CartBase):
    status: Optional[CartStatus] = None


class CartRead(CartBase):
    id: int
    code: str
    total: float
    total_items: int
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
