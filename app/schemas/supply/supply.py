from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class SupplyBase(BaseModel):
    name: str
    description: Optional[str] = None
    quantity: float
    unit: str
    type: str
    min_quantity: Optional[float] = 0
    unit_price: Optional[float] = 0.0
    is_active: Optional[bool] = True


class SupplyCreate(SupplyBase):
    company_id: int


class SupplyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    type: Optional[str] = None
    min_quantity: Optional[float] = None
    unit_price: Optional[float] = None
    is_active: Optional[bool] = None


class SupplyRead(BaseModel):
    id: int
    name: str
    description: Optional[str]
    quantity: float
    unit: str
    type: str
    min_quantity: Optional[float]
    unit_price: Optional[float]
    is_active: bool
    company_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    class Config:
        orm_mode = True

