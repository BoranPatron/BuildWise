from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from ..models.acceptance import AcceptanceStatus, AcceptanceType, DefectSeverity


# Request/Response Models für Abnahme
class AcceptanceDefectBase(BaseModel):
    title: str = Field(..., description="Kurze Beschreibung des Mangels")
    description: Optional[str] = Field(None, description="Detaillierte Beschreibung")
    severity: DefectSeverity = Field(default=DefectSeverity.MINOR, description="Schweregrad")
    location: Optional[str] = Field(None, description="Ort des Mangels")
    room: Optional[str] = Field(None, description="Raum/Bereich")
    estimated_cost: Optional[float] = Field(None, description="Geschätzte Behebungskosten")
    deadline: Optional[datetime] = Field(None, description="Frist zur Behebung")
    photos: Optional[List[str]] = Field(default=[], description="Foto-URLs")
    photo_annotations: Optional[Dict[str, Any]] = Field(default={}, description="Foto-Annotation Daten")


class AcceptanceDefectCreate(AcceptanceDefectBase):
    pass


class AcceptanceDefectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[DefectSeverity] = None
    location: Optional[str] = None
    room: Optional[str] = None
    resolved: Optional[bool] = None
    resolution_notes: Optional[str] = None
    actual_cost: Optional[float] = None
    deadline: Optional[datetime] = None
    photos: Optional[List[str]] = None
    resolution_photos: Optional[List[str]] = None


class AcceptanceDefectResponse(AcceptanceDefectBase):
    id: int
    acceptance_id: int
    resolved: bool
    resolution_notes: Optional[str]
    resolved_at: Optional[datetime]
    resolved_by: Optional[int]
    actual_cost: Optional[float]
    resolution_photos: Optional[List[str]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Abnahme Base Models
class AcceptanceBase(BaseModel):
    acceptance_type: AcceptanceType = Field(default=AcceptanceType.FINAL, description="Art der Abnahme")
    scheduled_date: Optional[datetime] = Field(None, description="Geplanter Abnahme-Termin")
    acceptance_notes: Optional[str] = Field(None, description="Allgemeine Notizen")
    contractor_notes: Optional[str] = Field(None, description="Notizen des Bauträgers")
    service_provider_notes: Optional[str] = Field(None, description="Notizen des Dienstleisters")
    quality_rating: Optional[int] = Field(None, ge=1, le=5, description="Qualitätsbewertung (1-5)")
    timeliness_rating: Optional[int] = Field(None, ge=1, le=5, description="Terminbewertung (1-5)")
    overall_rating: Optional[int] = Field(None, ge=1, le=5, description="Gesamtbewertung (1-5)")
    photos: Optional[List[str]] = Field(default=[], description="Foto-URLs")
    documents: Optional[List[str]] = Field(default=[], description="Dokument-URLs")
    checklist_data: Optional[Dict[str, Any]] = Field(default={}, description="Checkliste Daten")
    review_date: Optional[datetime] = Field(None, description="Wiedervorlage-Datum")
    review_notes: Optional[str] = Field(None, description="Wiedervorlage-Notizen")
    warranty_period_months: int = Field(default=24, description="Gewährleistungszeit in Monaten")


class AcceptanceCreate(AcceptanceBase):
    project_id: int = Field(..., description="Projekt-ID")
    milestone_id: int = Field(..., description="Gewerk-ID")
    service_provider_id: int = Field(..., description="Dienstleister-ID")
    appointment_id: Optional[int] = Field(None, description="Termin-ID (optional)")


class AcceptanceUpdate(BaseModel):
    status: Optional[AcceptanceStatus] = None
    acceptance_type: Optional[AcceptanceType] = None
    scheduled_date: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    accepted: Optional[bool] = None
    acceptance_notes: Optional[str] = None
    contractor_notes: Optional[str] = None
    service_provider_notes: Optional[str] = None
    quality_rating: Optional[int] = Field(None, ge=1, le=5)
    timeliness_rating: Optional[int] = Field(None, ge=1, le=5)
    overall_rating: Optional[int] = Field(None, ge=1, le=5)
    photos: Optional[List[str]] = None
    documents: Optional[List[str]] = None
    checklist_data: Optional[Dict[str, Any]] = None
    review_date: Optional[datetime] = None
    review_notes: Optional[str] = None
    warranty_period_months: Optional[int] = None


class AcceptanceResponse(AcceptanceBase):
    id: int
    project_id: int
    milestone_id: int
    appointment_id: Optional[int]
    contractor_id: int
    service_provider_id: int
    created_by: int
    status: AcceptanceStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    accepted: Optional[bool]
    protocol_pdf_path: Optional[str]
    protocol_generated_at: Optional[datetime]
    warranty_start_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    # Nested relationships
    defects: List[AcceptanceDefectResponse] = []

    class Config:
        from_attributes = True


# Spezielle Request Models
class AcceptanceScheduleRequest(BaseModel):
    """Request für Terminvereinbarung zur Abnahme"""
    milestone_id: int = Field(..., description="Gewerk-ID")
    proposed_date: datetime = Field(..., description="Vorgeschlagener Termin")
    notes: Optional[str] = Field(None, description="Zusätzliche Notizen")


class AcceptanceScheduleResponse(BaseModel):
    """Response für Terminvorschlag"""
    accepted: bool = Field(..., description="Termin akzeptiert")
    message: Optional[str] = Field(None, description="Nachricht")
    counter_proposal: Optional[datetime] = Field(None, description="Gegenvorschlag")


class AcceptanceStartRequest(BaseModel):
    """Request für Start der Abnahme"""
    acceptance_id: int = Field(..., description="Abnahme-ID")
    notes: Optional[str] = Field(None, description="Anfangsnotizen")


class AcceptanceCompleteRequest(BaseModel):
    """Request für Abschluss der Abnahme"""
    acceptance_id: int = Field(..., description="Abnahme-ID")
    accepted: bool = Field(..., description="Abnahme erfolgreich")
    acceptance_notes: Optional[str] = Field(None, description="Abnahme-Notizen")
    contractor_notes: Optional[str] = Field(None, description="Bauträger-Notizen")
    quality_rating: Optional[int] = Field(None, ge=1, le=5, description="Qualitätsbewertung")
    timeliness_rating: Optional[int] = Field(None, ge=1, le=5, description="Terminbewertung")
    overall_rating: Optional[int] = Field(None, ge=1, le=5, description="Gesamtbewertung")
    photos: Optional[List[str]] = Field(default=[], description="Foto-URLs")
    defects: Optional[List[AcceptanceDefectCreate]] = Field(default=[], description="Mängelliste")


class AcceptanceStatusUpdate(BaseModel):
    """Status-Update für Abnahme"""
    status: AcceptanceStatus = Field(..., description="Neuer Status")
    notes: Optional[str] = Field(None, description="Notizen zum Status-Update")


# Dashboard/Übersicht Models
class AcceptanceSummary(BaseModel):
    """Zusammenfassung für Dashboard"""
    total_acceptances: int
    pending_acceptances: int
    completed_acceptances: int
    accepted_count: int
    rejected_count: int
    defects_count: int
    average_rating: Optional[float]


class AcceptanceListItem(BaseModel):
    """Listeneintrag für Übersichten"""
    id: int
    project_id: int
    milestone_id: int
    milestone_title: str
    project_title: str
    status: AcceptanceStatus
    acceptance_type: AcceptanceType
    scheduled_date: Optional[datetime]
    completed_at: Optional[datetime]
    accepted: Optional[bool]
    defects_count: int
    overall_rating: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True