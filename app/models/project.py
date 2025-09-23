from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, Enum, Float, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from .base import Base


class ProjectType(enum.Enum):
    NEW_BUILD = "new_build"
    RENOVATION = "renovation"
    EXTENSION = "extension"
    REFURBISHMENT = "refurbishment"


class ProjectStatus(enum.Enum):
    PLANNING = "planning"
    PREPARATION = "preparation"
    EXECUTION = "execution"
    COMPLETION = "completion"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    project_type = Column(Enum(ProjectType), nullable=False)
    status = Column(Enum(ProjectStatus), nullable=False, default=ProjectStatus.PLANNING)
    
    # Geo-basierte Projektadresse
    address = Column(String, nullable=True)  # Vollständige Adresse als String
    address_street = Column(String, nullable=True)  # Straße und Hausnummer
    address_zip = Column(String, nullable=True)  # PLZ
    address_city = Column(String, nullable=True)  # Ort
    address_country = Column(String, nullable=True, default="Deutschland")  # Land
    address_latitude = Column(Float, nullable=True)  # Geokoordinate Latitude
    address_longitude = Column(Float, nullable=True)  # Geokoordinate Longitude
    address_geocoded = Column(Boolean, default=False)  # Wurde die Adresse geocodiert
    address_geocoding_date = Column(DateTime(timezone=True), nullable=True)  # Wann geocodiert
    
    # Projektdetails
    property_size = Column(Float, nullable=True)  # in m²
    construction_area = Column(Float, nullable=True)  # in m²
    
    # Zeitplan
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    estimated_duration = Column(Integer, nullable=True)  # in Tagen
    
    # Budget
    budget = Column(Float, nullable=True)
    current_costs = Column(Float, default=0.0)
    
    # Fortschritt
    progress_percentage = Column(Float, default=0.0)
    
    # Einstellungen
    is_public = Column(Boolean, default=False)  # Für Dienstleister sichtbar
    allow_quotes = Column(Boolean, default=True)
    
    # Bauphasen (für Neubau-Projekte)
    construction_phase = Column(String, nullable=True)  # Aktuelle Bauphase
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="projects")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    milestones = relationship("Milestone", back_populates="project", cascade="all, delete-orphan")
    quotes = relationship("Quote", back_populates="project", cascade="all, delete-orphan")
    # cost_positions = relationship("CostPosition", back_populates="project", cascade="all, delete-orphan")  # Entfernt - CostPosition gehört zu Invoice, nicht direkt zu Project
    buildwise_fees = relationship("BuildWiseFee", back_populates="project", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="project", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="project", cascade="all, delete-orphan")
    acceptances = relationship("Acceptance", back_populates="project", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="project", cascade="all, delete-orphan")
    resources = relationship("Resource", foreign_keys="Resource.project_id", back_populates="project")
