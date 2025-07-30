from datetime import date, datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
# Enums wurden zu Strings geändert - keine Imports mehr nötig


class MilestoneBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "planned"
    priority: str = "medium"
    category: Optional[str] = None
    planned_date: date
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget: Optional[float] = None
    actual_costs: Optional[float] = None
    contractor: Optional[str] = None
    is_critical: bool = False
    notify_on_completion: bool = True
    notes: Optional[str] = None
    # Bauphasen-Tracking
    construction_phase: Optional[str] = None
    # Besichtigungssystem
    requires_inspection: bool = False


class MilestoneCreate(MilestoneBase):
    project_id: int
    documents: List[Dict[str, Any]] = []


class MilestoneUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    planned_date: Optional[date] = None
    actual_date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget: Optional[float] = None
    actual_costs: Optional[float] = None
    contractor: Optional[str] = None
    progress_percentage: Optional[int] = None
    is_critical: Optional[bool] = None
    notify_on_completion: Optional[bool] = None
    notes: Optional[str] = None
    # Bauphasen-Tracking
    construction_phase: Optional[str] = None
    # Besichtigungssystem
    requires_inspection: Optional[bool] = None


class MilestoneRead(MilestoneBase):
    id: int
    project_id: int
    created_by: int
    actual_date: Optional[date] = None
    progress_percentage: int
    documents: List[Dict[str, Any]] = []  # Immer Liste, nie None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    # Bauphasen-Tracking
    construction_phase: Optional[str] = None

    class Config:
        from_attributes = True
        use_enum_values = True  # Enum als String serialisieren
    
    def __init__(self, **data):
        # Sichere JSON-Deserialisierung für documents falls direkt aus DB-Objekt erstellt
        if 'documents' in data and isinstance(data['documents'], str):
            import json
            try:
                parsed = json.loads(data['documents'])
                data['documents'] = parsed if isinstance(parsed, list) else []
            except (json.JSONDecodeError, TypeError):
                data['documents'] = []
        super().__init__(**data)
        
    @classmethod
    def from_orm(cls, obj):
        import json
        
        # Sichere JSON-Deserialisierung für documents
        documents = []
        if hasattr(obj, 'documents') and obj.documents:
            try:
                if isinstance(obj.documents, str):
                    # JSON-String parsen
                    parsed = json.loads(obj.documents)
                    documents = parsed if isinstance(parsed, list) else []
                elif isinstance(obj.documents, list):
                    # Bereits eine Liste
                    documents = obj.documents
                else:
                    # Fallback für andere Typen
                    documents = []
            except (json.JSONDecodeError, TypeError, AttributeError) as e:
                print(f"⚠️ [SCHEMA] Fehler beim Parsen von documents: {e}")
                documents = []
        
        print(f"🔧 [SCHEMA] Documents parsed: {documents} (type: {type(documents)})")
        
        data = {
            'id': obj.id,
            'title': obj.title,
            'description': obj.description,
            'status': obj.status,
            'priority': obj.priority,
            'category': obj.category,
            'planned_date': obj.planned_date,
            'actual_date': obj.actual_date,
            'start_date': obj.start_date,
            'end_date': obj.end_date,
            'budget': obj.budget,
            'actual_costs': obj.actual_costs,
            'contractor': obj.contractor,
            'progress_percentage': obj.progress_percentage,
            'is_critical': obj.is_critical,
            'notify_on_completion': obj.notify_on_completion,
            'notes': obj.notes,
            'project_id': obj.project_id,
            'created_by': obj.created_by,
            'documents': documents,  # Sichere Liste-Konvertierung
            'created_at': obj.created_at,
            'updated_at': obj.updated_at,
            'completed_at': obj.completed_at,
            'construction_phase': obj.construction_phase,
            'requires_inspection': obj.requires_inspection
        }
        return cls(**data)


class MilestoneSummary(BaseModel):
    id: int
    title: str
    status: str  # String statt Enum
    priority: str  # String statt Enum
    category: Optional[str] = None
    planned_date: date
    actual_date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget: Optional[float] = None
    actual_costs: Optional[float] = None
    contractor: Optional[str] = None
    progress_percentage: int
    is_critical: bool
    project_id: Optional[int] = None  # Projekt-ID hinzufügen
    documents: List[Dict[str, Any]] = []
    # Bauphasen-Tracking
    construction_phase: Optional[str] = None
    # Besichtigungssystem
    requires_inspection: bool = False

    class Config:
        from_attributes = True 
        use_enum_values = True  # Enum als String serialisieren
        
    @classmethod
    def from_orm(cls, obj):
        import json
        
        # Parse documents JSON string zu Liste
        documents = []
        if obj.documents:
            try:
                if isinstance(obj.documents, str):
                    documents = json.loads(obj.documents)
                elif isinstance(obj.documents, list):
                    documents = obj.documents
                else:
                    documents = []
            except (json.JSONDecodeError, TypeError):
                documents = []
        
        # Status und Priority sind bereits Strings
        data = {
            'id': obj.id,
            'title': obj.title,
            'status': obj.status,
            'priority': obj.priority,
            'category': obj.category,
            'planned_date': obj.planned_date,
            'actual_date': obj.actual_date,
            'start_date': obj.start_date,
            'end_date': obj.end_date,
            'budget': obj.budget,
            'actual_costs': obj.actual_costs,
            'contractor': obj.contractor,
            'progress_percentage': obj.progress_percentage,
            'is_critical': obj.is_critical,
            'project_id': obj.project_id,
            'documents': documents,  # Jetzt echte Liste
            'construction_phase': obj.construction_phase,
            'requires_inspection': obj.requires_inspection
        }
        return cls(**data) 

class CompletionPhoto(BaseModel):
    """Schema für Abschluss-Fotos"""
    url: str
    caption: Optional[str] = None
    category: str  # "before", "after", "detail", "overview"
    timestamp: datetime
    location: Optional[Dict[str, float]] = None  # lat, lng

class DefectItem(BaseModel):
    """Schema für Mängel"""
    id: str
    description: str
    category: str  # "critical", "minor", "cosmetic"
    location: Optional[str] = None
    photo_urls: List[str] = []
    deadline: Optional[date] = None
    status: str = "open"  # "open", "in_progress", "resolved"

class CompletionChecklist(BaseModel):
    """Schema für Abnahme-Checkliste"""
    category: str
    items: List[Dict[str, Any]]  # Flexible Struktur je nach Kategorie
    overall_rating: int  # 1-5 Sterne
    notes: Optional[str] = None
    completed_by: int
    completed_at: datetime

class InspectionReport(BaseModel):
    """Schema für Abnahme-Protokoll"""
    inspector_id: int
    inspection_date: datetime
    overall_assessment: str  # "accepted", "accepted_with_conditions", "rejected"
    quality_rating: int  # 1-5 Sterne
    notes: Optional[str] = None
    defects: List[DefectItem] = []
    photos: List[CompletionPhoto] = []

class InvoiceData(BaseModel):
    """Schema für automatisch generierte Rechnung"""
    invoice_number: str
    total_amount: float
    items: List[Dict[str, Any]]
    generated_at: datetime
    pdf_url: Optional[str] = None

class MilestoneCompletionRequest(BaseModel):
    """Schema für Abschluss-Antrag"""
    milestone_id: int
    checklist: CompletionChecklist
    photos: List[CompletionPhoto] = []
    documents: List[str] = []  # URLs zu Dokumenten
    notes: Optional[str] = None

class MilestoneInspectionUpdate(BaseModel):
    """Schema für Abnahme-Update"""
    milestone_id: int
    inspection_report: InspectionReport

class MilestoneInvoiceRequest(BaseModel):
    """Schema für Rechnungsstellung"""
    milestone_id: int
    use_custom_invoice: bool = False
    custom_invoice_url: Optional[str] = None
    invoice_data: Optional[InvoiceData] = None

# Erweiterte Milestone Response Schemas
class MilestoneResponse(MilestoneBase):
    id: int
    project_id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    
    # Neue Felder für Abschluss-Workflow
    completion_status: str
    completion_requested_at: Optional[datetime] = None
    completion_checklist: Optional[CompletionChecklist] = None
    completion_photos: List[CompletionPhoto] = []
    completion_documents: List[str] = []
    
    # Abnahme
    inspection_date: Optional[datetime] = None
    inspection_report: Optional[InspectionReport] = None
    defects_list: List[DefectItem] = []
    acceptance_date: Optional[datetime] = None
    accepted_by: Optional[int] = None
    
    # Rechnungsstellung
    invoice_generated: bool = False
    invoice_data: Optional[InvoiceData] = None
    custom_invoice_url: Optional[str] = None
    invoice_approved: bool = False
    invoice_approved_at: Optional[datetime] = None
    invoice_approved_by: Optional[int] = None
    
    # Archivierung
    archived: bool = False
    archived_at: Optional[datetime] = None

    class Config:
        from_attributes = True 