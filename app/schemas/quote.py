from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from ..models.quote import QuoteStatus


class QuoteBase(BaseModel):
    title: str
    description: Optional[str] = None
    project_id: int
    milestone_id: Optional[int] = None
    service_provider_id: int
    total_amount: float
    currency: str = "EUR"
    valid_until: datetime
    labor_cost: float
    material_cost: float
    overhead_cost: float
    estimated_duration: int
    start_date: datetime
    completion_date: datetime
    payment_terms: str
    warranty_period: int
    company_name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    class Config:
        orm_mode = True


class QuoteCreate(QuoteBase):
    pass


class QuoteUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    total_amount: Optional[float] = None
    currency: Optional[str] = None
    valid_until: Optional[datetime] = None
    labor_cost: Optional[float] = None
    material_cost: Optional[float] = None
    overhead_cost: Optional[float] = None
    estimated_duration: Optional[int] = None
    start_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    payment_terms: Optional[str] = None
    warranty_period: Optional[int] = None
    company_name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    class Config:
        orm_mode = True


class QuoteRead(QuoteBase):
    id: int
    status: QuoteStatus
    risk_score: Optional[float] = None
    price_deviation: Optional[float] = None
    ai_recommendation: Optional[str] = None
    contact_released: bool
    pdf_upload_path: Optional[str] = None
    additional_documents: Optional[str] = None
    rating: Optional[int] = None
    feedback: Optional[str] = None
    rejection_reason: Optional[str] = None
    submitted_at: Optional[datetime] = None
    accepted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    class Config:
        orm_mode = True


class QuoteSummary(BaseModel):
    id: int
    title: str
    status: QuoteStatus
    total_amount: float
    currency: str
    company_name: Optional[str] = None
    contact_person: Optional[str] = None
    risk_score: Optional[float] = None
    price_deviation: Optional[float] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuoteAnalysis(BaseModel):
    risk_score: float
    price_deviation: float
    recommendation: str
    factors: list[str]


class QuoteForMilestone(BaseModel):
    id: int
    title: str
    status: QuoteStatus
    total_amount: float
    currency: str
    company_name: Optional[str] = None
    contact_person: Optional[str] = None
    risk_score: Optional[float] = None
    price_deviation: Optional[float] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True) 