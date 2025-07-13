from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from ..models.document import DocumentType


class DocumentBase(BaseModel):
    title: str
    description: Optional[str] = None
    document_type: DocumentType = DocumentType.OTHER
    project_id: int
    tags: Optional[str] = None
    category: Optional[str] = None
    is_public: bool = True


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    document_type: Optional[DocumentType] = None
    tags: Optional[str] = None
    category: Optional[str] = None
    is_public: Optional[bool] = None


class DocumentRead(DocumentBase):
    id: int
    uploaded_by: int
    file_name: str
    file_path: str
    file_size: int
    mime_type: str
    version: int
    is_latest: bool
    is_encrypted: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentSummary(BaseModel):
    id: int
    title: str
    document_type: DocumentType
    file_name: str
    file_size: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentUpload(BaseModel):
    file: bytes
    title: str
    description: Optional[str] = None
    document_type: DocumentType = DocumentType.OTHER
    project_id: int
    tags: Optional[str] = None
    category: Optional[str] = None
    is_public: bool = True 