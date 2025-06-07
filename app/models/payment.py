from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Column, Enum
from sqlmodel import Field, Relationship, SQLModel

from typing import TYPE_CHECKING

from app.enums.payment_status import PaymentStatus

if TYPE_CHECKING:
    from app.models.order import Order

class Payment(SQLModel, table=True):
    __tablename__ = "tb_payment"

    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="tb_order.id")
    method: str = Field(default="pix")
    amount: float = Field(default=0.0)
    transaction_code: Optional[str] = Field(default=None)
    
    status: PaymentStatus = Field(default=PaymentStatus.PENDING, sa_column=Column(Enum(PaymentStatus), nullable=False))
    
    qr_code: Optional[str] = Field(default=None)

    paid_at: Optional[datetime] = Field(default=None)
    expires_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = Field(default=None)

    order: Optional["Order"] = Relationship()

    class Config:
        from_attributes = True

    @property
    def paid_at_utc(self) -> Optional[datetime]:
        if self.paid_at is None:
            return None
        if self.paid_at.tzinfo is None:
            return self.paid_at.replace(tzinfo=timezone.utc)
        return self.paid_at.astimezone(timezone.utc)

    @property
    def expires_at_utc(self) -> Optional[datetime]:
        if self.expires_at is None:
            return None
        if self.expires_at.tzinfo is None:
            return self.expires_at.replace(tzinfo=timezone.utc)
        return self.expires_at.astimezone(timezone.utc)

    @property
    def created_at_utc(self) -> datetime:
        if self.created_at.tzinfo is None:
            return self.created_at.replace(tzinfo=timezone.utc)
        return self.created_at.astimezone(timezone.utc)

    @property
    def updated_at_utc(self) -> Optional[datetime]:
        if self.updated_at is None:
            return None
        if self.updated_at.tzinfo is None:
            return self.updated_at.replace(tzinfo=timezone.utc)
        return self.updated_at.astimezone(timezone.utc)

    
    class Config:
        from_attributes = True
