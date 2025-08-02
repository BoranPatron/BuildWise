"""
Service für Baufortschrittsdokumentation und Kommentare
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from datetime import datetime
import json
import os

from ..models import MilestoneProgress, ProgressUpdateType, User, Milestone
from ..schemas.milestone_progress import (
    MilestoneProgressCreate,
    MilestoneProgressUpdate,
    MilestoneProgressResponse
)
from ..core.exceptions import NotFoundException, ForbiddenException


class MilestoneProgressService:
    """Service für Verwaltung von Baufortschritt-Updates"""
    
    async def create_progress_update(
        self,
        db: AsyncSession,
        milestone_id: int,
        user_id: int,
        data: MilestoneProgressCreate
    ) -> MilestoneProgress:
        """Erstellt ein neues Progress Update"""
        
        # Prüfe ob Milestone existiert
        milestone = await db.get(Milestone, milestone_id)
        if not milestone:
            raise NotFoundException("Gewerk nicht gefunden")
        
        # Erstelle Progress Update
        progress_update = MilestoneProgress(
            milestone_id=milestone_id,
            user_id=user_id,
            update_type=data.update_type,
            message=data.message,
            progress_percentage=data.progress_percentage,
            parent_id=data.parent_id,
            defect_severity=data.defect_severity,
            revision_deadline=data.revision_deadline,
            is_internal=data.is_internal
        )
        
        # Verarbeite Anhänge
        if data.attachments:
            progress_update.attachments = json.dumps(data.attachments)
        
        db.add(progress_update)
        
        # Update Milestone Fortschritt wenn angegeben
        if data.progress_percentage is not None:
            milestone.progress_percentage = data.progress_percentage
            
        # Wenn es eine Fertigstellungsmeldung ist
        if data.update_type == ProgressUpdateType.COMPLETION.value:
            milestone.completion_status = "completion_requested"
            milestone.completion_requested_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(progress_update)
        
        return progress_update
    
    async def get_progress_updates(
        self,
        db: AsyncSession,
        milestone_id: int,
        user_id: int,
        is_bautraeger: bool
    ) -> List[MilestoneProgress]:
        """Holt alle Progress Updates für ein Milestone"""
        
        print(f"🔍 [SERVICE] get_progress_updates: milestone_id={milestone_id}, user_id={user_id}, is_bautraeger={is_bautraeger}")
        
        query = select(MilestoneProgress).where(
            MilestoneProgress.milestone_id == milestone_id
        ).options(
            selectinload(MilestoneProgress.user),
            selectinload(MilestoneProgress.replies)
        ).order_by(MilestoneProgress.created_at)
        
        # Filtere interne Updates für Nicht-Bauträger
        if not is_bautraeger:
            query = query.where(MilestoneProgress.is_internal == False)
            print(f"🔍 [SERVICE] Filtere interne Updates für Dienstleister")
        
        result = await db.execute(query)
        updates = result.scalars().all()
        print(f"🔍 [SERVICE] Query executed, found {len(updates)} updates")
        return updates
    
    async def update_progress(
        self,
        db: AsyncSession,
        progress_id: int,
        user_id: int,
        data: MilestoneProgressUpdate
    ) -> MilestoneProgress:
        """Aktualisiert ein Progress Update"""
        
        progress_update = await db.get(MilestoneProgress, progress_id)
        if not progress_update:
            raise NotFoundException("Progress Update nicht gefunden")
            
        # Nur der Ersteller kann bearbeiten
        if progress_update.user_id != user_id:
            raise ForbiddenException("Nur der Ersteller kann dieses Update bearbeiten")
        
        # Update Felder
        if data.message is not None:
            progress_update.message = data.message
        if data.defect_resolved is not None:
            progress_update.defect_resolved = data.defect_resolved
        if data.revision_completed is not None:
            progress_update.revision_completed = data.revision_completed
            
        progress_update.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(progress_update)
        
        return progress_update
    
    async def upload_attachment(
        self,
        db: AsyncSession,
        progress_id: int,
        user_id: int,
        file_path: str
    ) -> MilestoneProgress:
        """Fügt einen Anhang zu einem Progress Update hinzu"""
        
        progress_update = await db.get(MilestoneProgress, progress_id)
        if not progress_update:
            raise NotFoundException("Progress Update nicht gefunden")
            
        # Nur der Ersteller kann Anhänge hinzufügen
        if progress_update.user_id != user_id:
            raise ForbiddenException("Nur der Ersteller kann Anhänge hinzufügen")
        
        # Parse bestehende Anhänge
        attachments = []
        if progress_update.attachments:
            attachments = json.loads(progress_update.attachments)
        
        # Füge neuen Anhang hinzu
        # Konvertiere absoluten Pfad zu relativer URL mit Forward-Slashes
        relative_path = file_path.replace("storage/", "").replace("\\", "/")
        attachments.append({
            "url": f"/api/v1/files/serve/{relative_path}",
            "uploaded_at": datetime.utcnow().isoformat(),
            "filename": os.path.basename(file_path)
        })
        
        print(f"🔍 [ATTACHMENT] Added attachment: {os.path.basename(file_path)}")
        print(f"🔍 [ATTACHMENT] URL: /api/v1/files/serve/{relative_path}")
        
        progress_update.attachments = json.dumps(attachments)
        
        await db.commit()
        await db.refresh(progress_update)
        
        return progress_update
    
    async def handle_completion_response(
        self,
        db: AsyncSession,
        milestone_id: int,
        user_id: int,
        accepted: bool,
        message: Optional[str] = None,
        revision_deadline: Optional[datetime] = None
    ) -> MilestoneProgress:
        """Behandelt die Antwort auf eine Fertigstellungsmeldung"""
        
        milestone = await db.get(Milestone, milestone_id)
        if not milestone:
            raise NotFoundException("Gewerk nicht gefunden")
        
        if accepted:
            # Abnahme bestätigt
            update_type = ProgressUpdateType.COMMENT.value
            milestone.completion_status = "completed"
            milestone.accepted_by = user_id
            milestone.acceptance_date = datetime.utcnow()
            milestone.archived = True
            milestone.archived_at = datetime.utcnow()
            message = message or "Gewerk abgenommen und archiviert."
        else:
            # Nachbesserung angefordert
            update_type = ProgressUpdateType.REVISION.value
            milestone.completion_status = "under_review"
            message = message or "Nachbesserung erforderlich."
        
        # Erstelle Progress Update
        progress_update = MilestoneProgress(
            milestone_id=milestone_id,
            user_id=user_id,
            update_type=update_type,
            message=message,
            revision_deadline=revision_deadline
        )
        
        db.add(progress_update)
        await db.commit()
        await db.refresh(progress_update)
        
        return progress_update


# Singleton-Instanz
milestone_progress_service = MilestoneProgressService()