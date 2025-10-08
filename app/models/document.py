from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .base import Base

class DocumentType(enum.Enum):
    PLAN = "plan"
    PERMIT = "permit"
    QUOTE = "quote"
    INVOICE = "invoice"
    CONTRACT = "contract"
    PHOTO = "photo"
    BLUEPRINT = "blueprint"
    CERTIFICATE = "certificate"
    REPORT = "report"
    VIDEO = "video"
    PDF = "pdf"  # Hinzugefügt für PDF-Dokumente
    ACCEPTANCE_PROTOCOL = "acceptance_protocol"  # Abnahmeprotokoll
    OTHER = "other"

class DocumentCategory(enum.Enum):
    PLANNING = "planning"
    CONTRACTS = "contracts"
    FINANCE = "finance"
    EXECUTION = "execution"
    DOCUMENTATION = "documentation"
    ORDER_CONFIRMATIONS = "order_confirmations"  # Neue Kategorie für Auftragsbestätigungen
    PROJECT_MANAGEMENT = "project_management"  # Projektmanagement-Dokumente
    PROCUREMENT = "procurement"  # Ausschreibungen und Angebote

class DocumentStatus(enum.Enum):
    DRAFT = "DRAFT"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"

class WorkflowStage(enum.Enum):
    CREATED = "CREATED"
    UPLOADED = "UPLOADED"
    CATEGORIZED = "CATEGORIZED"
    REVIEWED = "REVIEWED"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"
    SHARED = "SHARED"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"

class ApprovalStatus(enum.Enum):
    PENDING = "PENDING"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REQUIRES_CHANGES = "REQUIRES_CHANGES"

class ReviewStatus(enum.Enum):
    NOT_REVIEWED = "NOT_REVIEWED"
    IN_REVIEW = "IN_REVIEW"
    REVIEWED = "REVIEWED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class ShareType(enum.Enum):
    READ_ONLY = "READ_ONLY"
    DOWNLOAD = "DOWNLOAD"
    COMMENT = "COMMENT"
    EDIT = "EDIT"
    FULL_ACCESS = "FULL_ACCESS"

class AccessLevel(enum.Enum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"

class ChangeType(enum.Enum):
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    PATCH = "PATCH"
    HOTFIX = "HOTFIX"

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    # Datei-Informationen
    file_name = Column(String)
    file_path = Column(String)
    file_size = Column(Integer)
    mime_type = Column(String)
    
    # Klassifizierung
    document_type = Column(String, nullable=False)
    category = Column(String)
    subcategory = Column(String)
    tags = Column(Text)
    
    # Versionierung (NEU)
    version_number = Column(String(50), default="1.0.0")
    version_major = Column(Integer, default=1)
    version_minor = Column(Integer, default=0)
    version_patch = Column(Integer, default=0)
    is_latest_version = Column(Boolean, default=True)
    parent_document_id = Column(Integer, ForeignKey("documents.id"))
    
    # Status-Management (NEU)
    document_status = Column(String(50), default="DRAFT")
    workflow_stage = Column(String(50), default="CREATED")
    approval_status = Column(String(50), default="PENDING")
    review_status = Column(String(50), default="NOT_REVIEWED")
    
    # Locking (NEU)
    locked_by = Column(Integer, ForeignKey("users.id"))
    locked_at = Column(DateTime)
    
    # Genehmigung (NEU)
    approved_by = Column(Integer, ForeignKey("users.id"))
    approved_at = Column(DateTime)
    rejected_by = Column(Integer, ForeignKey("users.id"))
    rejected_at = Column(DateTime)
    rejection_reason = Column(Text)
    
    # Lifecycle (NEU)
    expires_at = Column(DateTime)
    archived_at = Column(DateTime)
    
    # Integrität (NEU)
    checksum = Column(String(255))
    file_format_version = Column(String(50))
    metadata_json = Column(Text)
    
    # Zugriff (NEU)
    access_level = Column(String(50), default="INTERNAL")
    sharing_permissions = Column(Text)
    download_count = Column(Integer, default=0)
    last_accessed_by = Column(Integer, ForeignKey("users.id"))
    last_accessed_at = Column(DateTime)
    
    # Standard-Felder
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_public = Column(Boolean, default=False)
    is_favorite = Column(Boolean, default=False)
    
    # Service Provider Soft-Delete
    hidden_for_service_providers = Column(Boolean, default=False)
    
    # Relationships
    project = relationship("Project", back_populates="documents")
    uploaded_by_user = relationship("User", foreign_keys=[uploaded_by], back_populates="uploaded_documents")
    locked_by_user = relationship("User", foreign_keys=[locked_by], back_populates="locked_documents")
    approved_by_user = relationship("User", foreign_keys=[approved_by], back_populates="approved_documents")
    rejected_by_user = relationship("User", foreign_keys=[rejected_by], back_populates="rejected_documents")
    last_accessed_by_user = relationship("User", foreign_keys=[last_accessed_by], back_populates="last_accessed_documents")
    
    # Self-referencing relationship für Versionierung
    parent_document = relationship("Document", remote_side=[id], back_populates="child_versions")
    child_versions = relationship("Document", back_populates="parent_document")
    
    # Relationships zu neuen Tabellen
    versions = relationship("DocumentVersion", back_populates="document")
    status_history = relationship("DocumentStatusHistory", back_populates="document")
    shares = relationship("DocumentShare", back_populates="document")
    access_logs = relationship("DocumentAccessLog", back_populates="document")
    
    # Comments Relationship
    comments = relationship("Comment", back_populates="document", cascade="all, delete-orphan")

class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    version_number = Column(String(50), nullable=False)
    version_major = Column(Integer, nullable=False)
    version_minor = Column(Integer, nullable=False)
    version_patch = Column(Integer, nullable=False)
    
    # Datei-Informationen der Version
    file_path = Column(String(500))
    file_name = Column(String(255))
    file_size = Column(Integer)
    mime_type = Column(String(100))
    checksum = Column(String(255))
    
    # Änderungs-Informationen
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    change_description = Column(Text)
    change_type = Column(String(50), default="MINOR")
    is_active = Column(Boolean, default=True)
    metadata_json = Column(Text)
    
    # Relationships
    document = relationship("Document", back_populates="versions")
    created_by_user = relationship("User")
    
    # Unique constraint
    __table_args__ = (UniqueConstraint('document_id', 'version_number', name='uq_document_version'),)

class DocumentStatusHistory(Base):
    __tablename__ = "document_status_history"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    version_number = Column(String(50))
    
    # Status-Änderungen
    old_status = Column(String(50))
    new_status = Column(String(50))
    old_workflow_stage = Column(String(50))
    new_workflow_stage = Column(String(50))
    
    # Änderungs-Informationen
    changed_by = Column(Integer, ForeignKey("users.id"))
    changed_at = Column(DateTime, default=datetime.utcnow)
    change_reason = Column(Text)
    metadata_json = Column(Text)
    
    # Relationships
    document = relationship("Document", back_populates="status_history")
    changed_by_user = relationship("User")

class DocumentShare(Base):
    __tablename__ = "document_shares"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    
    # Sharing-Ziele
    shared_with_user_id = Column(Integer, ForeignKey("users.id"))
    shared_with_project_id = Column(Integer, ForeignKey("projects.id"))
    shared_with_trade_id = Column(Integer)  # Referenz zu trades Tabelle
    
    # Berechtigungen
    share_type = Column(String(50), default="READ_ONLY")
    permissions = Column(Text)
    
    # Sharing-Informationen
    shared_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    shared_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    
    # Zugriffs-Tracking
    access_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    metadata_json = Column(Text)
    
    # Relationships
    document = relationship("Document", back_populates="shares")
    shared_with_user = relationship("User", foreign_keys=[shared_with_user_id])
    shared_with_project = relationship("Project", foreign_keys=[shared_with_project_id])
    shared_by_user = relationship("User", foreign_keys=[shared_by])

class DocumentAccessLog(Base):
    __tablename__ = "document_access_log"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    version_number = Column(String(50))
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Zugriffs-Informationen
    access_type = Column(String(50), nullable=False)  # VIEW, DOWNLOAD, EDIT, etc.
    ip_address = Column(String(45))
    user_agent = Column(Text)
    accessed_at = Column(DateTime, default=datetime.utcnow)
    duration_seconds = Column(Integer)
    
    # Erfolg/Fehler
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    metadata_json = Column(Text)
    
    # Relationships
    document = relationship("Document", back_populates="access_logs")
    user = relationship("User") 