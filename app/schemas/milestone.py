from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from ..models.milestone import MilestoneStatus, MilestonePriority


class MilestoneBase(BaseModel):
    title: str
    description: Optional[str] = None
    project_id: int
    status: MilestoneStatus = MilestoneStatus.PLANNED
    priority: MilestonePriority = MilestonePriority.MEDIUM
    planned_date: datetime
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    category: Optional[str] = None
    budget: Optional[float] = None
    contractor: Optional[str] = None
    is_critical: bool = False
    notify_on_completion: bool = True
    notes: Optional[str] = None
    class Config:
        orm_mode = True


class MilestoneCreate(MilestoneBase):
    pass


class MilestoneUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[MilestoneStatus] = None
    priority: Optional[MilestonePriority] = None
    planned_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    category: Optional[str] = None
    budget: Optional[float] = None
    actual_costs: Optional[float] = None
    contractor: Optional[str] = None
    progress_percentage: Optional[int] = None
    is_critical: Optional[bool] = None
    notify_on_completion: Optional[bool] = None
    notes: Optional[str] = None
    class Config:
        orm_mode = True


class MilestoneRead(MilestoneBase):
    id: int
    actual_costs: Optional[float] = None
    progress_percentage: int
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    class Config:
        orm_mode = True


class MilestoneSummary(BaseModel):
    id: int
    title: str
    status: MilestoneStatus
    priority: MilestonePriority
    planned_date: datetime
    progress_percentage: int
    budget: Optional[float] = None
    actual_costs: Optional[float] = None
    is_critical: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True) 