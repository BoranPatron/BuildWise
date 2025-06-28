from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, Enum, Boolean
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


class Milestone(Base):
    __tablename__ = "milestones"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(MilestoneStatus), nullable=False, default=MilestoneStatus.PLANNED)
    
    # Zeitplan
    planned_date = Column(Date, nullable=False)
    actual_date = Column(Date, nullable=True)
    
    # Fortschritt
    progress_percentage = Column(Integer, default=0)
    
    # Einstellungen
    is_critical = Column(Boolean, default=False)
    notify_on_completion = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="milestones")
    creator = relationship("User") 