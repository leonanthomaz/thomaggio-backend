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
    size: Optional[List[str]] = None  # Lista de tamanhos válidos
    selected_flavors: Optional[List[str]] = None
    prices_by_size: Optional[Dict[str, float]] = None  # Preço por tamanho
    attributes: Optional[Dict[str, List[str]]] = None
    is_active: bool = True
    category_id: Optional[int] = None
    company_id: Optional[int] = None
    type: Optional[str] = "geral"

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
    attributes: Optional[Dict[str, List[str]]] = None
    is_active: Optional[bool] = None
    category_id: Optional[int] = None
    company_id: Optional[int] = None
    type: Optional[str] = None

class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    prices_by_size: Optional[Dict[str, float]] = None  # Incluído na response também

    class Config:
        from_attributes = True
