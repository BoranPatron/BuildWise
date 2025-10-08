"""
Contact Schemas
Pydantic models für Kontaktbuch-Daten
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class ContactBase(BaseModel):
    """Basis-Schema für Contact"""
    company_name: str = Field(..., min_length=1, max_length=255, description="Firmenname")
    contact_person: Optional[str] = Field(None, max_length=255, description="Ansprechpartner")
    email: Optional[EmailStr] = Field(None, description="E-Mail-Adresse")
    phone: Optional[str] = Field(None, max_length=50, description="Telefonnummer")
    website: Optional[str] = Field(None, max_length=255, description="Website")
    category: Optional[str] = Field(None, max_length=100, description="Kategorie/Gewerk")
    rating: Optional[float] = Field(None, ge=0, le=5, description="Bewertung (0-5)")
    notes: Optional[str] = Field(None, description="Notizen")
    address_street: Optional[str] = Field(None, max_length=255, description="Straße")
    address_city: Optional[str] = Field(None, max_length=100, description="Stadt")
    address_zip: Optional[str] = Field(None, max_length=20, description="PLZ")
    address_country: Optional[str] = Field("Deutschland", max_length=100, description="Land")
    milestone_id: Optional[int] = Field(None, description="Verknüpftes Gewerk")
    project_id: Optional[int] = Field(None, description="Verknüpftes Projekt")
    service_provider_id: Optional[int] = Field(None, description="Dienstleister-ID")
    favorite: Optional[bool] = Field(False, description="Favorit")


class ContactCreate(ContactBase):
    """Schema für Contact-Erstellung"""
    pass


class ContactUpdate(BaseModel):
    """Schema für Contact-Aktualisierung"""
    company_name: Optional[str] = Field(None, min_length=1, max_length=255)
    contact_person: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = Field(None, max_length=255)
    category: Optional[str] = Field(None, max_length=100)
    rating: Optional[float] = Field(None, ge=0, le=5)
    notes: Optional[str] = None
    address_street: Optional[str] = Field(None, max_length=255)
    address_city: Optional[str] = Field(None, max_length=100)
    address_zip: Optional[str] = Field(None, max_length=20)
    address_country: Optional[str] = Field(None, max_length=100)
    milestone_id: Optional[int] = None
    project_id: Optional[int] = None
    service_provider_id: Optional[int] = None
    favorite: Optional[bool] = None


class ContactRead(ContactBase):
    """Schema für Contact-Ausgabe"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

