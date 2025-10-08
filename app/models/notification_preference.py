from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base

class NotificationPreference(Base):
    """
    Benachrichtigungspräferenzen für Dienstleister
    
    Ein Bauträger kann für jeden Kontakt (Dienstleister) festlegen,
    ob und für welche Kategorien dieser Benachrichtigungen erhalten soll.
    """
    __tablename__ = "notification_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)  # Bauträger
    service_provider_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)  # Dienstleister
    enabled = Column(Boolean, default=True, nullable=False, index=True)
    categories = Column(Text, nullable=False)  # JSON Array: ["electrical", "plumbing", "heating"]
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    contact = relationship("Contact", back_populates="notification_preference")
    user = relationship("User", foreign_keys=[user_id], backref="notification_preferences_sent")
    service_provider = relationship("User", foreign_keys=[service_provider_id], backref="notification_preferences_received")
    
    def __repr__(self):
        return f"<NotificationPreference(id={self.id}, contact_id={self.contact_id}, enabled={self.enabled})>"

