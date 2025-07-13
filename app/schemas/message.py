from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from ..models.message import MessageType


class MessageBase(BaseModel):
    content: str
    sender_id: int
    recipient_id: Optional[int] = None
    message_type: MessageType = MessageType.TEXT
    project_id: int


class MessageCreate(MessageBase):
    pass


class MessageUpdate(BaseModel):
    content: Optional[str] = None
    message_type: Optional[MessageType] = None
    is_read: Optional[bool] = None


class MessageRead(MessageBase):
    id: int
    is_read: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageSummary(BaseModel):
    id: int
    content: str
    message_type: MessageType
    is_read: bool
    created_at: datetime
    sender: Optional[dict] = None
    recipient: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


class ChatRoom(BaseModel):
    id: int
    name: str
    project_id: int
    message_count: int
    last_message_at: Optional[datetime] = None
    participants: list[dict]

    model_config = ConfigDict(from_attributes=True) 