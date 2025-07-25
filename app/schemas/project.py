from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel
from ..models.project import ProjectType, ProjectStatus


class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    project_type: ProjectType
    status: ProjectStatus = ProjectStatus.PLANNING
    address: Optional[str] = None
    address_street: Optional[str] = None
    address_zip: Optional[str] = None
    address_city: Optional[str] = None
    address_country: Optional[str] = None
    address_latitude: Optional[float] = None
    address_longitude: Optional[float] = None
    address_geocoded: Optional[bool] = False
    property_size: Optional[float] = None
    construction_area: Optional[float] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    estimated_duration: Optional[int] = None
    budget: Optional[float] = None
    is_public: bool = False
    allow_quotes: bool = True
    construction_phase: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    project_type: Optional[ProjectType] = None
    status: Optional[ProjectStatus] = None
    address: Optional[str] = None
    address_street: Optional[str] = None
    address_zip: Optional[str] = None
    address_city: Optional[str] = None
    address_country: Optional[str] = None
    address_latitude: Optional[float] = None
    address_longitude: Optional[float] = None
    address_geocoded: Optional[bool] = None
    property_size: Optional[float] = None
    construction_area: Optional[float] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    estimated_duration: Optional[int] = None
    budget: Optional[float] = None
    current_costs: Optional[float] = None
    progress_percentage: Optional[float] = None
    is_public: Optional[bool] = None
    allow_quotes: Optional[bool] = None
    construction_phase: Optional[str] = None


class ProjectRead(ProjectBase):
    id: int
    owner_id: int
    current_costs: float
    progress_percentage: float
    address_geocoding_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectSummary(BaseModel):
    id: int
    name: str
    project_type: ProjectType
    status: ProjectStatus
    progress_percentage: float
    budget: Optional[float] = None
    current_costs: float
    address: Optional[str] = None
    address_latitude: Optional[float] = None
    address_longitude: Optional[float] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    created_at: datetime
    # Neue Felder für Bauphasen
    construction_phase: Optional[str] = None
    address_country: Optional[str] = None

    class Config:
        from_attributes = True


class ProjectDashboard(BaseModel):
    project: ProjectRead
    task_count: int
    completed_tasks: int
    milestone_count: int
    completed_milestones: int
    document_count: int
    quote_count: int
    recent_activities: List[dict] = []

    class Config:
        from_attributes = True
