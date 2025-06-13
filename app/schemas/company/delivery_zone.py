from typing import Optional
from sqlmodel import SQLModel

class DeliveryZoneBase(SQLModel):
    name: str
    price: float
    lat: float
    lng: float
    cep: str

class DeliveryZoneCreate(DeliveryZoneBase):
    config_id: int

class DeliveryZoneRead(DeliveryZoneBase):
    id: int
    config_id: int

class DeliveryZoneUpdate(SQLModel):
    name: Optional[str] = None
    price: Optional[float] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    cep: str
