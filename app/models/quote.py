from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, Enum, Float, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from .base import Base


class QuoteStatus(enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class Quote(Base):
    __tablename__ = "quotes"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    milestone_id = Column(Integer, ForeignKey("milestones.id", ondelete="CASCADE"), nullable=True)  # Verknüpfung zum Gewerk
    service_provider_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(QuoteStatus), nullable=False, default=QuoteStatus.DRAFT)
    
    # Angebotsdetails
    total_amount = Column(Float, nullable=False)
    currency = Column(String, default="CHF")
    valid_until = Column(Date, nullable=True)
    
    # Aufschlüsselung
    labor_cost = Column(Float, nullable=True)
    material_cost = Column(Float, nullable=True)
    overhead_cost = Column(Float, nullable=True)
    
    # Zeitplan
    estimated_duration = Column(Integer, nullable=True)  # in Tagen
    start_date = Column(Date, nullable=True)
    completion_date = Column(Date, nullable=True)
    
    # Bedingungen
    payment_terms = Column(Text, nullable=True)
    warranty_period = Column(Integer, nullable=True)  # in Monaten
    
    # KI-Analyse
    risk_score = Column(Float, nullable=True)  # 0-100
    price_deviation = Column(Float, nullable=True)  # Prozent vom Durchschnitt
    ai_recommendation = Column(String, nullable=True)
    
    # Kontaktfreigabe
    contact_released = Column(Boolean, default=False)
    contact_released_at = Column(DateTime(timezone=True), nullable=True)
    
    # Zusätzliche Felder für Dienstleister-Angebote
    quote_number = Column(String, nullable=True)  # Angebotsnummer
    company_name = Column(String, nullable=True)  # Firmenname des Dienstleisters
    contact_person = Column(String, nullable=True)  # Ansprechpartner
    phone = Column(String, nullable=True)  # Telefonnummer
    email = Column(String, nullable=True)  # E-Mail
    website = Column(String, nullable=True)  # Website
    
    # Qualifikationen und Referenzen
    qualifications = Column(Text, nullable=True)  # Qualifikationen & Zertifizierungen
    references = Column(Text, nullable=True)  # Referenzen
    certifications = Column(Text, nullable=True)  # Zertifizierungen
    
    # Technische Details
    technical_approach = Column(Text, nullable=True)  # Technischer Ansatz
    quality_standards = Column(Text, nullable=True)  # Qualitätsstandards
    safety_measures = Column(Text, nullable=True)  # Sicherheitsmaßnahmen
    environmental_compliance = Column(Text, nullable=True)  # Umweltcompliance
    
    # Risiko-Bewertung
    risk_assessment = Column(Text, nullable=True)  # Risikobewertung
    contingency_plan = Column(Text, nullable=True)  # Notfallplan
    
    # Zusätzliche Informationen
    additional_notes = Column(Text, nullable=True)  # Zusätzliche Notizen
    
    # Dokumente
    pdf_upload_path = Column(String, nullable=True)  # Pfad zum hochgeladenen PDF
    additional_documents = Column(Text, nullable=True)  # JSON-Array mit zusätzlichen Dokumenten
    
    # Bewertung und Feedback
    rating = Column(Float, nullable=True)  # Bewertung (1-5 Sterne)
    feedback = Column(Text, nullable=True)  # Feedback vom Bauträger
    
    # Ablehnungsgrund
    rejection_reason = Column(Text, nullable=True)  # Grund für Ablehnung
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="quotes")
    milestone = relationship("Milestone")  # Verknüpfung zum Gewerk
    service_provider = relationship("User")
    buildwise_fees = relationship("BuildWiseFee", back_populates="quote")
    resource_allocations = relationship("ResourceAllocation", back_populates="quote")
