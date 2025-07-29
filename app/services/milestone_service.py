from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import logging
import uuid
import json
import os
from fastapi import UploadFile

from ..models import Milestone, Project
from ..models.user import User
from ..models.project import Project
from ..schemas.milestone import (
    MilestoneCreate,
    MilestoneUpdate,
    MilestoneCompletionRequest,
    MilestoneInspectionUpdate,
    MilestoneInvoiceRequest,
    CompletionChecklist,
    InspectionReport,
    DefectItem,
    InvoiceData
)


async def create_milestone(db: AsyncSession, milestone_in: MilestoneCreate, created_by: int, documents: List[UploadFile] = None, shared_document_ids: List[int] = None) -> Milestone:
    """Erstellt ein neues Gewerk mit automatischer Bauphasen-Zuordnung"""
    from ..models import Project
    
    # Hole das Projekt, um die aktuelle Bauphase zu ermitteln
    project_result = await db.execute(
        select(Project).where(Project.id == milestone_in.project_id)
    )
    project = project_result.scalar_one_or_none()
    
    # Erstelle das Gewerk mit den grundlegenden Daten
    milestone_data = {
        'project_id': milestone_in.project_id,
        'created_by': created_by,
        'title': milestone_in.title,
        'description': milestone_in.description or "",
        'status': milestone_in.status,
        'priority': milestone_in.priority,
        'category': milestone_in.category,
        'planned_date': milestone_in.planned_date,
        'start_date': milestone_in.start_date,
        'end_date': milestone_in.end_date,
        'budget': milestone_in.budget,
        'actual_costs': milestone_in.actual_costs,
        'contractor': milestone_in.contractor,
        'is_critical': milestone_in.is_critical,
        'notify_on_completion': milestone_in.notify_on_completion,
        'notes': milestone_in.notes,
        'documents': milestone_in.documents,
        # Besichtigungssystem
        'requires_inspection': milestone_in.requires_inspection
    }
    
    # Setze automatisch die aktuelle Bauphase des Projekts
    if project and project.construction_phase:
        milestone_data['construction_phase'] = project.construction_phase
        print(f"🏗️ Gewerk erstellt mit Bauphase: {project.construction_phase}")
    else:
        print(f"⚠️ Projekt hat keine Bauphase gesetzt")
    
    milestone = Milestone(**milestone_data)
    db.add(milestone)
    await db.flush()  # Flush um ID zu erhalten, aber noch nicht committen
    
    # Verarbeite hochgeladene Dokumente
    if documents:
        uploaded_documents = await process_milestone_documents(documents, project, milestone.id)
        milestone.documents = uploaded_documents
    
    # Speichere geteilte Dokument-IDs als JSON
    if shared_document_ids:
        import json
        milestone.shared_document_ids = json.dumps(shared_document_ids)
        print(f"📄 Geteilte Dokumente für Gewerk {milestone.id}: {shared_document_ids}")
    
    await db.commit()
    await db.refresh(milestone)
    return milestone


async def process_milestone_documents(documents: List[UploadFile], project, milestone_id: int) -> List[Dict]:
    """Verarbeitet hochgeladene Dokumente für ein Milestone"""
    uploaded_documents = []
    
    for file in documents:
        # Validiere Dateityp
        allowed_types = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-powerpoint',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation'
        ]
        
        if file.content_type not in allowed_types:
            continue  # Überspringe ungültige Dateitypen
        
        # Lese Dateiinhalt
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:  # 10MB Limit
            continue  # Überspringe zu große Dateien
        
        # Erstelle Speicherpfad
        upload_dir = f"storage/uploads/project_{project.id}"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generiere sicheren Dateinamen
        file_extension = os.path.splitext(file.filename)[1]
        safe_filename = f"milestone_{milestone_id}_{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, safe_filename)
        
        # Speichere Datei
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        # Erstelle Dokument-Metadaten
        document_data = {
            "id": str(uuid.uuid4()),
            "name": file.filename,
            "url": f"/{file_path}",
            "type": file.content_type,
            "size": len(content),
            "uploaded_at": datetime.now().isoformat()
        }
        
        uploaded_documents.append(document_data)
    
    return uploaded_documents


async def get_milestone_by_id(db: AsyncSession, milestone_id: int) -> Milestone | None:
    result = await db.execute(select(Milestone).where(Milestone.id == milestone_id))
    return result.scalars().first()


async def get_milestones_for_project(db: AsyncSession, project_id: int) -> List[Milestone]:
    result = await db.execute(
        select(Milestone)
        .where(Milestone.project_id == project_id)
        .order_by(Milestone.planned_date)
    )
    return list(result.scalars().all())


async def get_all_milestones_for_user(db: AsyncSession, user_id: int) -> List[Milestone]:
    """Holt alle Gewerke für alle Projekte des Benutzers"""
    # Hole alle Projekte des Benutzers
    projects_result = await db.execute(
        select(Project.id).where(Project.owner_id == user_id)
    )
    project_ids = [row[0] for row in projects_result.fetchall()]
    
    if not project_ids:
        return []
    
    # Hole alle Gewerke für diese Projekte
    result = await db.execute(
        select(Milestone)
        .where(Milestone.project_id.in_(project_ids))
        .order_by(Milestone.planned_date)
    )
    return list(result.scalars().all())


async def update_milestone(db: AsyncSession, milestone_id: int, milestone_update: MilestoneUpdate) -> Milestone | None:
    milestone = await get_milestone_by_id(db, milestone_id)
    if not milestone:
        return None
    
    update_data = milestone_update.dict(exclude_unset=True)
    if update_data:
        # Wenn Meilenstein abgeschlossen wird, setze completed_at
        new_status = update_data.get('status')
        if new_status == "completed" and milestone.status != "completed":
            update_data['completed_at'] = datetime.utcnow()
            update_data['progress_percentage'] = 100
            update_data['actual_date'] = datetime.utcnow().date()
        
        await db.execute(
            update(Milestone)
            .where(Milestone.id == milestone_id)
            .values(**update_data, updated_at=datetime.utcnow())
        )
        await db.commit()
        await db.refresh(milestone)
    
    return milestone


async def delete_milestone(db: AsyncSession, milestone_id: int) -> bool:
    milestone = await get_milestone_by_id(db, milestone_id)
    if not milestone:
        return False
    
    await db.delete(milestone)
    await db.commit()
    return True


async def get_milestone_statistics(db: AsyncSession, project_id: int) -> dict:
    """Holt Statistiken für Meilensteine eines Projekts"""
    result = await db.execute(
        select(
            func.count(Milestone.id).label('total'),
            func.count(Milestone.id).filter(Milestone.status == "planned").label('planned'),
            func.count(Milestone.id).filter(Milestone.status == "in_progress").label('in_progress'),
            func.count(Milestone.id).filter(Milestone.status == "completed").label('completed'),
            func.count(Milestone.id).filter(Milestone.status == "delayed").label('delayed'),
            func.avg(Milestone.progress_percentage).label('avg_progress')
        ).where(Milestone.project_id == project_id)
    )
    
    stats = result.first()
    
    return {
        "total": int(stats.total) if stats and stats.total is not None else 0,
        "planned": int(stats.planned) if stats and stats.planned is not None else 0,
        "in_progress": int(stats.in_progress) if stats and stats.in_progress is not None else 0,
        "completed": int(stats.completed) if stats and stats.completed is not None else 0,
        "delayed": int(stats.delayed) if stats and stats.delayed is not None else 0,
        "avg_progress": round(float(stats.avg_progress), 1) if stats and stats.avg_progress is not None else 0.0
    }


async def get_upcoming_milestones(db: AsyncSession, project_id: Optional[int] = None, days: int = 30) -> List[Milestone]:
    """Holt anstehende Meilensteine in den nächsten X Tagen"""
    start_date = date.today()
    end_date = start_date + timedelta(days=days)
    
    query = select(Milestone).where(
        Milestone.planned_date >= start_date,
        Milestone.planned_date <= end_date,
        Milestone.status.in_(["planned", "in_progress"])
    )
    
    if project_id:
        query = query.where(Milestone.project_id == project_id)
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_overdue_milestones(db: AsyncSession, project_id: Optional[int] = None) -> List[Milestone]:
    """Holt überfällige Meilensteine"""
    query = select(Milestone).where(
        Milestone.planned_date < date.today(),
        Milestone.status.in_(["planned", "in_progress"])
    )
    
    if project_id:
        query = query.where(Milestone.project_id == project_id)
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def search_milestones(db: AsyncSession, search_term: str, project_id: Optional[int] = None) -> List[Milestone]:
    query = select(Milestone)
    
    if project_id:
        query = query.where(Milestone.project_id == project_id)
    
    # Suche in Titel und Beschreibung
    search_filter = (
        Milestone.title.ilike(f"%{search_term}%") |
        Milestone.description.ilike(f"%{search_term}%")
    )
    
    query = query.where(search_filter)
    result = await db.execute(query)
    return list(result.scalars().all()) 


async def get_all_active_milestones(db: AsyncSession) -> list:
    from ..models import Project
    from ..models.quote import Quote, QuoteStatus
    import logging
    session_id = str(uuid.uuid4())
    logging.warning(f"[SERVICE] get_all_active_milestones: Session {session_id} gestartet")
    
    # Debug: Prüfe alle Projekte
    projects_result = await db.execute(select(Project))
    all_projects = list(projects_result.scalars().all())
    logging.warning(f"[SERVICE] Session {session_id}: Alle Projekte: {len(all_projects)}")
    for p in all_projects:
        logging.warning(f"[SERVICE] Session {session_id}: Projekt: id={p.id}, name={p.name}, is_public={p.is_public}, allow_quotes={p.allow_quotes}")
    
    # Debug: Prüfe alle Milestones
    milestones_result = await db.execute(select(Milestone))
    all_milestones = list(milestones_result.scalars().all())
    logging.warning(f"[SERVICE] Session {session_id}: Alle Milestones: {len(all_milestones)}")
    for m in all_milestones:
        logging.warning(f"[SERVICE] Session {session_id}: Milestone: id={m.id}, status={m.status}, project_id={m.project_id}")
    
    # Alle aktiven Gewerke zurückgeben (unabhängig von Projekt-Öffentlichkeit)
    result = await db.execute(
        select(Milestone)
        .where(
            Milestone.status.in_(["planned", "in_progress"])
        )
        .order_by(Milestone.planned_date)
    )
    milestones = list(result.scalars().all())
    
    # Lade Quote-Statistiken für jedes Milestone
    milestones_with_stats = []
    for milestone in milestones:
        # Lade alle Quotes für dieses Milestone
        quote_result = await db.execute(
            select(Quote).where(Quote.milestone_id == milestone.id)
        )
        quotes = list(quote_result.scalars().all())
        
        # Berechne Quote-Statistiken
        total_quotes = len(quotes)
        accepted_quotes = len([q for q in quotes if q.status == QuoteStatus.ACCEPTED])
        pending_quotes = len([q for q in quotes if q.status in [QuoteStatus.SUBMITTED, QuoteStatus.UNDER_REVIEW]])
        rejected_quotes = len([q for q in quotes if q.status == QuoteStatus.REJECTED])
        
        # Erstelle ein Dictionary mit Milestone-Daten und Quote-Stats
        milestone_dict = {
            "id": milestone.id,
            "title": milestone.title,
            "description": milestone.description,
            "category": milestone.category,
            "status": milestone.status,
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
            # Quote-Statistiken hinzufügen
            "quote_stats": {
                "total_quotes": total_quotes,
                "accepted_quotes": accepted_quotes,
                "pending_quotes": pending_quotes,
                "rejected_quotes": rejected_quotes,
                "has_accepted_quote": accepted_quotes > 0,
                "has_pending_quotes": pending_quotes > 0,
                "has_rejected_quotes": rejected_quotes > 0
            }
        }
        milestones_with_stats.append(milestone_dict)
    
    logging.warning(f"[SERVICE] Session {session_id}: get_all_active_milestones: {len(milestones_with_stats)} gefunden mit Quote-Stats.")
    for m in milestones_with_stats:
        logging.warning(f"[SERVICE] Session {session_id}: Milestone: id={m['id']}, title={m['title']}, quotes={m['quote_stats']['total_quotes']}")
    
    return milestones_with_stats


async def get_milestones_by_construction_phase(db: AsyncSession, project_id: int, construction_phase: str) -> List[Milestone]:
    """Holt Gewerke nach Bauphase"""
    result = await db.execute(
        select(Milestone)
        .where(
            Milestone.project_id == project_id,
            Milestone.construction_phase == construction_phase
        )
        .order_by(Milestone.planned_date)
    )
    return list(result.scalars().all())


async def get_milestone_statistics_by_phase(db: AsyncSession, project_id: int) -> dict:
    """Holt Statistiken für Gewerke nach Bauphasen"""
    # Gesamtanzahl pro Bauphase
    phase_distribution_result = await db.execute(
        select(
            Milestone.construction_phase,
            func.count(Milestone.id).label('count'),
            func.sum(Milestone.budget).label('total_budget'),
            func.sum(Milestone.actual_costs).label('total_costs'),
            func.avg(Milestone.progress_percentage).label('avg_progress')
        )
        .where(Milestone.project_id == project_id)
        .group_by(Milestone.construction_phase)
    )
    
    phase_distribution = {}
    for row in phase_distribution_result.all():
        phase = row.construction_phase or 'Keine Phase'
        phase_distribution[phase] = {
            'count': row.count,
            'total_budget': float(row.total_budget or 0),
            'total_costs': float(row.total_costs or 0),
            'avg_progress': round(float(row.avg_progress or 0), 1),
            'budget_variance': float((row.total_budget or 0) - (row.total_costs or 0))
        }
    
    # Gesamtstatistiken
    total_stats_result = await db.execute(
        select(
            func.count(Milestone.id).label('total_count'),
            func.sum(Milestone.budget).label('total_budget'),
            func.sum(Milestone.actual_costs).label('total_costs'),
            func.avg(Milestone.progress_percentage).label('avg_progress')
        )
        .where(Milestone.project_id == project_id)
    )
    
    total_stats = total_stats_result.scalar_one()
    
    return {
        "phase_distribution": phase_distribution,
        "total_count": total_stats.total_count,
        "total_budget": float(total_stats.total_budget or 0),
        "total_costs": float(total_stats.total_costs or 0),
        "avg_progress": round(float(total_stats.avg_progress or 0), 1),
        "total_budget_variance": float((total_stats.total_budget or 0) - (total_stats.total_costs or 0))
    } 

# ==================== ABSCHLUSS-WORKFLOW FUNKTIONEN ====================

async def request_milestone_completion(
    db: AsyncSession, 
    completion_request: MilestoneCompletionRequest,
    service_provider_id: int
) -> Milestone:
    """
    Dienstleister beantragt Abschluss eines Gewerkes
    """
    # Hole das Gewerk
    result = await db.execute(
        select(Milestone).where(Milestone.id == completion_request.milestone_id)
    )
    milestone = result.scalar_one_or_none()
    
    if not milestone:
        raise ValueError("Gewerk nicht gefunden")
    
    # Prüfe, ob Dienstleister berechtigt ist
    if milestone.created_by != service_provider_id:
        raise ValueError("Keine Berechtigung für dieses Gewerk")
    
    # Update Milestone Status
    milestone.completion_status = "completion_requested"
    milestone.completion_requested_at = datetime.utcnow()
    milestone.completion_checklist = completion_request.checklist.dict()
    milestone.completion_photos = [photo.dict() for photo in completion_request.photos]
    milestone.completion_documents = completion_request.documents
    
    await db.commit()
    await db.refresh(milestone)
    
    # TODO: Benachrichtigung an Bauträger senden
    # await send_completion_request_notification(milestone)
    
    return milestone

async def conduct_milestone_inspection(
    db: AsyncSession,
    inspection_update: MilestoneInspectionUpdate,
    inspector_id: int
) -> Milestone:
    """
    Bauträger führt Abnahme durch
    """
    # Hole das Gewerk
    result = await db.execute(
        select(Milestone).where(Milestone.id == inspection_update.milestone_id)
    )
    milestone = result.scalar_one_or_none()
    
    if not milestone:
        raise ValueError("Gewerk nicht gefunden")
    
    # Update Milestone mit Abnahme-Ergebnis
    milestone.inspection_date = inspection_update.inspection_report.inspection_date
    milestone.inspection_report = inspection_update.inspection_report.dict()
    
    # Setze Status basierend auf Abnahme-Ergebnis
    assessment = inspection_update.inspection_report.overall_assessment
    if assessment == "accepted":
        milestone.completion_status = "completed"
        milestone.acceptance_date = datetime.utcnow()
        milestone.accepted_by = inspector_id
    elif assessment == "accepted_with_conditions":
        milestone.completion_status = "under_review"
        milestone.defects_list = [defect.dict() for defect in inspection_update.inspection_report.defects]
    else:  # rejected
        milestone.completion_status = "in_progress"
        milestone.defects_list = [defect.dict() for defect in inspection_update.inspection_report.defects]
    
    await db.commit()
    await db.refresh(milestone)
    
    # TODO: Benachrichtigung an Dienstleister senden
    # await send_inspection_result_notification(milestone)
    
    return milestone

async def generate_milestone_invoice(
    db: AsyncSession,
    invoice_request: MilestoneInvoiceRequest,
    service_provider_id: int
) -> Milestone:
    """
    Dienstleister erstellt Rechnung für abgeschlossenes Gewerk
    """
    # Hole das Gewerk
    result = await db.execute(
        select(Milestone).where(Milestone.id == invoice_request.milestone_id)
    )
    milestone = result.scalar_one_or_none()
    
    if not milestone:
        raise ValueError("Gewerk nicht gefunden")
    
    # Prüfe, ob Gewerk abgeschlossen ist
    if milestone.completion_status != "completed":
        raise ValueError("Gewerk muss erst abgeschlossen werden")
    
    # Prüfe Berechtigung
    if milestone.created_by != service_provider_id:
        raise ValueError("Keine Berechtigung für dieses Gewerk")
    
    # Update Milestone mit Rechnungsdaten
    milestone.invoice_generated = True
    
    if invoice_request.use_custom_invoice:
        milestone.custom_invoice_url = invoice_request.custom_invoice_url
    else:
        # Automatische Rechnungsgenerierung
        invoice_data = await _generate_automatic_invoice(milestone)
        milestone.invoice_data = invoice_data.dict()
    
    await db.commit()
    await db.refresh(milestone)
    
    # TODO: Benachrichtigung an Bauträger senden
    # await send_invoice_notification(milestone)
    
    return milestone

async def approve_milestone_invoice(
    db: AsyncSession,
    milestone_id: int,
    approver_id: int
) -> Milestone:
    """
    Bauträger genehmigt Rechnung
    """
    # Hole das Gewerk
    result = await db.execute(
        select(Milestone).where(Milestone.id == milestone_id)
    )
    milestone = result.scalar_one_or_none()
    
    if not milestone:
        raise ValueError("Gewerk nicht gefunden")
    
    # Prüfe, ob Rechnung vorhanden ist
    if not milestone.invoice_generated:
        raise ValueError("Keine Rechnung vorhanden")
    
    # Update Milestone
    milestone.invoice_approved = True
    milestone.invoice_approved_at = datetime.utcnow()
    milestone.invoice_approved_by = approver_id
    
    await db.commit()
    await db.refresh(milestone)
    
    # TODO: Benachrichtigung an Dienstleister senden
    # await send_invoice_approval_notification(milestone)
    
    return milestone

async def archive_milestone(
    db: AsyncSession,
    milestone_id: int,
    user_id: int
) -> Milestone:
    """
    Archiviert ein abgeschlossenes Gewerk
    """
    # Hole das Gewerk
    result = await db.execute(
        select(Milestone).where(Milestone.id == milestone_id)
    )
    milestone = result.scalar_one_or_none()
    
    if not milestone:
        raise ValueError("Gewerk nicht gefunden")
    
    # Prüfe, ob Gewerk komplett abgeschlossen ist
    if not (milestone.completion_status == "completed" and milestone.invoice_approved):
        raise ValueError("Gewerk muss komplett abgeschlossen und Rechnung genehmigt sein")
    
    # Archiviere Gewerk
    milestone.archived = True
    milestone.archived_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(milestone)
    
    return milestone

async def get_archived_milestones(
    db: AsyncSession,
    user_id: int,
    is_service_provider: bool = False,
    search_query: Optional[str] = None,
    category_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Milestone]:
    """
    Holt archivierte Gewerke für einen Benutzer
    """
    query = select(Milestone).where(Milestone.archived == True)
    
    if is_service_provider:
        query = query.where(Milestone.created_by == user_id)
    else:
        # Bauträger sieht alle archivierten Gewerke seiner Projekte
        query = query.join(Project).where(Project.created_by == user_id)
    
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
    query = query.order_by(Milestone.archived_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()

# ==================== HILFSFUNKTIONEN ====================

async def _generate_automatic_invoice(milestone: Milestone) -> InvoiceData:
    """
    Generiert automatisch eine Rechnung basierend auf Gewerk-Daten
    """
    invoice_number = f"RE-{milestone.id}-{datetime.now().strftime('%Y%m%d')}"
    
    # Basis-Rechnungsdaten aus Gewerk extrahieren
    items = []
    total_amount = 0.0
    
    # Hauptleistung
    if milestone.budget:
        items.append({
            "description": f"Gewerk: {milestone.title}",
            "quantity": 1,
            "unit_price": milestone.budget,
            "total": milestone.budget
        })
        total_amount += milestone.budget
    
    # Zusatzleistungen aus Beschreibung extrahieren (falls vorhanden)
    # TODO: Erweiterte Logik für Zusatzleistungen
    
    return InvoiceData(
        invoice_number=invoice_number,
        total_amount=total_amount,
        items=items,
        generated_at=datetime.utcnow()
    )

def get_completion_checklist_template(category: str) -> Dict[str, Any]:
    """
    Gibt kategorie-spezifische Abnahme-Checkliste zurück
    """
    templates = {
        "elektro": {
            "items": [
                {"id": "safety_check", "label": "Sicherheitsprüfung durchgeführt", "required": True, "checked": False},
                {"id": "function_test", "label": "Funktionstest aller Anschlüsse", "required": True, "checked": False},
                {"id": "documentation", "label": "Installationsdokumentation vollständig", "required": True, "checked": False},
                {"id": "cleanup", "label": "Arbeitsplatz gereinigt", "required": True, "checked": False},
                {"id": "certificates", "label": "Prüfzertifikate vorhanden", "required": True, "checked": False}
            ]
        },
        "sanitaer": {
            "items": [
                {"id": "pressure_test", "label": "Druckprüfung erfolgreich", "required": True, "checked": False},
                {"id": "function_test", "label": "Funktionstest aller Armaturen", "required": True, "checked": False},
                {"id": "sealing_check", "label": "Abdichtung geprüft", "required": True, "checked": False},
                {"id": "cleanup", "label": "Arbeitsplatz gereinigt", "required": True, "checked": False},
                {"id": "documentation", "label": "Installationsdokumentation vollständig", "required": True, "checked": False}
            ]
        },
        "heizung": {
            "items": [
                {"id": "system_test", "label": "Anlagenprüfung durchgeführt", "required": True, "checked": False},
                {"id": "efficiency_test", "label": "Effizienztest bestanden", "required": True, "checked": False},
                {"id": "safety_devices", "label": "Sicherheitseinrichtungen funktionsfähig", "required": True, "checked": False},
                {"id": "documentation", "label": "Wartungsdokumentation übergeben", "required": True, "checked": False},
                {"id": "cleanup", "label": "Arbeitsplatz gereinigt", "required": True, "checked": False}
            ]
        },
        "dach": {
            "items": [
                {"id": "waterproof_test", "label": "Dichtheitsprüfung erfolgreich", "required": True, "checked": False},
                {"id": "material_check", "label": "Materialqualität geprüft", "required": True, "checked": False},
                {"id": "safety_measures", "label": "Absturzsicherung installiert", "required": True, "checked": False},
                {"id": "cleanup", "label": "Arbeitsplatz gereinigt", "required": True, "checked": False},
                {"id": "warranty", "label": "Gewährleistungsunterlagen übergeben", "required": True, "checked": False}
            ]
        },
        "fenster_tueren": {
            "items": [
                {"id": "function_test", "label": "Öffnungs-/Schließfunktion geprüft", "required": True, "checked": False},
                {"id": "sealing_check", "label": "Abdichtung geprüft", "required": True, "checked": False},
                {"id": "hardware_check", "label": "Beschläge justiert", "required": True, "checked": False},
                {"id": "cleanup", "label": "Arbeitsplatz gereinigt", "required": True, "checked": False},
                {"id": "keys_handed", "label": "Schlüssel übergeben", "required": True, "checked": False}
            ]
        },
        "boden": {
            "items": [
                {"id": "surface_quality", "label": "Oberflächenqualität geprüft", "required": True, "checked": False},
                {"id": "level_check", "label": "Ebenheit geprüft", "required": True, "checked": False},
                {"id": "joint_check", "label": "Fugen ordnungsgemäß", "required": True, "checked": False},
                {"id": "cleanup", "label": "Arbeitsplatz gereinigt", "required": True, "checked": False},
                {"id": "care_instructions", "label": "Pflegeanleitung übergeben", "required": True, "checked": False}
            ]
        },
        "wand": {
            "items": [
                {"id": "surface_quality", "label": "Oberflächenqualität geprüft", "required": True, "checked": False},
                {"id": "straightness", "label": "Geradheit geprüft", "required": True, "checked": False},
                {"id": "finish_quality", "label": "Oberflächenbehandlung vollständig", "required": True, "checked": False},
                {"id": "cleanup", "label": "Arbeitsplatz gereinigt", "required": True, "checked": False},
                {"id": "touch_up", "label": "Nachbesserungen durchgeführt", "required": False, "checked": False}
            ]
        },
        "fundament": {
            "items": [
                {"id": "concrete_quality", "label": "Betonqualität geprüft", "required": True, "checked": False},
                {"id": "dimension_check", "label": "Maße geprüft", "required": True, "checked": False},
                {"id": "reinforcement", "label": "Bewehrung ordnungsgemäß", "required": True, "checked": False},
                {"id": "waterproofing", "label": "Abdichtung vollständig", "required": True, "checked": False},
                {"id": "cleanup", "label": "Arbeitsplatz gereinigt", "required": True, "checked": False}
            ]
        },
        "garten": {
            "items": [
                {"id": "planting_complete", "label": "Bepflanzung vollständig", "required": True, "checked": False},
                {"id": "irrigation_test", "label": "Bewässerung funktionsfähig", "required": True, "checked": False},
                {"id": "soil_quality", "label": "Bodenqualität geprüft", "required": True, "checked": False},
                {"id": "cleanup", "label": "Arbeitsplatz gereinigt", "required": True, "checked": False},
                {"id": "care_instructions", "label": "Pflegeanleitung übergeben", "required": True, "checked": False}
            ]
        },
        "eigene": {
            "items": [
                {"id": "quality_check", "label": "Qualitätsprüfung durchgeführt", "required": True, "checked": False},
                {"id": "specification_met", "label": "Spezifikationen erfüllt", "required": True, "checked": False},
                {"id": "function_test", "label": "Funktionstest durchgeführt", "required": True, "checked": False},
                {"id": "cleanup", "label": "Arbeitsplatz gereinigt", "required": True, "checked": False},
                {"id": "documentation", "label": "Dokumentation vollständig", "required": True, "checked": False}
            ]
        }
    }
    
    return templates.get(category, templates["eigene"]) 