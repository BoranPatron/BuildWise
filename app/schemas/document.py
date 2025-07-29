from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Enums für Frontend
class DocumentTypeEnum(str, Enum):
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
    PDF = "pdf"
    OTHER = "other"

class DocumentCategoryEnum(str, Enum):
    PLANNING = "planning"
    CONTRACTS = "contracts"
    FINANCE = "finance"
    EXECUTION = "execution"
    DOCUMENTATION = "documentation"
    ORDER_CONFIRMATIONS = "order_confirmations"

class DocumentStatusEnum(str, Enum):
    DRAFT = "DRAFT"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"

class WorkflowStageEnum(str, Enum):
    CREATED = "CREATED"
    UPLOADED = "UPLOADED"
    CATEGORIZED = "CATEGORIZED"
    REVIEWED = "REVIEWED"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"
    SHARED = "SHARED"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"

class ApprovalStatusEnum(str, Enum):
    PENDING = "PENDING"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REQUIRES_CHANGES = "REQUIRES_CHANGES"

class ReviewStatusEnum(str, Enum):
    NOT_REVIEWED = "NOT_REVIEWED"
    IN_REVIEW = "IN_REVIEW"
    REVIEWED = "REVIEWED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class ShareTypeEnum(str, Enum):
    READ_ONLY = "READ_ONLY"
    DOWNLOAD = "DOWNLOAD"
    COMMENT = "COMMENT"
    EDIT = "EDIT"
    FULL_ACCESS = "FULL_ACCESS"

class AccessLevelEnum(str, Enum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"

class ChangeTypeEnum(str, Enum):
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    PATCH = "PATCH"
    HOTFIX = "HOTFIX"

# Base Schemas
class DocumentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    document_type: DocumentTypeEnum
    category: Optional[DocumentCategoryEnum] = None
    subcategory: Optional[str] = Field(None, max_length=100)
    tags: Optional[str] = Field(None, max_length=500)
    is_public: bool = False
    access_level: AccessLevelEnum = AccessLevelEnum.INTERNAL
    
    @validator('category', pre=True, allow_reuse=True)
    def normalize_category(cls, v):
        """Normalisiert Kategorien - akzeptiert sowohl uppercase als auch lowercase"""
        if v is None:
            return None
        
        if isinstance(v, str):
            # Mapping von verschiedenen Eingabeformaten zu korrekten Enum-Werten
            category_mapping = {
                # Uppercase (Backend)
                'PLANNING': DocumentCategoryEnum.PLANNING,
                'CONTRACTS': DocumentCategoryEnum.CONTRACTS,
                'FINANCE': DocumentCategoryEnum.FINANCE,
                'EXECUTION': DocumentCategoryEnum.EXECUTION,
                'DOCUMENTATION': DocumentCategoryEnum.DOCUMENTATION,
                'ORDER_CONFIRMATIONS': DocumentCategoryEnum.ORDER_CONFIRMATIONS,
                # Lowercase (Frontend)
                'planning': DocumentCategoryEnum.PLANNING,
                'contracts': DocumentCategoryEnum.CONTRACTS,
                'finance': DocumentCategoryEnum.FINANCE,
                'execution': DocumentCategoryEnum.EXECUTION,
                'documentation': DocumentCategoryEnum.DOCUMENTATION,
                'order_confirmations': DocumentCategoryEnum.ORDER_CONFIRMATIONS,
            }
            
            return category_mapping.get(v, DocumentCategoryEnum.DOCUMENTATION)
        
        return v
    
    @validator('document_type', pre=True, allow_reuse=True)
    def normalize_document_type(cls, v):
        """Normalisiert Document Types - akzeptiert sowohl uppercase als auch lowercase"""
        if isinstance(v, str):
            # Mapping von verschiedenen Eingabeformaten zu korrekten Enum-Werten
            type_mapping = {
                # Uppercase
                'PLAN': DocumentTypeEnum.PLAN,
                'PERMIT': DocumentTypeEnum.PERMIT,
                'QUOTE': DocumentTypeEnum.QUOTE,
                'INVOICE': DocumentTypeEnum.INVOICE,
                'CONTRACT': DocumentTypeEnum.CONTRACT,
                'PHOTO': DocumentTypeEnum.PHOTO,
                'BLUEPRINT': DocumentTypeEnum.BLUEPRINT,
                'CERTIFICATE': DocumentTypeEnum.CERTIFICATE,
                'REPORT': DocumentTypeEnum.REPORT,
                'VIDEO': DocumentTypeEnum.VIDEO,
                'PDF': DocumentTypeEnum.PDF,
                'OTHER': DocumentTypeEnum.OTHER,
                # Lowercase
                'plan': DocumentTypeEnum.PLAN,
                'permit': DocumentTypeEnum.PERMIT,
                'quote': DocumentTypeEnum.QUOTE,
                'invoice': DocumentTypeEnum.INVOICE,
                'contract': DocumentTypeEnum.CONTRACT,
                'photo': DocumentTypeEnum.PHOTO,
                'blueprint': DocumentTypeEnum.BLUEPRINT,
                'certificate': DocumentTypeEnum.CERTIFICATE,
                'report': DocumentTypeEnum.REPORT,
                'video': DocumentTypeEnum.VIDEO,
                'pdf': DocumentTypeEnum.PDF,
                'other': DocumentTypeEnum.OTHER,
            }
            
            return type_mapping.get(v, DocumentTypeEnum.OTHER)
        
        return v

class DocumentCreate(DocumentBase):
    project_id: int
    # Datei-Informationen für Upload
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    # Versionierung
    version_number: Optional[str] = "1.0.0"
    change_description: Optional[str] = Field(None, max_length=500)
    change_type: ChangeTypeEnum = ChangeTypeEnum.MINOR

class DocumentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[DocumentCategoryEnum] = None
    subcategory: Optional[str] = Field(None, max_length=100)
    tags: Optional[str] = Field(None, max_length=500)
    is_public: Optional[bool] = None
    access_level: Optional[AccessLevelEnum] = None
    
    # Status-Updates
    document_status: Optional[DocumentStatusEnum] = None
    workflow_stage: Optional[WorkflowStageEnum] = None
    approval_status: Optional[ApprovalStatusEnum] = None
    review_status: Optional[ReviewStatusEnum] = None
    rejection_reason: Optional[str] = Field(None, max_length=1000)

# Version Schemas
class DocumentVersionBase(BaseModel):
    version_number: str = Field(..., min_length=1, max_length=50)
    change_description: Optional[str] = Field(None, max_length=500)
    change_type: ChangeTypeEnum = ChangeTypeEnum.MINOR

class DocumentVersionCreate(DocumentVersionBase):
    document_id: int

class DocumentVersion(DocumentVersionBase):
    id: int
    document_id: int
    version_major: int
    version_minor: int
    version_patch: int
    file_path: Optional[str]
    file_name: Optional[str]
    file_size: Optional[int]
    mime_type: Optional[str]
    checksum: Optional[str]
    created_by: Optional[int]
    created_at: datetime
    is_active: bool
    metadata_json: Optional[str]

    class Config:
        from_attributes = True

# Status History Schemas
class DocumentStatusHistoryBase(BaseModel):
    change_reason: Optional[str] = Field(None, max_length=500)

class DocumentStatusHistoryCreate(DocumentStatusHistoryBase):
    document_id: int
    version_number: Optional[str]
    old_status: Optional[str]
    new_status: Optional[str]
    old_workflow_stage: Optional[str]
    new_workflow_stage: Optional[str]

class DocumentStatusHistory(DocumentStatusHistoryBase):
    id: int
    document_id: int
    version_number: Optional[str]
    old_status: Optional[str]
    new_status: Optional[str]
    old_workflow_stage: Optional[str]
    new_workflow_stage: Optional[str]
    changed_by: Optional[int]
    changed_at: datetime
    metadata_json: Optional[str]

    class Config:
        from_attributes = True

# Sharing Schemas
class DocumentShareBase(BaseModel):
    share_type: ShareTypeEnum = ShareTypeEnum.READ_ONLY
    permissions: Optional[str] = Field(None, max_length=1000)
    expires_at: Optional[datetime] = None

class DocumentShareCreate(DocumentShareBase):
    document_id: int
    shared_with_user_id: Optional[int] = None
    shared_with_project_id: Optional[int] = None
    shared_with_trade_id: Optional[int] = None

class DocumentShare(DocumentShareBase):
    id: int
    document_id: int
    shared_with_user_id: Optional[int]
    shared_with_project_id: Optional[int]
    shared_with_trade_id: Optional[int]
    shared_by: int
    shared_at: datetime
    access_count: int
    last_accessed_at: Optional[datetime]
    is_active: bool
    metadata_json: Optional[str]

    class Config:
        from_attributes = True

# Access Log Schemas
class DocumentAccessLogBase(BaseModel):
    access_type: str = Field(..., min_length=1, max_length=50)
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = Field(None, max_length=1000)
    duration_seconds: Optional[int] = None

class DocumentAccessLogCreate(DocumentAccessLogBase):
    document_id: int
    version_number: Optional[str] = None
    user_id: Optional[int] = None

class DocumentAccessLog(DocumentAccessLogBase):
    id: int
    document_id: int
    version_number: Optional[str]
    user_id: Optional[int]
    accessed_at: datetime
    success: bool
    error_message: Optional[str]
    metadata_json: Optional[str]

    class Config:
        from_attributes = True

# Main Document Schema (erweitert)
class Document(DocumentBase):
    id: int
    project_id: int
    
    # Datei-Informationen
    file_name: Optional[str]
    file_path: Optional[str]
    file_size: Optional[int]
    mime_type: Optional[str]
    
    # Versionierung
    version_number: str
    version_major: int
    version_minor: int
    version_patch: int
    is_latest_version: bool
    parent_document_id: Optional[int]
    
    # Status-Management
    document_status: str
    workflow_stage: str
    approval_status: str
    review_status: str
    
    # Locking
    locked_by: Optional[int]
    locked_at: Optional[datetime]
    
    # Genehmigung
    approved_by: Optional[int]
    approved_at: Optional[datetime]
    rejected_by: Optional[int]
    rejected_at: Optional[datetime]
    rejection_reason: Optional[str]
    
    # Lifecycle
    expires_at: Optional[datetime]
    archived_at: Optional[datetime]
    
    # Integrität
    checksum: Optional[str]
    file_format_version: Optional[str]
    metadata_json: Optional[str]
    
    # Zugriff
    sharing_permissions: Optional[str]
    download_count: int
    last_accessed_by: Optional[int]
    last_accessed_at: Optional[datetime]
    
    # Standard-Felder
    uploaded_by: int
    created_at: datetime
    updated_at: datetime
    is_favorite: bool
    
    # Relationships (optional für Performance)
    versions: Optional[List[DocumentVersion]] = None
    status_history: Optional[List[DocumentStatusHistory]] = None
    shares: Optional[List[DocumentShare]] = None
    access_logs: Optional[List[DocumentAccessLog]] = None

    class Config:
        from_attributes = True

# Spezielle Schemas für API-Responses
class DocumentSummary(BaseModel):
    """Lightweight Document Schema für Listen"""
    id: int
    title: str
    document_type: str
    category: Optional[str]
    subcategory: Optional[str]
    version_number: str
    document_status: str
    workflow_stage: str
    file_name: Optional[str]
    file_size: Optional[int]
    created_at: datetime
    updated_at: datetime
    is_favorite: bool
    download_count: int

    class Config:
        from_attributes = True

class DocumentWithVersions(Document):
    """Document mit vollständiger Versions-Historie"""
    versions: List[DocumentVersion]
    status_history: List[DocumentStatusHistory]

    class Config:
        from_attributes = True

class DocumentShareRequest(BaseModel):
    """Request Schema für Dokument-Sharing"""
    document_ids: List[int] = Field(..., min_items=1)
    shared_with_user_id: Optional[int] = None
    shared_with_project_id: Optional[int] = None
    shared_with_trade_id: Optional[int] = None
    share_type: ShareTypeEnum = ShareTypeEnum.READ_ONLY
    permissions: Optional[str] = None
    expires_at: Optional[datetime] = None
    message: Optional[str] = Field(None, max_length=500)

class DocumentBulkOperation(BaseModel):
    """Schema für Bulk-Operationen"""
    document_ids: List[int] = Field(..., min_items=1)
    operation: str = Field(..., min_length=1)
    parameters: Optional[Dict[str, Any]] = None

class DocumentUploadResponse(BaseModel):
    """Response Schema für Dokument-Upload"""
    id: int
    title: str
    file_name: str
    file_size: int
    version_number: str
    document_status: str
    workflow_stage: str
    upload_success: bool
    message: Optional[str] = None

    class Config:
        from_attributes = True

# Validation Schemas
class VersionNumberValidator(BaseModel):
    version_number: str
    
    @validator('version_number')
    def validate_version_number(cls, v):
        """Validiert Semantic Version Format (Major.Minor.Patch)"""
        parts = v.split('.')
        if len(parts) != 3:
            raise ValueError('Version number must be in format Major.Minor.Patch')
        
        try:
            major, minor, patch = map(int, parts)
            if major < 0 or minor < 0 or patch < 0:
                raise ValueError('Version components must be non-negative integers')
        except ValueError:
            raise ValueError('Version components must be integers')
        
        return v 