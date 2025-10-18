from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from .base import Base


class ServiceProviderRatingAggregate(Base):
    """Aggregierte Bewertungen pro Service Provider"""
    __tablename__ = "service_provider_rating_aggregates"
    
    service_provider_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    
    # Anzahl der Bewertungen
    total_ratings = Column(Integer, default=0, nullable=False)
    
    # Durchschnittsbewertungen (mit einer Nachkommastelle)
    avg_quality_rating = Column(Float(3, 1), default=0.0, nullable=False)
    avg_timeliness_rating = Column(Float(3, 1), default=0.0, nullable=False)
    avg_communication_rating = Column(Float(3, 1), default=0.0, nullable=False)
    avg_value_rating = Column(Float(3, 1), default=0.0, nullable=False)
    avg_overall_rating = Column(Float(3, 1), default=0.0, nullable=False)
    
    # Timestamps
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship
    service_provider = relationship("User", foreign_keys=[service_provider_id])

