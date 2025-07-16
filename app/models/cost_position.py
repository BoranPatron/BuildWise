from sqlalchemy import Column, Integer, String, Float, Text, Date, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from .base import Base


class CostCategory(enum.Enum):
    """Kategorien für Kostenpositionen"""
    ELECTRICAL = "electrical"
    PLUMBING = "plumbing"
    HEATING = "heating"
    ROOFING = "roofing"
    MASONRY = "masonry"
    DRYWALL = "drywall"
    PAINTING = "painting"
    FLOORING = "flooring"
    LANDSCAPING = "landscaping"
    KITCHEN = "kitchen"
    BATHROOM = "bathroom"
    OTHER = "other"


class CostType(enum.Enum):
    """Typen von Kostenpositionen"""
    QUOTE_ACCEPTED = "quote_accepted"
    MANUAL = "manual"
    MATERIAL = "material"
    LABOR = "labor"
    EQUIPMENT = "equipment"
    SERVICES = "services"
    PERMITS = "permits"


class CostStatus(enum.Enum):
    """Status von Kostenpositionen"""
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class CostPosition(Base):
    """Kostenpositionen für Projekte (z.B. aus akzeptierten Angeboten)"""
    __tablename__ = "cost_positions"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    
    # Grundinformationen
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="EUR")
    
    # Kategorisierung
    category = Column(Enum(CostCategory), nullable=False, default=CostCategory.OTHER)
    cost_type = Column(Enum(CostType), nullable=False, default=CostType.MANUAL)
    status = Column(Enum(CostStatus), nullable=False, default=CostStatus.ACTIVE)
    
    # Zahlungsbedingungen
    payment_terms = Column(Text, nullable=True)
    warranty_period = Column(Integer, nullable=True)  # in Monaten
    
    # Zeitplan
    estimated_duration = Column(Integer, nullable=True)  # in Tagen
    start_date = Column(Date, nullable=True)
    completion_date = Column(Date, nullable=True)
    
    # Auftragnehmer-Informationen (aus akzeptierten Angeboten)
    contractor_name = Column(String, nullable=True)
    contractor_contact = Column(String, nullable=True)
    contractor_phone = Column(String, nullable=True)
    contractor_email = Column(String, nullable=True)
    contractor_website = Column(String, nullable=True)
    
    # Verknüpfungen zu anderen Modellen
    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=True)  # Verknüpfung zum ursprünglichen Angebot
    milestone_id = Column(Integer, ForeignKey("milestones.id"), nullable=True)  # Verknüpfung zum Gewerk
    service_provider_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Verknüpfung zum Dienstleister
    
    # Kostenaufschlüsselung
    labor_cost = Column(Float, nullable=True)
    material_cost = Column(Float, nullable=True)
    overhead_cost = Column(Float, nullable=True)
    
    # KI-Analyse (aus dem ursprünglichen Angebot)
    risk_score = Column(Float, nullable=True)  # 0-100
    price_deviation = Column(Float, nullable=True)  # Prozent vom Durchschnitt
    ai_recommendation = Column(String, nullable=True)
    
    # Fortschritt und Abrechnung
    progress_percentage = Column(Float, default=0.0)
    paid_amount = Column(Float, default=0.0)
    last_payment_date = Column(Date, nullable=True)
    
    # Notizen und Dokumente
    notes = Column(Text, nullable=True)
    invoice_references = Column(Text, nullable=True)  # JSON-Array mit Rechnungsreferenzen
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="cost_positions")
    quote = relationship("Quote")
    milestone = relationship("Milestone")
    service_provider = relationship("User")
    buildwise_fees = relationship("BuildWiseFee", back_populates="cost_position") 