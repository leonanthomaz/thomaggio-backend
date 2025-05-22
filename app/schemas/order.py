from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from app.models.address import Address
from app.schemas.address import AddressCreate, AddressRead
from app.schemas.user import UserResponse  # Caso queira embutir o user no retorno (opcional)
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
    observation: Optional[str] = None


class OrderItemRead(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: float
    total_price: float
    size: Optional[str]
    observation: Optional[str]
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
    cart_code: Optional[str] = None  # Para pedidos de carrinho (opcional)


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

    class Config:
        from_attributes = True
