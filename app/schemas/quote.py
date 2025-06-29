from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel
from ..models.quote import QuoteStatus


class QuoteBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: QuoteStatus = QuoteStatus.DRAFT
    total_amount: float
    currency: str = "EUR"
    valid_until: Optional[date] = None
    labor_cost: Optional[float] = None
    material_cost: Optional[float] = None
    overhead_cost: Optional[float] = None
    estimated_duration: Optional[int] = None
    start_date: Optional[date] = None
    completion_date: Optional[date] = None
    payment_terms: Optional[str] = None
    warranty_period: Optional[int] = None


class QuoteCreate(QuoteBase):
    project_id: int


class QuoteUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[QuoteStatus] = None
    total_amount: Optional[float] = None
    currency: Optional[str] = None
    valid_until: Optional[date] = None
    labor_cost: Optional[float] = None
    material_cost: Optional[float] = None
    overhead_cost: Optional[float] = None
    estimated_duration: Optional[int] = None
    start_date: Optional[date] = None
    completion_date: Optional[date] = None
    payment_terms: Optional[str] = None
    warranty_period: Optional[int] = None


class QuoteRead(QuoteBase):
    id: int
    project_id: int
    service_provider_id: int
    risk_score: Optional[float] = None
    price_deviation: Optional[float] = None
    ai_recommendation: Optional[str] = None
    contact_released: bool
    contact_released_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime] = None
    accepted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class QuoteSummary(BaseModel):
    id: int
    title: str
    status: QuoteStatus
    total_amount: float
    currency: str
    service_provider_id: int
    risk_score: Optional[float] = None
    price_deviation: Optional[float] = None
    contact_released: bool
    created_at: datetime

    class Config:
        from_attributes = True


class QuoteAnalysis(BaseModel):
    quote_id: int
    risk_score: float
    price_deviation: float
    ai_recommendation: str
    comparison_data: dict 