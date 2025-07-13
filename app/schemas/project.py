from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
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


class ProjectRead(ProjectBase):
    id: int
    owner_id: int
    progress_percentage: int
    current_costs: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectSummary(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    project_type: ProjectType
    status: ProjectStatus
    progress_percentage: int
    budget: Optional[float] = None
    current_costs: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectDashboard(BaseModel):
    project: ProjectRead
    task_count: int
    completed_tasks: int
    milestone_count: int
    completed_milestones: int
    document_count: int
    quote_count: int
    recent_activities: list[dict]

    model_config = ConfigDict(from_attributes=True)
