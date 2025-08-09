from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Enum,
    ForeignKey,
    Boolean,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from .base import Base


class VisualizationCategory(enum.Enum):
    INTERIOR = "interior"
    EXTERIOR = "exterior"
    INDIVIDUAL = "individual"


class VisualizationStatus(enum.Enum):
    PENDING = "PENDING"          # eingereicht, wartet auf Visualisierung
    IN_PROGRESS = "IN_PROGRESS"  # in Bearbeitung
    COMPLETED = "COMPLETED"      # Ergebnis verfügbar
    REJECTED = "REJECTED"        # abgelehnt (z. B. mangelhaft)


class Visualization(Base):
    __tablename__ = "visualizations"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    milestone_id = Column(Integer, ForeignKey("milestones.id", ondelete="SET NULL"))

    category = Column(Enum(VisualizationCategory), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)

    # Eingereichte Pläne (lokal im DMS referenziert oder externer Link)
    plan_document_id = Column(Integer, ForeignKey("documents.id"))
    plan_external_url = Column(String(1024))  # z. B. Google Drive Upload-Link

    # Ergebnis-Visualisierung (DMS oder externer Link)
    result_document_id = Column(Integer, ForeignKey("documents.id"))
    result_external_url = Column(String(1024))

    # Google Drive Integration (Ordner/Laufwerkbezug)
    drive_folder_url = Column(String(1024))

    status = Column(Enum(VisualizationStatus), default=VisualizationStatus.PENDING)
    is_archived = Column(Boolean, default=False)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    project = relationship("Project")
    milestone = relationship("Milestone")
    plan_document = relationship("Document", foreign_keys=[plan_document_id])
    result_document = relationship("Document", foreign_keys=[result_document_id])





