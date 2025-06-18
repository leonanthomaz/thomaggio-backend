from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING
import uuid
from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import Column, Enum

from app.enums.order_status import OrderStatus
from app.enums.payment_status import PaymentStatus
from app.models.user.address import Address
from app.core.utils.hash_utils import generate_hash

if TYPE_CHECKING:
    from app.models.order.order_item import OrderItem
    from app.models.user.user import User
    
ORDER_CODE_HASH_LENGTH = 10

def generate_order_code() -> str:
    timestamp = datetime.now(timezone.utc).isoformat()
    raw = f"{timestamp}-{uuid.uuid4()}"
    return generate_hash(raw)[:ORDER_CODE_HASH_LENGTH]

class Order(SQLModel, table=True):
    __tablename__ = "tb_order"

    id: Optional[int] = Field(default=None, primary_key=True)

    user_id: int = Field(foreign_key="tb_user.id")
    user: "User" = Relationship(back_populates="orders")

    code: str = Field(default_factory=generate_order_code, index=True, unique=True)
    
    customer_name: Optional[str] = None  
    phone: Optional[str] = None        
    whatsapp_id: Optional[str] = None
    is_whatsapp: Optional[bool] = None

    status: OrderStatus = Field(default=OrderStatus.PENDING, sa_column=Column(Enum(OrderStatus), nullable=False))
    
    table_number: Optional[int] = None      
    payment_method: str = Field(default="pix")
    delivery_fee: float = Field(default=0.0)
    total_amount: float = Field(default=0.0)
    total_amount_with_discount: float = Field(default=0.0)

    discount_code: Optional[str] = Field(default=None, index=True)
    discount_percentage: Optional[float] = Field(default=None)
    discount_value: Optional[float] = Field(default=None)
    discount_description: Optional[str] = Field(default=None) 
    
    cash_change_for: Optional[float] = Field(default=None, description="Valor informado pelo cliente para troco se o pagamento for em dinheiro")
    cash_change: Optional[float] = Field(default=None, description="Valor processado de troco")
    payment_status: PaymentStatus = Field(default=PaymentStatus.PENDING, sa_column=Column(Enum(PaymentStatus), nullable=False))
    
    delivery_address_id: Optional[int] = Field(default=None, foreign_key="tb_address.id")
    delivery_address: Optional["Address"] = Relationship()
    
    privacy_policy_version: Optional[str] = None
    privacy_policy_accepted_at: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    items: List["OrderItem"] = Relationship(back_populates="order")
    
    class Config:
        from_attributes = True