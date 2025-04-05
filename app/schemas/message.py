from typing import Optional, List
from pydantic import BaseModel, UUID4
from datetime import datetime

from app.schemas.user import UserResponse

class MessageBase(BaseModel):
    text: str

class MessageCreate(MessageBase):
    chat_id: UUID4

class MessageResponse(MessageBase):
    id: UUID4
    chat_id: UUID4
    sender_id: UUID4
    sender: UserResponse
    timestamp: datetime
    is_read: bool
    
    class Config:
        orm_mode = True

class ChatHistoryParams(BaseModel):
    limit: Optional[int] = 100
    offset: Optional[int] = 0

class ChatHistoryResponse(BaseModel):
    messages: List[MessageResponse]
    total: int 