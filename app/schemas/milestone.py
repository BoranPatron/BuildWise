from datetime import date, datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel
# Enums wurden zu Strings geändert - keine Imports mehr nötig


class MilestoneBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "planned"
    priority: str = "medium"
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
    # Bauphasen-Tracking
    construction_phase: Optional[str] = None
    # Besichtigungssystem
    requires_inspection: bool = False


class MilestoneCreate(MilestoneBase):
    project_id: int
    # Zusätzliche Felder für kategorie-spezifische Informationen
    category_specific_fields: Optional[Dict[str, Any]] = None
    technical_specifications: Optional[str] = None
    quality_requirements: Optional[str] = None
    safety_requirements: Optional[str] = None
    environmental_requirements: Optional[str] = None


class MilestoneUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
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
    # Bauphasen-Tracking
    construction_phase: Optional[str] = None
    # Besichtigungssystem
    requires_inspection: Optional[bool] = None


class MilestoneRead(MilestoneBase):
    id: int
    project_id: int
    created_by: int
    actual_date: Optional[date] = None
    progress_percentage: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    # Bauphasen-Tracking
    construction_phase: Optional[str] = None

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
    # Bauphasen-Tracking
    construction_phase: Optional[str] = None
    # Besichtigungssystem
    requires_inspection: bool = False

    class Config:
        from_attributes = True 
        use_enum_values = True  # Enum als String serialisieren
        
    @classmethod
    def from_orm(cls, obj):
        # Status und Priority sind bereits Strings
        data = {
            'id': obj.id,
            'title': obj.title,
            'status': obj.status,
            'priority': obj.priority,
            'category': obj.category,
            'planned_date': obj.planned_date,
            'actual_date': obj.actual_date,
            'start_date': obj.start_date,
            'end_date': obj.end_date,
            'budget': obj.budget,
            'actual_costs': obj.actual_costs,
            'contractor': obj.contractor,
            'progress_percentage': obj.progress_percentage,
            'is_critical': obj.is_critical,
            'project_id': obj.project_id,
            'construction_phase': obj.construction_phase,
            'requires_inspection': obj.requires_inspection
        }
        return cls(**data) 