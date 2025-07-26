from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, Enum, Boolean, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from .base import Base


class InspectionStatus(enum.Enum):
    PLANNED = "planned"  # Besichtigung geplant
    INVITED = "invited"  # Dienstleister eingeladen
    CONFIRMED = "confirmed"  # Dienstleister bestätigt
    COMPLETED = "completed"  # Besichtigung durchgeführt
    CANCELLED = "cancelled"  # Besichtigung abgesagt


class InspectionInvitationStatus(enum.Enum):
    SENT = "sent"  # Einladung versendet
    CONFIRMED = "confirmed"  # Teilnahme bestätigt
    DECLINED = "declined"  # Teilnahme abgelehnt
    NO_RESPONSE = "no_response"  # Keine Antwort


class Inspection(Base):
    """
    Besichtigungstermin für ein Gewerk
    """
    __tablename__ = "inspections"

    id = Column(Integer, primary_key=True, index=True)
    milestone_id = Column(Integer, ForeignKey("milestones.id", ondelete="CASCADE"))
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))  # Bauträger
    
    # Termindetails
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(InspectionStatus), default=InspectionStatus.PLANNED)
    
    # Zeitplan
    scheduled_date = Column(Date, nullable=False)  # Vorgeschlagenes Datum
    scheduled_time_start = Column(String, nullable=True)  # z.B. "14:00"
    scheduled_time_end = Column(String, nullable=True)    # z.B. "16:00"
    duration_minutes = Column(Integer, default=120)  # Dauer in Minuten
    
    # Ort
    location_address = Column(String, nullable=True)  # Spezifische Adresse (falls abweichend vom Projekt)
    location_notes = Column(Text, nullable=True)  # Zusätzliche Ortsangaben
    
    # Kontakt
    contact_person = Column(String, nullable=True)  # Ansprechpartner vor Ort
    contact_phone = Column(String, nullable=True)   # Telefonnummer
    
    # Notizen
    preparation_notes = Column(Text, nullable=True)  # Was sollen Dienstleister mitbringen/vorbereiten
    completion_notes = Column(Text, nullable=True)   # Notizen nach der Besichtigung
    
    # Absage
    cancellation_reason = Column(Text, nullable=True)  # Grund der Absage
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    milestone = relationship("Milestone")
    project = relationship("Project")
    creator = relationship("User")
    invitations = relationship("InspectionInvitation", back_populates="inspection")


class InspectionInvitation(Base):
    """
    Einladung eines Dienstleisters zu einer Besichtigung
    """
    __tablename__ = "inspection_invitations"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("inspections.id", ondelete="CASCADE"))
    service_provider_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    quote_id = Column(Integer, ForeignKey("quotes.id", ondelete="CASCADE"), nullable=True)  # Ursprüngliches Angebot
    
    # Status
    status = Column(Enum(InspectionInvitationStatus), default=InspectionInvitationStatus.SENT)
    
    # Antwort des Dienstleisters
    response_message = Column(Text, nullable=True)  # Nachricht bei Zu-/Absage
    alternative_dates = Column(Text, nullable=True)  # JSON mit alternativen Terminen
    
    # Notification
    notification_sent = Column(Boolean, default=False)
    notification_sent_at = Column(DateTime(timezone=True), nullable=True)
    reminder_sent = Column(Boolean, default=False)
    reminder_sent_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    responded_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    inspection = relationship("Inspection", back_populates="invitations")
    service_provider = relationship("User")
    quote = relationship("Quote")


class QuoteRevision(Base):
    """
    Überarbeitetes Angebot nach Besichtigung
    """
    __tablename__ = "quote_revisions"

    id = Column(Integer, primary_key=True, index=True)
    original_quote_id = Column(Integer, ForeignKey("quotes.id", ondelete="CASCADE"))
    inspection_id = Column(Integer, ForeignKey("inspections.id", ondelete="CASCADE"))
    service_provider_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    
    # Revision Details
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    revision_reason = Column(Text, nullable=True)  # Grund für die Überarbeitung
    
    # Neue Angebotsdetails
    total_amount = Column(Float, nullable=False)
    currency = Column(String, default="EUR")
    valid_until = Column(Date, nullable=True)
    
    # Aufschlüsselung
    labor_cost = Column(Float, nullable=True)
    material_cost = Column(Float, nullable=True)
    overhead_cost = Column(Float, nullable=True)
    
    # Änderungen gegenüber Original
    amount_difference = Column(Float, nullable=True)  # Differenz zum Original
    amount_difference_percentage = Column(Float, nullable=True)  # Prozentuale Änderung
    
    # Zeitplan
    estimated_duration = Column(Integer, nullable=True)  # in Tagen
    start_date = Column(Date, nullable=True)
    completion_date = Column(Date, nullable=True)
    
    # Status
    status = Column(String, default="submitted")  # submitted, accepted, rejected
    
    # Bestätigung durch Bauträger
    confirmed_by_client = Column(Boolean, default=False)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Ablehnung durch Bauträger
    rejection_reason = Column(Text, nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    rejected_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Dokumente
    pdf_upload_path = Column(String, nullable=True)
    additional_documents = Column(Text, nullable=True)  # JSON
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    original_quote = relationship("Quote")
    inspection = relationship("Inspection")
    service_provider = relationship("User", foreign_keys=[service_provider_id])
    rejected_by_user = relationship("User", foreign_keys=[rejected_by]) 