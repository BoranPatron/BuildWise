from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from .base import Base


class DocumentType(enum.Enum):
    PLAN = "plan"
    PERMIT = "permit"
    QUOTE = "quote"
    INVOICE = "invoice"
    CONTRACT = "contract"
    PHOTO = "photo"
    OTHER = "other"


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    document_type = Column(Enum(DocumentType), nullable=False, default=DocumentType.OTHER)
    
    # Dateiinformationen
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)  # in Bytes
    mime_type = Column(String, nullable=False)
    
    # Versionierung
    version = Column(Integer, default=1)
    is_latest = Column(Boolean, default=True)
    parent_document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    
    # Metadaten
    tags = Column(String, nullable=True)  # Komma-getrennte Tags
    category = Column(String, nullable=True)
    
    # Sicherheit
    is_public = Column(Boolean, default=False)
    is_encrypted = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="documents")
    uploader = relationship("User")
    parent_document = relationship("Document", remote_side=[id])
    versions = relationship("Document", back_populates="parent_document") 