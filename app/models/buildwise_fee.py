from sqlalchemy import Column, Integer, String, Numeric, Date, Boolean, Text, ForeignKey, CheckConstraint, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
import enum

class BuildWiseFeeStatus(enum.Enum):
    OPEN = "open"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class BuildWiseFee(Base):
    __tablename__ = "buildwise_fees"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Referenzen
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=False)
    cost_position_id = Column(Integer, ForeignKey("cost_positions.id"), nullable=False)
    service_provider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Gebühren-Details
    fee_amount = Column(Numeric(10, 2), nullable=False)
    fee_percentage = Column(Numeric(5, 2), nullable=False, default=1.00)
    quote_amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="EUR")
    
    # Rechnungsdaten
    invoice_number = Column(String(50), unique=True, index=True)
    invoice_date = Column(Date)
    due_date = Column(Date)
    payment_date = Column(Date)
    
    # Status und Tracking
    status = Column(String(20), nullable=False, default=BuildWiseFeeStatus.OPEN.value)
    invoice_pdf_path = Column(String(255))
    invoice_pdf_generated = Column(Boolean, default=False)
    
    # Steuerrelevante Daten
    tax_rate = Column(Numeric(5, 2), default=19.00)
    tax_amount = Column(Numeric(10, 2))
    net_amount = Column(Numeric(10, 2))
    gross_amount = Column(Numeric(10, 2))
    
    # Metadaten
    fee_details = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Beziehungen - ohne lazy loading um Greenlet-Probleme zu vermeiden
    project = relationship("Project", back_populates="buildwise_fees", lazy="select")
    quote = relationship("Quote", back_populates="buildwise_fees", lazy="select")
    cost_position = relationship("CostPosition", back_populates="buildwise_fees", lazy="select")
    service_provider = relationship("User", back_populates="buildwise_fees", lazy="select")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('open', 'paid', 'overdue', 'cancelled')", name="valid_status"),
        CheckConstraint("fee_percentage >= 0 AND fee_percentage <= 100", name="valid_percentage"),
        CheckConstraint("fee_amount >= 0", name="valid_fee_amount"),
        CheckConstraint("quote_amount >= 0", name="valid_quote_amount"),
    )

class BuildWiseFeeItem(Base):
    __tablename__ = "buildwise_fee_items"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Referenzen
    buildwise_fee_id = Column(Integer, ForeignKey("buildwise_fees.id"), nullable=False)
    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=False)
    cost_position_id = Column(Integer, ForeignKey("cost_positions.id"), nullable=False)
    
    # Einzelne Gebühren-Positionen
    quote_amount = Column(Numeric(10, 2), nullable=False)
    fee_amount = Column(Numeric(10, 2), nullable=False)
    fee_percentage = Column(Numeric(5, 2), nullable=False, default=1.00)
    description = Column(Text)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # Beziehungen
    buildwise_fee = relationship("BuildWiseFee", back_populates=None)
    quote = relationship("Quote")
    cost_position = relationship("CostPosition")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("fee_percentage >= 0 AND fee_percentage <= 100", name="valid_item_percentage"),
        CheckConstraint("fee_amount >= 0", name="valid_item_fee_amount"),
        CheckConstraint("quote_amount >= 0", name="valid_item_quote_amount"),
    ) 