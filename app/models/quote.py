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
    service_provider_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(QuoteStatus), nullable=False, default=QuoteStatus.DRAFT)
    
    # Angebotsdetails
    total_amount = Column(Float, nullable=False)
    currency = Column(String, default="EUR")
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
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="quotes")
    service_provider = relationship("User") 