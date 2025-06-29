from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel
from ..models.milestone import MilestoneStatus


class MilestoneBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: MilestoneStatus = MilestoneStatus.PLANNED
    planned_date: date
    is_critical: bool = False
    notify_on_completion: bool = True


class MilestoneCreate(MilestoneBase):
    project_id: int


class MilestoneUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[MilestoneStatus] = None
    planned_date: Optional[date] = None
    actual_date: Optional[date] = None
    progress_percentage: Optional[int] = None
    is_critical: Optional[bool] = None
    notify_on_completion: Optional[bool] = None


class MilestoneRead(MilestoneBase):
    id: int
    project_id: int
    created_by: int
    actual_date: Optional[date] = None
    progress_percentage: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MilestoneSummary(BaseModel):
    id: int
    title: str
    status: MilestoneStatus
    planned_date: date
    actual_date: Optional[date] = None
    progress_percentage: int
    is_critical: bool

    class Config:
        from_attributes = True 