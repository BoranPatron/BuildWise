from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel
from ..models.milestone import MilestoneStatus, MilestonePriority


class MilestoneBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: MilestoneStatus = MilestoneStatus.PLANNED
    priority: MilestonePriority = MilestonePriority.MEDIUM
    category: Optional[str] = None
    planned_date: date
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget: Optional[float] = None
    actual_costs: Optional[float] = None
    contractor: Optional[str] = None
    is_critical: bool = False
    notify_on_completion: bool = True
    notes: Optional[str] = None


class MilestoneCreate(MilestoneBase):
    project_id: int


class MilestoneUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[MilestoneStatus] = None
    priority: Optional[MilestonePriority] = None
    category: Optional[str] = None
    planned_date: Optional[date] = None
    actual_date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget: Optional[float] = None
    actual_costs: Optional[float] = None
    contractor: Optional[str] = None
    progress_percentage: Optional[int] = None
    is_critical: Optional[bool] = None
    notify_on_completion: Optional[bool] = None
    notes: Optional[str] = None


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
        use_enum_values = True  # Enum als String serialisieren


class MilestoneSummary(BaseModel):
    id: int
    title: str
    status: str  # String statt Enum
    priority: str  # String statt Enum
    category: Optional[str] = None
    planned_date: date
    actual_date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget: Optional[float] = None
    actual_costs: Optional[float] = None
    contractor: Optional[str] = None
    progress_percentage: int
    is_critical: bool
    project_id: Optional[int] = None  # Projekt-ID hinzufügen

    class Config:
        from_attributes = True
        use_enum_values = True  # Enum als String serialisieren 