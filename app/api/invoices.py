"""
API endpoints for invoice management
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import json
from pathlib import Path

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models import User, UserRole, UserType, Invoice, InvoiceStatus, Milestone
from app.schemas.invoice import (
    InvoiceCreate, InvoiceUpdate, InvoiceRead, InvoiceSummary,
    InvoiceUpload, InvoicePayment, InvoiceRating, InvoiceStats
)
from app.services.invoice_service import InvoiceService
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.delete("/debug/delete-all-invoices")
async def delete_all_invoices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Debug-Endpoint zum Löschen aller Rechnungen"""
    try:
        # Prüfe ob User ein Admin oder Bauträger ist
        if not (current_user.user_role == UserRole.ADMIN or current_user.user_role == UserRole.BAUTRAEGER):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Nur Admins und Bauträger können alle Rechnungen löschen"
            )
        
        # Lösche alle Rechnungen und zugehörige Kostenpositionen
        from sqlalchemy import text
        
        # Lösche zuerst die Kostenpositionen
        await db.execute(text("DELETE FROM cost_positions"))
        
        # Dann lösche die Rechnungen
        await db.execute(text("DELETE FROM invoices"))
        
        await db.commit()
        
        return {"message": "Alle Rechnungen und Kostenpositionen wurden gelöscht"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Löschen der Rechnungen: {str(e)}"
        )


@router.get("/my-invoices", response_model=List[dict])
async def get_my_invoices_simple(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lade alle Rechnungen des aktuellen Dienstleisters (vereinfacht)"""
    try:
        print(f"🔍 Lade Rechnungen für User: {current_user.id} (Type: {current_user.user_type}, Role: {current_user.user_role})")
        
        # Prüfe ob User ein Dienstleister ist
        is_service_provider = (
            current_user.user_type == UserType.SERVICE_PROVIDER or
            current_user.user_role == UserRole.DIENSTLEISTER or
            str(current_user.user_type).lower() == 'service_provider' or
            str(current_user.user_role).lower() == 'dienstleister'
        )
        
        if not is_service_provider:
            print(f"❌ Zugriff verweigert - User Type: {current_user.user_type}, User Role: {current_user.user_role}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Nur Dienstleister können ihre Rechnungen einsehen"
            )
        
        # Lade alle Rechnungen des Dienstleisters
        stmt = select(Invoice).where(
            Invoice.service_provider_id == current_user.id
        ).options(
            selectinload(Invoice.milestone).selectinload(Milestone.project)
        ).order_by(Invoice.created_at.desc())
        
        result = await db.execute(stmt)
        invoices = result.scalars().all()
        
        print(f"✅ {len(invoices)} Rechnungen gefunden für Dienstleister {current_user.id}")
        
        invoice_list = []
        for invoice in invoices:
            invoice_data = {
                'id': invoice.id,
                'invoice_number': invoice.invoice_number,
                'milestone_id': invoice.milestone_id,
                'milestone_title': invoice.milestone.title if invoice.milestone else 'Unbekannt',
                'project_name': invoice.milestone.project.name if invoice.milestone and invoice.milestone.project else 'Unbekannt',
                'total_amount': float(invoice.total_amount) if invoice.total_amount else 0.0,
                'status': invoice.status.value if invoice.status else 'draft',
                'due_date': invoice.due_date.isoformat() if invoice.due_date else None,
                'created_at': invoice.created_at.isoformat() if invoice.created_at else None,
                'updated_at': invoice.updated_at.isoformat() if invoice.updated_at else None,
                'pdf_path': invoice.pdf_file_path
            }
            invoice_list.append(invoice_data)
        
        return invoice_list
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Fehler beim Laden der Rechnungen: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Laden der Rechnungen: {str(e)}"
        )


@router.post("/create")
async def create_manual_invoice(
    invoice_data: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Erstelle eine manuelle Rechnung"""
    
    # Berechtigung prüfen: Nur Dienstleister können Rechnungen erstellen
    is_service_provider = (
        current_user.user_type == UserType.SERVICE_PROVIDER or
        current_user.user_role == UserRole.DIENSTLEISTER or
        str(current_user.user_type).lower() == 'service_provider' or
        str(current_user.user_role).lower() == 'dienstleister'
    )
    
    if not is_service_provider:
        print(f"❌ Zugriff verweigert - User Type: {current_user.user_type}, User Role: {current_user.user_role}")
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
        
        # Konvertiere Invoice-Objekt zu Dictionary (minimal)
        return {
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "total_amount": float(invoice.total_amount),
            "status": str(invoice.status),
            "message": "Rechnung erfolgreich erstellt"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der Rechnung: {e}")
        import traceback
        print(f"🔍 Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Interner Server-Fehler: {str(e)}")

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
    if current_user.user_type not in [UserType.SERVICE_PROVIDER]:
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
    
    try:
        print(f"🔍 Lade Rechnung für Milestone {milestone_id}, User: {current_user.id}")
        
        invoice = await InvoiceService.get_invoice_by_milestone(db, milestone_id)
        if not invoice:
            print(f"ℹ️ Keine Rechnung für Milestone {milestone_id} gefunden")
            return None
        
        print(f"✅ Rechnung gefunden: {invoice.id}, Service Provider: {invoice.service_provider_id}")
        print(f"🔍 Project Owner ID: {getattr(invoice.project, 'owner_id', 'NOT_LOADED')}")
        print(f"🔍 Current User: {current_user.id}, Role: {current_user.user_role}, Type: {current_user.user_type}")
        
        # Erweiterte Berechtigung prüfen - auch für Bauträger
        from ..models.user import UserRole, UserType
        is_bautraeger = (
            current_user.user_role == UserRole.BAUTRAEGER or 
            current_user.user_type in [UserType.PROFESSIONAL, 'bautraeger', 'developer', 'PROFESSIONAL', 'professional']
        )
        
        is_authorized = (
            current_user.id == invoice.service_provider_id or  # Dienstleister
            (hasattr(invoice.project, 'owner_id') and current_user.id == invoice.project.owner_id) or  # Projektbesitzer
            is_bautraeger or  # Bauträger
            current_user.user_role == UserRole.ADMIN  # Admin
        )
        
        if not is_authorized:
            print(f"❌ Berechtigung verweigert für User {current_user.id}")
            raise HTTPException(status_code=403, detail="Keine Berechtigung")
        
        print(f"✅ Berechtigung gewährt für User {current_user.id}")
        return invoice
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Fehler beim Laden der Rechnung für Milestone {milestone_id}: {e}")
        import traceback
        print(f"🔍 Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Laden der Rechnung: {str(e)}"
        )

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

@router.post("/{invoice_id}/mark-viewed", response_model=InvoiceRead)
async def mark_invoice_viewed(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Markiere eine Rechnung als angesehen"""
    
    try:
        print(f"🔍 Mark-viewed für Rechnung {invoice_id}, User: {current_user.id}")
        
        invoice = await InvoiceService.get_invoice_by_id(db, invoice_id)
        if not invoice:
            raise HTTPException(status_code=404, detail="Rechnung nicht gefunden")
        
        print(f"✅ Rechnung gefunden: {invoice.id}, Service Provider: {invoice.service_provider_id}")
        print(f"🔍 Current User: {current_user.id}, Role: {current_user.user_role}, Type: {current_user.user_type}")
        
        # Erweiterte Berechtigung prüfen - auch für Bauträger
        from ..models.user import UserRole, UserType
        is_bautraeger = (
            current_user.user_role == UserRole.BAUTRAEGER or 
            current_user.user_type in [UserType.PROFESSIONAL, 'bautraeger', 'developer', 'PROFESSIONAL', 'professional']
        )
        
        is_authorized = (
            current_user.id == invoice.service_provider_id or  # Dienstleister
            (hasattr(invoice.project, 'owner_id') and current_user.id == invoice.project.owner_id) or  # Projektbesitzer
            is_bautraeger or  # Bauträger
            current_user.user_role == UserRole.ADMIN  # Admin
        )
        
        if not is_authorized:
            print(f"❌ Berechtigung verweigert für User {current_user.id}")
            raise HTTPException(status_code=403, detail="Keine Berechtigung")
        
        print(f"✅ Berechtigung gewährt für User {current_user.id}")
        
        # ✅ Automatische DMS-Integration falls noch nicht vorhanden
        try:
            # Generiere PDF falls nicht vorhanden
            if not invoice.pdf_file_path or not Path(invoice.pdf_file_path).exists():
                print(f"🔍 Generiere PDF für Rechnung {invoice_id}")
                pdf_path = await InvoiceService.generate_invoice_pdf(db, invoice_id)
                invoice.pdf_file_path = pdf_path
                invoice.pdf_file_name = f"Rechnung_{invoice.invoice_number}.pdf"
                await db.commit()
                print(f"✅ PDF generiert: {pdf_path}")
            else:
                print(f"ℹ️ PDF bereits vorhanden: {invoice.pdf_file_path}")
            
            # DMS-Integration (optional - Fehler blockiert nicht)
            if not hasattr(invoice, 'dms_document_id') or not getattr(invoice, 'dms_document_id', None):
                try:
                    print(f"🔍 Starte DMS-Integration für Rechnung {invoice_id}")
                    await InvoiceService.create_dms_document(db, invoice, invoice.pdf_file_path)
                    print(f"✅ DMS-Dokument für Rechnung {invoice_id} erstellt und kategorisiert")
                except Exception as dms_error:
                    print(f"⚠️ DMS-Integration fehlgeschlagen (nicht kritisch): {dms_error}")
                    # DMS-Fehler blockiert nicht die Hauptfunktion
            else:
                print(f"ℹ️ DMS-Dokument bereits vorhanden für Rechnung {invoice_id}")
                
        except Exception as e:
            print(f"❌ Fehler bei PDF-Generierung: {e}")
            # Auch PDF-Fehler sollten nicht blockieren, wenn die Rechnung bereits existiert
        
        return invoice
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Fehler beim mark-viewed für Rechnung {invoice_id}: {e}")
        import traceback
        print(f"🔍 Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Markieren als angesehen: {str(e)}"
        )

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
    project_owner_id = None
    if invoice.project:
        project_owner_id = invoice.project.owner_id
    elif invoice.milestone and invoice.milestone.project:
        project_owner_id = invoice.milestone.project.owner_id
    
    # Erweiterte Berechtigung prüfen - auch für Bauträger
    from ..models.user import UserRole, UserType
    is_bautraeger = (
        current_user.user_role == UserRole.BAUTRAEGER or 
        current_user.user_type in [UserType.PROFESSIONAL, 'bautraeger', 'developer', 'PROFESSIONAL', 'professional']
    )
    
    is_authorized = (
        current_user.user_role == UserRole.ADMIN or  # Admin
        is_bautraeger or  # Bauträger
        (project_owner_id and current_user.id == project_owner_id)  # Projektbesitzer
    )
    
    if not is_authorized:
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
    
    try:
        print(f"🔍 Download-Request für Rechnung {invoice_id}, User: {current_user.id}")
        
        invoice = await InvoiceService.get_invoice_by_id(db, invoice_id)
        if not invoice:
            raise HTTPException(status_code=404, detail="Rechnung nicht gefunden")
        
        print(f"✅ Rechnung gefunden: {invoice.id}, Service Provider: {invoice.service_provider_id}")
        print(f"🔍 Current User: {current_user.id}, Role: {current_user.user_role}, Type: {current_user.user_type}")
        
        # Erweiterte Berechtigung prüfen - auch für Bauträger
        from ..models.user import UserRole, UserType
        is_bautraeger = (
            current_user.user_role == UserRole.BAUTRAEGER or 
            current_user.user_type in [UserType.PROFESSIONAL, 'bautraeger', 'developer', 'PROFESSIONAL', 'professional']
        )
        
        is_authorized = (
            current_user.id == invoice.service_provider_id or  # Dienstleister
            (hasattr(invoice.project, 'owner_id') and current_user.id == invoice.project.owner_id) or  # Projektbesitzer
            is_bautraeger or  # Bauträger
            current_user.user_role == UserRole.ADMIN  # Admin
        )
        
        if not is_authorized:
            print(f"❌ Berechtigung verweigert für User {current_user.id}")
            raise HTTPException(status_code=403, detail="Keine Berechtigung")
        
        print(f"✅ Berechtigung gewährt für User {current_user.id}")
        
        # Prüfe ob PDF-Datei existiert
        if not invoice.pdf_file_path or not Path(invoice.pdf_file_path).exists():
            # ✅ PDF generieren falls nicht vorhanden (für manuelle Rechnungen)
            print(f"🔍 PDF nicht gefunden für Rechnung {invoice_id}, generiere...")
            pdf_path = await InvoiceService.generate_invoice_pdf(db, invoice_id)
            
            # Update invoice mit PDF-Pfad
            invoice.pdf_file_path = pdf_path
            invoice.pdf_file_name = f"Rechnung_{invoice.invoice_number}.pdf"
            await db.commit()
            await db.refresh(invoice)
            
            # ✅ Automatische DMS-Integration für bestehende Rechnungen
            try:
                if not hasattr(invoice, 'dms_document_id') or not getattr(invoice, 'dms_document_id', None):
                    await InvoiceService.create_dms_document(db, invoice, pdf_path)
                    print(f"✅ DMS-Dokument erstellt für Rechnung {invoice_id}")
            except Exception as dms_error:
                print(f"⚠️ DMS-Integration fehlgeschlagen (nicht kritisch): {dms_error}")
            
            print(f"✅ PDF generiert: {pdf_path}")
        else:
            print(f"ℹ️ PDF bereits vorhanden: {invoice.pdf_file_path}")
        
        # Prüfe nochmal ob die Datei existiert
        if not Path(invoice.pdf_file_path).exists():
            raise HTTPException(status_code=500, detail="PDF-Datei konnte nicht erstellt werden")
        
        return FileResponse(
            path=str(invoice.pdf_file_path),
            filename=invoice.pdf_file_name or f"Rechnung_{invoice.invoice_number}.pdf",
            media_type="application/pdf"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Fehler beim Download für Rechnung {invoice_id}: {e}")
        import traceback
        print(f"🔍 Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Herunterladen der Rechnung: {str(e)}"
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


@router.get("/service-provider", response_model=List[dict])
async def get_service_provider_invoices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lade alle Rechnungen eines Dienstleisters"""
    try:
        print(f"🔍 Lade Rechnungen für Dienstleister: {current_user.id}")
        
        # Nur für Dienstleister
        is_service_provider = (
            current_user.user_type in ['service_provider', 'SERVICE_PROVIDER'] or
            current_user.user_role in ['DIENSTLEISTER', 'service_provider'] or
            str(current_user.user_type).lower() == 'service_provider'
        )
        
        if not is_service_provider:
            print(f"❌ Zugriff verweigert - User Type: {current_user.user_type}, User Role: {current_user.user_role}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Nur Dienstleister können ihre Rechnungen einsehen"
            )
        
        # Lade alle Rechnungen des Dienstleisters
        stmt = select(Invoice).where(
            Invoice.service_provider_id == current_user.id
        ).options(
            selectinload(Invoice.milestone).selectinload(Milestone.project)
        ).order_by(Invoice.created_at.desc())
        
        result = await db.execute(stmt)
        invoices = result.scalars().all()
        
        invoice_list = []
        for invoice in invoices:
            invoice_data = {
                'id': invoice.id,
                'invoice_number': invoice.invoice_number,
                'milestone_id': invoice.milestone_id,
                'milestone_title': invoice.milestone.title if invoice.milestone else 'Unbekanntes Gewerk',
                'project_name': invoice.milestone.project.title if invoice.milestone and invoice.milestone.project else 'Unbekanntes Projekt',
                'total_amount': invoice.total_amount,
                'currency': invoice.currency,
                'status': invoice.status,
                'created_at': invoice.created_at.isoformat(),
                'due_date': invoice.due_date.isoformat() if invoice.due_date else None,
                'paid_at': invoice.paid_at.isoformat() if invoice.paid_at else None
            }
            
            invoice_list.append(invoice_data)
        
        print(f"✅ {len(invoice_list)} Rechnungen für Dienstleister gefunden")
        return invoice_list
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Fehler beim Laden der Rechnungen: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Laden der Rechnungen: {str(e)}"
        )


@router.get("/milestone/{milestone_id}", response_model=dict)
async def get_invoice_for_milestone(
    milestone_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lade Rechnung für ein spezifisches Gewerk"""
    try:
        print(f"🔍 Lade Rechnung für Milestone: {milestone_id}")
        
        # Prüfe ob Milestone existiert und dem Dienstleister gehört
        milestone_stmt = select(Milestone).where(
            and_(
                Milestone.id == milestone_id,
                Milestone.service_provider_id == current_user.id
            )
        )
        milestone_result = await db.execute(milestone_stmt)
        milestone = milestone_result.scalar_one_or_none()
        
        if not milestone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gewerk nicht gefunden oder Sie haben keine Berechtigung"
            )
        
        # Lade Rechnung für dieses Gewerk
        invoice_stmt = select(Invoice).where(
            Invoice.milestone_id == milestone_id
        )
        invoice_result = await db.execute(invoice_stmt)
        invoice = invoice_result.scalar_one_or_none()
        
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Keine Rechnung für dieses Gewerk gefunden"
            )
        
        invoice_data = {
            'id': invoice.id,
            'invoice_number': invoice.invoice_number,
            'milestone_id': invoice.milestone_id,
            'milestone_title': milestone.title,
            'project_name': milestone.project.title if milestone.project else 'Unbekanntes Projekt',
            'total_amount': invoice.total_amount,
            'currency': invoice.currency,
            'status': invoice.status,
            'created_at': invoice.created_at.isoformat(),
            'due_date': invoice.due_date.isoformat() if invoice.due_date else None,
            'paid_at': invoice.paid_at.isoformat() if invoice.paid_at else None
        }
        
        print(f"✅ Rechnung für Milestone {milestone_id} gefunden")
        return invoice_data
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Fehler beim Laden der Rechnung: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Laden der Rechnung: {str(e)}"
        )