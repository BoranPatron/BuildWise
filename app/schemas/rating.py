"""
Schemas für Dienstleister-Bewertungen
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict
from datetime import datetime


class ServiceProviderRatingBase(BaseModel):
    """Basis-Schema für Bewertungen"""
    service_provider_id: int = Field(..., description="ID des bewerteten Dienstleisters")
    project_id: int = Field(..., description="ID des Projekts")
    milestone_id: int = Field(..., description="ID des Gewerks/Milestones")
    quote_id: Optional[int] = Field(None, description="ID des Angebots")
    
    quality_rating: float = Field(..., ge=1, le=5, description="Qualität der Ausführung (1-5)")
    timeliness_rating: float = Field(..., ge=1, le=5, description="Termintreue (1-5)")
    communication_rating: float = Field(..., ge=1, le=5, description="Kommunikation & Erreichbarkeit (1-5)")
    value_rating: float = Field(..., ge=1, le=5, description="Preis-Leistungs-Verhältnis (1-5)")
    
    comment: Optional[str] = Field(None, description="Optionaler Kommentar")
    is_public: int = Field(default=1, description="Ob die Bewertung öffentlich ist")
    
    @field_validator('quality_rating', 'timeliness_rating', 'communication_rating', 'value_rating')
    def validate_rating(cls, v):
        """Validiert dass Bewertungen zwischen 1 und 5 liegen"""
        if v < 1 or v > 5:
            raise ValueError('Bewertung muss zwischen 1 und 5 liegen')
        # Erlaube nur halbe Sterne (0.5er Schritte)
        if v % 0.5 != 0:
            raise ValueError('Bewertung muss in 0.5er Schritten erfolgen')
        return v


class ServiceProviderRatingCreate(ServiceProviderRatingBase):
    """Schema für Erstellung von Bewertungen"""
    pass


class BautraegerInfo(BaseModel):
    """Bauträger Info für Response"""
    id: int
    first_name: Optional[str]
    last_name: Optional[str]
    full_name: Optional[str] = None  # Computed field
    company_name: Optional[str]
    
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


class ServiceProviderInfo(BaseModel):
    """Dienstleister Info für Response"""
    id: int
    first_name: Optional[str]
    last_name: Optional[str]
    full_name: Optional[str] = None  # Computed field
    company_name: Optional[str]
    email: Optional[str]
    
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


class MilestoneInfo(BaseModel):
    """Milestone Info für Response"""
    id: int
    title: str
    category: Optional[str]


class ServiceProviderRatingResponse(ServiceProviderRatingBase):
    """Response-Schema für Bewertungen"""
    id: int
    bautraeger_id: int
    bautraeger: Optional[BautraegerInfo]
    service_provider: Optional[ServiceProviderInfo]
    milestone: Optional[MilestoneInfo]
    overall_rating: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ServiceProviderRatingSummary(BaseModel):
    """Zusammenfassung der Bewertungen eines Dienstleisters"""
    service_provider_id: int
    total_ratings: int = Field(..., description="Gesamtanzahl der Bewertungen")
    average_overall_rating: float = Field(..., description="Durchschnittliche Gesamtbewertung")
    average_quality_rating: float = Field(..., description="Durchschnitt Qualität")
    average_timeliness_rating: float = Field(..., description="Durchschnitt Termintreue")
    average_communication_rating: float = Field(..., description="Durchschnitt Kommunikation")
    average_value_rating: float = Field(..., description="Durchschnitt Preis-Leistung")
    rating_distribution: Dict[int, int] = Field(default_factory=dict, description="Verteilung der Bewertungen (1-5)")


class ServiceProviderAggregatedRatingResponse(BaseModel):
    """Response-Schema für aggregierte Bewertungen"""
    service_provider_id: int
    total_ratings: int = Field(..., description="Gesamtanzahl der Bewertungen")
    avg_quality_rating: float = Field(..., description="Durchschnitt Qualität (1 Nachkommastelle)")
    avg_timeliness_rating: float = Field(..., description="Durchschnitt Termintreue (1 Nachkommastelle)")
    avg_communication_rating: float = Field(..., description="Durchschnitt Kommunikation (1 Nachkommastelle)")
    avg_value_rating: float = Field(..., description="Durchschnitt Preis-Leistung (1 Nachkommastelle)")
    avg_overall_rating: float = Field(..., description="Durchschnitt Gesamtbewertung (1 Nachkommastelle)")
    last_updated: datetime
    
    class Config:
        from_attributes = True


class RatingCheckResponse(BaseModel):
    """Response für Prüfung ob Rechnung angesehen werden kann"""
    can_view_invoice: bool = Field(..., description="Ob die Rechnung angesehen werden kann")
    rating_required: bool = Field(..., description="Ob eine Bewertung erforderlich ist")
    rating_exists: bool = Field(..., description="Ob bereits eine Bewertung existiert")