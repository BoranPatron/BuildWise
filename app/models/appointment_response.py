from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class AppointmentResponse(Base):
    """
    Modell für Terminantworten von Dienstleistern
    Ersetzt das JSON-basierte responses System in der appointments Tabelle
    """
    __tablename__ = "appointment_responses"

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id", ondelete="CASCADE"), nullable=False, index=True)
    service_provider_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Status der Antwort
    status = Column(String(50), nullable=False)  # 'accepted', 'rejected', 'rejected_with_suggestion'
    
    # Optional: Nachricht des Dienstleisters
    message = Column(Text, nullable=True)
    
    # Optional: Alternativtermin bei Ablehnung
    suggested_date = Column(DateTime, nullable=True)
    
    # Zeitstempel
    responded_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    appointment = relationship("Appointment", back_populates="appointment_responses")
    service_provider = relationship("User", foreign_keys=[service_provider_id])

    def __repr__(self):
        return f"<AppointmentResponse(id={self.id}, appointment_id={self.appointment_id}, service_provider_id={self.service_provider_id}, status='{self.status}')>"

    def to_dict(self, include_service_provider=False):
        """Konvertiere zu Dictionary für API-Responses
        
        Args:
            include_service_provider: If True, includes service_provider details (requires eager loading)
        """
        result = {
            "id": self.id,
            "appointment_id": self.appointment_id,
            "service_provider_id": self.service_provider_id,
            "status": self.status,
            "message": self.message,
            "suggested_date": self.suggested_date.isoformat() if self.suggested_date else None,
            "responded_at": self.responded_at.isoformat() if self.responded_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        # Only include service_provider if explicitly requested and already loaded
        if include_service_provider:
            try:
                # Check if relationship is already loaded to avoid lazy loading
                if hasattr(self, '_sa_instance_state') and 'service_provider' in self._sa_instance_state.loaded_attrs:
                    result["service_provider"] = {
                        "id": self.service_provider.id,
                        "first_name": self.service_provider.first_name,
                        "last_name": self.service_provider.last_name,
                        "company_name": self.service_provider.company_name,
                        "email": self.service_provider.email,
                    } if self.service_provider else None
                else:
                    result["service_provider"] = None
            except Exception as e:
                print(f"⚠️ Warning: Could not load service_provider for response {self.id}: {e}")
                result["service_provider"] = None
        
        return result 