from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from .base import Base


class ProgressUpdateType(enum.Enum):
    COMMENT = "comment"          # Normaler Kommentar
    DEFECT = "defect"           # Mangel dokumentiert
    COMPLETION = "completion"    # Fertigstellungsmeldung
    REVISION = "revision"       # Nachbesserungsanforderung


class MilestoneProgress(Base):
    __tablename__ = "milestone_progress"

    id = Column(Integer, primary_key=True, index=True)
    milestone_id = Column(Integer, ForeignKey("milestones.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Typ des Updates
    update_type = Column(String, nullable=False, default="comment")
    
    # Inhalt
    message = Column(Text, nullable=False)
    
    # Fortschritt (nur bei Progress-Updates)
    progress_percentage = Column(Integer, nullable=True)  # 0-100
    
    # Fotos/Anhänge
    attachments = Column(JSON, nullable=True)  # Array von Datei-URLs/Pfaden
    
    # Reply-to Funktionalität
    parent_id = Column(Integer, ForeignKey("milestone_progress.id"), nullable=True)
    
    # Spezielle Felder für Mängel
    defect_severity = Column(String, nullable=True)  # minor, major, critical
    defect_resolved = Column(Boolean, default=False)
    
    # Spezielle Felder für Nachbesserungen
    revision_deadline = Column(DateTime, nullable=True)
    revision_completed = Column(Boolean, default=False)
    
    # Sichtbarkeit
    is_internal = Column(Boolean, default=False)  # Nur für Bauträger sichtbar
    
    # Neue Felder für Ausschreibungs-Kommunikation
    is_tender_communication = Column(Boolean, default=False)  # Kennzeichnet Ausschreibungs-Kommunikation
    visible_to_all_bidders = Column(Boolean, default=True)  # Sichtbar für alle Bieter (vor Vergabe)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    milestone = relationship("Milestone", back_populates="progress_updates")
    user = relationship("User")
    parent = relationship("MilestoneProgress", remote_side=[id])
    replies = relationship("MilestoneProgress", back_populates="parent")