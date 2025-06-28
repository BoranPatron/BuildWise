from sqlalchemy import Column, DateTime, Integer, String, Boolean, Enum, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from .base import Base


class UserType(enum.Enum):
    PRIVATE = "private"
    PROFESSIONAL = "professional"
    SERVICE_PROVIDER = "service_provider"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    user_type = Column(Enum(UserType), nullable=False, default=UserType.PRIVATE)
    
    # Firmendaten für Dienstleister
    company_name = Column(String, nullable=True)
    company_address = Column(Text, nullable=True)
    company_phone = Column(String, nullable=True)
    company_website = Column(String, nullable=True)
    business_license = Column(String, nullable=True)  # Gewerbeschein
    
    # Profilinformationen
    bio = Column(Text, nullable=True)
    profile_image = Column(String, nullable=True)
    region = Column(String, nullable=True)
    languages = Column(String, nullable=True)  # Komma-getrennte Liste
    
    # Einstellungen
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    two_factor_enabled = Column(Boolean, default=False)
    language_preference = Column(String, default="de")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    projects = relationship("Project", back_populates="owner")
    assigned_tasks = relationship("Task", foreign_keys="Task.assigned_to", back_populates="assigned_user")
    created_tasks = relationship("Task", foreign_keys="Task.created_by", back_populates="creator")
    created_milestones = relationship("Milestone", back_populates="creator")
    uploaded_documents = relationship("Document", back_populates="uploader")
    sent_messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    received_messages = relationship("Message", foreign_keys="Message.recipient_id", back_populates="recipient")
    quotes = relationship("Quote", back_populates="service_provider")
