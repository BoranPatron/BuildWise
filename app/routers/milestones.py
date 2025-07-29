from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..auth import get_current_user
from ..models.user import User
from ..schemas.milestone import (
    MilestoneCreate, 
    MilestoneUpdate, 
    MilestoneResponse,
    MilestoneCompletionRequest,
    MilestoneInspectionUpdate,
    MilestoneInvoiceRequest
)
from ..services import milestone_service

router = APIRouter()

# ==================== ABSCHLUSS-WORKFLOW ENDPOINTS ====================

@router.post("/completion/request")
async def request_milestone_completion(
    completion_request: MilestoneCompletionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Dienstleister beantragt Abschluss eines Gewerkes
    """
    try:
        milestone = await milestone_service.request_milestone_completion(
            db, completion_request, current_user.id
        )
        return {
            "message": "Abschluss-Antrag erfolgreich eingereicht",
            "milestone": milestone
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/completion/checklist/{category}")
async def get_completion_checklist_template(
    category: str,
    current_user: User = Depends(get_current_user)
):
    """
    Holt kategorie-spezifische Abnahme-Checkliste Vorlage
    """
    template = milestone_service.get_completion_checklist_template(category)
    return {
        "category": category,
        "template": template
    }

@router.post("/inspection/conduct")
async def conduct_milestone_inspection(
    inspection_update: MilestoneInspectionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Bauträger führt Abnahme durch
    """
    try:
        milestone = await milestone_service.conduct_milestone_inspection(
            db, inspection_update, current_user.id
        )
        return {
            "message": "Abnahme erfolgreich durchgeführt",
            "milestone": milestone
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/invoice/generate")
async def generate_milestone_invoice(
    invoice_request: MilestoneInvoiceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Dienstleister erstellt Rechnung für abgeschlossenes Gewerk
    """
    try:
        milestone = await milestone_service.generate_milestone_invoice(
            db, invoice_request, current_user.id
        )
        return {
            "message": "Rechnung erfolgreich erstellt",
            "milestone": milestone
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/invoice/{milestone_id}/approve")
async def approve_milestone_invoice(
    milestone_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Bauträger genehmigt Rechnung
    """
    try:
        milestone = await milestone_service.approve_milestone_invoice(
            db, milestone_id, current_user.id
        )
        return {
            "message": "Rechnung erfolgreich genehmigt",
            "milestone": milestone
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{milestone_id}/archive")
async def archive_milestone(
    milestone_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Archiviert ein abgeschlossenes Gewerk
    """
    try:
        milestone = await milestone_service.archive_milestone(
            db, milestone_id, current_user.id
        )
        return {
            "message": "Gewerk erfolgreich archiviert",
            "milestone": milestone
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/archived")
async def get_archived_milestones(
    search_query: Optional[str] = None,
    category_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Holt archivierte Gewerke für den aktuellen Benutzer
    """
    # Bestimme, ob Benutzer ein Dienstleister ist
    is_service_provider = current_user.user_type == "service_provider"
    
    milestones = await milestone_service.get_archived_milestones(
        db, 
        current_user.id, 
        is_service_provider,
        search_query,
        category_filter,
        skip,
        limit
    )
    
    return {
        "milestones": milestones,
        "total": len(milestones),
        "skip": skip,
        "limit": limit
    }

@router.post("/photos/upload")
async def upload_completion_photo(
    file: UploadFile = File(...),
    milestone_id: int = None,
    category: str = "overview",
    caption: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Upload von Fotos für Gewerke-Abschluss
    """
    # TODO: Implementiere Foto-Upload Logik
    # - Validiere Dateityp (nur Bilder)
    # - Speichere in Cloud Storage (AWS S3, etc.)
    # - Generiere URL
    # - Speichere Metadaten
    
    return {
        "message": "Foto erfolgreich hochgeladen",
        "photo_url": f"https://storage.example.com/photos/{file.filename}",
        "category": category,
        "caption": caption
    }

@router.post("/documents/upload")
async def upload_completion_document(
    file: UploadFile = File(...),
    milestone_id: int = None,
    document_type: str = "certificate",
    current_user: User = Depends(get_current_user)
):
    """
    Upload von Dokumenten für Gewerke-Abschluss
    """
    # TODO: Implementiere Dokument-Upload Logik
    # - Validiere Dateityp (PDF, DOC, etc.)
    # - Speichere in Cloud Storage
    # - Generiere URL
    # - Speichere Metadaten
    
    return {
        "message": "Dokument erfolgreich hochgeladen",
        "document_url": f"https://storage.example.com/documents/{file.filename}",
        "document_type": document_type
    }

# ==================== STATUS-ENDPOINTS ====================

@router.get("/{milestone_id}/completion-status")
async def get_milestone_completion_status(
    milestone_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Holt den aktuellen Abschluss-Status eines Gewerkes
    """
    milestone = await milestone_service.get_milestone(db, milestone_id)
    
    if not milestone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gewerk nicht gefunden"
        )
    
    return {
        "milestone_id": milestone_id,
        "completion_status": milestone.completion_status,
        "completion_requested_at": milestone.completion_requested_at,
        "inspection_date": milestone.inspection_date,
        "acceptance_date": milestone.acceptance_date,
        "invoice_generated": milestone.invoice_generated,
        "invoice_approved": milestone.invoice_approved,
        "archived": milestone.archived
    }

@router.get("/completion-pending")
async def get_completion_pending_milestones(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Holt alle Gewerke, die auf Abnahme warten (für Bauträger)
    """
    # TODO: Implementiere Abfrage für Gewerke mit Status "completion_requested"
    return {
        "pending_milestones": [],
        "count": 0
    } 