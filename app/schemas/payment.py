# app/schemas/payment.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.enums.payment_status import PaymentStatus

class PaymentRequest(BaseModel):
    order_id: int
    amount: float
    method: str = "pix"
    token: Optional[str] = None  # Token do cartão, gerado no frontend
    payment_method_id: Optional[str] = None  # "visa", "master", etc.
    installments: Optional[int] = 1  # Parcelas, default 1
    document_number: Optional[str] = None  # CPF do pagador    
    qr_code: Optional[str] = None

class PaymentResponse(BaseModel):
    id: int
    order_id: int
    method: str
    amount: float
    status: PaymentStatus
    transaction_code: Optional[str]
    paid_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    qr_code: Optional[str]

    class Config:
        orm_mode = True  # Permite retornar direto models do SQLModel
