# app/schemas/payment.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.enums.payment_status import PaymentStatus

class PaymentRequest(BaseModel):
    order_id: int
    amount: float
    method: str = "pix"

class PaymentResponse(BaseModel):
    id: int
    order_id: int
    method: str
    amount: float
    status: PaymentStatus
    transaction_code: Optional[str]
    paid_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True
