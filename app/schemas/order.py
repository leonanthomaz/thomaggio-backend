from datetime import datetime
from typing import Any, Dict, Optional, List
from app.enums.payment_status import PaymentStatus
from pydantic import BaseModel, Field, validator
from app.models.address import Address
from app.schemas.address import AddressRead
from app.models.order import OrderStatus  # ou de onde você declarou esse Enum

# --- CUSTOMER (cache opcional no pedido) ---
class CustomerCreate(BaseModel):
    name: str
    phone: str


# --- ORDER ITEM ---
class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int
    unit_price: float
    total_price: float
    size: Optional[str] = None
    selected_flavors: Optional[List[Dict[str, Any]]] = None
    observation: Optional[str] = None
    
    @validator('selected_flavors')
    def validate_flavors(cls, v):
        if v is not None:
            for flavor in v:
                if not isinstance(flavor, dict):
                    raise ValueError("Cada sabor deve ser um dicionário")
                if 'name' not in flavor or 'quantity' not in flavor:
                    raise ValueError("Cada sabor deve ter 'name' e 'quantity'")
        return v


class OrderItemRead(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: float
    total_price: float
    size: Optional[str]
    observation: Optional[str]
    selected_flavors: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Lista de sabores selecionados com suas quantidades"
    )
    created_at: datetime

    class Config:
        from_attributes = True


# --- ORDER CREATE ---
class OrderCreate(BaseModel):
    customer: CustomerCreate
    address: Address
    items: List[OrderItemCreate]
    payment_method: str
    delivery_fee: float
    total_amount: float
    table_number: Optional[int] = None
    whatsapp_id: Optional[str] = None
    cart_code: Optional[str] = None
    cash_change_for: Optional[float] = None
    cash_amount_given: Optional[float] = None
    promo_code: Optional[str] = None
    is_whatsapp: Optional[bool] = None
    privacy_policy_version: Optional[str]
    privacy_policy_accepted_at: datetime

# --- ORDER UPDATE ---
class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    delivery_address_id: Optional[int] = None
    payment_method: Optional[str] = None
    customer_name: Optional[str] = None
    phone: Optional[str] = None
    table_number: Optional[int] = None
    whatsapp_id: Optional[str] = None
    updated_at: Optional[datetime] = None
    cash_change_for: Optional[float] = None
    promo_code: Optional[str] = None
    
class StatusUpdateRequest(BaseModel):
    status: OrderStatus


# --- ORDER READ ---
class OrderRead(BaseModel):
    id: int
    code: str
    user_id: int
    customer_name: Optional[str]
    phone: Optional[str]
    whatsapp_id: Optional[str]
    delivery_address: Optional[AddressRead]
    status: OrderStatus
    table_number: Optional[int]
    payment_method: str
    delivery_fee: float
    total_amount: float
    items: List[OrderItemRead]
    created_at: datetime
    updated_at: Optional[datetime]
    cash_change_for: Optional[float] = None
    promo_code: Optional[str] = None
    is_whatsapp: Optional[bool] = None
    privacy_policy_version: Optional[str]
    privacy_policy_accepted_at: Optional[datetime]

    
    class Config:
        from_attributes = True
