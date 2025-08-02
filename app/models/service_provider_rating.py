from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from .base import Base


class ServiceProviderRating(Base):
    __tablename__ = "service_provider_ratings"
    
    # Unique constraint, um sicherzustellen, dass ein Bauträger pro Projekt/Milestone nur einmal bewerten kann
    __table_args__ = (
        UniqueConstraint('bautraeger_id', 'service_provider_id', 'milestone_id', 
                        name='unique_rating_per_milestone'),
    )

    id = Column(Integer, primary_key=True, index=True)
    
    # Wer bewertet wen
    bautraeger_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    service_provider_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Zu welchem Projekt/Milestone
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    milestone_id = Column(Integer, ForeignKey("milestones.id", ondelete="CASCADE"), nullable=False)
    quote_id = Column(Integer, ForeignKey("quotes.id", ondelete="CASCADE"), nullable=True)
    
    # Bewertungskriterien (1-5 Sterne)
    quality_rating = Column(Float, nullable=False)  # Qualität der Ausführung
    timeliness_rating = Column(Float, nullable=False)  # Termintreue
    communication_rating = Column(Float, nullable=False)  # Kommunikation & Erreichbarkeit
    value_rating = Column(Float, nullable=False)  # Preis-Leistungs-Verhältnis
    
    # Durchschnittsbewertung (automatisch berechnet)
    overall_rating = Column(Float, nullable=False)
    
    # Optionaler Kommentar
    comment = Column(Text, nullable=True)
    
    # Status
    is_public = Column(Integer, default=1)  # Ob die Bewertung öffentlich sichtbar ist
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    bautraeger = relationship("User", foreign_keys=[bautraeger_id])
    service_provider = relationship("User", foreign_keys=[service_provider_id], back_populates="received_ratings")
    project = relationship("Project")
    milestone = relationship("Milestone")
    quote = relationship("Quote")