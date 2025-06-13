from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, conint

from app.models.product.product import Product


class CartItemBase(BaseModel):
    product_id: int
    quantity: conint(ge=1) = 1 # type: ignore
    size: str
    selected_flavors: Optional[List[Dict[str, Any]]] = None
    observation: Optional[str] = None
    options: Optional[Dict[str, float]] = None
    
class CartItemCreate(CartItemBase):
    pass


class CartItemUpdate(BaseModel):
    quantity: conint(ge=1)
    size: Optional[str]
    selected_flavors: Optional[List[Dict[str, Any]]] = None
    observation: Optional[str] = None
    options: Optional[Dict[str, float]] = None

class CartItemRead(CartItemBase):
    id: int
    product: Product
    unit_price: float
    subtotal: float
    created_at: datetime
    observation: Optional[str] = None
    options: Optional[Dict[str, float]] = None
    
    class Config:
        orm_mode = True
