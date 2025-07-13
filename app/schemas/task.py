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
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    progress_percentage: int = 0
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
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    progress_percentage: Optional[int] = None
    is_milestone: Optional[bool] = None

    class Config:
        orm_mode = True


class TaskRead(TaskBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class TaskStatistics(BaseModel):
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    overdue_tasks: int
    average_progress: float
    total_estimated_hours: float
    total_actual_hours: float

    class Config:
        orm_mode = True 