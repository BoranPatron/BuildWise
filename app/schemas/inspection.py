from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum

from ..models.inspection import InspectionStatus, InspectionInvitationStatus, QuoteRevision


# Enums
class RevisionReason(Enum):
    INSPECTION_FINDINGS = "inspection_findings"     # Erkenntnisse aus Besichtigung
    SCOPE_CHANGES = "scope_changes"                 # Änderungen im Leistungsumfang
    PRICE_ADJUSTMENT = "price_adjustment"           # Preisanpassung
    TIMELINE_ADJUSTMENT = "timeline_adjustment"     # Zeitplan-Anpassung
    TECHNICAL_REQUIREMENTS = "technical_requirements" # Technische Anforderungen
    OTHER = "other"                                 # Sonstige Gründe


# Base Schemas
class InspectionBase(BaseModel):
    title: str = Field(..., description="Titel der Besichtigung")
    description: Optional[str] = Field(None, description="Beschreibung der Besichtigung")
    scheduled_date: datetime = Field(..., description="Geplanter Besichtigungstermin")
    scheduled_time_start: Optional[str] = Field(None, description="Startzeit")
    scheduled_time_end: Optional[str] = Field(None, description="Endzeit")
    duration_minutes: int = Field(60, description="Dauer in Minuten")
    location_address: str = Field(..., description="Adresse der Besichtigung")
    location_notes: Optional[str] = Field(None, description="Ortshinweise")
    additional_location_info: Optional[str] = Field(None, description="Zusätzliche Ortsangaben")
    parking_info: Optional[str] = Field(None, description="Parkmöglichkeiten")
    access_instructions: Optional[str] = Field(None, description="Zugangshinweise")
    contact_person: Optional[str] = Field(None, description="Ansprechpartner")
    contact_phone: Optional[str] = Field(None, description="Telefonnummer")
    contact_email: Optional[str] = Field(None, description="E-Mail-Adresse")
    alternative_contact_person: Optional[str] = Field(None, description="Alternativer Ansprechpartner")
    alternative_contact_phone: Optional[str] = Field(None, description="Alternative Telefonnummer")
    preparation_notes: Optional[str] = Field(None, description="Vorbereitungshinweise")
    special_requirements: Optional[str] = Field(None, description="Besondere Anforderungen")


class InspectionCreate(InspectionBase):
    milestone_id: int = Field(..., description="ID des Gewerks")


class InspectionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    scheduled_time_start: Optional[str] = None
    scheduled_time_end: Optional[str] = None
    duration_minutes: Optional[int] = None
    location_address: Optional[str] = None
    location_notes: Optional[str] = None
    additional_location_info: Optional[str] = None
    parking_info: Optional[str] = None
    access_instructions: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    alternative_contact_person: Optional[str] = None
    alternative_contact_phone: Optional[str] = None
    preparation_notes: Optional[str] = None
    special_requirements: Optional[str] = None
    status: Optional[InspectionStatus] = None
    inspection_notes: Optional[str] = None
    completion_notes: Optional[str] = None


class InspectionInvitationBase(BaseModel):
    status: InspectionInvitationStatus
    response_message: Optional[str] = None


class InspectionInvitationUpdate(BaseModel):
    status: InspectionInvitationStatus
    response_message: Optional[str] = None


class InspectionInvitationRead(InspectionInvitationBase):
    id: int
    inspection_id: int
    quote_id: int
    service_provider_id: int
    notification_sent: bool
    notification_sent_at: Optional[datetime]
    reminder_sent: bool
    reminder_sent_at: Optional[datetime]
    responded_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InspectionRead(InspectionBase):
    id: int
    milestone_id: int
    project_id: int
    created_by: int
    status: InspectionStatus
    inspection_notes: Optional[str]
    completion_notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    invitations: List[InspectionInvitationRead] = []

    class Config:
        from_attributes = True


# Quote Revision Schemas
class QuoteRevisionBase(BaseModel):
    title: str = Field(..., description="Titel des überarbeiteten Angebots")
    description: Optional[str] = Field(None, description="Beschreibung")
    reason: RevisionReason = Field(..., description="Grund für die Überarbeitung")
    revision_notes: Optional[str] = Field(None, description="Erklärung der Änderungen")
    total_amount: float = Field(..., description="Neuer Gesamtbetrag")
    currency: str = Field("EUR", description="Währung")
    labor_cost: Optional[float] = Field(None, description="Arbeitskosten")
    material_cost: Optional[float] = Field(None, description="Materialkosten")
    overhead_cost: Optional[float] = Field(None, description="Gemeinkosten")
    estimated_duration: Optional[int] = Field(None, description="Geschätzte Dauer in Tagen")
    start_date: Optional[datetime] = Field(None, description="Geplanter Starttermin")
    completion_date: Optional[datetime] = Field(None, description="Geplanter Abschlusstermin")
    payment_terms: Optional[str] = Field(None, description="Zahlungsbedingungen")
    warranty_period: Optional[int] = Field(None, description="Garantiezeit in Monaten")


class QuoteRevisionCreate(QuoteRevisionBase):
    original_quote_id: int = Field(..., description="ID des ursprünglichen Angebots")
    inspection_id: Optional[int] = Field(None, description="ID der Besichtigung")


class QuoteRevisionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    revision_notes: Optional[str] = None
    total_amount: Optional[float] = None
    labor_cost: Optional[float] = None
    material_cost: Optional[float] = None
    overhead_cost: Optional[float] = None
    estimated_duration: Optional[int] = None
    start_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    payment_terms: Optional[str] = None
    warranty_period: Optional[int] = None
    is_final: Optional[bool] = None


class QuoteRevisionRead(QuoteRevisionBase):
    id: int
    original_quote_id: int
    inspection_id: Optional[int]
    service_provider_id: int
    revision_number: int
    price_change_amount: Optional[float]
    price_change_percentage: Optional[float]
    duration_change_days: Optional[int]
    revised_pdf_path: Optional[str]
    additional_documents: Optional[str]
    is_active: bool
    is_final: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Summary Schemas für Dashboard
class InspectionSummary(BaseModel):
    id: int
    title: str
    milestone_title: str
    project_name: str
    scheduled_date: datetime
    status: InspectionStatus
    invited_count: int
    accepted_count: int
    completed_count: int

    class Config:
        from_attributes = True 