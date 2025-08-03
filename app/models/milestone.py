from sqlalchemy import Column, Integer, String, Text, Float, Boolean, Date, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from .base import Base


class MilestoneStatus(enum.Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELAYED = "delayed"
    CANCELLED = "cancelled"


class MilestonePriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Milestone(Base):
    __tablename__ = "milestones"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="planned")
    
    # Gewerke-spezifische Felder
    priority = Column(String, nullable=False, default="medium")
    category = Column(String, nullable=True)  # Gewerke-Kategorie
    
    # Zeitplan
    planned_date = Column(Date, nullable=False)
    actual_date = Column(Date, nullable=True)
    start_date = Column(Date, nullable=True)  # Startdatum für Gewerke
    end_date = Column(Date, nullable=True)    # Enddatum für Gewerke
    
    # Budget und Kosten
    budget = Column(Float, nullable=True)     # Geplantes Budget
    actual_costs = Column(Float, default=0.0) # Tatsächliche Kosten
    
    # Auftragnehmer
    contractor = Column(String, nullable=True) # Name des Auftragnehmers
    
    # Fortschritt
    progress_percentage = Column(Integer, default=0)
    
    # Einstellungen
    is_critical = Column(Boolean, default=False)
    notify_on_completion = Column(Boolean, default=True)
    
    # Notizen
    notes = Column(Text, nullable=True)
    
    # Dokumente (Leistungsverzeichnisse, Bauinformationen etc.)
    documents = Column(JSON, nullable=True)  # Array von Dokumenten mit Metadaten
    
    # Bauphasen-Tracking
    construction_phase = Column(String, nullable=True)  # Aktuelle Bauphase beim Erstellen des Gewerks
    
    # Besichtigungssystem
    requires_inspection = Column(Boolean, default=False)  # Checkbox für Vor-Ort-Besichtigung erforderlich
    inspection_sent = Column(Boolean, default=False)      # Markiert ob Besichtigung versendet wurde
    inspection_sent_at = Column(DateTime(timezone=True), nullable=True)  # Zeitpunkt der Versendung
    
    # Neue Felder für Abschluss-Workflow
    completion_status = Column(String(50), default="in_progress")  # in_progress, completion_requested, under_review, completed, archived
    completion_requested_at = Column(DateTime, nullable=True)
    completion_checklist = Column(JSON, nullable=True)  # Abnahme-Checkliste Daten
    completion_photos = Column(JSON, nullable=True)  # Array von Foto-URLs mit Metadaten
    completion_documents = Column(JSON, nullable=True)  # Prüfprotokolle, Zertifikate etc.
    
    # Abnahme
    inspection_date = Column(DateTime, nullable=True)
    inspection_report = Column(JSON, nullable=True)  # Abnahme-Protokoll
    defects_list = Column(JSON, nullable=True)  # Mängelliste
    acceptance_date = Column(DateTime, nullable=True)
    accepted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Rechnungsstellung
    invoice_generated = Column(Boolean, default=False)
    invoice_data = Column(JSON, nullable=True)  # Automatisch generierte Rechnung
    custom_invoice_url = Column(String(500), nullable=True)  # Upload eigene Rechnung
    invoice_approved = Column(Boolean, default=False)
    invoice_approved_at = Column(DateTime, nullable=True)
    invoice_approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Archivierung
    archived = Column(Boolean, default=False)
    archived_at = Column(DateTime, nullable=True)
    
    # Geteilte Dokumente für Ausschreibung
    shared_document_ids = Column(Text, nullable=True)  # IDs der für Ausschreibung geteilten Dokumente (JSON Array)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="milestones")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_milestones")
    appointments = relationship("Appointment", back_populates="milestone", cascade="all, delete-orphan") 
    accepted_by_user = relationship("User", foreign_keys=[accepted_by])
    invoice_approved_by_user = relationship("User", foreign_keys=[invoice_approved_by])
    progress_updates = relationship("MilestoneProgress", back_populates="milestone", cascade="all, delete-orphan", order_by="MilestoneProgress.created_at")
    acceptances = relationship("Acceptance", back_populates="milestone", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="milestone", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="milestone", cascade="all, delete-orphan") 