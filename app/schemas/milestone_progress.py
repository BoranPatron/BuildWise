"""
Schemas für Baufortschrittsdokumentation
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class MilestoneProgressBase(BaseModel):
    """Basis-Schema für Progress Updates"""
    update_type: str = Field(default="comment", description="Typ des Updates")
    message: str = Field(..., description="Nachricht/Kommentar")
    progress_percentage: Optional[int] = Field(None, ge=0, le=100, description="Fortschritt in Prozent")
    parent_id: Optional[int] = Field(None, description="ID des Parent-Updates für Antworten")
    defect_severity: Optional[str] = Field(None, description="Schweregrad des Mangels")
    revision_deadline: Optional[datetime] = Field(None, description="Frist für Nachbesserung")
    is_internal: bool = Field(default=False, description="Nur für Bauträger sichtbar")


class MilestoneProgressCreate(MilestoneProgressBase):
    """Schema für Erstellung von Progress Updates"""
    attachments: Optional[List[dict]] = Field(None, description="Liste von Anhängen")


class MilestoneProgressUpdate(BaseModel):
    """Schema für Aktualisierung von Progress Updates"""
    message: Optional[str] = None
    defect_resolved: Optional[bool] = None
    revision_completed: Optional[bool] = None


class UserInfo(BaseModel):
    """Basis User Info für Response"""
    id: int
    first_name: Optional[str]
    last_name: Optional[str]
    full_name: Optional[str] = None  # Computed field
    company_name: Optional[str]
    user_type: str
    
    def __init__(self, **data):
        super().__init__(**data)
        # Compute full_name from first_name and last_name
        if self.first_name and self.last_name:
            self.full_name = f"{self.first_name} {self.last_name}"
        elif self.first_name:
            self.full_name = self.first_name
        elif self.last_name:
            self.full_name = self.last_name
        else:
            self.full_name = None


class MilestoneProgressResponse(MilestoneProgressBase):
    """Response-Schema für Progress Updates"""
    id: int
    milestone_id: int
    user_id: int
    user: UserInfo
    attachments: Optional[List[dict]] = None
    defect_resolved: bool = False
    revision_completed: bool = False
    created_at: datetime
    updated_at: datetime
    replies: List['MilestoneProgressResponse'] = []
    
    class Config:
        from_attributes = True


class CompletionRequestCreate(BaseModel):
    """Schema für Fertigstellungsanfrage"""
    message: Optional[str] = Field(None, description="Optionale Nachricht")
    completion_photos: Optional[List[dict]] = Field(None, description="Fotos der Fertigstellung")
    completion_documents: Optional[List[dict]] = Field(None, description="Dokumente zur Fertigstellung")


class CompletionResponseCreate(BaseModel):
    """Schema für Antwort auf Fertigstellungsanfrage"""
    accepted: bool = Field(..., description="Ob die Fertigstellung akzeptiert wird")
    message: Optional[str] = Field(None, description="Nachricht/Begründung")
    revision_deadline: Optional[datetime] = Field(None, description="Frist für Nachbesserung (wenn abgelehnt)")


# Für zirkuläre Referenzen
MilestoneProgressResponse.model_rebuild()