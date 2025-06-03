from datetime import time, datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field

from app.enums.chat_status import ChatbotStatus
from app.enums.company_status import CompanyStatus
from app.schemas.address import AddressUpdate

class CompanyBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    industry: Optional[str] = Field(None, max_length=255)
    business_type: Optional[str] = Field(None, max_length=255)
    cnpj: Optional[str] = Field(None, max_length=20)
    phone: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = Field(None, max_length=255)
    contact_email: Optional[str] = Field(None, max_length=255)
    logo_url: Optional[str] = Field(None, max_length=500)
    
    addresses: Optional[List[Dict]] = Field(default_factory=list)
    opening_time: Optional[time] = None
    closing_time: Optional[time] = None
    working_days: Optional[List[str]] = None
    social_media_links: Optional[Dict[str, str]] = None
    
    chatbot_status: ChatbotStatus = Field(default=ChatbotStatus.ACTIVE)
    status: CompanyStatus = Field(default=CompanyStatus.OPEN)

class CompanyRequest(CompanyBase):
    pass

class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    industry: Optional[str] = Field(None, max_length=255)
    business_type: Optional[str] = Field(None, max_length=255)
    cnpj: Optional[str] = Field(None, max_length=20)
    phone: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = Field(None, max_length=255)
    contact_email: Optional[str] = Field(None, max_length=255)
    logo_url: Optional[str] = Field(None, max_length=500)

    addresses: Optional[List[AddressUpdate]] = Field(default_factory=list)
    
    opening_time: Optional[time] = None
    closing_time: Optional[time] = None
    working_days: Optional[List[str]] = None
    social_media_links: Optional[Dict[str, str]] = None

    chatbot_status: Optional[ChatbotStatus] = Field(default=None)
    status: Optional[CompanyStatus] = Field(default=None)
    updated_at: Optional[datetime] = None


class CompanyPublicInfo(CompanyBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

class CompanyStatusUpdate(BaseModel):
    new_status: CompanyStatus
    
class CompanyStatusResponse(BaseModel):
    current_status: CompanyStatus
    message: Optional[str] = None