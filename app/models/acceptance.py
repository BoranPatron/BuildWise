from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Boolean, ForeignKey, Enum, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from .base import Base


class AcceptanceStatus(enum.Enum):
    """Status der Abnahme"""
    SCHEDULED = "SCHEDULED"  # Termin vereinbart
    IN_PROGRESS = "IN_PROGRESS"  # Abnahme läuft
    ACCEPTED = "ACCEPTED"  # Abgenommen
    ACCEPTED_WITH_DEFECTS = "ACCEPTED_WITH_DEFECTS"  # Abnahme unter Vorbehalt
    REJECTED = "REJECTED"  # Abgelehnt
    CANCELLED = "CANCELLED"  # Abgebrochen


class AcceptanceType(enum.Enum):
    """Art der Abnahme"""
    FINAL = "FINAL"  # Endabnahme
    PARTIAL = "PARTIAL"  # Teilabnahme
    TECHNICAL = "TECHNICAL"  # Technische Abnahme
    VISUAL = "VISUAL"  # Sichtabnahme


class DefectSeverity(enum.Enum):
    """Schweregrad von Mängeln"""
    MINOR = "MINOR"  # Geringfügig
    MAJOR = "MAJOR"  # Erheblich
    CRITICAL = "CRITICAL"  # Kritisch


class Acceptance(Base):
    """Abnahme-Protokoll für Gewerke"""
    __tablename__ = "acceptances"

    id = Column(Integer, primary_key=True, index=True)
    
    # Verknüpfungen
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    milestone_id = Column(Integer, ForeignKey("milestones.id", ondelete="CASCADE"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)  # Optional: Abnahme-Termin
    
    # Teilnehmer
    contractor_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Bauträger/Auftraggeber
    service_provider_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Dienstleister
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Abnahme-Details
    acceptance_type = Column(Enum(AcceptanceType), nullable=False, default=AcceptanceType.FINAL)
    status = Column(Enum(AcceptanceStatus), nullable=False, default=AcceptanceStatus.SCHEDULED)
    
    # Zeitstempel
    scheduled_date = Column(DateTime(timezone=True), nullable=True)  # Geplanter Abnahme-Termin
    started_at = Column(DateTime(timezone=True), nullable=True)  # Beginn der Abnahme
    completed_at = Column(DateTime(timezone=True), nullable=True)  # Ende der Abnahme
    
    # Abnahme-Ergebnis
    accepted = Column(Boolean, nullable=True)  # True = abgenommen, False = abgelehnt, None = noch offen
    acceptance_notes = Column(Text, nullable=True)  # Allgemeine Notizen
    contractor_notes = Column(Text, nullable=True)  # Notizen des Bauträgers
    service_provider_notes = Column(Text, nullable=True)  # Notizen des Dienstleisters
    
    # Bewertung
    quality_rating = Column(Integer, nullable=True)  # 1-5 Sterne
    timeliness_rating = Column(Integer, nullable=True)  # 1-5 Sterne
    overall_rating = Column(Integer, nullable=True)  # 1-5 Sterne
    
    # Checkliste für Vor-Ort Prüfung
    checklist_data = Column(JSON, nullable=True)  # Speichert checklist-Objekt
    
    # Wiedervorlage bei Abnahme unter Vorbehalt
    review_date = Column(Date, nullable=True)
    review_notes = Column(Text, nullable=True)
    review_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)  # Wiedervorlage-Task für Bauträger
    
    # Fotos und Dokumente
    photos = Column(JSON, nullable=True)  # Array von Foto-URLs
    documents = Column(JSON, nullable=True)  # Array von Dokument-URLs
    
    # PDF-Protokoll
    protocol_pdf_path = Column(String, nullable=True)  # Pfad zum generierten PDF
    protocol_generated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Gewährleistung
    warranty_start_date = Column(DateTime(timezone=True), nullable=True)
    warranty_period_months = Column(Integer, default=24)  # Standard: 2 Jahre
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="acceptances")
    milestone = relationship("Milestone", back_populates="acceptances")
    appointment = relationship("Appointment")
    contractor = relationship("User", foreign_keys=[contractor_id])
    service_provider = relationship("User", foreign_keys=[service_provider_id])
    creator = relationship("User", foreign_keys=[created_by])
    defects = relationship("AcceptanceDefect", back_populates="acceptance", cascade="all, delete-orphan")
    review_task = relationship("Task", foreign_keys=[review_task_id])


class AcceptanceDefect(Base):
    """Mängel bei der Abnahme"""
    __tablename__ = "acceptance_defects"

    id = Column(Integer, primary_key=True, index=True)
    acceptance_id = Column(Integer, ForeignKey("acceptances.id", ondelete="CASCADE"), nullable=False)
    
    # Mangel-Details
    title = Column(String, nullable=False)  # Kurze Beschreibung
    description = Column(Text, nullable=True)  # Detaillierte Beschreibung
    severity = Column(Enum(DefectSeverity), nullable=False, default=DefectSeverity.MINOR)
    
    # Lokalisierung
    location = Column(String, nullable=True)  # Wo ist der Mangel
    room = Column(String, nullable=True)  # Raum/Bereich
    
    # Status
    resolved = Column(Boolean, default=False)
    resolution_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Kosten
    estimated_cost = Column(Float, nullable=True)  # Geschätzte Behebungskosten
    actual_cost = Column(Float, nullable=True)  # Tatsächliche Kosten
    
    # Fristen
    deadline = Column(DateTime(timezone=True), nullable=True)  # Frist zur Behebung
    
    # Task-Integration
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)  # Zugehörige Task für Dienstleister
    
    # Fotos
    photos = Column(JSON, nullable=True)  # Array von Foto-URLs zum Mangel
    photo_annotations = Column(JSON, nullable=True)  # Annotation-Daten für Fotos
    resolution_photos = Column(JSON, nullable=True)  # Fotos nach Behebung
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    acceptance = relationship("Acceptance", back_populates="defects")
    resolver = relationship("User", foreign_keys=[resolved_by])
    # task = relationship("Task", back_populates="defect")  # Temporär deaktiviert