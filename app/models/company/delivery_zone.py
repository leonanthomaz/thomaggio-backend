from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel, Relationship

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.company.delivery_config import DeliveryConfig


class DeliveryZone(SQLModel, table=True):
    __tablename__ = "tb_delivery_zone"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    price: float
    lat: float
    lng: float
    cep: str

    config_id: Optional[int] = Field(default=None, foreign_key="tb_delivery_config.id")
    config: "DeliveryConfig" = Relationship(back_populates="zones")

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = Field(default=None)
    deleted_at: Optional[datetime] = Field(default=None)

    class Config:
        from_attributes = True
