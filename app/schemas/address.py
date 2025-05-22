# app/schemas/address.py
from typing import Optional, Annotated
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

class AddressBase(BaseModel):
    street: str = Field(..., min_length=1)
    number: str = Field(..., min_length=1)
    neighborhood: str = Field(..., min_length=1)
    zip_code: str = Field(..., min_length=8, max_length=9)
    complement: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    reference: Optional[str] = None

    @field_validator('zip_code')
    @classmethod
    def validate_zip_code(cls, v: str) -> str:
        cleaned = ''.join(filter(str.isdigit, v))
        if len(cleaned) != 8:
            raise ValueError("CEP deve conter exatamente 8 dígitos")
        return f"{cleaned[:5]}-{cleaned[5:]}"  # Formata com hífen

class AddressCreate(AddressBase):
    user_id: Optional[int] = None
    company_id: Optional[int] = None
    is_company_address: bool = False

class AddressUpdate(BaseModel):
    street: Optional[str] = Field(default=None, min_length=1)
    number: Optional[str] = Field(default=None, min_length=1)
    neighborhood: Optional[str] = Field(default=None, min_length=1)
    zip_code: Optional[str] = Field(default=None, min_length=8, max_length=9)
    complement: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    reference: Optional[str] = None

    @field_validator('zip_code')
    @classmethod
    def validate_optional_zip_code(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = ''.join(filter(str.isdigit, v))
        if len(cleaned) != 8:
            raise ValueError("CEP deve conter exatamente 8 dígitos")
        return f"{cleaned[:5]}-{cleaned[5:]}"

class AddressRead(AddressBase):
    id: int
    city: str  # Garante retorno mesmo se opcional no create
    state: str  # Garante retorno mesmo se opcional no create
    created_at: datetime
    is_company_address: bool

    class Config:
        from_attributes = True  # Substitui o orm_mode=True do Pydantic v1