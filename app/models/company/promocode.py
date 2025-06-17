from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

from datetime import datetime, timezone

class PromoCode(SQLModel, table=True):
    __tablename__ = "tb_promocode"
     
    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(index=True, unique=True, max_length=20)
    description: Optional[str] = Field(default=None, max_length=100)
    discount_percentage: float = Field(gt=0, le=100)
    is_active: bool = Field(default=True)
    valid_from: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    valid_until: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    max_uses: Optional[int] = Field(default=None, gt=0)
    current_uses: int = Field(default=0)
    min_order_value: Optional[float] = Field(default=None, gt=0)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = Field(default=None)

    class Config:
        from_attributes = True
