"""
Contact Model
Kontaktbuch-Model für die Datenbank
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from .base import Base


class Contact(Base):
    """
    Contact Model - Kontaktbuch für Bauträger und Dienstleister
    Speichert Kontakte zu Service Providern mit allen relevanten Informationen
    """
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Firma & Kontaktdaten
    company_name = Column(String(255), nullable=False, index=True)
    contact_person = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    website = Column(String(255), nullable=True)
    
    # Kategorisierung & Bewertung
    category = Column(String(100), nullable=True, index=True)  # z.B. 'electrical', 'plumbing', etc.
    rating = Column(Float, nullable=True)  # 0-5 Sterne
    
    # Notizen & Zusatzinformationen
    notes = Column(Text, nullable=True)
    
    # Adresse
    address_street = Column(String(255), nullable=True)
    address_city = Column(String(100), nullable=True)
    address_zip = Column(String(20), nullable=True)
    address_country = Column(String(100), nullable=True, default='Deutschland')
    
    # Verknüpfungen
    milestone_id = Column(Integer, ForeignKey("milestones.id", ondelete="SET NULL"), nullable=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    service_provider_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Favoriten
    favorite = Column(Boolean, default=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="contacts")
    service_provider = relationship("User", foreign_keys=[service_provider_id])
    milestone = relationship("Milestone", backref="contacts")
    project = relationship("Project", backref="contacts")
    notification_preference = relationship("NotificationPreference", back_populates="contact", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Contact(id={self.id}, company_name='{self.company_name}', user_id={self.user_id})>"

