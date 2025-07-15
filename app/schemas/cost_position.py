from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from ..models.cost_position import CostCategory, CostType, CostStatus


class CostPositionBase(BaseModel):
    title: str
    description: Optional[str] = None
    amount: float
    currency: str = "EUR"
    category: CostCategory = CostCategory.OTHER
    cost_type: CostType = CostType.MANUAL
    status: CostStatus = CostStatus.ACTIVE
    payment_terms: Optional[str] = None
    warranty_period: Optional[int] = None
    estimated_duration: Optional[int] = None
    start_date: Optional[date] = None
    completion_date: Optional[date] = None
    contractor_name: Optional[str] = None
    contractor_contact: Optional[str] = None
    contractor_phone: Optional[str] = None
    contractor_email: Optional[str] = None
    contractor_website: Optional[str] = None
    labor_cost: Optional[float] = None
    material_cost: Optional[float] = None
    overhead_cost: Optional[float] = None
    notes: Optional[str] = None


class CostPositionCreate(CostPositionBase):
    project_id: int
    quote_id: Optional[int] = None
    milestone_id: Optional[int] = None
    service_provider_id: Optional[int] = None


class CostPositionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    category: Optional[CostCategory] = None
    status: Optional[CostStatus] = None
    payment_terms: Optional[str] = None
    warranty_period: Optional[int] = None
    estimated_duration: Optional[int] = None
    start_date: Optional[date] = None
    completion_date: Optional[date] = None
    contractor_name: Optional[str] = None
    contractor_contact: Optional[str] = None
    contractor_phone: Optional[str] = None
    contractor_email: Optional[str] = None
    contractor_website: Optional[str] = None
    labor_cost: Optional[float] = None
    material_cost: Optional[float] = None
    overhead_cost: Optional[float] = None
    progress_percentage: Optional[float] = None
    paid_amount: Optional[float] = None
    last_payment_date: Optional[date] = None
    notes: Optional[str] = None


class CostPositionRead(CostPositionBase):
    id: int
    project_id: int
    quote_id: Optional[int] = None
    milestone_id: Optional[int] = None
    service_provider_id: Optional[int] = None
    risk_score: Optional[float] = None
    price_deviation: Optional[float] = None
    ai_recommendation: Optional[str] = None
    progress_percentage: float
    paid_amount: float
    last_payment_date: Optional[date] = None
    invoice_references: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CostPositionSummary(BaseModel):
    id: int
    title: str
    amount: float
    currency: str
    category: CostCategory
    cost_type: CostType
    status: CostStatus
    contractor_name: Optional[str] = None
    progress_percentage: float
    paid_amount: float
    created_at: datetime

    class Config:
        from_attributes = True


class CostPositionStatistics(BaseModel):
    total_cost_positions: int
    total_amount: float
    total_paid: float
    total_remaining: float
    category_distribution: dict
    status_distribution: dict
    cost_type_distribution: dict 