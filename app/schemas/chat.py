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