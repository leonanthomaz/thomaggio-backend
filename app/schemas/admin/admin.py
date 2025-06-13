from typing import Optional, List
from pydantic import BaseModel
from app.schemas.company.address import AddressCreate

class AdminUserUpdate(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    is_admin: Optional[bool] = None
    addresses: Optional[List[AddressCreate]] = None
