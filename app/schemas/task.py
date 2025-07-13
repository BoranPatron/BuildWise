from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from ..models.task import TaskStatus, TaskPriority


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    project_id: int
    assigned_to: Optional[int] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[int] = None
    is_milestone: bool = False
    class Config:
        orm_mode = True


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assigned_to: Optional[int] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[int] = None
    actual_hours: Optional[int] = None
    progress_percentage: Optional[int] = None
    is_milestone: Optional[bool] = None
    class Config:
        orm_mode = True


class TaskRead(TaskBase):
    id: int
    created_by: int
    actual_hours: Optional[int] = None
    progress_percentage: int
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    class Config:
        orm_mode = True


class TaskSummary(BaseModel):
    id: int
    title: str
    status: TaskStatus
    priority: TaskPriority
    progress_percentage: int
    due_date: Optional[datetime] = None
    is_milestone: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True) 