from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional

# Schema para criação de um ProductSupply
class ProductSupplyCreate(BaseModel):
    product_id: int
    supply_id: int
    quantity: float
    unit: str

    class Config:
        orm_mode = True

# Schema para atualização de um ProductSupply
class ProductSupplyUpdate(BaseModel):
    quantity: Optional[float] = None
    unit: Optional[str] = None

    class Config:
        orm_mode = True

# Schema de leitura detalhada (ProductSupplyRead)
class ProductSupplyRead(BaseModel):
    id: int
    product_id: int
    product_name: str  # Nome do produto (para facilitar a visualização)
    supply_id: int
    supply_name: str  # Nome do insumo (para facilitar a visualização)
    quantity: float
    unit: str
    created_at: datetime

    class Config:
        orm_mode = True


class SupplyInfo(BaseModel):
    id: int
    name: str
    unit_price: Optional[float]
    quantity: float
    unit: str
    cost: float

class ProductWithSuppliesRead(BaseModel):
    id: int
    name: str
    description: Optional[str]
    supplies: List[SupplyInfo]
    total_cost: float

    class Config:
        orm_mode = True
