

from typing import Optional

from pydantic import BaseModel
from app.enums.chat_status import ChatbotStatus


class StatusResponse(BaseModel):
    current_status: ChatbotStatus
    message: Optional[str] = None
    
    
class ChatbotStatusUpdate(BaseModel):
    new_status: ChatbotStatus