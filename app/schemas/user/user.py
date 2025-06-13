# app/schemas/user.py

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.schemas.company.address import AddressCreate, AddressRead, AddressUpdate

class UserBase(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None

class UserCreate(UserBase):
    username: Optional[str] = None
    password: Optional[str] = None
    company_id: Optional[int] = None
    role: Optional[str] = None
    is_admin: Optional[bool] = None
    addresses: List[AddressCreate] = []
    
class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    addresses: Optional[List[AddressUpdate]] = None


class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    is_admin: bool
    addresses: List[AddressRead] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
