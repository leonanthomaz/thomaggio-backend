from typing import Optional
from pydantic import BaseModel

class AuthCredentials(BaseModel):
    username: str
    password: str
    
class AuthRequestUpdate(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    is_admin: Optional[bool] = None
    company_id: Optional[int] = None
    password: Optional[str] = None
    
class AuthRequestCreate(BaseModel):
    name: str
    username: str
    email: str
    password: str
    company_id: Optional[int] = None
    is_admin: bool
    
class EmailResetRequest(BaseModel):
    email: str
    
class PasswordResetRequest(BaseModel):
    token: str
    password: str
    
class Token(BaseModel):
    token: str