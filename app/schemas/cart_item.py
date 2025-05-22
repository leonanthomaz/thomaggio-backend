from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, conint

from app.models.product import Product


class CartItemBase(BaseModel):
    product_id: int
    quantity: conint(ge=1) = 1 # type: ignore
    size: str
    selected_flavors: Optional[List[str]] = None  # aqui!
    observation: Optional[str] = None  # novo campo

class CartItemCreate(CartItemBase):
    pass


class CartItemUpdate(BaseModel):
    quantity: conint(ge=1) # type: ignore
    observation: Optional[str] = None  # se quiser permitir atualizar observação também


class CartItemRead(CartItemBase):
    id: int
    product: Product
    unit_price: float
    subtotal: float
    created_at: datetime

    class Config:
        orm_mode = True
