from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class AppointmentType(str, Enum):
    INSPECTION = "INSPECTION"
    MEETING = "MEETING"
    CONSULTATION = "CONSULTATION"
    REVIEW = "REVIEW"


class AppointmentStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    CONFIRMED = "CONFIRMED"
    PENDING_RESPONSE = "PENDING_RESPONSE"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    REJECTED_WITH_SUGGESTION = "REJECTED_WITH_SUGGESTION"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ServiceProviderInvite(BaseModel):
    """Service Provider Einladung für Termin"""
    id: int
    email: str
    name: str
    status: str = "pending"


class ServiceProviderResponse(BaseModel):
    """Antwort eines Service Providers auf eine Termineinladung"""
    service_provider_id: int
    status: str  # "accepted", "rejected", "rejected_with_suggestion"
    message: Optional[str] = None
    suggested_date: Optional[datetime] = None


class AppointmentBase(BaseModel):
    """Basis-Schema für Appointments"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    appointment_type: AppointmentType = AppointmentType.INSPECTION
    scheduled_date: datetime
    duration_minutes: int = Field(default=60, ge=15, le=480)
    location: Optional[str] = None
    location_details: Optional[str] = None


class AppointmentCreate(AppointmentBase):
    """Schema für das Erstellen eines Appointments"""
    project_id: int
    milestone_id: Optional[int] = None
    invited_service_provider_ids: List[int] = Field(default_factory=list)


class AppointmentUpdate(BaseModel):
    """Schema für das Aktualisieren eines Appointments"""
    title: Optional[str] = None
    description: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=15, le=480)
    location: Optional[str] = None
    location_details: Optional[str] = None
    status: Optional[AppointmentStatus] = None
    inspection_notes: Optional[str] = None
    requires_renegotiation: Optional[bool] = None
    renegotiation_details: Optional[str] = None


class AppointmentResponse(BaseModel):
    """Schema für Appointment-Antworten"""
    id: int
    project_id: int
    milestone_id: Optional[int]
    created_by: int
    title: str
    description: Optional[str]
    appointment_type: AppointmentType
    status: AppointmentStatus
    scheduled_date: datetime
    duration_minutes: int
    location: Optional[str]
    location_details: Optional[str]
    invited_service_providers: Optional[List[ServiceProviderInvite]]
    responses: Optional[List[ServiceProviderResponse]]
    inspection_completed: bool
    selected_service_provider_id: Optional[int]
    inspection_notes: Optional[str]
    requires_renegotiation: bool
    renegotiation_details: Optional[str]
    notification_sent: bool
    follow_up_notification_date: Optional[datetime]
    follow_up_sent: bool
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class InspectionDecisionRequest(BaseModel):
    """Schema für die Entscheidung nach der Besichtigung"""
    appointment_id: int
    selected_service_provider_id: int
    inspection_notes: Optional[str] = None
    requires_renegotiation: bool = False
    renegotiation_details: Optional[str] = None


class AppointmentResponseRequest(BaseModel):
    """Schema für Service Provider Antworten auf Termineinladungen"""
    appointment_id: int
    status: str  # "accepted", "rejected", "rejected_with_suggestion"
    message: Optional[str] = None
    suggested_date: Optional[datetime] = None


class CalendarEventData(BaseModel):
    """Schema für Kalendereintrag-Daten (.ics)"""
    title: str
    description: str
    start_date: datetime
    end_date: datetime
    location: str
    attendees: List[str]  # E-Mail-Adressen
    organizer: str


class NotificationRequest(BaseModel):
    """Schema für Benachrichtigungsanfragen"""
    appointment_id: int
    message: Optional[str] = None 