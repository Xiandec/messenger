from typing import List, Optional
from pydantic import BaseModel, UUID4
from enum import Enum
from datetime import datetime

from app.schemas.user import UserResponse

class ChatType(str, Enum):
    PERSONAL = "personal"
    GROUP = "group"

class ChatBase(BaseModel):
    name: Optional[str] = None
    type: ChatType

class ChatCreate(ChatBase):
    member_ids: List[UUID4]

class GroupChatCreate(ChatBase):
    name: str
    type: ChatType = ChatType.GROUP
    member_ids: List[UUID4]

class ChatResponse(ChatBase):
    id: UUID4
    members: List[UserResponse]
    
    class Config:
        orm_mode = True

class LastMessageInfo(BaseModel):
    id: UUID4
    sender_id: UUID4
    sender_name: str
    text: str
    timestamp: datetime
    is_read: bool

class ChatWithLastMessageResponse(ChatResponse):
    last_message: Optional[LastMessageInfo] = None
    unread_count: int = 0
    
    class Config:
        orm_mode = True 