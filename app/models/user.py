from sqlalchemy import Column, DateTime, Integer, String, Boolean, Enum, Text, Date, Float, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from .base import Base


class UserType(enum.Enum):
    PRIVATE = "private"
    PROFESSIONAL = "professional"
    SERVICE_PROVIDER = "service_provider"


class UserStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class AuthProvider(enum.Enum):
    EMAIL = "email"
    GOOGLE = "google"
    MICROSOFT = "microsoft"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    
    # Multi-Login Support
    hashed_password = Column(String, nullable=True)  # Nullable für Social-Login
    auth_provider = Column(Enum(AuthProvider), nullable=False, default=AuthProvider.EMAIL)
    
    # Social-Login Identifiers
    google_sub = Column(String, nullable=True, index=True)  # Google Subject ID
    microsoft_sub = Column(String, nullable=True, index=True)  # Microsoft Subject ID
    apple_sub = Column(String, nullable=True, index=True)  # Apple Subject ID (optional)
    
    # Social-Login Profile Data (verschlüsselt)
    social_profile_data = Column(JSON, nullable=True)  # Zusätzliche Social-Login Daten
    
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    user_type = Column(Enum(UserType), nullable=False, default=UserType.PRIVATE)
    
    # Geo-basierte Adressfelder (temporär deaktiviert für Kompatibilität)
    # address_street = Column(String, nullable=True)  # Straße und Hausnummer
    # address_zip = Column(String, nullable=True)  # PLZ
    # address_city = Column(String, nullable=True)  # Ort
    # address_country = Column(String, nullable=True, default="Deutschland")  # Land
    # address_latitude = Column(Float, nullable=True)  # Geokoordinate Latitude
    # address_longitude = Column(Float, nullable=True)  # Geokoordinate Longitude
    # address_geocoded = Column(Boolean, default=False)  # Wurde die Adresse geocodiert
    # address_geocoding_date = Column(DateTime(timezone=True), nullable=True)  # Wann geocodiert
    
    # DSGVO-konforme Felder - Erweitert
    status = Column(Enum(UserStatus), nullable=False, default=UserStatus.ACTIVE)
    
    # Consent Management (strukturiert)
    consent_fields = Column(JSON, nullable=True)  # Detaillierte Einwilligungen
    consent_history = Column(JSON, nullable=True)  # Historie der Einwilligungen
    
    # Legacy Consent Fields (für Kompatibilität)
    data_processing_consent = Column(Boolean, default=False)  # Einwilligung zur Datenverarbeitung
    marketing_consent = Column(Boolean, default=False)  # Einwilligung zu Marketing
    privacy_policy_accepted = Column(Boolean, default=False)  # Datenschutzerklärung akzeptiert
    terms_accepted = Column(Boolean, default=False)  # AGB akzeptiert
    
    # DSGVO: Erweiterte Datenlöschung und -archivierung
    data_retention_until = Column(Date, nullable=True)  # Bis wann Daten aufbewahrt werden
    data_deletion_requested = Column(Boolean, default=False)  # Löschung beantragt
    data_deletion_requested_at = Column(DateTime(timezone=True), nullable=True)
    data_anonymized = Column(Boolean, default=False)  # Daten anonymisiert
    data_export_requested = Column(Boolean, default=False)  # Datenexport beantragt
    data_export_requested_at = Column(DateTime(timezone=True), nullable=True)
    
    # DSGVO: Datenportabilität
    data_export_token = Column(String, nullable=True)  # Token für Datenexport
    data_export_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Audit-Logging - Erweitert
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    last_login_provider = Column(Enum(AuthProvider), nullable=True)  # Letzter Login-Provider
    failed_login_attempts = Column(Integer, default=0)
    account_locked_until = Column(DateTime(timezone=True), nullable=True)
    password_changed_at = Column(DateTime(timezone=True), nullable=True)
    
    # MFA (Multi-Factor Authentication)
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String, nullable=True)  # TOTP Secret (verschlüsselt)
    mfa_backup_codes = Column(JSON, nullable=True)  # Backup-Codes (verschlüsselt)
    mfa_last_used = Column(DateTime(timezone=True), nullable=True)
    
    # Firmendaten für Dienstleister (optional, nur bei Einwilligung)
    company_name = Column(String, nullable=True)
    company_address = Column(Text, nullable=True)
    company_phone = Column(String, nullable=True)
    company_website = Column(String, nullable=True)
    business_license = Column(String, nullable=True)  # Gewerbeschein
    
    # Profilinformationen (optional, nur bei Einwilligung)
    bio = Column(Text, nullable=True)
    profile_image = Column(String, nullable=True)
    region = Column(String, nullable=True)
    languages = Column(String, nullable=True)  # Komma-getrennte Liste
    
    # Einstellungen
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    two_factor_enabled = Column(Boolean, default=False)
    language_preference = Column(String, default="de")
    
    # DSGVO: Verschlüsselung und Sicherheit
    data_encrypted = Column(Boolean, default=True)  # Sind sensible Daten verschlüsselt
    encryption_key_id = Column(String, nullable=True)  # ID des Verschlüsselungsschlüssels
    
    # Timestamps mit DSGVO-Konformität
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_activity_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    projects = relationship("Project", back_populates="owner")
    assigned_tasks = relationship("Task", foreign_keys="Task.assigned_to", back_populates="assigned_user")
    created_tasks = relationship("Task", foreign_keys="Task.created_by", back_populates="creator")
    created_milestones = relationship("Milestone", back_populates="creator")
    uploaded_documents = relationship("Document", back_populates="uploader")
    sent_messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    received_messages = relationship("Message", foreign_keys="Message.recipient_id", back_populates="recipient")
    quotes = relationship("Quote", back_populates="service_provider")
    buildwise_fees = relationship("BuildWiseFee", back_populates="service_provider")
    
    # Constraints für Social-Login
    __table_args__ = (
        # Mindestens ein Login-Verfahren muss vorhanden sein
        # (hashed_password ODER google_sub ODER microsoft_sub ODER apple_sub)
    )
