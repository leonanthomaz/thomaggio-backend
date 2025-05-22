from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Relationship, Field

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.company import Company

class Supply(SQLModel, table=True):
    __tablename__ = "tb_supply"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str  # Nome do insumo
    description: Optional[str] = None  # Ex: Marca, uso, etc.
    quantity: float = 0  # Quantidade atual em estoque
    unit: str  # Unidade de medida (ex: kg, un, ml)
    type: str  # Ex: alimento, limpeza, utensilio, patrimonio
    min_quantity: Optional[float] = 0  # Estoque mínimo antes de alerta
    unit_price: Optional[float] = 0.0  # Preço unitário (pra custo e controle)

    company_id: int = Field(foreign_key="tb_company.id")
    company: Optional["Company"] = Relationship(back_populates="supply")

    is_active: bool = Field(default=True)  # Controle lógico
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = Field(default=None)
    deleted_at: Optional[datetime] = Field(default=None)

    class Config:
        from_attributes = True
