from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .base import Base

class NotificationType(enum.Enum):
    """Verschiedene Typen von Benachrichtigungen"""
    QUOTE_SUBMITTED = "quote_submitted"  # Neues Angebot eingereicht
    QUOTE_ACCEPTED = "quote_accepted"    # Angebot angenommen
    QUOTE_REJECTED = "quote_rejected"    # Angebot abgelehnt
    APPOINTMENT_REQUEST = "appointment_request"  # Terminanfrage
    APPOINTMENT_CONFIRMED = "appointment_confirmed"  # Termin bestätigt
    MILESTONE_COMPLETED = "milestone_completed"  # Meilenstein abgeschlossen
    INVOICE_SUBMITTED = "invoice_submitted"  # Rechnung eingereicht
    PAYMENT_RECEIVED = "payment_received"  # Zahlung erhalten
    DOCUMENT_UPLOADED = "document_uploaded"  # Dokument hochgeladen
    PROJECT_STATUS_CHANGED = "project_status_changed"  # Projektstatus geändert
    SYSTEM_ANNOUNCEMENT = "system_announcement"  # Systemankündigung

class NotificationPriority(enum.Enum):
    """Prioritätsstufen für Benachrichtigungen"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class Notification(Base):
    """
    Benachrichtigungsmodell für das BuildWise System
    
    Speichert alle Arten von Benachrichtigungen für Benutzer
    """
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    
    # Empfänger der Benachrichtigung
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Typ und Priorität
    type = Column(SQLEnum(NotificationType), nullable=False, index=True)
    priority = Column(SQLEnum(NotificationPriority), default=NotificationPriority.NORMAL)
    
    # Inhalt
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    # Zusätzliche Daten (JSON-ähnlich als Text)
    data = Column(Text, nullable=True)  # JSON-String für zusätzliche Daten
    
    # Status
    is_read = Column(Boolean, default=False, index=True)
    is_acknowledged = Column(Boolean, default=False, index=True)  # Vom Benutzer quittiert
    
    # Zeitstempel
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    read_at = Column(DateTime, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    
    # Optionale Verknüpfungen zu anderen Entitäten
    related_quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=True, index=True)
    related_project_id = Column(Integer, ForeignKey("projects.id"), nullable=True, index=True)
    related_milestone_id = Column(Integer, ForeignKey("milestones.id"), nullable=True, index=True)
    related_appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True, index=True)
    
    # Beziehungen
    recipient = relationship("User", foreign_keys=[recipient_id])
    related_quote = relationship("Quote", foreign_keys=[related_quote_id])
    related_project = relationship("Project", foreign_keys=[related_project_id])
    related_milestone = relationship("Milestone", foreign_keys=[related_milestone_id])
    related_appointment = relationship("Appointment", foreign_keys=[related_appointment_id])
    
    def __repr__(self):
        return f"<Notification(id={self.id}, type={self.type.value}, recipient_id={self.recipient_id}, title='{self.title}')>"
    
    def mark_as_read(self):
        """Markiert die Benachrichtigung als gelesen"""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.utcnow()
    
    def acknowledge(self):
        """Markiert die Benachrichtigung als quittiert"""
        if not self.is_acknowledged:
            self.is_acknowledged = True
            self.acknowledged_at = datetime.utcnow()
            # Automatisch auch als gelesen markieren
            self.mark_as_read()
    
    @property
    def is_urgent(self) -> bool:
        """Prüft ob die Benachrichtigung dringend ist"""
        return self.priority == NotificationPriority.URGENT
    
    @property
    def requires_attention(self) -> bool:
        """Prüft ob die Benachrichtigung Aufmerksamkeit erfordert (ungelesen und nicht quittiert)"""
        return not self.is_read or not self.is_acknowledged
