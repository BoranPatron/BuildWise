from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from ..models.message import MessageType


class MessageBase(BaseModel):
    content: str
    sender_id: int
    recipient_id: Optional[int] = None
    message_type: MessageType = MessageType.TEXT
    is_read: bool = False
    project_id: int

    class Config:
        orm_mode = True


class MessageCreate(MessageBase):
    pass


class MessageUpdate(BaseModel):
    content: Optional[str] = None
    is_read: Optional[bool] = None

    class Config:
        orm_mode = True


class MessageRead(MessageBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class MessageWithSender(MessageRead):
    sender: dict
    recipient: Optional[dict] = None

    class Config:
        orm_mode = True 