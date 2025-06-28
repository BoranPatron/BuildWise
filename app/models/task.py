from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from .base import Base


class TaskStatus(enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    assigned_to = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(TaskStatus), nullable=False, default=TaskStatus.TODO)
    priority = Column(Enum(TaskPriority), nullable=False, default=TaskPriority.MEDIUM)
    
    # Zeitplan
    due_date = Column(Date, nullable=True)
    estimated_hours = Column(Integer, nullable=True)
    actual_hours = Column(Integer, nullable=True)
    
    # Fortschritt
    progress_percentage = Column(Integer, default=0)
    
    # Einstellungen
    is_milestone = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="tasks")
    assigned_user = relationship("User", foreign_keys=[assigned_to])
    creator = relationship("User", foreign_keys=[created_by]) 