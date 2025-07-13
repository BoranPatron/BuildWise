from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from ..models.project import ProjectType, ProjectStatus


class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    project_type: ProjectType = ProjectType.NEW_BUILD
    status: ProjectStatus = ProjectStatus.PLANNING
    budget: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    address: Optional[str] = None
    property_size: Optional[float] = None
    construction_area: Optional[float] = None
    estimated_duration: Optional[int] = None
    is_public: bool = True
    allow_quotes: bool = True

    class Config:
        orm_mode = True


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    project_type: Optional[ProjectType] = None
    status: Optional[ProjectStatus] = None
    budget: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    address: Optional[str] = None
    property_size: Optional[float] = None
    construction_area: Optional[float] = None
    estimated_duration: Optional[int] = None
    is_public: Optional[bool] = None
    allow_quotes: Optional[bool] = None

    class Config:
        orm_mode = True


class ProjectRead(ProjectBase):
    id: int
    progress_percentage: int = 0
    current_costs: float = 0.0
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class ProjectDashboard(BaseModel):
    project: ProjectRead
    task_count: int
    completed_tasks: int
    milestone_count: int
    completed_milestones: int
    document_count: int
    quote_count: int
    recent_activities: list

    class Config:
        orm_mode = True
