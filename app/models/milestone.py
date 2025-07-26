from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, Enum, Boolean, Float
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
    
    # Bauphasen-Tracking
    construction_phase = Column(String, nullable=True)  # Aktuelle Bauphase beim Erstellen des Gewerks
    
    # Besichtigungssystem
    requires_inspection = Column(Boolean, default=False)  # Checkbox für Vor-Ort-Besichtigung erforderlich
    inspection_sent = Column(Boolean, default=False)      # Markiert ob Besichtigung versendet wurde
    inspection_sent_at = Column(DateTime(timezone=True), nullable=True)  # Zeitpunkt der Versendung
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="milestones")
    creator = relationship("User")
    appointments = relationship("Appointment", back_populates="milestone", cascade="all, delete-orphan") 