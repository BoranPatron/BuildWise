from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from ..models.document import DocumentType


class DocumentBase(BaseModel):
    title: str
    description: Optional[str] = None
    document_type: DocumentType = DocumentType.OTHER
    tags: Optional[str] = None
    category: Optional[str] = None
    is_public: bool = False


class DocumentCreate(DocumentBase):
    project_id: int
    file_name: str
    file_path: str
    file_size: int
    mime_type: str


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    document_type: Optional[DocumentType] = None
    tags: Optional[str] = None
    category: Optional[str] = None
    is_public: Optional[bool] = None


class DocumentRead(DocumentBase):
    id: int
    project_id: int
    uploaded_by: int
    file_name: str
    file_path: str
    file_size: int
    mime_type: str
    version: int
    is_latest: bool
    parent_document_id: Optional[int] = None
    is_encrypted: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class DocumentSummary(BaseModel):
    id: int
    title: str
    document_type: DocumentType
    file_name: str
    file_size: int
    mime_type: str
    created_at: datetime

    class Config:
        orm_mode = True


class DocumentUpload(BaseModel):
    title: str
    description: Optional[str] = None
    document_type: DocumentType = DocumentType.OTHER
    tags: Optional[str] = None
    category: Optional[str] = None
    is_public: bool = False 