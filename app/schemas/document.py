from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from ..models.document import DocumentType


class DocumentBase(BaseModel):
    title: str
    description: Optional[str] = None
    document_type: DocumentType = DocumentType.OTHER
    project_id: int
    file_name: str
    file_path: str
    file_size: int
    mime_type: str
    version: int = 1
    is_latest: bool = True
    tags: Optional[str] = None
    category: Optional[str] = None
    is_public: bool = True
    is_encrypted: bool = False

    class Config:
        orm_mode = True


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    document_type: Optional[DocumentType] = None
    tags: Optional[str] = None
    category: Optional[str] = None
    is_public: Optional[bool] = None

    class Config:
        orm_mode = True


class DocumentRead(DocumentBase):
    id: int
    uploaded_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class DocumentUpload(BaseModel):
    title: str
    description: Optional[str] = None
    document_type: DocumentType = DocumentType.OTHER
    project_id: int
    tags: Optional[str] = None
    category: Optional[str] = None
    is_public: bool = True

    class Config:
        orm_mode = True 