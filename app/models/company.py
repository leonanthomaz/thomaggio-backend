from datetime import datetime, time, timezone
from typing import List, Optional, Dict
from app.enums.chat_status import ChatbotStatus
from app.enums.company_status import CompanyStatus
from app.models.address import Address
from app.models.product import Product
from app.models.supply import Supply
from app.models.user import User
from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import Column, JSON, ARRAY, Enum, String

class Company(SQLModel, table=True):
    __tablename__ = "tb_company"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    industry: Optional[str] = None
    cnpj: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    contact_email: Optional[str] = None
    logo_url: Optional[str] = None

    opening_time: Optional[time] = None
    closing_time: Optional[time] = None
    working_days: Optional[List[str]] = Field(default=None, sa_column=Column(ARRAY(String)))
    
    social_media_links: Optional[Dict[str, str]] = Field(default=None, sa_column=Column(JSON))
    
    status: CompanyStatus = Field(default=CompanyStatus.OPEN, sa_column=Column(Enum(CompanyStatus), nullable=False))
    chatbot_status: ChatbotStatus = Field(default=ChatbotStatus.ACTIVE, sa_column=Column(Enum(ChatbotStatus), nullable=False))

    users: List["User"] = Relationship(back_populates="company")
    products: List["Product"] = Relationship(back_populates="company")
    supply: List["Supply"] = Relationship(back_populates="company")
    addresses: Optional[List["Address"]] = Relationship(back_populates="company")

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = Field(default=None)
    deleted_at: Optional[datetime] = Field(default=None)

    class Config:
        from_attributes = True
