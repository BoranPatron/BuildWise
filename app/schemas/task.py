from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel
from ..models.task import TaskStatus, TaskPriority


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[date] = None
    estimated_hours: Optional[int] = None
    is_milestone: bool = False


class TaskCreate(TaskBase):
    project_id: int
    assigned_to: Optional[int] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assigned_to: Optional[int] = None
    due_date: Optional[date] = None
    estimated_hours: Optional[int] = None
    actual_hours: Optional[int] = None
    progress_percentage: Optional[int] = None
    is_milestone: Optional[bool] = None


class TaskRead(TaskBase):
    id: int
    project_id: int
    assigned_to: Optional[int] = None
    created_by: int
    actual_hours: Optional[int] = None
    progress_percentage: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaskSummary(BaseModel):
    id: int
    title: str
    status: TaskStatus
    priority: TaskPriority
    progress_percentage: int
    due_date: Optional[date] = None
    assigned_to: Optional[int] = None
    is_milestone: bool

    class Config:
        from_attributes = True 