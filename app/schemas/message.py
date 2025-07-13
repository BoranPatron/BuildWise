from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from ..models.message import MessageType


class MessageBase(BaseModel):
    content: str
    sender_id: int
    recipient_id: Optional[int] = None
    message_type: MessageType = MessageType.TEXT
    project_id: int
    class Config:
        orm_mode = True


class MessageCreate(MessageBase):
    pass


class MessageUpdate(BaseModel):
    content: Optional[str] = None
    message_type: Optional[MessageType] = None
    is_read: Optional[bool] = None
    class Config:
        orm_mode = True


class MessageRead(MessageBase):
    id: int
    is_read: bool
    created_at: datetime
    updated_at: datetime
    class Config:
        orm_mode = True


class MessageSummary(BaseModel):
    id: int
    content: str
    message_type: MessageType
    is_read: bool
    created_at: datetime
    updated_at: datetime
    class Config:
        orm_mode = True


class ChatRoom(BaseModel):
    id: int
    name: str
    project_id: int
    message_count: int
    last_message_at: Optional[datetime] = None
    participants: list[dict]

    model_config = ConfigDict(from_attributes=True) 