from datetime import datetime, timezone
from typing import Optional, List, Dict
from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import Column, JSON
from pydantic import field_validator

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.company import Company
    from app.models.product_supply import ProductSupply

class Product(SQLModel, table=True):
    __tablename__ = "tb_product"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    image: Optional[str] = None
    
    size: Optional[List[str]] = Field(default_factory=list, sa_column=Column(JSON))
    prices_by_size: Dict[str, float] = Field(default_factory=dict, sa_column=Column(JSON))
    old_prices_by_size: Optional[Dict[str, float]] = Field(default_factory=dict, sa_column=Column(JSON))
        
    selected_flavors: Optional[List[str]] = Field(default=[], sa_column=Column(JSON))
    
    options: Optional[Dict[str, float]] = Field(default_factory=dict, sa_column=Column(JSON))
    
    min_flavors: Optional[int] = Field(default=None, description="Minimo de sabores a escolher")
    max_flavors: Optional[int] = Field(default=None, description="Maximo de sabores a escolher")

    flavors_required: bool = Field(default=False, description="Obrigatoriedade de sabores")
    options_required: bool = Field(default=False, description="Obrigatoriedade de opções")

    rating: Optional[float] = Field(default=0.0)
    reviews_count: Optional[int] = Field(default=0)
    attributes: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    is_active: bool = Field(default=True)
    
    is_promotion: Optional[bool] = Field(default=False)
    promotion_discount_percentage: Optional[float] = None
    promotion_start_at: Optional[datetime] = None
    promotion_end_at: Optional[datetime] = None

    company_id: Optional[int] = Field(default=None, foreign_key="tb_company.id")
    company: Optional["Company"] = Relationship(back_populates="products")
    supplies_used: List["ProductSupply"] = Relationship(back_populates="product")

    category_id: Optional[int] = Field(default=None, foreign_key="tb_category.id")
    category: Optional["Category"] = Relationship(back_populates="products")
    
    types: List[str] = Field(default=[], sa_column=Column(JSON), description="Subtipo do produto")

    tags: Optional[List[dict]] = Field(default=[], sa_column=Column(JSON))
    
    deactivated_by_category: Optional[bool] = Field(default=False)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = Field(default=None)
    deleted_at: Optional[datetime] = Field(default=None)
    
    @property
    def is_promotion_active(self) -> bool:
        now = datetime.now(timezone.utc)
        return self.is_promotion and (
            (self.promotion_start_at is None or self.promotion_start_at <= now) and
            (self.promotion_end_at is None or self.promotion_end_at >= now)
        )
    
    @field_validator("types", pre=True, always=True)
    def set_types_default(cls, v):
        if v is None:
            return []
        return v

    class Config:
        from_attributes = True
