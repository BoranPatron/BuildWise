"""
Invoice models for construction billing and payment management
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .base import Base

class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    VIEWED = "viewed"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class InvoiceType(str, enum.Enum):
    MANUAL = "manual"
    UPLOAD = "upload"

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    
    # Verknüpfungen
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    milestone_id = Column(Integer, ForeignKey("milestones.id"), nullable=False)
    service_provider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Rechnungsdetails
    invoice_number = Column(String(100), nullable=False, unique=True)
    invoice_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=False)
    
    # Beträge
    net_amount = Column(Float, nullable=False, default=0.0)
    vat_rate = Column(Float, nullable=False, default=19.0)
    vat_amount = Column(Float, nullable=False, default=0.0)
    total_amount = Column(Float, nullable=False)
    
    # Kostenaufstellung (für manuelle Rechnungen)
    material_costs = Column(Float, default=0.0)
    labor_costs = Column(Float, default=0.0)
    additional_costs = Column(Float, default=0.0)
    
    # Beschreibung und Leistungszeitraum
    description = Column(Text)
    work_period_from = Column(DateTime, nullable=True)
    work_period_to = Column(DateTime, nullable=True)
    
    # Status und Typ
    status = Column(SQLEnum(InvoiceStatus), default=InvoiceStatus.DRAFT)
    type = Column(SQLEnum(InvoiceType), nullable=False)
    
    # PDF-Datei (für Upload-Rechnungen)
    pdf_file_path = Column(String(500), nullable=True)
    pdf_file_name = Column(String(255), nullable=True)
    
    # Zusätzliche Informationen
    notes = Column(Text)
    
    # Zahlungsinformationen
    paid_at = Column(DateTime, nullable=True)
    payment_reference = Column(String(255), nullable=True)
    
    # Bewertung (wird nach Zahlung gesetzt)
    rating_quality = Column(Integer, nullable=True)  # 1-5 Sterne
    rating_timeliness = Column(Integer, nullable=True)  # 1-5 Sterne
    rating_overall = Column(Integer, nullable=True)  # 1-5 Sterne
    rating_notes = Column(Text, nullable=True)
    rated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    rated_at = Column(DateTime, nullable=True)
    
    # Metadaten
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    project = relationship("Project", back_populates="invoices")
    milestone = relationship("Milestone", back_populates="invoices")
    service_provider = relationship("User", foreign_keys=[service_provider_id], back_populates="created_invoices")
    creator = relationship("User", foreign_keys=[created_by])
    rater = relationship("User", foreign_keys=[rated_by])

    def __repr__(self):
        return f"<Invoice(id={self.id}, number={self.invoice_number}, total={self.total_amount})>"