from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime

from ..core.database import get_db
from ..api.deps import get_current_user
from ..models import User, Acceptance, AcceptanceStatus
from ..schemas.acceptance import (
    AcceptanceCreate, AcceptanceUpdate, AcceptanceResponse,
    AcceptanceDefectCreate, AcceptanceDefectUpdate, AcceptanceDefectResponse,
    AcceptanceScheduleRequest, AcceptanceScheduleResponse,
    AcceptanceStartRequest, AcceptanceCompleteRequest,
    AcceptanceStatusUpdate, AcceptanceSummary, AcceptanceListItem
)
from ..services.acceptance_service import AcceptanceService

router = APIRouter(prefix="/acceptance", tags=["acceptance"])


@router.post("/", response_model=AcceptanceResponse)
async def create_acceptance(
    acceptance_data: AcceptanceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Erstelle eine neue Abnahme"""
    try:
        # Nur Bauträger können Abnahmen erstellen
        from ..models.user import UserRole, UserType
        is_bautraeger = (
            current_user.user_role == UserRole.BAUTRAEGER or 
            current_user.user_type in [UserType.PROFESSIONAL, 'bautraeger', 'developer', 'PROFESSIONAL', 'professional']
        )
        
        if not is_bautraeger:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Nur Bauträger können Abnahmen erstellen"
            )
        
        acceptance = await AcceptanceService.create_acceptance(
            db, acceptance_data, current_user.id
        )
        
        return acceptance
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/schedule-appointment")
async def schedule_acceptance_appointment(
    request: AcceptanceScheduleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Terminvereinbarung für Abnahme"""
    try:
        # Nur Bauträger können Abnahme-Termine vorschlagen
        from ..models.user import UserRole, UserType
        is_bautraeger = (
            current_user.user_role == UserRole.BAUTRAEGER or 
            current_user.user_type in [UserType.PROFESSIONAL, 'bautraeger', 'developer', 'PROFESSIONAL', 'professional']
        )
        
        if not is_bautraeger:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Nur Bauträger können Abnahme-Termine vorschlagen"
            )
        
        # Lade Milestone um Service Provider ID zu ermitteln
        from ..services.milestone_service import MilestoneService
        milestone = await MilestoneService.get_milestone_by_id(db, request.milestone_id, current_user.id)
        
        if not milestone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gewerk nicht gefunden"
            )
        
        if not milestone.accepted_by:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Gewerk hat keinen zugewiesenen Dienstleister"
            )
        
        appointment = await AcceptanceService.schedule_acceptance_appointment(
            db=db,
            milestone_id=request.milestone_id,
            contractor_id=current_user.id,
            service_provider_id=milestone.accepted_by,
            proposed_date=request.proposed_date,
            notes=request.notes
        )
        
        return {
            "message": "Abnahme-Termin vorgeschlagen",
            "appointment_id": appointment.id,
            "scheduled_date": appointment.scheduled_date
        }
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/appointment/{appointment_id}/respond")
async def respond_to_acceptance_appointment(
    appointment_id: int,
    accepted: bool = Form(...),
    message: Optional[str] = Form(None),
    counter_proposal: Optional[datetime] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Antwort auf Abnahme-Terminvorschlag"""
    try:
        # Nur Dienstleister können auf Abnahme-Termine antworten
        if current_user.user_type not in ['dienstleister', 'service_provider']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Nur Dienstleister können auf Abnahme-Termine antworten"
            )
        
        appointment = await AcceptanceService.respond_to_acceptance_appointment(
            db=db,
            appointment_id=appointment_id,
            service_provider_id=current_user.id,
            accepted=accepted,
            message=message,
            counter_proposal=counter_proposal
        )
        
        return {
            "message": "Antwort gespeichert",
            "status": appointment.status.value,
            "accepted": accepted
        }
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{acceptance_id}/start")
async def start_acceptance(
    acceptance_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Starte die Abnahme"""
    try:
        # Lade Abnahme um Berechtigung zu prüfen
        acceptance = await AcceptanceService.get_acceptance_by_id(db, acceptance_id, current_user.id)
        
        if not acceptance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Abnahme nicht gefunden"
            )
        
        # Nur Bauträger können Abnahme starten
        if acceptance.contractor_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Nur der Bauträger kann die Abnahme starten"
            )
        
        acceptance = await AcceptanceService.start_acceptance(
            db, acceptance_id, current_user.id
        )
        
        return {
            "message": "Abnahme gestartet",
            "status": acceptance.status.value,
            "started_at": acceptance.started_at
        }
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))





@router.get("/{acceptance_id}", response_model=AcceptanceResponse)
async def get_acceptance(
    acceptance_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lade Abnahme mit allen Details"""
    acceptance = await AcceptanceService.get_acceptance_by_id(db, acceptance_id, current_user.id)
    
    if not acceptance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Abnahme nicht gefunden"
        )
    
    return acceptance


@router.get("/", response_model=List[AcceptanceResponse])
async def get_acceptances(
    status: Optional[AcceptanceStatus] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lade Abnahmen für aktuellen Benutzer"""
    acceptances = await AcceptanceService.get_acceptances_for_user(
        db, current_user.id, status, limit, offset
    )
    
    return acceptances


@router.get("/summary/dashboard", response_model=AcceptanceSummary)
async def get_acceptance_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Abnahme-Zusammenfassung für Dashboard"""
    summary = await AcceptanceService.get_acceptance_summary(db, current_user.id)
    return summary


@router.put("/{acceptance_id}", response_model=AcceptanceResponse)
async def update_acceptance(
    acceptance_id: int,
    update_data: AcceptanceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Aktualisiere Abnahme"""
    try:
        # Lade Abnahme um Berechtigung zu prüfen
        acceptance = await AcceptanceService.get_acceptance_by_id(db, acceptance_id, current_user.id)
        
        if not acceptance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Abnahme nicht gefunden"
            )
        
        # Nur Ersteller oder Teilnehmer können aktualisieren
        if acceptance.created_by != current_user.id and \
           acceptance.contractor_id != current_user.id and \
           acceptance.service_provider_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Keine Berechtigung zum Aktualisieren"
            )
        
        # Update Felder
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(acceptance, field, value)
        
        if hasattr(update_data, 'status') and update_data.status:
            acceptance.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(acceptance)
        
        return acceptance
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Mängel-Endpunkte
@router.post("/{acceptance_id}/defects", response_model=AcceptanceDefectResponse)
async def create_defect(
    acceptance_id: int,
    defect_data: AcceptanceDefectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Erstelle einen neuen Mangel"""
    try:
        # Lade Abnahme um Berechtigung zu prüfen
        acceptance = await AcceptanceService.get_acceptance_by_id(db, acceptance_id, current_user.id)
        
        if not acceptance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Abnahme nicht gefunden"
            )
        
        from ..models import AcceptanceDefect
        
        defect = AcceptanceDefect(
            acceptance_id=acceptance_id,
            **defect_data.dict()
        )
        
        db.add(defect)
        await db.commit()
        await db.refresh(defect)
        
        return defect
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/defects/{defect_id}", response_model=AcceptanceDefectResponse)
async def update_defect(
    defect_id: int,
    update_data: AcceptanceDefectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Aktualisiere einen Mangel"""
    try:
        from sqlalchemy import select
        from ..models import AcceptanceDefect
        
        # Lade Mangel
        result = await db.execute(
            select(AcceptanceDefect).where(AcceptanceDefect.id == defect_id)
        )
        defect = result.scalar_one_or_none()
        
        if not defect:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mangel nicht gefunden"
            )
        
        # Prüfe Berechtigung über Abnahme
        acceptance = await AcceptanceService.get_acceptance_by_id(db, defect.acceptance_id, current_user.id)
        
        if not acceptance:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Keine Berechtigung"
            )
        
        # Update Felder
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(defect, field, value)
        
        if update_data.resolved is not None and update_data.resolved:
            defect.resolved_at = datetime.utcnow()
            defect.resolved_by = current_user.id
        
        await db.commit()
        await db.refresh(defect)
        
        return defect
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/upload-photo")
async def upload_acceptance_photo(
    file: UploadFile = File(...),
    type: str = Form("defect_photo"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lade Foto für Abnahme hoch"""
    try:
        # Prüfe Dateityp
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nur Bilddateien sind erlaubt"
            )
        
        # Speichere Datei
        import os
        from datetime import datetime
        
        # Erstelle Upload-Verzeichnis
        upload_dir = f"storage/acceptances/photos"
        os.makedirs(upload_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(upload_dir, filename)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # URL für Frontend (absolut mit Backend-Server)
        photo_url = f"http://localhost:8000/storage/acceptances/photos/{filename}"
        
        return {
            "message": "Foto hochgeladen",
            "photo_url": photo_url,
            "filename": filename,
            "url": photo_url  # Für Frontend-Kompatibilität
        }
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/complete")
async def complete_acceptance(
    completion_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Schließt eine Abnahme ab und erstellt automatisch Tasks für Mängel
    """
    try:
        # Nur Bauträger können Abnahmen abschließen
        from ..models.user import UserRole, UserType
        is_bautraeger = (
            current_user.user_role == UserRole.BAUTRAEGER or 
            current_user.user_type in [UserType.PROFESSIONAL, 'bautraeger', 'developer', 'PROFESSIONAL', 'professional']
        )
        
        if not is_bautraeger:
            print(f"🔍 Access denied - User: {current_user.id}, Type: {current_user.user_type}, Role: {current_user.user_role}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Nur Bauträger können Abnahmen abschließen"
            )
        
        print(f"✅ Access granted - Bauträger {current_user.id} (Type: {current_user.user_type}, Role: {current_user.user_role})")
        
        # Extrahiere acceptance_id aus completion_data oder erstelle eine neue Abnahme
        acceptance_id = completion_data.get('acceptance_id')
        
        if acceptance_id:
            print(f"📝 Bauträger {current_user.id} schließt bestehende Abnahme {acceptance_id} ab")
        else:
            print(f"📝 Bauträger {current_user.id} erstellt neue Abnahme")
        
        print(f"📊 Completion Data: {completion_data}")
        
        # Schließe Abnahme ab und erstelle Tasks
        acceptance = await AcceptanceService.complete_acceptance(
            db=db,
            acceptance_id=acceptance_id,
            completion_data=completion_data,
            completed_by_user_id=current_user.id
        )
        
        return {
            "message": "Abnahme erfolgreich abgeschlossen",
            "acceptance_id": acceptance.id,
            "accepted": acceptance.accepted,
            "defects_count": len(acceptance.defects) if acceptance.defects else 0,
            "review_date": acceptance.review_date.isoformat() if acceptance.review_date else None,
            "status": acceptance.status.value if acceptance.status else None
        }
        
    except ValueError as e:
        await db.rollback()  # Explicit rollback
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await db.rollback()  # Explicit rollback
        print(f"❌ Fehler beim Abschließen der Abnahme: {e}")
        print(f"❌ Datenbankfehler: 500: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))