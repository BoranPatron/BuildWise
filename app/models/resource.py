from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Numeric, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .base import Base


class ResourceStatus(enum.Enum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    ALLOCATED = "allocated"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ResourceVisibility(enum.Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    RESTRICTED = "restricted"


class AllocationStatus(enum.Enum):
    PRE_SELECTED = "pre_selected"
    INVITED = "invited"
    OFFER_REQUESTED = "offer_requested"
    OFFER_SUBMITTED = "offer_submitted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COMPLETED = "completed"


class RequestStatus(enum.Enum):
    OPEN = "open"
    SEARCHING = "searching"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"


class CalendarEntryStatus(enum.Enum):
    AVAILABLE = "available"
    TENTATIVE = "tentative"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Resource(Base):
    """Ressource-Modell für die Verwaltung von Personal und Kapazitäten"""
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    service_provider_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True, index=True)
    
    # Zeitraum
    start_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime, nullable=False, index=True)
    
    # Ressourcen-Details
    title = Column(String(255), nullable=True)  # Titel der Ressource
    person_count = Column(Integer, nullable=False, default=1)
    daily_hours = Column(Numeric(5, 2), nullable=True, default=8.0)
    total_hours = Column(Numeric(8, 2), nullable=True)
    
    # Kategorie
    category = Column(String(100), nullable=False, index=True)
    subcategory = Column(String(100), nullable=True)
    
    # Adresse
    address_street = Column(String(255), nullable=True)
    address_city = Column(String(100), nullable=True, index=True)
    address_postal_code = Column(String(20), nullable=True)
    address_country = Column(String(100), nullable=True, default="Deutschland")
    latitude = Column(Numeric(10, 8), nullable=True, index=True)
    longitude = Column(Numeric(11, 8), nullable=True, index=True)
    
    # Status
    status = Column(Enum(ResourceStatus), nullable=False, default=ResourceStatus.AVAILABLE, index=True)
    visibility = Column(Enum(ResourceVisibility), nullable=False, default=ResourceVisibility.PUBLIC)
    
    # Preise
    hourly_rate = Column(Numeric(10, 2), nullable=True)
    daily_rate = Column(Numeric(10, 2), nullable=True)
    currency = Column(String(3), nullable=False, default="EUR")
    
    # Zusätzliche Informationen
    description = Column(Text, nullable=True)
    skills = Column(JSON, nullable=True)  # Array von Strings
    equipment = Column(JSON, nullable=True)  # Array von Strings
    
    # Computed fields (werden bei Bedarf berechnet)
    provider_name = Column(String(255), nullable=True)
    provider_email = Column(String(255), nullable=True)
    active_allocations = Column(Integer, nullable=True, default=0)
    
    # Bauträger-Zeitraum (gewünschter Zeitraum des Bauträgers)
    builder_preferred_start_date = Column(DateTime, nullable=True)
    builder_preferred_end_date = Column(DateTime, nullable=True)
    builder_date_range_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    service_provider = relationship("User", back_populates="resources", foreign_keys=[service_provider_id])
    project = relationship("Project", back_populates="resources", foreign_keys=[project_id])
    allocations = relationship("ResourceAllocation", back_populates="resource", cascade="all, delete-orphan")
    calendar_entries = relationship("ResourceCalendarEntry", back_populates="resource", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Resource(id={self.id}, category={self.category}, person_count={self.person_count}, status={self.status})>"


class ResourceAllocation(Base):
    """Zuweisung von Ressourcen zu Gewerken/Trades"""
    __tablename__ = "resource_allocations"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey("resources.id"), nullable=False, index=True)
    trade_id = Column(Integer, ForeignKey("milestones.id"), nullable=False, index=True)
    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=True, index=True)
    
    # Allokations-Details
    allocated_person_count = Column(Integer, nullable=False)
    allocated_start_date = Column(DateTime, nullable=False)
    allocated_end_date = Column(DateTime, nullable=False)
    allocated_hours = Column(Numeric(8, 2), nullable=True)
    
    # Status
    allocation_status = Column(Enum(AllocationStatus), nullable=False, default=AllocationStatus.PRE_SELECTED, index=True)
    
    # Preise
    agreed_hourly_rate = Column(Numeric(10, 2), nullable=True)
    agreed_daily_rate = Column(Numeric(10, 2), nullable=True)
    total_cost = Column(Numeric(12, 2), nullable=True)
    
    # Benachrichtigungen
    invitation_sent_at = Column(DateTime, nullable=True)
    invitation_viewed_at = Column(DateTime, nullable=True)
    offer_requested_at = Column(DateTime, nullable=True)
    offer_submitted_at = Column(DateTime, nullable=True)
    decision_made_at = Column(DateTime, nullable=True)
    
    # Zusätzliche Infos
    notes = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    priority = Column(Integer, nullable=True, default=5)  # 1 = höchste Priorität
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    resource = relationship("Resource", back_populates="allocations")
    trade = relationship("Milestone", back_populates="resource_allocations")
    quote = relationship("Quote", back_populates="resource_allocations")
    created_by_user = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<ResourceAllocation(id={self.id}, resource_id={self.resource_id}, trade_id={self.trade_id}, status={self.allocation_status})>"


class ResourceRequest(Base):
    """Anfrage für Ressourcen von Bauträgern"""
    __tablename__ = "resource_requests"

    id = Column(Integer, primary_key=True, index=True)
    trade_id = Column(Integer, ForeignKey("milestones.id"), nullable=False, index=True)
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Anfrage-Details
    category = Column(String(100), nullable=False, index=True)
    subcategory = Column(String(100), nullable=True)
    required_person_count = Column(Integer, nullable=False)
    required_start_date = Column(DateTime, nullable=False)
    required_end_date = Column(DateTime, nullable=False)
    
    # Standort
    location_address = Column(String(500), nullable=True)
    location_city = Column(String(100), nullable=True)
    location_postal_code = Column(String(20), nullable=True)
    max_distance_km = Column(Integer, nullable=True, default=50)
    
    # Budget
    max_hourly_rate = Column(Numeric(10, 2), nullable=True)
    max_total_budget = Column(Numeric(12, 2), nullable=True)
    
    # Anforderungen
    required_skills = Column(JSON, nullable=True)  # Array von Strings
    required_equipment = Column(JSON, nullable=True)  # Array von Strings
    requirements_description = Column(Text, nullable=True)
    
    # Status
    status = Column(Enum(RequestStatus), nullable=False, default=RequestStatus.OPEN, index=True)
    
    # Statistiken
    total_resources_found = Column(Integer, nullable=True, default=0)
    total_resources_selected = Column(Integer, nullable=True, default=0)
    total_offers_received = Column(Integer, nullable=True, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deadline_at = Column(DateTime, nullable=True)
    
    # Relationships
    trade = relationship("Milestone", back_populates="resource_requests")
    requested_by_user = relationship("User", back_populates="resource_requests")
    allocations = relationship("ResourceAllocation", 
                             primaryjoin="ResourceRequest.trade_id == ResourceAllocation.trade_id",
                             foreign_keys="ResourceAllocation.trade_id",
                             viewonly=True)

    def __repr__(self):
        return f"<ResourceRequest(id={self.id}, trade_id={self.trade_id}, category={self.category}, status={self.status})>"


class ResourceCalendarEntry(Base):
    """Kalendereinträge für Ressourcenplanung"""
    __tablename__ = "resource_calendar_entries"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey("resources.id"), nullable=True, index=True)
    allocation_id = Column(Integer, ForeignKey("resource_allocations.id"), nullable=True, index=True)
    service_provider_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    entry_date = Column(DateTime, nullable=False, index=True)
    person_count = Column(Integer, nullable=False, default=1)
    hours_allocated = Column(Numeric(5, 2), nullable=True)
    
    status = Column(Enum(CalendarEntryStatus), nullable=False, default=CalendarEntryStatus.AVAILABLE, index=True)
    
    color = Column(String(7), nullable=True)  # Hex color code
    label = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    resource = relationship("Resource", back_populates="calendar_entries")
    allocation = relationship("ResourceAllocation")
    service_provider = relationship("User", foreign_keys=[service_provider_id])

    def __repr__(self):
        return f"<ResourceCalendarEntry(id={self.id}, entry_date={self.entry_date}, status={self.status})>"


class ResourceKPIs(Base):
    """KPI-Berechnungen für Ressourcenverwaltung"""
    __tablename__ = "resource_kpis"

    id = Column(Integer, primary_key=True, index=True)
    service_provider_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    calculation_date = Column(DateTime, nullable=False, server_default=func.now())
    
    total_resources_available = Column(Integer, nullable=False, default=0)
    total_resources_allocated = Column(Integer, nullable=False, default=0)
    total_resources_completed = Column(Integer, nullable=False, default=0)
    
    total_person_days_available = Column(Integer, nullable=False, default=0)
    total_person_days_allocated = Column(Integer, nullable=False, default=0)
    total_person_days_completed = Column(Integer, nullable=False, default=0)
    
    utilization_rate = Column(Numeric(5, 2), nullable=True)  # Percentage
    average_hourly_rate = Column(Numeric(10, 2), nullable=True)
    total_revenue = Column(Numeric(12, 2), nullable=True)
    
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    service_provider = relationship("User", foreign_keys=[service_provider_id])

    def __repr__(self):
        return f"<ResourceKPIs(id={self.id}, service_provider_id={self.service_provider_id}, utilization_rate={self.utilization_rate})>"