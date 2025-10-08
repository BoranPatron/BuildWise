from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any, Union
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
    InvoiceData
)

# Milestone CRUD Operations
async def create_milestone(
    db: AsyncSession,
    milestone_in: MilestoneCreate,
    created_by: int,
    documents: List[UploadFile] = None,
    shared_document_ids: List[int] = None,
    document_ids: List[int] = None
) -> Milestone:
    """
    Erstellt ein neues Milestone/Gewerk
    """
    try:
        # Erstelle Milestone-Objekt
        milestone_data = milestone_in.dict()
        milestone_data['created_by'] = created_by
        milestone_data['created_at'] = datetime.utcnow()
        milestone_data['updated_at'] = datetime.utcnow()
        
        # Entferne documents aus den Daten, da es nicht direkt in der DB gespeichert wird
        milestone_data.pop('documents', None)
        
        # Füge shared_document_ids als JSON-String hinzu
        if shared_document_ids:
            import json
            milestone_data['shared_document_ids'] = json.dumps(shared_document_ids)
            print(f"[SUCCESS] Shared document IDs gespeichert: {shared_document_ids}")
        else:
            milestone_data['shared_document_ids'] = None
            print("ℹ️  Keine shared document IDs")
        
        milestone = Milestone(**milestone_data)
        
        # Setze document_ids nach der Erstellung des Objekts
        if document_ids:
            import json
            milestone.documents = json.dumps(document_ids)
            print(f"[SUCCESS] Document IDs gespeichert: {document_ids}")
        else:
            milestone.documents = None
            print("ℹ️  Keine document IDs")
        db.add(milestone)
        await db.flush()  # Um die ID zu bekommen
        
        print(f"[SUCCESS] Milestone erstellt mit ID: {milestone.id}")
        
        # TODO: Dokument-Upload implementieren
        # if documents:
        #     # Upload und Verknüpfung der Dokumente
        #     pass
        
        await db.commit()
        await db.refresh(milestone)
        
        # Benachrichtige Dienstleister basierend auf ihren Präferenzen
        try:
            from .notification_service import NotificationService
            await NotificationService.notify_service_providers_for_new_tender(
                db=db,
                milestone=milestone,
                bautraeger_id=created_by
            )
        except Exception as e:
            print(f"[WARNING] Fehler beim Benachrichtigen der Dienstleister: {str(e)}")
            # Fehler beim Benachrichtigen sollte nicht das Erstellen des Milestones verhindern
        
        return milestone
        
    except Exception as e:
        await db.rollback()
        print(f"[ERROR] Fehler beim Erstellen des Milestones: {str(e)}")
        raise


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
    
    # Prüfe, ob Gewerk archiviert werden kann
    if milestone.completion_status not in ["completed", "completed_with_defects"]:
        raise ValueError("Gewerk muss abgeschlossen sein (completed oder completed_with_defects)")
    
    # Archiviere Gewerk
    milestone.archived = True
    milestone.archived_at = datetime.utcnow()
    milestone.completion_status = "archived"  # Setze Status auf archived
    
    await db.commit()
    await db.refresh(milestone)
    
    return milestone

def _generate_milestone_template_data(category: str) -> dict:
    """Generiert Template-Daten für verschiedene Gewerk-Kategorien"""
    templates = {
        "electrical": {
            "title": "Elektroinstallation",
            "description": "Installation der elektrischen Anlagen",
            "priority": "high"
        },
        "plumbing": {
            "title": "Sanitärinstallation", 
            "description": "Installation der Sanitäranlagen",
            "priority": "medium"
        },
        "eigene": {
            "title": "Eigenes Gewerk",
            "description": "Individuelles Gewerk",
            "priority": "medium"
        }
    }
    
    return templates.get(category, templates["eigene"])


async def get_milestone_by_id(db: AsyncSession, milestone_id: int) -> Optional[Milestone]:
    """Holt ein Milestone anhand der ID"""
    result = await db.execute(
        select(Milestone)
        .options(selectinload(Milestone.project))
        .where(Milestone.id == milestone_id)
    )
    return result.scalar_one_or_none()


async def get_milestone_statistics(db: AsyncSession, project_id: int) -> Dict[str, Any]:
    """Holt Statistiken für Milestones eines Projekts"""
    try:
        # Gesamtanzahl der Milestones
        total_result = await db.execute(
            select(func.count(Milestone.id))
            .where(Milestone.project_id == project_id)
        )
        total_milestones = total_result.scalar() or 0
        
        # Abgeschlossene Milestones
        completed_result = await db.execute(
            select(func.count(Milestone.id))
            .where(
                and_(
                    Milestone.project_id == project_id,
                    Milestone.completion_status == "completed"
                )
            )
        )
        completed_milestones = completed_result.scalar() or 0
        
        # In Bearbeitung
        in_progress_result = await db.execute(
            select(func.count(Milestone.id))
            .where(
                and_(
                    Milestone.project_id == project_id,
                    Milestone.completion_status == "in_progress"
                )
            )
        )
        in_progress_milestones = in_progress_result.scalar() or 0
        
        # Geplant
        planned_result = await db.execute(
            select(func.count(Milestone.id))
            .where(
                and_(
                    Milestone.project_id == project_id,
                    Milestone.completion_status == "planned"
                )
            )
        )
        planned_milestones = planned_result.scalar() or 0
        
        return {
            "total_milestones": total_milestones,
            "completed_milestones": completed_milestones,
            "in_progress_milestones": in_progress_milestones,
            "planned_milestones": planned_milestones,
            "completion_rate": (completed_milestones / total_milestones * 100) if total_milestones > 0 else 0
        }
    except Exception as e:
        print(f"[ERROR] Fehler beim Laden der Milestone-Statistiken: {e}")
        return {
            "total_milestones": 0,
            "completed_milestones": 0,
            "in_progress_milestones": 0,
            "planned_milestones": 0,
            "completion_rate": 0
        }


async def get_upcoming_milestones(
    db: AsyncSession, 
    project_id: Optional[int] = None, 
    days: int = 30
) -> List[Milestone]:
    """Holt anstehende Milestones in den nächsten X Tagen"""
    try:
        from datetime import date, timedelta
        
        end_date = date.today() + timedelta(days=days)
        
        query = select(Milestone).where(
            and_(
                Milestone.planned_date <= end_date,
                Milestone.planned_date >= date.today(),
                Milestone.completion_status.in_(["planned", "in_progress"])
            )
        )
        
        if project_id:
            query = query.where(Milestone.project_id == project_id)
        
        query = query.order_by(Milestone.planned_date)
        
        result = await db.execute(query)
        return list(result.scalars().all())
        
    except Exception as e:
        print(f"[ERROR] Fehler beim Laden anstehender Milestones: {e}")
        return []


async def get_overdue_milestones(
    db: AsyncSession, 
    project_id: Optional[int] = None
) -> List[Milestone]:
    """Holt überfällige Milestones"""
    try:
        from datetime import date
        
        query = select(Milestone).where(
            and_(
                Milestone.planned_date < date.today(),
                Milestone.completion_status.in_(["planned", "in_progress"])
            )
        )
        
        if project_id:
            query = query.where(Milestone.project_id == project_id)
        
        query = query.order_by(Milestone.planned_date)
        
        result = await db.execute(query)
        return list(result.scalars().all())
        
    except Exception as e:
        print(f"[ERROR] Fehler beim Laden überfälliger Milestones: {e}")
        return []


async def search_milestones(
    db: AsyncSession, 
    search_term: str, 
    project_id: Optional[int] = None
) -> List[Milestone]:
    """Sucht nach Milestones"""
    try:
        query = select(Milestone).where(
            or_(
                Milestone.title.ilike(f"%{search_term}%"),
                Milestone.description.ilike(f"%{search_term}%"),
                Milestone.category.ilike(f"%{search_term}%")
            )
        )
        
        if project_id:
            query = query.where(Milestone.project_id == project_id)
        
        query = query.order_by(Milestone.created_at.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
        
    except Exception as e:
        print(f"[ERROR] Fehler beim Suchen nach Milestones: {e}")
        return []