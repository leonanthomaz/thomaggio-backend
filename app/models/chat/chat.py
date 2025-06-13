from sqlalchemy import Column, UniqueConstraint, Enum
from sqlmodel import SQLModel, Field, JSON
from typing import  Optional, Dict
from datetime import datetime, timezone

from app.enums.chat_step import ChatStep

class Chat(SQLModel, table=True):
    __tablename__ = "tb_chat"
    __table_args__ = (
        UniqueConstraint("whatsapp_id", "cart_code", name="uix_whatsapp_cart"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    whatsapp_id: Optional[str] = Field(default=None, index=True)
    phone: Optional[str] = Field(default=None, index=True)
    cart_code: Optional[str] = Field(default=None, index=True)

    # Controle de etapas
    step: ChatStep = Field(default=ChatStep.INICIO, sa_column=Column(Enum(ChatStep), nullable=False))
        
    # Controle de atendimento
    human_attendance: Optional[bool] = Field(default=False, index=True)
    
    interaction_count: Optional[int] = Field(default=0)
    max_interaction: Optional[int] = Field(default=20)
    last_interaction_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Estado do fluxo (pode conter carrinho, escolhas, etc)
    context_json: Optional[Dict] = Field(default={}, sa_column=Column(JSON, nullable=False))
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None

