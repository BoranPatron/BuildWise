"""
Notification Preference Schemas
Pydantic Schemas für Benachrichtigungspräferenzen
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class NotificationPreferenceBase(BaseModel):
    """Basis-Schema für Benachrichtigungspräferenzen"""
    contact_id: int = Field(..., description="ID des Kontakts")
    service_provider_id: int = Field(..., description="ID des Dienstleisters")
    enabled: bool = Field(True, description="Benachrichtigungen aktiviert")
    categories: List[str] = Field(default_factory=list, description="Liste der Kategorien für Benachrichtigungen")


class NotificationPreferenceCreate(NotificationPreferenceBase):
    """Schema zum Erstellen einer Benachrichtigungspräferenz"""
    pass


class NotificationPreferenceUpdate(BaseModel):
    """Schema zum Aktualisieren einer Benachrichtigungspräferenz"""
    enabled: Optional[bool] = Field(None, description="Benachrichtigungen aktiviert")
    categories: Optional[List[str]] = Field(None, description="Liste der Kategorien")


class NotificationPreferenceToggle(BaseModel):
    """Schema zum Umschalten des enabled-Status"""
    enabled: bool = Field(..., description="Benachrichtigungen aktiviert")


class NotificationPreferenceCategories(BaseModel):
    """Schema zum Aktualisieren der Kategorien"""
    categories: List[str] = Field(..., description="Liste der Kategorien")


class NotificationPreference(NotificationPreferenceBase):
    """Vollständiges Schema für Benachrichtigungspräferenz (Response)"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class NotificationPreferenceInDB(NotificationPreference):
    """Schema für Datenbankrepräsentation"""
    pass

