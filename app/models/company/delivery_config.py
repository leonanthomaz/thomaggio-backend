from datetime import datetime, timezone
from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.company.delivery_zone import DeliveryZone

class DeliveryConfig(SQLModel, table=True):
    __tablename__ = "tb_delivery_config"

    id: Optional[int] = Field(default=None, primary_key=True)
    cep: str
    central_point_lat: float
    central_point_lng: float
    radius: float
    default_delivery_fee: Optional[float] = 0.0

    zones: List["DeliveryZone"] = Relationship(back_populates="config")

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = Field(default=None)
    deleted_at: Optional[datetime] = Field(default=None)

    class Config:
        from_attributes = True
