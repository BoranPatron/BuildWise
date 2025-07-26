from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from .base import Base


class AppointmentType(enum.Enum):
    """Arten von Terminen"""
    INSPECTION = "INSPECTION"
    MEETING = "MEETING"
    CONSULTATION = "CONSULTATION"
    REVIEW = "REVIEW"


class AppointmentStatus(enum.Enum):
    """Status von Terminen"""
    SCHEDULED = "SCHEDULED"
    CONFIRMED = "CONFIRMED"
    PENDING_RESPONSE = "PENDING_RESPONSE"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    REJECTED_WITH_SUGGESTION = "REJECTED_WITH_SUGGESTION"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Appointment(Base):
    """Termine für Besichtigungen und andere Meetings"""
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    
    # Verknüpfungen
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    milestone_id = Column(Integer, ForeignKey("milestones.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Termin-Details
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    appointment_type = Column(Enum(AppointmentType), nullable=False, default=AppointmentType.INSPECTION)
    status = Column(Enum(AppointmentStatus), nullable=False, default=AppointmentStatus.SCHEDULED)
    
    # Zeitplanung
    scheduled_date = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer, default=60)
    
    # Teilnehmer (JSON Array mit Service Provider IDs und E-Mails)
    invited_service_providers = Column(JSON, nullable=True)  # [{"id": 1, "email": "...", "status": "pending"}]
    
    # Ort
    location = Column(String, nullable=True)
    location_details = Column(Text, nullable=True)
    
    # Antworten und Vorschläge
    responses = Column(JSON, nullable=True)  # [{"service_provider_id": 1, "status": "accepted", "message": "...", "suggested_date": "..."}]
    
    # Ergebnis der Besichtigung
    inspection_completed = Column(Boolean, default=False)
    selected_service_provider_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    inspection_notes = Column(Text, nullable=True)
    inspection_photos = Column(JSON, nullable=True)  # Array von Foto-URLs
    
    # Nachverhandlung
    requires_renegotiation = Column(Boolean, default=False)
    renegotiation_details = Column(Text, nullable=True)
    
    # Kalender-Download (.ics Datei)
    calendar_event_data = Column(JSON, nullable=True)  # ICS-Datei Inhalt als JSON
    
    # Benachrichtigungen
    notification_sent = Column(Boolean, default=False)
    follow_up_notification_date = Column(DateTime(timezone=True), nullable=True)
    follow_up_sent = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="appointments")
    milestone = relationship("Milestone", back_populates="appointments")
    creator = relationship("User", foreign_keys=[created_by])
    selected_service_provider = relationship("User", foreign_keys=[selected_service_provider_id])
    appointment_responses = relationship("AppointmentResponse", back_populates="appointment", cascade="all, delete-orphan") 