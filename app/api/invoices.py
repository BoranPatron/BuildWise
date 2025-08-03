"""
API endpoints for invoice management
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import json
from pathlib import Path

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models import User, UserRole, UserType, Invoice, InvoiceStatus
from app.schemas.invoice import (
    InvoiceCreate, InvoiceUpdate, InvoiceRead, InvoiceSummary,
    InvoiceUpload, InvoicePayment, InvoiceRating, InvoiceStats
)
from app.services.invoice_service import InvoiceService

router = APIRouter()

@router.post("/create", response_model=InvoiceRead)
async def create_manual_invoice(
    invoice_data: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Erstelle eine manuelle Rechnung"""
    
    # Berechtigung prüfen: Nur Dienstleister können Rechnungen erstellen
    if current_user.user_type not in [UserType.COMPANY, UserType.FREELANCER]:
        raise HTTPException(
            status_code=403,
            detail="Nur Dienstleister können Rechnungen erstellen"
        )
    
    try:
        # Setze den service_provider_id auf den aktuellen Benutzer
        invoice_data.service_provider_id = current_user.id
        
        invoice = await InvoiceService.create_manual_invoice(
            db=db,
            invoice_data=invoice_data,
            created_by_user_id=current_user.id
        )
        
        return invoice
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der Rechnung: {e}")
        raise HTTPException(status_code=500, detail="Interner Server-Fehler")

@router.post("/upload", response_model=InvoiceRead)
async def upload_invoice_pdf(
    milestone_id: int = Form(...),
    invoice_number: str = Form(...),
    total_amount: float = Form(...),
    notes: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lade eine PDF-Rechnung hoch"""
    
    # Berechtigung prüfen
    if current_user.user_type not in [UserType.COMPANY, UserType.FREELANCER]:
        raise HTTPException(
            status_code=403,
            detail="Nur Dienstleister können Rechnungen hochladen"
        )
    
    # Validiere Datei
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Nur PDF-Dateien sind erlaubt"
        )
    
    if file.size > 10 * 1024 * 1024:  # 10MB Limit
        raise HTTPException(
            status_code=400,
            detail="Datei ist zu groß (Maximum: 10MB)"
        )
    
    try:
        # Lese Datei-Inhalt
        pdf_content = await file.read()
        
        # Erstelle InvoiceUpload-Objekt
        invoice_data = InvoiceUpload(
            milestone_id=milestone_id,
            invoice_number=invoice_number,
            total_amount=total_amount,
            notes=notes
        )
        
        invoice = await InvoiceService.upload_invoice_pdf(
            db=db,
            invoice_data=invoice_data,
            pdf_file=pdf_content,
            original_filename=file.filename,
            created_by_user_id=current_user.id
        )
        
        return invoice
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"❌ Fehler beim Hochladen der Rechnung: {e}")
        raise HTTPException(status_code=500, detail="Interner Server-Fehler")

@router.get("/{invoice_id}", response_model=InvoiceRead)
async def get_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Hole eine bestimmte Rechnung"""
    
    invoice = await InvoiceService.get_invoice_by_id(db, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Rechnung nicht gefunden")
    
    # Berechtigung prüfen: Nur Ersteller, Bauträger des Projekts oder Admin
    if (current_user.id != invoice.service_provider_id and 
        current_user.id != invoice.project.owner_id and
        current_user.user_role != UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Keine Berechtigung")
    
    # Markiere als angesehen wenn vom Bauträger aufgerufen
    if (current_user.id == invoice.project.owner_id and 
        invoice.status == InvoiceStatus.SENT):
        invoice.status = InvoiceStatus.VIEWED
        await db.commit()
    
    return invoice

@router.get("/project/{project_id}", response_model=List[InvoiceSummary])
async def get_project_invoices(
    project_id: int,
    status: Optional[InvoiceStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Hole alle Rechnungen für ein Projekt"""
    
    # Berechtigung prüfen: Nur Projektinhaber oder Admin
    if current_user.user_role != UserRole.ADMIN:
        # TODO: Prüfe ob User der Projektinhaber ist
        pass
    
    invoices = await InvoiceService.get_invoices_for_project(
        db=db, 
        project_id=project_id, 
        status=status
    )
    
    # Konvertiere zu InvoiceSummary
    summaries = []
    for invoice in invoices:
        summary = InvoiceSummary(
            id=invoice.id,
            invoice_number=invoice.invoice_number,
            invoice_date=invoice.invoice_date,
            due_date=invoice.due_date,
            total_amount=invoice.total_amount,
            status=invoice.status,
            type=invoice.type,
            milestone_title=invoice.milestone.title if invoice.milestone else None,
            service_provider_name=f"{invoice.service_provider.first_name} {invoice.service_provider.last_name}" if invoice.service_provider else None,
            is_overdue=invoice.status == InvoiceStatus.OVERDUE
        )
        summaries.append(summary)
    
    return summaries

@router.get("/milestone/{milestone_id}", response_model=Optional[InvoiceRead])
async def get_milestone_invoice(
    milestone_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Hole die Rechnung für einen Meilenstein"""
    
    invoice = await InvoiceService.get_invoice_by_milestone(db, milestone_id)
    if not invoice:
        return None
    
    # Berechtigung prüfen
    if (current_user.id != invoice.service_provider_id and 
        current_user.id != invoice.project.owner_id and
        current_user.user_role != UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Keine Berechtigung")
    
    return invoice

@router.get("/service-provider/my-invoices", response_model=List[InvoiceSummary])
async def get_my_invoices(
    status: Optional[InvoiceStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Hole alle Rechnungen des aktuellen Dienstleisters"""
    
    if current_user.user_type not in [UserType.COMPANY, UserType.FREELANCER]:
        raise HTTPException(
            status_code=403,
            detail="Nur Dienstleister können ihre Rechnungen abrufen"
        )
    
    invoices = await InvoiceService.get_invoices_for_service_provider(
        db=db,
        service_provider_id=current_user.id,
        status=status
    )
    
    # Konvertiere zu InvoiceSummary
    summaries = []
    for invoice in invoices:
        summary = InvoiceSummary(
            id=invoice.id,
            invoice_number=invoice.invoice_number,
            invoice_date=invoice.invoice_date,
            due_date=invoice.due_date,
            total_amount=invoice.total_amount,
            status=invoice.status,
            type=invoice.type,
            milestone_title=invoice.milestone.title if invoice.milestone else None,
            service_provider_name=f"{current_user.first_name} {current_user.last_name}",
            is_overdue=invoice.status == InvoiceStatus.OVERDUE
        )
        summaries.append(summary)
    
    return summaries

@router.post("/{invoice_id}/mark-paid", response_model=InvoiceRead)
async def mark_invoice_paid(
    invoice_id: int,
    payment_data: InvoicePayment,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Markiere eine Rechnung als bezahlt"""
    
    invoice = await InvoiceService.get_invoice_by_id(db, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Rechnung nicht gefunden")
    
    # Berechtigung prüfen: Nur Bauträger oder Admin
    if (current_user.id != invoice.project.owner_id and
        current_user.user_role != UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Keine Berechtigung")
    
    try:
        updated_invoice = await InvoiceService.mark_invoice_as_paid(
            db=db,
            invoice_id=invoice_id,
            payment_data=payment_data
        )
        return updated_invoice
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{invoice_id}/rate", response_model=InvoiceRead)
async def rate_service_provider(
    invoice_id: int,
    rating_data: InvoiceRating,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bewerte den Dienstleister nach Rechnungsstellung"""
    
    invoice = await InvoiceService.get_invoice_by_id(db, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Rechnung nicht gefunden")
    
    # Berechtigung prüfen: Nur Bauträger
    if current_user.id != invoice.project.owner_id:
        raise HTTPException(status_code=403, detail="Nur der Bauträger kann bewerten")
    
    try:
        updated_invoice = await InvoiceService.rate_service_provider(
            db=db,
            invoice_id=invoice_id,
            rating_data=rating_data,
            rated_by_user_id=current_user.id
        )
        return updated_invoice
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{invoice_id}/download")
async def download_invoice_pdf(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lade die PDF-Rechnung herunter"""
    
    invoice = await InvoiceService.get_invoice_by_id(db, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Rechnung nicht gefunden")
    
    # Berechtigung prüfen
    if (current_user.id != invoice.service_provider_id and 
        current_user.id != invoice.project.owner_id and
        current_user.user_role != UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Keine Berechtigung")
    
    # Prüfe ob PDF-Datei existiert
    if not invoice.pdf_file_path or not Path(invoice.pdf_file_path).exists():
        raise HTTPException(status_code=404, detail="PDF-Datei nicht gefunden")
    
    return FileResponse(
        path=invoice.pdf_file_path,
        filename=invoice.pdf_file_name or f"Rechnung_{invoice.invoice_number}.pdf",
        media_type="application/pdf"
    )

@router.get("/stats/project/{project_id}", response_model=InvoiceStats)
async def get_project_invoice_stats(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Hole Rechnungsstatistiken für ein Projekt"""
    
    # Berechtigung prüfen: Nur Projektinhaber oder Admin
    if current_user.user_role != UserRole.ADMIN:
        # TODO: Prüfe ob User der Projektinhaber ist
        pass
    
    stats = await InvoiceService.get_invoice_statistics(
        db=db,
        project_id=project_id
    )
    
    return stats

@router.get("/stats/service-provider/my-stats", response_model=InvoiceStats)
async def get_my_invoice_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Hole Rechnungsstatistiken des aktuellen Dienstleisters"""
    
    if current_user.user_type not in [UserType.COMPANY, UserType.FREELANCER]:
        raise HTTPException(
            status_code=403,
            detail="Nur Dienstleister können ihre Statistiken abrufen"
        )
    
    stats = await InvoiceService.get_invoice_statistics(
        db=db,
        service_provider_id=current_user.id
    )
    
    return stats