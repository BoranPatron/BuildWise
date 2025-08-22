from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, and_, or_
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
            print(f"✅ Shared document IDs gespeichert: {shared_document_ids}")
        else:
            milestone_data['shared_document_ids'] = None
            print("ℹ️  Keine shared document IDs")
        
        milestone = Milestone(**milestone_data)
        
        # Setze document_ids nach der Erstellung des Objekts
        if document_ids:
            import json
            milestone.documents = json.dumps(document_ids)
            print(f"✅ Document IDs gespeichert: {document_ids}")
        else:
            milestone.documents = None
            print("ℹ️  Keine document IDs")
        db.add(milestone)
        await db.flush()  # Um die ID zu bekommen
        
        print(f"✅ Milestone erstellt mit ID: {milestone.id}")
        
        # TODO: Dokument-Upload implementieren
        # if documents:
        #     # Upload und Verknüpfung der Dokumente
        #     pass
        
        await db.commit()
        await db.refresh(milestone)
        
        return milestone
        
    except Exception as e:
        await db.rollback()
        print(f"❌ Fehler beim Erstellen des Milestones: {str(e)}")
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
