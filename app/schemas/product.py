from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field

class ProductBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    price: Optional[float] = None
    stock: Optional[int] = None
    image: Optional[str] = None
    tags: Optional[List[dict]] = None
    rating: Optional[float] = 0.0
    reviews_count: Optional[int] = 0
    size: Optional[List[str]] = None  
    selected_flavors: Optional[List[str]] = None
    prices_by_size: Optional[Dict[str, float]] = None  
    old_prices_by_size: Optional[Dict[str, float]] = None  
    attributes: Optional[Dict[str, List[str]]] = None
    is_active: bool = True
    is_promotion: Optional[bool] = True
    promotion_discount_percentage: Optional[float] = None
    promotion_start_at: Optional[datetime] = None
    promotion_end_at: Optional[datetime] = None
    category_id: Optional[int] = None
    company_id: Optional[int] = None
    type: Optional[str] = "geral"
    deactivated_by_category: Optional[bool] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    price: Optional[float] = None
    stock: Optional[int] = None
    image: Optional[str] = None
    tags: Optional[List[dict]] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    size: Optional[List[str]] = None
    selected_flavors: Optional[List[str]] = None
    prices_by_size: Optional[Dict[str, float]] = None
    old_prices_by_size: Optional[Dict[str, float]] = None 
    is_promotion: Optional[bool] = True
    promotion_discount_percentage: Optional[float] = None
    promotion_start_at: Optional[datetime] = None
    promotion_end_at: Optional[datetime] = None
    attributes: Optional[Dict[str, List[str]]] = None
    is_active: Optional[bool] = None
    category_id: Optional[int] = None
    company_id: Optional[int] = None
    type: Optional[str] = None
    deactivated_by_category: Optional[bool] = None

class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    prices_by_size: Optional[Dict[str, float]] = None
    old_prices_by_size: Optional[Dict[str, float]] = None 
    deactivated_by_category: Optional[bool] = None

    class Config:
        from_attributes = True
