from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CommentBase(BaseModel):
    content: str
    page_number: Optional[int] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None

class CommentCreate(CommentBase):
    document_id: int

class CommentUpdate(BaseModel):
    content: Optional[str] = None

class CommentInDB(CommentBase):
    id: int
    document_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Comment(CommentInDB):
    user_name: str  # Wird durch Join mit User-Tabelle gefüllt

    class Config:
        from_attributes = True 