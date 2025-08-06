"""
Cost Position models for flexible invoice line items
"""
from sqlalchemy import Column, Integer, Float, DateTime, Text, String, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class CostPosition(Base):
    """Einzelne Kostenposition in einer Rechnung"""
    __tablename__ = "cost_positions"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)  # Hinzugefügt für DB-Kompatibilität
    description = Column(Text, nullable=False)
    amount = Column(Float, nullable=False, default=0.0)
    position_order = Column(Integer, default=0)
    category = Column(String, nullable=False, default="custom")  # Kategorie: material, labor, other, custom
    cost_type = Column(String, nullable=False, default="standard")  # Fehlende Spalte
    status = Column(String, nullable=False, default="active")  # Status: active, deleted, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Beziehung zur Rechnung
    invoice = relationship("Invoice", back_populates="cost_positions")
    
    # Beziehung zu BuildWise Fees
    buildwise_fees = relationship("BuildWiseFee", back_populates="cost_position")
    
    def __repr__(self):
        return f"<CostPosition(id={self.id}, description='{self.description}', amount={self.amount})>" 