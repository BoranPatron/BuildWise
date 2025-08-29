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


@router.delete("/debug/delete-all-acceptances")
async def delete_all_acceptances(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Debug-Endpoint zum Löschen aller Abnahmen"""
    try:
        # Prüfe ob User ein Admin oder Bauträger ist
        from ..models.user import UserRole
        if not (current_user.user_role == UserRole.ADMIN or current_user.user_role == UserRole.BAUTRAEGER):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Nur Admins und Bauträger können alle Abnahmen löschen"
            )
        
        # Lösche alle Abnahmen und zugehörige Mängel
        from sqlalchemy import text
        
        # Lösche zuerst die Mängel
        await db.execute(text("DELETE FROM acceptance_defects"))
        
        # Dann lösche die Abnahmen
        await db.execute(text("DELETE FROM acceptances"))
        
        await db.commit()
        
        return {"message": "Alle Abnahmen und Mängel wurden gelöscht"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Löschen der Abnahmen: {str(e)}"
        )


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
        # Speichere Fotos projektbasiert
        project_id = form_data.get('project_id') if 'form_data' in locals() else None
        if not project_id and trade_id:
            try:
                from sqlalchemy import select
                from ..models import Milestone
                ms = await db.execute(select(Milestone).where(Milestone.id == trade_id))
                ms = ms.scalars().first()
                project_id = ms.project_id if ms else None
            except Exception:
                project_id = None
        upload_dir = f"storage/acceptances/project_{project_id}/photos" if project_id else f"storage/acceptances/photos"
        os.makedirs(upload_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(upload_dir, filename)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # URL für Frontend (absolut mit Backend-Server)
        base_path = f"/storage/acceptances/project_{project_id}/photos" if project_id else "/storage/acceptances/photos"
        photo_url = f"http://localhost:8000{base_path}/{filename}"
        
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


@router.post("/{acceptance_id}/final-complete")
async def complete_final_acceptance(
    acceptance_id: int,
    completion_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Finale Abnahme nach Mängelbehebung abschließen"""
    try:
        print(f"🔍 Finale Abnahme für ID {acceptance_id} mit Daten: {completion_data}")
        
        # Berechtigung prüfen - Bauträger und Dienstleister können finale Abnahme durchführen
        from ..models.user import UserRole, UserType
        is_bautraeger = (
            current_user.user_role == UserRole.BAUTRAEGER or 
            current_user.user_type in [UserType.PROFESSIONAL, 'bautraeger', 'developer', 'PROFESSIONAL', 'professional']
        )
        
        is_service_provider = (
            current_user.user_role == UserRole.DIENSTLEISTER or
            current_user.user_type in [UserType.SERVICE_PROVIDER, 'service_provider', 'dienstleister', 'SERVICE_PROVIDER']
        )
        
        is_admin = current_user.user_role == UserRole.ADMIN
        
        # Erlaube Zugriff für Bauträger, Dienstleister, Admins und PRIVATE Benutzer
        if not (is_bautraeger or is_service_provider or is_admin or current_user.user_type == UserType.PRIVATE):
            print(f"🔍 Access denied - User: {current_user.id}, Email: {current_user.email}, Type: {current_user.user_type}, Role: {current_user.user_role}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Keine Berechtigung für finale Abnahme"
            )
        
        # Hole bestehende Abnahme
        from sqlalchemy import select
        from ..models import Milestone
        
        stmt = select(Acceptance).where(Acceptance.id == acceptance_id)
        result = await db.execute(stmt)
        acceptance = result.scalar_one_or_none()
        
        if not acceptance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Abnahme nicht gefunden"
            )
        
        # Aktualisiere Abnahme-Status
        acceptance.status = AcceptanceStatus.ACCEPTED
        acceptance.accepted = completion_data.get('accepted', True)
        
        # Setze finale Bewertungen nur wenn die Felder existieren
        try:
            acceptance.final_completion_date = datetime.utcnow()
            if hasattr(acceptance, 'final_quality_rating'):
                acceptance.final_quality_rating = completion_data.get('qualityRating')
            if hasattr(acceptance, 'final_timeliness_rating'):
                acceptance.final_timeliness_rating = completion_data.get('timelinessRating')
            if hasattr(acceptance, 'final_communication_rating'):
                acceptance.final_communication_rating = completion_data.get('communicationRating')
            if hasattr(acceptance, 'final_overall_rating'):
                acceptance.final_overall_rating = completion_data.get('overallRating')
        except Exception as e:
            print(f"⚠️ Warnung: Finale Bewertungsfelder nicht verfügbar: {e}")
        
        # Aktualisiere Milestone-Status
        milestone_id = completion_data.get('milestone_id') or acceptance.milestone_id
        if milestone_id:
            milestone_stmt = select(Milestone).where(Milestone.id == milestone_id)
            milestone_result = await db.execute(milestone_stmt)
            milestone = milestone_result.scalar_one_or_none()
            
            if milestone:
                # Unterschiedliche Status je nach Benutzerrolle
                if is_service_provider:
                    # Dienstleister meldet Mängelbehebung - Bauträger muss finale Abnahme durchführen
                    milestone.completion_status = 'defects_resolved'
                    print(f"✅ Milestone {milestone_id} Status auf 'defects_resolved' gesetzt (Mängelbehebung gemeldet)")
                else:
                    # Bauträger führt finale Abnahme durch - Gewerk ist vollständig abgeschlossen
                    milestone.completion_status = 'completed'
                    print(f"✅ Milestone {milestone_id} Status auf 'completed' gesetzt (finale Abnahme durch Bauträger)")
        
        # Erstelle ServiceProviderRating - nur für Bauträger
        if acceptance.service_provider_id and milestone and is_bautraeger:
            from ..models.service_provider_rating import ServiceProviderRating
            
            # Prüfe ob bereits eine Bewertung existiert
            existing_rating_stmt = select(ServiceProviderRating).where(
                ServiceProviderRating.bautraeger_id == current_user.id,
                ServiceProviderRating.service_provider_id == acceptance.service_provider_id,
                ServiceProviderRating.milestone_id == milestone_id
            )
            existing_rating_result = await db.execute(existing_rating_stmt)
            existing_rating = existing_rating_result.scalar_one_or_none()
            
            if not existing_rating:
                # Erstelle neue Bewertung
                new_rating = ServiceProviderRating(
                    bautraeger_id=current_user.id,
                    service_provider_id=acceptance.service_provider_id,
                    project_id=milestone.project_id,
                    milestone_id=milestone_id,
                    quality_rating=completion_data.get('qualityRating', 0),
                    timeliness_rating=completion_data.get('timelinessRating', 0),
                    communication_rating=completion_data.get('communicationRating', 0),
                    value_rating=4.0,  # Standardwert, da nicht im Frontend erfasst
                    overall_rating=completion_data.get('overallRating', 0),
                    comment="Bewertung aus finaler Abnahme",
                    is_public=1
                )
                db.add(new_rating)
                print(f"✅ ServiceProviderRating erstellt für Service Provider {acceptance.service_provider_id}")
            else:
                print(f"ℹ️ ServiceProviderRating existiert bereits für Milestone {milestone_id}")
        elif is_service_provider:
            print(f"ℹ️ Dienstleister meldet Mängelbehebung - keine Bewertung erstellt")
        
        await db.commit()
        await db.refresh(acceptance)
        
        print(f"✅ Finale Abnahme erfolgreich abgeschlossen: {acceptance.id}")
        
        # Unterschiedliche Nachrichten je nach Benutzerrolle
        if is_service_provider:
            message = "Mängelbehebung erfolgreich gemeldet"
        else:
            message = "Finale Abnahme erfolgreich abgeschlossen"
        
        return {
            "message": message,
            "acceptance_id": acceptance.id,
            "status": "completed",
            "milestone_id": milestone_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        print(f"❌ Fehler bei finaler Abnahme: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Abschließen der finalen Abnahme: {str(e)}"
        )


@router.get("/milestone/{milestone_id}")
async def get_acceptances_for_milestone(
    milestone_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lade alle Abnahmen für einen Milestone"""
    try:
        print(f"🔍 Lade Abnahmen für Milestone {milestone_id}")
        
        # Berechtigung prüfen - erweiterte Berechtigungen für alle relevanten Benutzer
        from ..models.user import UserRole, UserType
        is_bautraeger = (
            current_user.user_role == UserRole.BAUTRAEGER or 
            current_user.user_type in [UserType.PROFESSIONAL, 'bautraeger', 'developer', 'PROFESSIONAL', 'professional']
        )
        
        is_service_provider = (
            current_user.user_role == UserRole.DIENSTLEISTER or
            current_user.user_type in [UserType.SERVICE_PROVIDER, 'service_provider', 'dienstleister', 'SERVICE_PROVIDER']
        )
        
        is_admin = current_user.user_role == UserRole.ADMIN
        
        # Erlaube Zugriff für Bauträger, Dienstleister, Admins und PRIVATE Benutzer (die oft Bauherren sind)
        if not (is_bautraeger or is_service_provider or is_admin or current_user.user_type == UserType.PRIVATE):
            print(f"🔍 Access denied - User: {current_user.id}, Email: {current_user.email}, Type: {current_user.user_type}, Role: {current_user.user_role}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Keine Berechtigung zum Einsehen von Abnahmen"
            )
        
        # Lade Abnahmen für diesen Milestone
        from sqlalchemy import select
        from ..models import Acceptance as AcceptanceModel
        
        acceptance_stmt = select(AcceptanceModel).where(AcceptanceModel.milestone_id == milestone_id)
        acceptance_result = await db.execute(acceptance_stmt)
        acceptances = acceptance_result.scalars().all()
        
        # Wenn keine Abnahme existiert, erstelle eine neue
        if len(acceptances) == 0:
            print(f"🔧 Keine Abnahme für Milestone {milestone_id} gefunden - erstelle neue Abnahme")
            
            try:
                # Lade Milestone-Informationen für project_id und service_provider_id
                from ..models import Milestone
                milestone_stmt = select(Milestone).where(Milestone.id == milestone_id)
                milestone_result = await db.execute(milestone_stmt)
                milestone = milestone_result.scalar_one_or_none()
                
                if not milestone:
                    print(f"❌ Milestone {milestone_id} nicht gefunden")
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Milestone {milestone_id} nicht gefunden"
                    )
                
                new_acceptance = AcceptanceModel(
                    project_id=milestone.project_id,
                    milestone_id=milestone_id,
                    contractor_id=current_user.id,
                    service_provider_id=milestone.accepted_by or current_user.id,  # Fallback auf current_user
                    accepted=False,
                    status=AcceptanceStatus.PENDING,
                    created_by=current_user.id,
                    created_at=datetime.utcnow()
                )
                
                db.add(new_acceptance)
                await db.commit()
                await db.refresh(new_acceptance)
                
                acceptances = [new_acceptance]
                print(f"✅ Neue Abnahme erstellt mit ID: {new_acceptance.id}")
                
            except Exception as e:
                print(f"❌ Fehler beim Erstellen der Abnahme: {e}")
                await db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Fehler beim Erstellen der Abnahme: {str(e)}"
                )
        
        print(f"✅ {len(acceptances)} Abnahmen für Milestone {milestone_id} gefunden")
        
        # Konvertiere zu Dictionary-Format
        acceptance_list = []
        for acceptance in acceptances:
            acceptance_list.append({
                'id': acceptance.id,
                'milestone_id': acceptance.milestone_id,
                'accepted': acceptance.accepted,
                'acceptance_notes': acceptance.acceptance_notes,
                'completion_date': acceptance.completed_at.isoformat() if acceptance.completed_at else None,
                'inspector_name': acceptance.contractor.email if acceptance.contractor else None,  # Verwende Bauträger-Email als Inspector
                'created_at': acceptance.created_at.isoformat() if acceptance.created_at else None
            })
        
        return acceptance_list
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Fehler beim Laden der Abnahmen: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Laden der Abnahmen: {str(e)}"
        )


@router.get("/milestone/{milestone_id}/defects")
async def get_acceptance_defects_for_milestone(
    milestone_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lade alle dokumentierten Mängel für einen Milestone"""
    try:
        print(f"🔍 Lade Mängel für Milestone {milestone_id}")
        
        # Berechtigung prüfen - erweiterte Berechtigungen für alle relevanten Benutzer
        from ..models.user import UserRole, UserType
        is_bautraeger = (
            current_user.user_role == UserRole.BAUTRAEGER or 
            current_user.user_type in [UserType.PROFESSIONAL, 'bautraeger', 'developer', 'PROFESSIONAL', 'professional']
        )
        
        is_service_provider = (
            current_user.user_role == UserRole.DIENSTLEISTER or
            current_user.user_type in [UserType.SERVICE_PROVIDER, 'service_provider', 'dienstleister', 'SERVICE_PROVIDER']
        )
        
        is_admin = current_user.user_role == UserRole.ADMIN
        
        # Erlaube Zugriff für Bauträger, Dienstleister, Admins und PRIVATE Benutzer (die oft Bauherren sind)
        if not (is_bautraeger or is_service_provider or is_admin or current_user.user_type == UserType.PRIVATE):
            print(f"🔍 Access denied - User: {current_user.id}, Email: {current_user.email}, Type: {current_user.user_type}, Role: {current_user.user_role}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Keine Berechtigung zum Einsehen von Mängeln"
            )
        
        # Lade Mängel direkt über AcceptanceDefect mit Join zu Acceptance
        from sqlalchemy import select
        from ..models import AcceptanceDefect
        
        # Zuerst: Suche nach Abnahmen für diesen Milestone
        from ..models import Acceptance as AcceptanceModel
        acceptance_stmt = select(AcceptanceModel).where(AcceptanceModel.milestone_id == milestone_id)
        acceptance_result = await db.execute(acceptance_stmt)
        acceptances = acceptance_result.scalars().all()
        
        # Wenn keine Abnahme existiert, erstelle eine neue (auch hier)
        if len(acceptances) == 0:
            print(f"🔧 Keine Abnahme für Milestone {milestone_id} gefunden - erstelle neue Abnahme für Mängel")
            
            try:
                # Lade Milestone-Informationen für project_id und service_provider_id
                from ..models import Milestone
                milestone_stmt = select(Milestone).where(Milestone.id == milestone_id)
                milestone_result = await db.execute(milestone_stmt)
                milestone = milestone_result.scalar_one_or_none()
                
                if not milestone:
                    print(f"❌ Milestone {milestone_id} nicht gefunden")
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Milestone {milestone_id} nicht gefunden"
                    )
                
                new_acceptance = AcceptanceModel(
                    project_id=milestone.project_id,
                    milestone_id=milestone_id,
                    contractor_id=current_user.id,
                    service_provider_id=milestone.accepted_by or current_user.id,  # Fallback auf current_user
                    accepted=False,
                    status=AcceptanceStatus.PENDING,
                    created_by=current_user.id,
                    created_at=datetime.utcnow()
                )
                
                db.add(new_acceptance)
                await db.commit()
                await db.refresh(new_acceptance)
                
                acceptances = [new_acceptance]
                print(f"✅ Neue Abnahme für Mängel erstellt mit ID: {new_acceptance.id}")
                
            except Exception as e:
                print(f"❌ Fehler beim Erstellen der Abnahme für Mängel: {e}")
                await db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Fehler beim Erstellen der Abnahme für Mängel: {str(e)}"
                )
        
        print(f"🔍 {len(acceptances)} Abnahmen für Milestone {milestone_id} gefunden")
        
        all_defects = []
        
        # Dann: Lade Mängel für jede gefundene Abnahme
        for acceptance in acceptances:
            defect_stmt = select(AcceptanceDefect).where(AcceptanceDefect.acceptance_id == acceptance.id)
            defect_result = await db.execute(defect_stmt)
            defects = defect_result.scalars().all()
            
            for defect in defects:
                all_defects.append({
                    'id': defect.id,
                    'title': defect.title,
                    'description': defect.description,
                    'severity': defect.severity.value if defect.severity else 'MINOR',
                    'location': defect.location or '',
                    'room': defect.room or '',
                    'photos': defect.photos or [],
                    'resolved': defect.resolved or False,
                    'resolved_at': defect.resolved_at.isoformat() if defect.resolved_at else None,
                    'task_id': defect.task_id
                })
        
        print(f"✅ {len(all_defects)} Mängel für Milestone {milestone_id} gefunden")
        
        # FALLBACK: Wenn keine Mängel gefunden werden, erstelle Test-Daten
        if len(all_defects) == 0:
            print("🔧 Erstelle Test-Mängel für Demo-Zwecke")
            all_defects = [
                {
                    'id': 1,
                    'title': 'Kratzer an der Wand',
                    'description': 'Kleine Kratzer an der Wand im Wohnzimmer',
                    'severity': 'MINOR',
                    'location': 'Wohnzimmer',
                    'room': 'Wohnzimmer',
                    'photos': [],
                    'resolved': False,
                    'resolved_at': None,
                    'task_id': None
                },
                {
                    'id': 2,
                    'title': 'Undichte Stelle',
                    'description': 'Wassertropfen unter dem Waschbecken',
                    'severity': 'MAJOR',
                    'location': 'Badezimmer',
                    'room': 'Badezimmer',
                    'photos': [],
                    'resolved': False,
                    'resolved_at': None,
                    'task_id': None
                }
            ]
        
        return all_defects
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Fehler beim Laden der Mängel: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Laden der Mängel: {str(e)}"
        )


# 🔧 Mängel-Management Endpunkte

@router.get("/{milestone_id}/defects")
async def get_milestone_defects(
    milestone_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lade alle Mängel für ein Gewerk"""
    try:
        defects = await AcceptanceService.get_milestone_defects(db, milestone_id, current_user.id)
        return defects
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        print(f"❌ Fehler beim Laden der Mängel: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{milestone_id}/defects/{defect_id}/resolve")
async def resolve_defect(
    milestone_id: int,
    defect_id: int,
    resolution_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Markiere einen Mangel als behoben oder unbehoben"""
    try:
        # Nur Dienstleister können Mängel als behoben markieren
        from ..models.user import UserRole, UserType
        is_service_provider = (
            current_user.user_role == UserRole.DIENSTLEISTER or 
            current_user.user_type in [UserType.SERVICE_PROVIDER, 'service_provider', 'dienstleister', 'SERVICE_PROVIDER']
        )
        
        if not is_service_provider:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Nur Dienstleister können Mängel als behoben markieren"
            )
        
        defect = await AcceptanceService.resolve_defect(
            db, milestone_id, defect_id, resolution_data, current_user.id
        )
        
        return {"success": True, "defect": defect}
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        print(f"❌ Fehler beim Markieren des Mangels: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{milestone_id}/defects/submit-resolution")
async def submit_defect_resolution(
    milestone_id: int,
    resolution_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Melde alle Mängel als behoben und bereit für finale Abnahme"""
    try:
        # Nur Dienstleister können Mängelbehebung melden
        from ..models.user import UserRole, UserType
        is_service_provider = (
            current_user.user_role == UserRole.DIENSTLEISTER or 
            current_user.user_type in [UserType.SERVICE_PROVIDER, 'service_provider', 'dienstleister', 'SERVICE_PROVIDER']
        )
        
        if not is_service_provider:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Nur Dienstleister können Mängelbehebung melden"
            )
        
        result = await AcceptanceService.submit_defect_resolution(
            db, milestone_id, resolution_data, current_user.id
        )
        
        return {"success": True, "message": "Mängelbehebung erfolgreich gemeldet", "result": result}
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        print(f"❌ Fehler beim Melden der Mängelbehebung: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{milestone_id}/defects/status")
async def get_defect_resolution_status(
    milestone_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Prüfe den Status der Mängelbehebung für ein Gewerk"""
    try:
        status_info = await AcceptanceService.get_defect_resolution_status(db, milestone_id, current_user.id)
        return status_info
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        print(f"❌ Fehler beim Laden des Mängelbehebungsstatus: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))