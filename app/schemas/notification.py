from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from ..models.notification import NotificationType, NotificationPriority

class NotificationBase(BaseModel):
    """Basis-Schema für Benachrichtigungen"""
    recipient_id: int
    type: NotificationType
    priority: NotificationPriority = NotificationPriority.NORMAL
    title: str = Field(..., max_length=255)
    message: str
    data: Optional[str] = None  # JSON-String
    related_quote_id: Optional[int] = None
    related_project_id: Optional[int] = None
    related_milestone_id: Optional[int] = None
    related_appointment_id: Optional[int] = None

class NotificationCreate(NotificationBase):
    """Schema für das Erstellen von Benachrichtigungen"""
    pass

class NotificationUpdate(BaseModel):
    """Schema für das Aktualisieren von Benachrichtigungen"""
    is_read: Optional[bool] = None
    is_acknowledged: Optional[bool] = None

class NotificationRead(NotificationBase):
    """Schema für das Lesen von Benachrichtigungen"""
    id: int
    is_read: bool
    is_acknowledged: bool
    created_at: datetime
    read_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class NotificationStats(BaseModel):
    """Schema für Benachrichtigungsstatistiken"""
    total_count: int
    unread_count: int
    unacknowledged_count: int
    urgent_count: int
    
class NotificationBulkAction(BaseModel):
    """Schema für Bulk-Aktionen auf Benachrichtigungen"""
    notification_ids: list[int]
    action: str = Field(..., pattern="^(mark_read|acknowledge|delete)$")

# Spezielle Schemas für verschiedene Benachrichtigungstypen
class QuoteNotificationData(BaseModel):
    """Datenstruktur für Quote-bezogene Benachrichtigungen"""
    quote_id: int
    quote_title: str
    service_provider_name: str
    project_name: str
    milestone_title: str
    total_amount: Optional[float] = None
    currency: Optional[str] = "CHF"

class AppointmentNotificationData(BaseModel):
    """Datenstruktur für Termin-bezogene Benachrichtigungen"""
    appointment_id: int
    appointment_title: str
    scheduled_date: datetime
    location: Optional[str] = None
    organizer_name: str
    participant_names: list[str] = []
