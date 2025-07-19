from sqlalchemy import Column, DateTime, Integer, String, Boolean, Enum, Text, Date, Float, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from .base import Base


class UserType(enum.Enum):
    PRIVATE = "private"  # Bauträger/Bauherr
    PROFESSIONAL = "professional"  # Professioneller Bauträger
    SERVICE_PROVIDER = "service_provider"  # Dienstleister


class SubscriptionPlan(enum.Enum):
    BASIS = "basis"  # Basis-Modell (nur Gewerke, Docs, Visualize)
    PRO = "pro"  # Pro-Modell (alle Features)


class UserStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"
    PENDING_VERIFICATION = "pending_verification"  # Wartet auf E-Mail-Verifizierung


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    user_type = Column(Enum(UserType), nullable=False, default=UserType.PRIVATE)
    
    # Subscription und Zahlungsmodell
    subscription_plan = Column(Enum(SubscriptionPlan), nullable=False, default=SubscriptionPlan.BASIS)
    subscription_start_date = Column(Date, nullable=True)
    subscription_end_date = Column(Date, nullable=True)
    subscription_active = Column(Boolean, default=True)
    
    # Geo-basierte Adressfelder (temporär deaktiviert für Kompatibilität)
    # address_street = Column(String, nullable=True)  # Straße und Hausnummer
    # address_zip = Column(String, nullable=True)  # PLZ
    # address_city = Column(String, nullable=True)  # Ort
    # address_country = Column(String, nullable=True, default="Deutschland")  # Land
    # address_latitude = Column(Float, nullable=True)  # Geokoordinate Latitude
    # address_longitude = Column(Float, nullable=True)  # Geokoordinate Longitude
    # address_geocoded = Column(Boolean, default=False)  # Wurde die Adresse geocodiert
    # address_geocoding_date = Column(DateTime(timezone=True), nullable=True)  # Wann geocodiert
    
    # DSGVO-konforme Felder
    status = Column(Enum(UserStatus), nullable=False, default=UserStatus.PENDING_VERIFICATION)
    data_processing_consent = Column(Boolean, default=False)  # Einwilligung zur Datenverarbeitung
    marketing_consent = Column(Boolean, default=False)  # Einwilligung zu Marketing
    privacy_policy_accepted = Column(Boolean, default=False)  # Datenschutzerklärung akzeptiert
    terms_accepted = Column(Boolean, default=False)  # AGB akzeptiert
    
    # E-Mail-Verifizierung
    email_verification_token = Column(String, nullable=True)
    email_verification_sent_at = Column(DateTime(timezone=True), nullable=True)
    email_verified = Column(Boolean, default=False)
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Passwort-Reset
    password_reset_token = Column(String, nullable=True)
    password_reset_sent_at = Column(DateTime(timezone=True), nullable=True)
    password_reset_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Datenlöschung und -archivierung
    data_retention_until = Column(Date, nullable=True)  # Bis wann Daten aufbewahrt werden
    data_deletion_requested = Column(Boolean, default=False)  # Löschung beantragt
    data_deletion_requested_at = Column(DateTime(timezone=True), nullable=True)
    data_anonymized = Column(Boolean, default=False)  # Daten anonymisiert
    
    # Audit-Logging
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    account_locked_until = Column(DateTime(timezone=True), nullable=True)
    password_changed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Firmendaten für Dienstleister (optional, nur bei Einwilligung)
    company_name = Column(String, nullable=True)
    company_address = Column(Text, nullable=True)
    company_phone = Column(String, nullable=True)
    company_website = Column(String, nullable=True)
    business_license = Column(String, nullable=True)  # Gewerbeschein
    tax_id = Column(String, nullable=True)  # Steuernummer
    vat_id = Column(String, nullable=True)  # USt-ID
    
    # Profilinformationen (optional, nur bei Einwilligung)
    bio = Column(Text, nullable=True)
    profile_image = Column(String, nullable=True)
    region = Column(String, nullable=True)
    languages = Column(String, nullable=True)  # Komma-getrennte Liste
    
    # Einstellungen
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    two_factor_enabled = Column(Boolean, default=False)
    language_preference = Column(String, default="de")
    
    # Berechtigungen und Rollen (JSON für Flexibilität)
    permissions = Column(JSON, default=dict)  # Spezifische Berechtigungen
    roles = Column(JSON, default=list)  # Rollen-Liste
    
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
