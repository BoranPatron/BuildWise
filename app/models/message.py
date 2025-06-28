from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from .base import Base


class MessageType(enum.Enum):
    TEXT = "text"
    DOCUMENT = "document"
    SYSTEM = "system"
    NOTIFICATION = "notification"


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    recipient_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    
    message_type = Column(Enum(MessageType), nullable=False, default=MessageType.TEXT)
    content = Column(Text, nullable=False)
    
    # Für Dokumente
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    
    # Status
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # Einstellungen
    is_system_message = Column(Boolean, default=False)
    is_encrypted = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project")
    sender = relationship("User", foreign_keys=[sender_id])
    recipient = relationship("User", foreign_keys=[recipient_id])
    document = relationship("Document") 