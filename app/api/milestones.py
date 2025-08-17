from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..api.deps import get_current_user
from ..models import User, Milestone, Quote, CostPosition
import os
from ..schemas.milestone import MilestoneCreate, MilestoneRead, MilestoneUpdate, MilestoneSummary
# Milestone service functions sind direkt in dieser Datei implementiert
# from ..services.milestone_service import archive_milestone

router = APIRouter(prefix="/milestones", tags=["milestones"])


@router.post("/", response_model=MilestoneRead, status_code=status.HTTP_201_CREATED)
async def create_new_milestone(
    milestone_in: MilestoneCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Erstellt ein neues Milestone ohne Dokumente"""
    try:
        user_id = getattr(current_user, 'id')
        print(f"🔧 [API] create_new_milestone called for user {user_id}")
        print(f"🔧 [API] Milestone data: {milestone_in.model_dump()}")
        
        # milestone = await create_milestone(db, milestone_in, user_id)
        # Temporär deaktiviert - Funktion nicht verfügbar
        raise HTTPException(status_code=501, detail="create_milestone temporarily disabled")
        print(f"✅ [API] Milestone erfolgreich erstellt: ID={milestone.id}, Title='{milestone.title}', Project={milestone.project_id}")
        
        # 🎯 KRITISCH: Explizite Schema-Konvertierung für konsistente Response
        milestone_read = MilestoneRead.from_orm(milestone)
        print(f"🔧 [API] Schema-Konvertierung abgeschlossen, documents type: {type(milestone_read.documents)}")
        return milestone_read
        
    except Exception as e:
        print(f"❌ [API] Fehler beim Erstellen des Milestones: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Fehler beim Erstellen des Gewerks: {str(e)}")


@router.post("/with-documents", response_model=MilestoneRead, status_code=status.HTTP_201_CREATED)
async def create_milestone_with_documents(
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    priority: str = Form("medium"),
    planned_date: str = Form(...),
    notes: str = Form(""),
    requires_inspection: bool = Form(False),
    project_id: int = Form(...),
    document_ids: str = Form(None),  # JSON string mit IDs der hochgeladenen Dokumente
    shared_document_ids: str = Form(None),  # JSON string mit IDs der geteilten Dokumente
    documents: List[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Erstellt ein neues Milestone mit Dokumenten"""
    from datetime import datetime
    import json
    
    try:
        print(f"🔧 [API] create_milestone_with_documents called")
        print(f"🔧 [API] title: {title}, category: {category}, project_id: {project_id}")
        print(f"🔧 [API] documents: {len(documents) if documents else 0} files")
        print(f"🔧 [API] shared_document_ids: {shared_document_ids}")
        
        # Parse JSON-Strings für Dokument-IDs
        parsed_document_ids = []
        parsed_shared_document_ids = []
        
        if document_ids:
            try:
                parsed_document_ids = json.loads(document_ids)
                print(f"🔧 [API] parsed_document_ids: {parsed_document_ids}")
            except json.JSONDecodeError as e:
                print(f"⚠️ [API] JSON decode error for document_ids: {e}")
                pass
        
        if shared_document_ids:
            try:
                parsed_shared_document_ids = json.loads(shared_document_ids)
                print(f"🔧 [API] parsed_shared_document_ids: {parsed_shared_document_ids}")
            except json.JSONDecodeError as e:
                print(f"⚠️ [API] JSON decode error for shared_document_ids: {e}")
                pass
        
        # Validiere Eingabedaten
        if not title or not title.strip():
            raise HTTPException(status_code=400, detail="Titel ist erforderlich")
        if not category or not category.strip():
            raise HTTPException(status_code=400, detail="Kategorie ist erforderlich")
        if not planned_date:
            raise HTTPException(status_code=400, detail="Geplantes Datum ist erforderlich")
        
        # Erstelle MilestoneCreate Objekt aus Form-Daten
        milestone_data = {
            "title": title.strip(),
            "description": description.strip() if description else "",
            "category": category.strip(),
            "priority": priority,
            "planned_date": datetime.fromisoformat(planned_date).date(),
            "notes": notes.strip() if notes else "",
            "requires_inspection": requires_inspection,
            "project_id": project_id,
            "status": "planned",  # Explizit setzen
            "documents": []  # Explizit als leere Liste initialisieren
        }
        
        print(f"🔧 [API] Validierte Milestone-Daten: {milestone_data}")
        
        milestone_in = MilestoneCreate(**milestone_data)
        user_id = getattr(current_user, 'id')
        
        # Erstelle Milestone mit Dokumenten und geteilten Dokument-IDs
        from ..services.milestone_service import create_milestone
        milestone = await create_milestone(db, milestone_in, user_id, documents, parsed_shared_document_ids)
        print(f"✅ [API] Milestone erfolgreich erstellt: {milestone.id}")
        
        # Explizite Konvertierung über Schema um JSON-String zu Liste zu konvertieren
        milestone_read = MilestoneRead.from_orm(milestone)
        print(f"🔧 [API] Schema-Konvertierung abgeschlossen, documents type: {type(milestone_read.documents)}")
        return milestone_read
        
    except Exception as e:
        print(f"❌ [API] Fehler beim Erstellen des Milestones: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Fehler beim Erstellen des Gewerks: {str(e)}")


@router.get("/", response_model=List[MilestoneSummary])
async def read_milestones(
    project_id: int = Query(..., description="Projekt-ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        print(f"🔧 [API] read_milestones called with project_id: {project_id}")
        print(f"🔧 [API] current_user: {current_user.id}, {current_user.email}")
        
        # Direkte Implementierung von get_milestones_for_project
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        result = await db.execute(
            select(Milestone)
            .where(Milestone.project_id == project_id)
            .order_by(Milestone.planned_date)
        )
        milestone_objects = result.scalars().all()
        
        # Konvertiere zu Dictionary-Format wie die ursprüngliche Funktion
        milestones = []
        for milestone in milestone_objects:
            milestone_dict = {
                "id": milestone.id,
                "title": milestone.title,
                "description": milestone.description,
                "category": milestone.category,
                "status": milestone.status,
                "completion_status": milestone.completion_status,
                "archived": milestone.archived,
                "archived_at": milestone.archived_at.isoformat() if milestone.archived_at else None,
                "priority": milestone.priority,
                "budget": milestone.budget,
                "planned_date": milestone.planned_date.isoformat() if milestone.planned_date else None,
                "start_date": milestone.start_date.isoformat() if milestone.start_date else None,
                "end_date": milestone.end_date.isoformat() if milestone.end_date else None,
                "progress_percentage": milestone.progress_percentage,
                "contractor": milestone.contractor,
                "requires_inspection": getattr(milestone, 'requires_inspection', False),
                "project_id": milestone.project_id,
                "created_at": milestone.created_at.isoformat() if milestone.created_at else None,
                "updated_at": milestone.updated_at.isoformat() if milestone.updated_at else None,
                "documents": [],  # Vereinfacht
                "quote_stats": {
                    "total_quotes": 0,  # TODO: Quotes laden wenn nötig
                    "accepted_quotes": 0,
                    "pending_quotes": 0,
                    "rejected_quotes": 0,
                    "has_accepted_quote": False,
                    "has_pending_quotes": False,
                    "has_rejected_quotes": False
                }
            }
            milestones.append(milestone_dict)
        print(f"🔧 [API] Found {len(milestones)} milestones for project {project_id}")
        
        # Konvertiere Dictionary-Format zu MilestoneSummary
        result = []
        for i, milestone_dict in enumerate(milestones):
            milestone = milestone_objects[i]  # Hole das entsprechende Milestone-Objekt
            # Erstelle MilestoneSummary aus Dictionary
            milestone_summary = MilestoneSummary(
                id=milestone_dict["id"],
                title=milestone_dict["title"],
                status=milestone_dict["status"],
                completion_status=milestone_dict.get("completion_status"),
                priority=milestone_dict["priority"],
                category=milestone_dict["category"],
                planned_date=milestone.planned_date,  # Direkt das date-Objekt verwenden
                actual_date=milestone.actual_date,
                start_date=milestone.start_date,
                end_date=milestone.end_date,
                budget=milestone_dict["budget"],
                actual_costs=milestone.actual_costs,
                contractor=milestone_dict["contractor"],
                progress_percentage=milestone_dict["progress_percentage"],
                is_critical=getattr(milestone, 'is_critical', False),
                project_id=milestone_dict["project_id"],
                documents=milestone_dict["documents"],
                construction_phase=getattr(milestone, 'construction_phase', None),
                requires_inspection=milestone_dict["requires_inspection"]
            )
            result.append(milestone_summary)
        
        print(f"✅ [API] Successfully converted {len(result)} milestones")
        return result
        
    except Exception as e:
        print(f"❌ [API] Error in read_milestones: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Laden der Meilensteine: {str(e)}"
        )


@router.get("/all")
async def read_all_milestones(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    import logging
    from ..models import UserType
    logging.warning(f"[API] User: {getattr(current_user, 'id', None)}, type: {getattr(current_user, 'user_type', None)}, email: {getattr(current_user, 'email', None)}")
    
    # Prüfe explizit auf Dienstleister-Rolle
    is_service_provider = current_user.user_type == UserType.SERVICE_PROVIDER
    logging.warning(f"[API] is_service_provider: {is_service_provider}")
    
    if is_service_provider:
        # Dienstleister: Alle aktiven Gewerke (Ausschreibungen)
        milestones = await get_all_active_milestones(db)
        logging.warning(f"[API] get_all_active_milestones liefert {len(milestones)} Milestones: {milestones}")
    else:
        # Bauträger: Nur eigene Gewerke
        user_id = getattr(current_user, 'id')
        milestones = await get_all_milestones_for_user(db, user_id)
        logging.warning(f"[API] get_all_milestones_for_user liefert {len(milestones)} Milestones: {milestones}")
    
    return milestones


@router.get("/{milestone_id}", response_model=MilestoneRead)
async def read_milestone(
    milestone_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        # milestone = await get_milestone_by_id(db, milestone_id)
        # Direkte Implementierung
        from sqlalchemy import select
        result = await db.execute(select(Milestone).where(Milestone.id == milestone_id))
        milestone = result.scalar_one_or_none()
        if not milestone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meilenstein nicht gefunden"
            )
        
        # Konvertiere zu MilestoneRead Schema für korrekte JSON-Deserialisierung
        milestone_read = MilestoneRead.from_orm(milestone)
        print(f"🔍 read_milestone: Milestone {milestone_id} geladen")
        print(f"🔍 read_milestone: completion_status in DB: {milestone.completion_status}")
        print(f"🔍 read_milestone: completion_status in Schema: {milestone_read.completion_status}")
        print(f"🔍 read_milestone: Documents type: {type(milestone_read.documents)}")
        print(f"🔍 read_milestone: Documents: {milestone_read.documents}")
        
        return milestone_read
        
    except Exception as e:
        print(f"❌ Fehler in read_milestone: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Laden des Meilensteins: {str(e)}"
        )


@router.put("/{milestone_id}", response_model=MilestoneRead)
async def update_milestone_endpoint(
    milestone_id: int,
    milestone_update: MilestoneUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    milestone = await get_milestone_by_id(db, milestone_id)
    if not milestone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meilenstein nicht gefunden"
        )
    
    updated_milestone = await update_milestone(db, milestone_id, milestone_update)
    return updated_milestone


@router.delete("/{milestone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_milestone_endpoint(
    milestone_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    milestone = await get_milestone_by_id(db, milestone_id)
    if not milestone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meilenstein nicht gefunden"
        )
    
    success = await delete_milestone(db, milestone_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meilenstein konnte nicht gelöscht werden"
        )
    
    return None


@router.get("/project/{project_id}/statistics")
async def get_project_milestone_statistics(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Holt Statistiken für Meilensteine eines Projekts"""
    stats = await get_milestone_statistics(db, project_id)
    return stats


@router.get("/upcoming", response_model=List[MilestoneSummary])
async def get_upcoming_milestones_endpoint(
    project_id: Optional[int] = None,
    days: int = Query(30, ge=1, le=365, description="Anzahl Tage"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Holt anstehende Meilensteine in den nächsten X Tagen"""
    milestones = await get_upcoming_milestones(db, project_id, days)
    return milestones


@router.get("/overdue", response_model=List[MilestoneSummary])
async def get_overdue_milestones_endpoint(
    project_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Holt überfällige Meilensteine"""
    milestones = await get_overdue_milestones(db, project_id)
    return milestones


@router.get("/search", response_model=List[MilestoneSummary])
async def search_milestones_endpoint(
    q: str = Query(..., min_length=2, description="Suchbegriff"),
    project_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Sucht nach Meilensteinen"""
    milestones = await search_milestones(db, q, project_id)
    return milestones 


@router.delete("/debug/delete-all-milestones-and-quotes", tags=["debug"])
async def debug_delete_all_milestones_and_quotes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Löscht alle Milestones, Quotes und abhängige CostPositions. Nur im Entwicklungsmodus erlaubt!
    """
    if os.getenv("ENVIRONMENT") != "development":
        raise HTTPException(status_code=403, detail="Nur im Entwicklungsmodus erlaubt.")

    # Kostenpositionen löschen, die zu Quotes gehören
    await db.execute(CostPosition.__table__.delete().where(CostPosition.quote_id.isnot(None)))
    # Quotes löschen
    await db.execute(Quote.__table__.delete())
    # Milestones löschen
    await db.execute(Milestone.__table__.delete())
    await db.commit()
    return {"message": "Alle Gewerke, Angebote und zugehörige Kostenpositionen wurden gelöscht."}


@router.post("/{milestone_id}/invoice", status_code=status.HTTP_201_CREATED)
async def upload_invoice(
    milestone_id: int,
    amount: float = Form(...),
    due_date: str = Form(...),
    invoice_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lädt eine Rechnung für ein abgeschlossenes Gewerk hoch (nur Dienstleister)"""
    from datetime import datetime
    from ..models import UserType
    
    # Prüfe Berechtigung
    if current_user.user_type != UserType.DIENSTLEISTER:
        raise HTTPException(
            status_code=403,
            detail="Nur Dienstleister können Rechnungen hochladen"
        )
    
    # Hole Milestone
    milestone = await db.get(Milestone, milestone_id)
    if not milestone:
        raise HTTPException(status_code=404, detail="Gewerk nicht gefunden")
    
    # Prüfe ob Gewerk abgenommen wurde
    if milestone.completion_status != "completed":
        raise HTTPException(
            status_code=400,
            detail="Rechnung kann nur für abgenommene Gewerke hochgeladen werden"
        )
    
    # Prüfe ob bereits eine Rechnung existiert
    if milestone.invoice_generated:
        raise HTTPException(
            status_code=400,
            detail="Für dieses Gewerk wurde bereits eine Rechnung hochgeladen"
        )
    
    # Validiere Dateityp
    if invoice_file.content_type != 'application/pdf':
        raise HTTPException(
            status_code=400,
            detail="Nur PDF-Dateien sind für Rechnungen erlaubt"
        )
    
    # Erstelle Upload-Verzeichnis
    upload_dir = f"storage/invoices/project_{milestone.project_id}"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Speichere Datei
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"invoice_{milestone_id}_{timestamp}.pdf"
    file_path = os.path.join(upload_dir, filename)
    
    content = await invoice_file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Update Milestone
    milestone.invoice_generated = True
    milestone.invoice_amount = amount
    milestone.invoice_due_date = datetime.fromisoformat(due_date).date()
    milestone.invoice_pdf_url = file_path
    
    await db.commit()
    await db.refresh(milestone)
    
    return {
        "message": "Rechnung erfolgreich hochgeladen",
        "invoice_url": file_path,
        "amount": amount,
        "due_date": due_date
    }


@router.get("/{milestone_id}/invoice", response_model=dict)
async def get_invoice(
    milestone_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Holt Rechnungsinformationen für ein Gewerk"""
    from ..models import UserType
    
    # Hole Milestone
    milestone = await db.get(Milestone, milestone_id)
    if not milestone:
        raise HTTPException(status_code=404, detail="Gewerk nicht gefunden")
    
    # Prüfe ob Rechnung existiert
    if not milestone.invoice_generated:
        raise HTTPException(status_code=404, detail="Keine Rechnung vorhanden")
    
    # Für Bauträger: Prüfe ob Bewertung abgegeben wurde
    # Bauträger sind PRIVATE oder PROFESSIONAL User (nicht SERVICE_PROVIDER)
    if current_user.user_type != UserType.SERVICE_PROVIDER:
        from ..services.rating_service import rating_service
        
        can_view = await rating_service.check_invoice_viewable(
            db=db,
            milestone_id=milestone_id,
            bautraeger_id=current_user.id
        )
        
        if not can_view:
            raise HTTPException(
                status_code=403,
                detail="Bitte bewerten Sie zuerst den Dienstleister, um die Rechnung einzusehen"
            )
    
    return {
        "invoice_url": milestone.invoice_pdf_url,
        "amount": milestone.invoice_amount,
        "due_date": milestone.invoice_due_date.isoformat() if milestone.invoice_due_date else None,
        "approved": milestone.invoice_approved,
        "approved_at": milestone.invoice_approved_at.isoformat() if milestone.invoice_approved_at else None
    }


# ==================== COMPLETION STATUS ENDPOINT ====================

@router.get("/{milestone_id}/completion-status")
async def get_milestone_completion_status(
    milestone_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Holt den aktuellen Abschluss-Status eines Gewerkes
    """
    from ..services.milestone_service import get_milestone_by_id
    
    milestone = await get_milestone_by_id(db, milestone_id)
    
    if not milestone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gewerk nicht gefunden"
        )
    
    return {
        "milestone_id": milestone_id,
        "completion_status": milestone.completion_status,
        "progress_percentage": milestone.progress_percentage,
        "completion_requested_at": milestone.completion_requested_at,
        "inspection_date": milestone.inspection_date,
        "acceptance_date": milestone.acceptance_date,
        "invoice_generated": milestone.invoice_generated,
        "invoice_approved": milestone.invoice_approved,
        "archived": milestone.archived
    }


@router.get("/archived", response_model=List[dict])
async def get_archived_milestones(
    search_query: Optional[str] = None,
    category_filter: Optional[str] = None,
    project_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lade archivierte Gewerke für den aktuellen Benutzer"""
    try:
        print(f"🔍 API: get_archived_milestones aufgerufen mit project_id={project_id}")
        
        # Vereinfachte direkte Abfrage ohne milestone_service
        from sqlalchemy import select, or_
        from ..models import Milestone, Project
        
        # Basis-Query für archivierte Milestones
        query = select(Milestone).where(
            or_(
                Milestone.archived == True,
                Milestone.completion_status == "archived"
            )
        )
        
        # Bauträger sieht nur seine Projekte
        if current_user.user_type != "service_provider":
            query = query.join(Project).where(Project.created_by == current_user.id)
        else:
            query = query.where(Milestone.created_by == current_user.id)
        
        # Projekt-Filter
        if project_id:
            query = query.where(Milestone.project_id == project_id)
        
        # Filter anwenden
        if search_query:
            query = query.where(
                or_(
                    Milestone.title.ilike(f"%{search_query}%"),
                    Milestone.description.ilike(f"%{search_query}%")
                )
            )
        
        if category_filter:
            query = query.where(Milestone.category == category_filter)
        
        # Sortierung und Paginierung
        query = query.order_by(Milestone.id.desc()).offset(skip).limit(limit)
        
        result = await db.execute(query)
        milestones = result.scalars().all()
        
        print(f"🔍 Gefundene archivierte Milestones: {len(milestones)}")
        
        # Vereinfachte Rückgabe
        archived_data = []
        for milestone in milestones:
            archived_data.append({
                "id": milestone.id,
                "title": milestone.title,
                "description": milestone.description or "",
                "category": milestone.category or "eigene",
                "budget": float(milestone.budget) if milestone.budget else 0.0,
                "completion_status": milestone.completion_status,
                "archived_at": milestone.archived_at.isoformat() if milestone.archived_at else None,
                "archived_by": "bautraeger",
                "archive_reason": "Gewerk abgeschlossen und Rechnung bezahlt",
                "project": {
                    "id": milestone.project_id,
                    "title": "Projekt",
                    "address": ""
                },
                "service_provider": None,
                "accepted_quote": None,
                "invoice": None
            })
        
        print(f"✅ Returning {len(archived_data)} archived milestones")
        return archived_data
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Fehler beim Laden archivierter Gewerke: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Laden archivierter Gewerke: {str(e)}"
        )


@router.get("/service-provider/completed", response_model=List[dict])
async def get_completed_milestones_for_service_provider(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lade abgeschlossene Gewerke für Dienstleister (für Rechnungsstellung)"""
    try:
        from sqlalchemy import select, and_
        from sqlalchemy.orm import selectinload
        from ..models import Project, Quote
        
        print(f"🔍 Lade abgeschlossene Gewerke für Dienstleister: {current_user.id}")
        
        # Nur für Dienstleister
        if current_user.user_type not in ['service_provider', 'SERVICE_PROVIDER']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Nur Dienstleister können abgeschlossene Gewerke einsehen"
            )
        
        # Lade abgeschlossene Milestones des Dienstleisters
        stmt = select(Milestone).where(
            and_(
                Milestone.service_provider_id == current_user.id,
                Milestone.completion_status == 'completed'
            )
        ).options(
            selectinload(Milestone.project),
            selectinload(Milestone.quotes)
        ).order_by(Milestone.acceptance_date.desc())
        
        result = await db.execute(stmt)
        milestones = result.scalars().all()
        
        completed_milestones = []
        for milestone in milestones:
            # Finde das akzeptierte Angebot
            accepted_quote = None
            for quote in milestone.quotes:
                if quote.status == 'accepted':
                    accepted_quote = quote
                    break
            
            completed_milestone = {
                'id': milestone.id,
                'title': milestone.title,
                'description': milestone.description or '',
                'category': milestone.category or 'eigene',
                'completion_status': milestone.completion_status,
                'completed_date': milestone.acceptance_date.isoformat() if milestone.acceptance_date else milestone.updated_at.isoformat(),
                'total_amount': accepted_quote.total_amount if accepted_quote else 0,
                'currency': accepted_quote.currency if accepted_quote else 'EUR',
                'project_name': milestone.project.title if milestone.project else 'Unbekanntes Projekt',
                'project_id': milestone.project_id,
                'has_invoice': False  # TODO: Prüfe ob bereits Rechnung existiert
            }
            
            completed_milestones.append(completed_milestone)
        
        print(f"✅ {len(completed_milestones)} abgeschlossene Gewerke für Rechnungsstellung gefunden")
        return completed_milestones
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Fehler beim Laden abgeschlossener Gewerke: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Laden abgeschlossener Gewerke: {str(e)}"
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
        from sqlalchemy import select
        from datetime import datetime
        
        # Hole das Gewerk
        result = await db.execute(select(Milestone).where(Milestone.id == milestone_id))
        milestone = result.scalar_one_or_none()
        
        if not milestone:
            raise HTTPException(status_code=404, detail="Gewerk nicht gefunden")
        
        # Prüfe, ob Gewerk archiviert werden kann
        if milestone.completion_status not in ["completed", "completed_with_defects"]:
            raise HTTPException(
                status_code=400, 
                detail="Gewerk muss abgeschlossen sein (completed oder completed_with_defects)"
            )
        
        # Archiviere Gewerk
        milestone.archived = True
        milestone.archived_at = datetime.utcnow()
        milestone.completion_status = "archived"
        
        await db.commit()
        await db.refresh(milestone)
        
        return {
            "message": "Gewerk erfolgreich archiviert",
            "milestone": {
                "id": milestone.id,
                "title": milestone.title,
                "completion_status": milestone.completion_status,
                "archived": milestone.archived,
                "archived_at": milestone.archived_at.isoformat() if milestone.archived_at else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Fehler beim Archivieren: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Archivieren: {str(e)}"
        ) 