from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..api.deps import get_current_user
from ..models import User, Milestone, Quote, CostPosition
import os
from ..schemas.milestone import MilestoneCreate, MilestoneRead, MilestoneUpdate, MilestoneSummary
from ..services.milestone_service import (
    create_milestone, get_milestone_by_id, get_milestones_for_project,
    update_milestone, delete_milestone, get_milestone_statistics,
    get_upcoming_milestones, get_overdue_milestones, search_milestones,
    get_all_milestones_for_user, get_all_active_milestones
)

router = APIRouter(prefix="/milestones", tags=["milestones"])


@router.post("/", response_model=MilestoneRead, status_code=status.HTTP_201_CREATED)
async def create_new_milestone(
    milestone_in: MilestoneCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = getattr(current_user, 'id')
    milestone = await create_milestone(db, milestone_in, user_id)
    return milestone


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
    
    # Parse JSON-Strings für Dokument-IDs
    parsed_document_ids = []
    parsed_shared_document_ids = []
    
    if document_ids:
        try:
            parsed_document_ids = json.loads(document_ids)
        except json.JSONDecodeError:
            pass
    
    if shared_document_ids:
        try:
            parsed_shared_document_ids = json.loads(shared_document_ids)
        except json.JSONDecodeError:
            pass
    
    # Erstelle MilestoneCreate Objekt aus Form-Daten
    milestone_data = {
        "title": title,
        "description": description,
        "category": category,
        "priority": priority,
        "planned_date": datetime.fromisoformat(planned_date).date(),
        "notes": notes,
        "requires_inspection": requires_inspection,
        "project_id": project_id
    }
    
    milestone_in = MilestoneCreate(**milestone_data)
    user_id = getattr(current_user, 'id')
    
    # Erstelle Milestone mit Dokumenten und geteilten Dokument-IDs
    milestone = await create_milestone(db, milestone_in, user_id, documents, parsed_shared_document_ids)
    return milestone


@router.get("/", response_model=List[MilestoneSummary])
async def read_milestones(
    project_id: int = Query(..., description="Projekt-ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        print(f"🔧 [API] read_milestones called with project_id: {project_id}")
        print(f"🔧 [API] current_user: {current_user.id}, {current_user.email}")
        
        milestones = await get_milestones_for_project(db, project_id)
        print(f"🔧 [API] Found {len(milestones)} milestones for project {project_id}")
        
        # Konvertiere zu MilestoneSummary mit korrektem JSON-Parsing
        import json
        result = []
        for milestone in milestones:
            # Parse documents JSON string zu Liste
            documents = []
            if milestone.documents:
                try:
                    if isinstance(milestone.documents, str):
                        documents = json.loads(milestone.documents)
                    elif isinstance(milestone.documents, list):
                        documents = milestone.documents
                    else:
                        documents = []
                except (json.JSONDecodeError, TypeError):
                    documents = []
            
            # Erstelle MilestoneSummary manuell
            milestone_summary = MilestoneSummary(
                id=milestone.id,
                title=milestone.title,
                status=milestone.status,
                priority=milestone.priority,
                category=milestone.category,
                planned_date=milestone.planned_date,
                actual_date=milestone.actual_date,
                start_date=milestone.start_date,
                end_date=milestone.end_date,
                budget=milestone.budget,
                actual_costs=milestone.actual_costs,
                contractor=milestone.contractor,
                progress_percentage=milestone.progress_percentage,
                is_critical=milestone.is_critical,
                project_id=milestone.project_id,
                documents=documents,  # ✅ Echte Liste
                construction_phase=milestone.construction_phase,
                requires_inspection=milestone.requires_inspection
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
    milestone = await get_milestone_by_id(db, milestone_id)
    if not milestone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meilenstein nicht gefunden"
        )
    return milestone


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