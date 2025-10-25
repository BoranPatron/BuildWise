from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum
import json


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
    
    @field_validator('suggested_date', mode='before')
    @classmethod
    def parse_date_strings(cls, v):
        """Konvertiert Datum-Strings zu DateTime-Objekten"""
        if isinstance(v, str):
            # Wenn nur Datum ohne Zeit, füge 00:00:00 hinzu
            if len(v) == 10 and v.count('-') == 2:  # Format: YYYY-MM-DD
                return datetime.fromisoformat(f"{v}T00:00:00")
            # Versuche direkt zu parsen
            try:
                return datetime.fromisoformat(v)
            except ValueError:
                # Fallback: versuche verschiedene Formate
                try:
                    # Einfacher Fallback ohne dateutil
                    import datetime as dt
                    return dt.datetime.strptime(v, '%Y-%m-%d')
                except ValueError:
                    # Letzter Fallback
                    return datetime.fromisoformat(f"{v}T00:00:00")
        return v


class AppointmentBase(BaseModel):
    """Basis-Schema für Appointments"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    appointment_type: AppointmentType = AppointmentType.INSPECTION
    scheduled_date: datetime
    duration_minutes: int = Field(default=60, ge=15, le=480)
    location: Optional[str] = None
    location_details: Optional[str] = None
    # Erweiterte Besichtigungsdetails
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    preparation_notes: Optional[str] = None
    
    @field_validator('scheduled_date', mode='before')
    @classmethod
    def parse_date_strings(cls, v):
        """Konvertiert Datum-Strings zu DateTime-Objekten"""
        if isinstance(v, str):
            # Wenn nur Datum ohne Zeit, füge 00:00:00 hinzu
            if len(v) == 10 and v.count('-') == 2:  # Format: YYYY-MM-DD
                return datetime.fromisoformat(f"{v}T00:00:00")
            # Versuche direkt zu parsen
            try:
                return datetime.fromisoformat(v)
            except ValueError:
                # Fallback: versuche verschiedene Formate
                try:
                    # Einfacher Fallback ohne dateutil
                    import datetime as dt
                    return dt.datetime.strptime(v, '%Y-%m-%d')
                except ValueError:
                    # Letzter Fallback
                    return datetime.fromisoformat(f"{v}T00:00:00")
        return v


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
    
    @field_validator('scheduled_date', mode='before')
    @classmethod
    def parse_date_strings(cls, v):
        """Konvertiert Datum-Strings zu DateTime-Objekten"""
        if isinstance(v, str):
            # Wenn nur Datum ohne Zeit, füge 00:00:00 hinzu
            if len(v) == 10 and v.count('-') == 2:  # Format: YYYY-MM-DD
                return datetime.fromisoformat(f"{v}T00:00:00")
            # Versuche direkt zu parsen
            try:
                return datetime.fromisoformat(v)
            except ValueError:
                # Fallback: versuche verschiedene Formate
                try:
                    # Einfacher Fallback ohne dateutil
                    import datetime as dt
                    return dt.datetime.strptime(v, '%Y-%m-%d')
                except ValueError:
                    # Letzter Fallback
                    return datetime.fromisoformat(f"{v}T00:00:00")
        return v


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
    # Erweiterte Besichtigungsdetails
    contact_person: Optional[str]
    contact_phone: Optional[str]
    preparation_notes: Optional[str]
    invited_service_providers: Optional[Union[List[ServiceProviderInvite], List[Dict[str, Any]]]]
    responses: Optional[Union[List[ServiceProviderResponse], List[Dict[str, Any]]]]
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
    
    @field_validator('invited_service_providers', mode='before')
    @classmethod
    def validate_invited_service_providers(cls, v):
        """Konvertiere JSON/Dict zu ServiceProviderInvite Objekten"""
        if v is None:
            return None
        
        # Wenn es ein JSON-String ist, parse ihn
        if isinstance(v, str):
            try:
                v = json.loads(v)
            except json.JSONDecodeError:
                return None
        
        # Wenn es bereits eine Liste von ServiceProviderInvite Objekten ist, returniere sie
        if isinstance(v, list) and all(isinstance(item, ServiceProviderInvite) for item in v):
            return v
        
        # Konvertiere Dictionaries zu ServiceProviderInvite Objekten
        if isinstance(v, list):
            result = []
            for item in v:
                if isinstance(item, dict):
                    result.append(ServiceProviderInvite(**item))
                elif isinstance(item, ServiceProviderInvite):
                    result.append(item)
            return result
        
        return None
    
    @field_validator('responses', mode='before')
    @classmethod
    def validate_responses(cls, v):
        """Konvertiere JSON/Dict zu ServiceProviderResponse Objekten"""
        if v is None:
            return None
        
        # Wenn es ein JSON-String ist, parse ihn
        if isinstance(v, str):
            try:
                v = json.loads(v)
            except json.JSONDecodeError:
                return None
        
        # Wenn es bereits eine Liste von ServiceProviderResponse Objekten ist, returniere sie
        if isinstance(v, list) and all(isinstance(item, ServiceProviderResponse) for item in v):
            return v
        
        # Konvertiere Dictionaries zu ServiceProviderResponse Objekten
        if isinstance(v, list):
            result = []
            for item in v:
                if isinstance(item, dict):
                    # ServiceProviderResponse erwartet bestimmte Felder
                    result.append(ServiceProviderResponse(**item))
                elif isinstance(item, ServiceProviderResponse):
                    result.append(item)
            return result
        
        return None


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