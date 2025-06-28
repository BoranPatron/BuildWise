from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from ..models.message import MessageType


class MessageBase(BaseModel):
    message_type: MessageType = MessageType.TEXT
    content: str
    document_id: Optional[int] = None


class MessageCreate(MessageBase):
    project_id: int
    recipient_id: Optional[int] = None


class MessageRead(MessageBase):
    id: int
    project_id: int
    sender_id: int
    recipient_id: Optional[int] = None
    is_read: bool
    read_at: Optional[datetime] = None
    is_system_message: bool
    is_encrypted: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class MessageSummary(BaseModel):
    id: int
    message_type: MessageType
    content: str
    sender_id: int
    is_read: bool
    created_at: datetime

    class Config:
        orm_mode = True


class ChatRoom(BaseModel):
    project_id: int
    messages: list[MessageRead]
    unread_count: int 