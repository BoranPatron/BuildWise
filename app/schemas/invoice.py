"""
Pydantic schemas for invoice management
"""
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional
from app.models.invoice import InvoiceStatus, InvoiceType

class InvoiceBase(BaseModel):
    invoice_number: str = Field(..., description="Eindeutige Rechnungsnummer")
    invoice_date: datetime = Field(default_factory=datetime.utcnow, description="Rechnungsdatum")
    due_date: datetime = Field(..., description="Fälligkeitsdatum")
    
    net_amount: float = Field(..., ge=0, description="Nettobetrag")
    vat_rate: float = Field(default=19.0, ge=0, le=100, description="Mehrwertsteuersatz in Prozent")
    vat_amount: float = Field(..., ge=0, description="Mehrwertsteuerbetrag")
    total_amount: float = Field(..., ge=0, description="Gesamtbetrag")
    
    material_costs: Optional[float] = Field(default=0.0, ge=0, description="Materialkosten")
    labor_costs: Optional[float] = Field(default=0.0, ge=0, description="Arbeitskosten")
    additional_costs: Optional[float] = Field(default=0.0, ge=0, description="Zusatzkosten")
    
    description: Optional[str] = Field(None, description="Leistungsbeschreibung")
    work_period_from: Optional[datetime] = Field(None, description="Leistungszeitraum von")
    work_period_to: Optional[datetime] = Field(None, description="Leistungszeitraum bis")
    
    type: InvoiceType = Field(..., description="Art der Rechnung (manual/upload)")
    notes: Optional[str] = Field(None, description="Interne Notizen")

    @validator('vat_amount')
    def validate_vat_amount(cls, v, values):
        if 'net_amount' in values and 'vat_rate' in values:
            expected_vat = values['net_amount'] * (values['vat_rate'] / 100)
            if abs(v - expected_vat) > 0.01:  # Toleranz für Rundungsfehler
                raise ValueError(f"MwSt.-Betrag stimmt nicht überein. Erwartet: {expected_vat:.2f}, erhalten: {v:.2f}")
        return v

    @validator('total_amount')
    def validate_total_amount(cls, v, values):
        if 'net_amount' in values and 'vat_amount' in values:
            expected_total = values['net_amount'] + values['vat_amount']
            if abs(v - expected_total) > 0.01:  # Toleranz für Rundungsfehler
                raise ValueError(f"Gesamtbetrag stimmt nicht überein. Erwartet: {expected_total:.2f}, erhalten: {v:.2f}")
        return v

class InvoiceCreate(InvoiceBase):
    project_id: int = Field(..., description="Projekt-ID")
    milestone_id: int = Field(..., description="Meilenstein-ID")
    service_provider_id: int = Field(..., description="Dienstleister-ID")

class InvoiceUpdate(BaseModel):
    invoice_number: Optional[str] = None
    due_date: Optional[datetime] = None
    net_amount: Optional[float] = Field(None, ge=0)
    vat_rate: Optional[float] = Field(None, ge=0, le=100)
    vat_amount: Optional[float] = Field(None, ge=0)
    total_amount: Optional[float] = Field(None, ge=0)
    material_costs: Optional[float] = Field(None, ge=0)
    labor_costs: Optional[float] = Field(None, ge=0)
    additional_costs: Optional[float] = Field(None, ge=0)
    description: Optional[str] = None
    work_period_from: Optional[datetime] = None
    work_period_to: Optional[datetime] = None
    notes: Optional[str] = None
    status: Optional[InvoiceStatus] = None

class InvoiceUpload(BaseModel):
    milestone_id: int = Field(..., description="Meilenstein-ID")
    invoice_number: str = Field(..., description="Rechnungsnummer")
    total_amount: float = Field(..., ge=0, description="Gesamtbetrag")
    notes: Optional[str] = Field(None, description="Notizen")
    type: InvoiceType = Field(default=InvoiceType.UPLOAD, description="Rechnungstyp")

class InvoicePayment(BaseModel):
    payment_reference: Optional[str] = Field(None, description="Zahlungsreferenz")
    paid_at: datetime = Field(default_factory=datetime.utcnow, description="Zahlungsdatum")

class InvoiceRating(BaseModel):
    rating_quality: int = Field(..., ge=1, le=5, description="Qualitätsbewertung (1-5 Sterne)")
    rating_timeliness: int = Field(..., ge=1, le=5, description="Termintreue-Bewertung (1-5 Sterne)")
    rating_overall: int = Field(..., ge=1, le=5, description="Gesamtbewertung (1-5 Sterne)")
    rating_notes: Optional[str] = Field(None, description="Bewertungsnotizen")

class InvoiceRead(InvoiceBase):
    id: int
    project_id: int
    milestone_id: int
    service_provider_id: int
    status: InvoiceStatus
    
    # PDF-Datei Info
    pdf_file_path: Optional[str] = None
    pdf_file_name: Optional[str] = None
    
    # Zahlungsinformationen
    paid_at: Optional[datetime] = None
    payment_reference: Optional[str] = None
    
    # Bewertung
    rating_quality: Optional[int] = None
    rating_timeliness: Optional[int] = None
    rating_overall: Optional[int] = None
    rating_notes: Optional[str] = None
    rated_by: Optional[int] = None
    rated_at: Optional[datetime] = None
    
    # Metadaten
    created_at: datetime
    updated_at: datetime
    created_by: int

    class Config:
        from_attributes = True

class InvoiceSummary(BaseModel):
    id: int
    invoice_number: str
    invoice_date: datetime
    due_date: datetime
    total_amount: float
    status: InvoiceStatus
    type: InvoiceType
    milestone_title: Optional[str] = None
    service_provider_name: Optional[str] = None
    is_overdue: bool = False

    class Config:
        from_attributes = True

class InvoiceStats(BaseModel):
    total_invoices: int = 0
    total_amount: float = 0.0
    paid_amount: float = 0.0
    outstanding_amount: float = 0.0
    overdue_count: int = 0
    overdue_amount: float = 0.0
    average_payment_days: Optional[float] = None