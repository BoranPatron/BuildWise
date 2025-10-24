from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, field_validator
from ..models.task import TaskStatus, TaskPriority


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[date] = None
    estimated_hours: Optional[float] = None
    is_milestone: bool = False
    milestone_id: Optional[int] = None
    
    @field_validator('status', mode='before')
    @classmethod
    def normalize_status(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v
    
    @field_validator('priority', mode='before')
    @classmethod
    def normalize_priority(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v


class TaskCreate(TaskBase):
    project_id: Optional[int] = None
    assigned_to: Optional[int] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assigned_to: Optional[int] = None
    due_date: Optional[date] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    progress_percentage: Optional[int] = None
    is_milestone: Optional[bool] = None
    milestone_id: Optional[int] = None
    
    @field_validator('status', mode='before')
    @classmethod
    def normalize_status(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v
    
    @field_validator('priority', mode='before')
    @classmethod
    def normalize_priority(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v


class TaskRead(TaskBase):
    id: int
    project_id: Optional[int] = None
    assigned_to: Optional[int] = None
    created_by: int
    actual_hours: Optional[float] = None
    progress_percentage: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaskSummary(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: TaskStatus
    priority: TaskPriority
    progress_percentage: int
    due_date: Optional[date] = None
    estimated_hours: Optional[float] = None
    assigned_to: Optional[int] = None
    is_milestone: bool
    milestone_id: Optional[int] = None
    archived_at: Optional[datetime] = None

    class Config:
        from_attributes = True 