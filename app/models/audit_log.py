from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, JSON, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from .base import Base


class AuditAction(enum.Enum):
    # Benutzer-Aktionen
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_REGISTER = "user_register"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    
    # DSGVO-spezifische Aktionen
    CONSENT_GIVEN = "consent_given"
    CONSENT_WITHDRAWN = "consent_withdrawn"
    DATA_ACCESS_REQUEST = "data_access_request"
    DATA_DELETION_REQUEST = "data_deletion_request"
    DATA_EXPORT_REQUEST = "data_export_request"
    DATA_ANONYMIZATION = "data_anonymization"
    
    # Datenzugriff
    DATA_READ = "data_read"
    DATA_CREATE = "data_create"
    DATA_UPDATE = "data_update"
    DATA_DELETE = "data_delete"
    
    # Sicherheitsereignisse
    FAILED_LOGIN = "failed_login"
    ACCOUNT_LOCKED = "account_locked"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    UNAUTHORIZED_ACCESS = "unauthorized_access"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Wer hat die Aktion ausgeführt
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    session_id = Column(String, nullable=True)  # Session-ID für anonyme Aktionen
    ip_address = Column(String, nullable=True)  # IP-Adresse (anonymisiert)
    user_agent = Column(Text, nullable=True)  # User-Agent (anonymisiert)
    
    # Was wurde gemacht
    action = Column(Enum(AuditAction), nullable=False)
    resource_type = Column(String, nullable=True)  # z.B. "user", "project", "document"
    resource_id = Column(Integer, nullable=True)  # ID der betroffenen Ressource
    
    # Details der Aktion
    description = Column(Text, nullable=True)  # Beschreibung der Aktion
    details = Column(JSON, nullable=True)  # Zusätzliche Details (verschlüsselt)
    
    # DSGVO: Zweck der Datenverarbeitung
    processing_purpose = Column(String, nullable=True)  # Zweck der Datenverarbeitung
    legal_basis = Column(String, nullable=True)  # Rechtsgrundlage
    
    # Sicherheit
    risk_level = Column(String, nullable=True)  # Risikobewertung: low, medium, high
    requires_review = Column(Boolean, default=False)  # Benötigt manuelle Überprüfung
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User") 