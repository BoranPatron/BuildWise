"""
API Endpoints für Baufortschrittsdokumentation
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request, Body
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
import os
import json
from datetime import datetime
from sqlalchemy import select

from ..core.database import get_db
from ..api.deps import get_current_user
from ..models import User, UserType
from ..services.milestone_progress_service import milestone_progress_service
from ..schemas.milestone_progress import (
    MilestoneProgressCreate,
    MilestoneProgressUpdate,
    MilestoneProgressResponse,
    CompletionRequestCreate,
    CompletionResponseCreate
)

router = APIRouter(
    prefix="/milestones/{milestone_id}/progress",
    tags=["milestone-progress"]
)


@router.post("/debug")
async def debug_progress_update(
    milestone_id: int,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Debug Endpoint um zu sehen was ankommt"""
    
    print(f"🎯 [DEBUG] Endpoint erreicht! milestone_id={milestone_id}")
    print(f"🎯 [DEBUG] current_user={current_user.id}")
    
    try:
        print(f"🔍 [DEBUG] Received Data: {data}")
        parsed_data = data
        
        # Versuche Pydantic-Validierung
        from ..schemas.milestone_progress import MilestoneProgressCreate
        try:
            validated_data = MilestoneProgressCreate(**parsed_data)
            print(f"🔍 [DEBUG] Pydantic OK: {validated_data.model_dump()}")
            
            # Versuche Datenbank-Insert
            from ..models.milestone_progress import MilestoneProgress
            progress_update = MilestoneProgress(
                milestone_id=milestone_id,
                user_id=current_user.id,
                update_type=validated_data.update_type,
                message=validated_data.message,
                progress_percentage=validated_data.progress_percentage,
                parent_id=validated_data.parent_id,
                defect_severity=validated_data.defect_severity,
                is_internal=validated_data.is_internal
            )
            
            db.add(progress_update)
            await db.commit()
            await db.refresh(progress_update)
            print(f"🔍 [DEBUG] DB Insert OK: ID {progress_update.id}")
            
            return {"status": "ok", "data": validated_data.model_dump(), "id": progress_update.id}
            
        except Exception as pydantic_error:
            print(f"❌ [DEBUG] Pydantic Fehler: {pydantic_error}")
            return {"status": "pydantic_error", "error": str(pydantic_error)}
        
    except Exception as e:
        print(f"❌ [DEBUG] Allgemeiner Fehler: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "error": str(e)}


@router.post("/", response_model=MilestoneProgressResponse)
async def create_progress_update(
    milestone_id: int,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> MilestoneProgressResponse:
    """Erstellt ein neues Progress Update"""
    
    print(f"🔍 [PROGRESS] Milestone ID: {milestone_id}")
    print(f"🔍 [PROGRESS] User ID: {current_user.id}")
    print(f"🔍 [PROGRESS] Raw Data: {data}")
    
    try:
        # Prüfe ob User ein Dienstleister ist (sowohl user_type als auch user_role)
        from ..models.user import UserRole
        is_service_provider = (
            current_user.user_type == UserType.SERVICE_PROVIDER or
            (hasattr(current_user, 'user_role') and current_user.user_role == UserRole.DIENSTLEISTER)
        )
        is_bautraeger = not is_service_provider
        print(f"🔍 [PROGRESS] Is Bauträger: {is_bautraeger}")
        
        # Prüfe Zugriff auf Kommunikation
        has_access = await milestone_progress_service.check_communication_access(
            db=db,
            milestone_id=milestone_id,
            user_id=current_user.id,
            is_bautraeger=is_bautraeger
        )
        
        if not has_access:
            print(f"❌ [PROGRESS] Zugriff verweigert für User {current_user.id} auf Milestone {milestone_id}")
            raise HTTPException(
                status_code=403,
                detail="Zugriff auf diese Kommunikation nicht mehr möglich. Die Ausschreibung wurde bereits vergeben."
            )
        
        # Validiere und konvertiere die Daten zu MilestoneProgressCreate
        validated_data = MilestoneProgressCreate(**data)
        print(f"🔍 [PROGRESS] Validated Data: {validated_data.model_dump()}")
        
        progress_update = await milestone_progress_service.create_progress_update(
            db=db,
            milestone_id=milestone_id,
            user_id=current_user.id,
            data=validated_data
        )
    except ValidationError as e:
        print(f"❌ [PROGRESS] Validation Error: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Ungültige Daten: {e}"
        )
    except Exception as e:
        print(f"❌ [PROGRESS] Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Interner Serverfehler: {str(e)}"
        )
    
    # Lade User-Daten für Response
    await db.refresh(progress_update, ['user', 'replies'])
    
    return progress_update


@router.get("/", response_model=List[MilestoneProgressResponse])
async def get_progress_updates(
    milestone_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[MilestoneProgressResponse]:
    """Holt alle Progress Updates für ein Milestone mit Zugriffskontrolle"""
    
    print(f"🔍 [GET_PROGRESS] Milestone ID: {milestone_id}")
    print(f"🔍 [GET_PROGRESS] User ID: {current_user.id}")
    print(f"🔍 [GET_PROGRESS] User Type: {current_user.user_type}")
    
    # Prüfe ob User ein Dienstleister ist (sowohl user_type als auch user_role)
    from ..models.user import UserRole
    is_service_provider = (
        current_user.user_type == UserType.SERVICE_PROVIDER or
        (hasattr(current_user, 'user_role') and current_user.user_role == UserRole.DIENSTLEISTER)
    )
    is_bautraeger = not is_service_provider
    print(f"🔍 [GET_PROGRESS] Is Bauträger: {is_bautraeger}")
    
    # Debug: Prüfe ob Milestone existiert
    from ..models import Milestone
    milestone_result = await db.execute(select(Milestone).where(Milestone.id == milestone_id))
    milestone = milestone_result.scalar_one_or_none()
    if milestone:
        print(f"🔍 [GET_PROGRESS] Milestone gefunden: ID={milestone.id}, Title='{milestone.title}', Project={milestone.project_id}")
    else:
        print(f"❌ [GET_PROGRESS] Milestone mit ID {milestone_id} nicht gefunden!")
    
    # Prüfe Zugriff auf Kommunikation
    has_access = await milestone_progress_service.check_communication_access(
        db=db,
        milestone_id=milestone_id,
        user_id=current_user.id,
        is_bautraeger=is_bautraeger
    )
    
    if not has_access:
        raise HTTPException(
            status_code=403,
            detail="Zugriff auf diese Kommunikation nicht mehr möglich. Die Ausschreibung wurde bereits vergeben."
        )
    
    updates = await milestone_progress_service.get_progress_updates(
        db=db,
        milestone_id=milestone_id,
        user_id=current_user.id,
        is_bautraeger=is_bautraeger
    )
    
    print(f"🔍 [GET_PROGRESS] Found {len(updates)} updates")
    
    return updates


@router.put("/{progress_id}", response_model=MilestoneProgressResponse)
async def update_progress(
    milestone_id: int,
    progress_id: int,
    data: MilestoneProgressUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> MilestoneProgressResponse:
    """Aktualisiert ein Progress Update"""
    
    progress_update = await milestone_progress_service.update_progress(
        db=db,
        progress_id=progress_id,
        user_id=current_user.id,
        data=data
    )
    
    # Lade User-Daten für Response
    await db.refresh(progress_update, ['user', 'replies'])
    
    return progress_update


@router.post("/{progress_id}/attachments/", response_model=MilestoneProgressResponse)
async def upload_attachment(
    milestone_id: int,
    progress_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> MilestoneProgressResponse:
    """Lädt einen Anhang zu einem Progress Update hoch"""
    
    print(f"🔍 [ATTACHMENT] Milestone ID: {milestone_id}")
    print(f"🔍 [ATTACHMENT] Progress ID: {progress_id}")
    print(f"🔍 [ATTACHMENT] User ID: {current_user.id}")
    print(f"🔍 [ATTACHMENT] File: {file.filename}, Type: {file.content_type}")
    
    # Validiere Dateityp
    allowed_types = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf']
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Nur Bilder (JPG, PNG) und PDFs sind erlaubt"
        )
    
    # Erstelle Upload-Verzeichnis
    upload_dir = f"storage/uploads/milestone_{milestone_id}/progress"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Speichere Datei
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(upload_dir, filename)
    
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Update Progress mit Anhang
    progress_update = await milestone_progress_service.upload_attachment(
        db=db,
        progress_id=progress_id,
        user_id=current_user.id,
        file_path=file_path
    )
    
    # Lade User-Daten für Response
    await db.refresh(progress_update, ['user', 'replies'])
    
    return progress_update


@router.post("/completion", response_model=MilestoneProgressResponse)
async def request_completion(
    milestone_id: int,
    data: CompletionRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> MilestoneProgressResponse:
    """Meldet Gewerk als fertiggestellt (nur Dienstleister)"""
    
    # Prüfe ob User ein Dienstleister ist (sowohl user_type als auch user_role)
    from ..models.user import UserRole
    is_service_provider = (
        current_user.user_type == UserType.SERVICE_PROVIDER or
        (hasattr(current_user, 'user_role') and current_user.user_role == UserRole.DIENSTLEISTER)
    )
    
    if not is_service_provider:
        raise HTTPException(
            status_code=403,
            detail="Nur Dienstleister können Fertigstellung melden"
        )
    
    # Erstelle Fertigstellungsmeldung
    progress_data = MilestoneProgressCreate(
        update_type="completion",
        message=data.message or "Gewerk fertiggestellt. Bitte um Abnahme.",
        progress_percentage=100
    )
    
    # Füge Fotos/Dokumente als Anhänge hinzu
    attachments = []
    if data.completion_photos:
        attachments.extend(data.completion_photos)
    if data.completion_documents:
        attachments.extend(data.completion_documents)
    if attachments:
        progress_data.attachments = attachments
    
    progress_update = await milestone_progress_service.create_progress_update(
        db=db,
        milestone_id=milestone_id,
        user_id=current_user.id,
        data=progress_data
    )
    
    # Lade User-Daten für Response
    await db.refresh(progress_update, ['user', 'replies'])
    
    return progress_update


@router.post("/completion/response", response_model=MilestoneProgressResponse)
async def respond_to_completion(
    milestone_id: int,
    data: CompletionResponseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> MilestoneProgressResponse:
    """Antwortet auf Fertigstellungsmeldung (nur Bauträger)"""
    
    # Nur Bauträger können Fertigstellung bestätigen (nicht Dienstleister)
    from ..models.user import UserRole
    is_service_provider = (
        current_user.user_type == UserType.SERVICE_PROVIDER or
        (hasattr(current_user, 'user_role') and current_user.user_role == UserRole.DIENSTLEISTER)
    )
    
    if is_service_provider:
        raise HTTPException(
            status_code=403,
            detail="Nur Bauträger können auf Fertigstellung antworten"
        )
    
    progress_update = await milestone_progress_service.handle_completion_response(
        db=db,
        milestone_id=milestone_id,
        user_id=current_user.id,
        accepted=data.accepted,
        message=data.message,
        revision_deadline=data.revision_deadline
    )
    
    # Lade User-Daten für Response
    await db.refresh(progress_update, ['user', 'replies'])
    
    return progress_update