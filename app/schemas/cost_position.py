from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CostPositionBase(BaseModel):
    title: str
    description: Optional[str] = None
    amount: float
    currency: str = "EUR"
    category: str
    cost_type: str = "material"
    status: str = "planned"
    contractor_name: Optional[str] = None
    contractor_contact: Optional[str] = None
    contractor_phone: Optional[str] = None
    contractor_email: Optional[str] = None
    contractor_website: Optional[str] = None
    payment_terms: Optional[str] = None
    warranty_period: Optional[int] = None
    estimated_duration: Optional[int] = None
    start_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    labor_cost: Optional[float] = None
    material_cost: Optional[float] = None
    overhead_cost: Optional[float] = None
    risk_score: Optional[float] = None
    price_deviation: Optional[float] = None
    ai_recommendation: Optional[str] = None
    quote_id: Optional[int] = None
    milestone_id: Optional[int] = None
    project_id: int
    class Config:
        orm_mode = True


class CostPositionCreate(CostPositionBase):
    pass


class CostPositionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    category: Optional[str] = None
    cost_type: Optional[str] = None
    status: Optional[str] = None
    contractor_name: Optional[str] = None
    contractor_contact: Optional[str] = None
    contractor_phone: Optional[str] = None
    contractor_email: Optional[str] = None
    contractor_website: Optional[str] = None
    payment_terms: Optional[str] = None
    warranty_period: Optional[int] = None
    estimated_duration: Optional[int] = None
    start_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    labor_cost: Optional[float] = None
    material_cost: Optional[float] = None
    overhead_cost: Optional[float] = None
    risk_score: Optional[float] = None
    price_deviation: Optional[float] = None
    ai_recommendation: Optional[str] = None
    quote_id: Optional[int] = None
    milestone_id: Optional[int] = None
    project_id: Optional[int] = None
    class Config:
        orm_mode = True


class CostPositionRead(CostPositionBase):
    id: int
    progress_percentage: float
    paid_amount: float
    created_at: datetime
    updated_at: datetime
    class Config:
        orm_mode = True


class CostPositionSummary(BaseModel):
    id: int
    title: str
    amount: float
    currency: str
    category: str
    status: str
    progress_percentage: int
    paid_amount: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CostPositionStatistics(BaseModel):
    total_cost_positions: int
    total_amount: float
    total_paid: float
    total_remaining: float
    average_risk_score: float
    average_price_deviation: float
    category_breakdown: list[dict]
    status_breakdown: list[dict]

    model_config = ConfigDict(from_attributes=True) 