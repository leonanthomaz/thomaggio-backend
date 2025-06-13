from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel


class PromoCodeCreate(SQLModel):
    code: str
    description: Optional[str] = None
    discount_percentage: float
    is_active: Optional[bool] = True 
    valid_from: datetime
    valid_until: datetime
    max_uses: Optional[int] = None
    min_order_value: Optional[float] = None

    
class PromoCodeUpdate(SQLModel):
    code: Optional[str]
    description: Optional[str]
    discount_percentage: Optional[float]
    is_active: Optional[bool]
    valid_from: Optional[datetime]
    valid_until: Optional[datetime]
    max_uses: Optional[int]
    min_order_value: Optional[float]

class PromoCodeResponse(SQLModel):
    id: int
    code: str
    description: Optional[str]
    discount_percentage: float
    is_active: bool
    valid_from: datetime
    valid_until: datetime
    max_uses: Optional[int]
    current_uses: int
    min_order_value: Optional[float]
    created_at: datetime
    updated_at: datetime


