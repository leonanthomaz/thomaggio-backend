from typing import Optional, List
from sqlmodel import SQLModel
from .delivery_zone import DeliveryZoneRead  # importa o read das zonas

class DeliveryConfigBase(SQLModel):
    cep: str
    central_point_lat: float
    central_point_lng: float
    radius: float
    default_delivery_fee: Optional[float] = 0.0

class DeliveryConfigCreate(DeliveryConfigBase):
    pass

class DeliveryConfigRead(DeliveryConfigBase):
    id: int
    zones: Optional[List[DeliveryZoneRead]] = []

class DeliveryConfigUpdate(SQLModel):
    cep: Optional[str] = None
    central_point_lat: Optional[float] = None
    central_point_lng: Optional[float] = None
    radius: Optional[float] = None
    default_delivery_fee: Optional[float] = None
