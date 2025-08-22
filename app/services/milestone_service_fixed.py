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

# Nur die Funktionen, die tatsächlich verwendet werden
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




