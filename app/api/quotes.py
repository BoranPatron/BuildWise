from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import os
import shutil
from pathlib import Path
import uuid
from datetime import datetime

from ..core.database import get_db
from ..api.deps import get_current_user
from ..models import User, QuoteStatus
from ..schemas.quote import QuoteCreate, QuoteRead, QuoteUpdate, QuoteSummary, QuoteForMilestone
from ..services.quote_service import (
    create_quote, get_quote_by_id, get_quotes_for_project,
    update_quote, delete_quote, submit_quote, accept_quote,
    get_quote_statistics, analyze_quote, get_quotes_for_service_provider,
    get_quotes_for_milestone, get_quotes_for_milestone_by_service_provider,
    create_mock_quotes_for_milestone, get_all_quotes, get_quotes_by_project, 
    get_quotes_by_service_provider
)
from ..schemas.quote import QuoteUpdate
from ..models.quote import QuoteStatus
from ..core.security import can_accept_or_reject_quote
from app.services.cost_position_service import create_cost_position, get_cost_position_by_quote_id
from app.schemas.cost_position import CostPositionCreate

router = APIRouter(prefix="/quotes", tags=["quotes"])


class QuoteRejectRequest(BaseModel):
    rejection_reason: Optional[str] = None


@router.post("/", response_model=QuoteRead, status_code=status.HTTP_201_CREATED)
async def create_new_quote(
    quote_in: QuoteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Prüfe ob User ein Dienstleister ist (sowohl user_type als auch user_role)
    from ..models.user import UserRole, UserType
    
    # Debug: Zeige User-Informationen
    print(f"🔍 [QUOTE-CREATE] User ID: {current_user.id}")
    print(f"🔍 [QUOTE-CREATE] User Type: {current_user.user_type}")
    print(f"🔍 [QUOTE-CREATE] User Role: {getattr(current_user, 'user_role', 'N/A')}")
    print(f"🔍 [QUOTE-CREATE] User Email: {current_user.email}")
    
    is_service_provider = (
        current_user.user_type == UserType.SERVICE_PROVIDER or
        (hasattr(current_user, 'user_role') and current_user.user_role == UserRole.DIENSTLEISTER) or
        (current_user.email and "dienstleister" in current_user.email.lower())
    )
    
    print(f"🔍 [QUOTE-CREATE] Is Service Provider: {is_service_provider}")
    
    # TEMPORÄRE LÖSUNG: Wenn User noch keine Rolle hat, setze automatisch Dienstleister-Rolle
    if not is_service_provider and (not hasattr(current_user, 'user_role') or current_user.user_role is None):
        print(f"🔧 [QUOTE-CREATE] User hat keine Rolle - setze automatisch auf DIENSTLEISTER")
        from sqlalchemy import update
        from datetime import datetime
        await db.execute(
            update(User)
            .where(User.id == current_user.id)
            .values(
                user_role=UserRole.DIENSTLEISTER,
                role_selected=True,
                role_selected_at=datetime.utcnow()
            )
        )
        await db.commit()
        # Aktualisiere current_user
        current_user.user_role = UserRole.DIENSTLEISTER
        is_service_provider = True
    
    if not is_service_provider:
        raise HTTPException(
            status_code=403,
            detail=f"Nur Dienstleister können Angebote erstellen. User-Type: {current_user.user_type}, User-Role: {getattr(current_user, 'user_role', 'N/A')}"
        )
    
    user_id = getattr(current_user, 'id', 0)
    quote = await create_quote(db, quote_in, user_id)
    
    # Setze Status auf SUBMITTED (da das Angebot direkt eingereicht wird)
    from ..schemas.quote import QuoteUpdate
    from ..models.quote import QuoteStatus
    quote_update = QuoteUpdate(status=QuoteStatus.SUBMITTED)
    quote = await update_quote(db, quote.id, quote_update)
    
    return quote


@router.get("/", response_model=List[QuoteRead])
async def get_quotes_endpoint(
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Ruft Angebote ab - für Admin alle, für andere projektbasiert"""
    user_id = getattr(current_user, 'id', 0)
    user_type = getattr(current_user, 'user_type', '')
    user_email = getattr(current_user, 'email', '')
    
    # Admin-User sehen alle Angebote
    is_admin = (user_type in ("admin", "superuser", "super_admin") or 
                user_email == "admin@buildwise.de")
    
    if is_admin:
        # Admin: Alle Angebote zurückgeben
        quotes = await get_all_quotes(db)
        return quotes
    else:
        # Nicht-Admin: Projektbasierte Filterung
        if project_id:
            quotes = await get_quotes_by_project(db, project_id)
        else:
            quotes = await get_quotes_by_service_provider(db, user_id)
    return quotes


@router.get("/milestone/{milestone_id}", response_model=List[QuoteForMilestone])
async def read_quotes_for_milestone(
    milestone_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Holt alle Angebote für ein bestimmtes Gewerk"""
    user_id = getattr(current_user, 'id', 0)
    user_type = getattr(current_user, 'user_type', '')
    user_role = getattr(current_user, 'user_role', '')
    user_email = getattr(current_user, 'email', '')
    
    # DEBUG: Ausgabe der Benutzer-Informationen
    print(f"🔍 DEBUG quotes/milestone/{milestone_id}: user_id={user_id}, user_type='{user_type}', user_role='{user_role}', user_email='{user_email}'")
    
    # TEMPORÄR: Alle Benutzer sehen alle Angebote (für Debugging)
    quotes = await get_quotes_for_milestone(db, milestone_id)
    print(f"✅ DEBUG: Lade alle {len(quotes)} Angebote für Gewerk {milestone_id} (ohne Filterung)")
    
    return quotes


@router.post("/milestone/{milestone_id}/mock", response_model=List[QuoteForMilestone])
async def create_mock_quotes_for_milestone_endpoint(
    milestone_id: int,
    project_id: int = Query(..., description="Projekt-ID für die Mock-Angebote"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Erstellt Mock-Angebote für ein Gewerk (für Demonstrationszwecke)"""
    quotes = await create_mock_quotes_for_milestone(db, milestone_id, project_id)
    return quotes


@router.get("/{quote_id}", response_model=QuoteRead)
async def read_quote(
    quote_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    quote = await get_quote_by_id(db, quote_id)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Angebot nicht gefunden"
        )
    
    # Prüfe Zugriffsberechtigung
    user_id = getattr(current_user, 'id', 0)
    project_owner_id = getattr(quote.project, 'owner_id', 0) if quote.project else 0
    service_provider_id = getattr(quote, 'service_provider_id', 0)
    
    if service_provider_id != user_id and project_owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für dieses Angebot"
        )
    
    return quote


@router.put("/{quote_id}", response_model=QuoteRead)
async def update_quote_endpoint(
    quote_id: int,
    quote_update: QuoteUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    quote = await get_quote_by_id(db, quote_id)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Angebot nicht gefunden"
        )
    
    # Nur der Dienstleister kann sein Angebot bearbeiten
    user_id = getattr(current_user, 'id', 0)
    service_provider_id = getattr(quote, 'service_provider_id', 0)
    
    if service_provider_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für dieses Angebot"
        )
    
    updated_quote = await update_quote(db, quote_id, quote_update)
    return updated_quote


@router.post("/{quote_id}/submit", response_model=QuoteRead)
async def submit_quote_endpoint(
    quote_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reicht ein Angebot ein"""
    quote = await get_quote_by_id(db, quote_id)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Angebot nicht gefunden"
        )
    
    user_id = getattr(current_user, 'id', 0)
    service_provider_id = getattr(quote, 'service_provider_id', 0)
    
    if service_provider_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für dieses Angebot"
        )
    
    submitted_quote = await submit_quote(db, quote_id)
    return submitted_quote


@router.post("/{quote_id}/accept", response_model=QuoteRead)
async def accept_quote_endpoint(
    quote_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Akzeptiert ein Angebot und erstellt automatisch eine Kostenposition"""
    quote = await get_quote_by_id(db, quote_id)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Angebot nicht gefunden"
        )
    
    # Robuste Berechtigungsprüfung
    if not can_accept_or_reject_quote(current_user, quote):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nur Projekt-Owner, Admin oder Superuser dürfen Angebote annehmen."
        )
    
    # Akzeptiere das Angebot
    accepted_quote = await accept_quote(db, quote_id)
    
    # Kostenposition erzeugen, falls nicht vorhanden
    try:
        # Verwende die robuste Service-Funktion direkt
        from ..services.quote_service import create_cost_position_from_quote
        success = await create_cost_position_from_quote(db, quote)
        if not success:
            print(f"⚠️ Warnung: Kostenposition für Angebot {quote.id} konnte nicht erstellt werden")
    except Exception as e:
        print(f"⚠️ Fehler beim Erstellen der Kostenposition: {e}")
    
    # Aktualisiere Kommunikationszugriff nach Angebotsannahme
    try:
        from ..services.milestone_progress_service import milestone_progress_service
        await milestone_progress_service.update_communication_access_after_award(
            db=db,
            milestone_id=quote.milestone_id,
            accepted_service_provider_id=quote.service_provider_id
        )
        print(f"✅ Kommunikationszugriff für Milestone {quote.milestone_id} aktualisiert")
    except Exception as e:
        print(f"⚠️ Fehler beim Aktualisieren des Kommunikationszugriffs: {e}")
    
    return accepted_quote


@router.post("/{quote_id}/reset", response_model=QuoteRead)
async def reset_quote_endpoint(
    quote_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Setzt ein angenommenes Angebot zurück"""
    quote = await get_quote_by_id(db, quote_id)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Angebot nicht gefunden"
        )
    
    user_id = getattr(current_user, 'id', 0)
    project_owner_id = getattr(quote.project, 'owner_id', 0) if quote.project else 0
    
    if project_owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für dieses Angebot"
        )
    
    # Setze das Angebot zurück auf "submitted"
    from ..schemas.quote import QuoteUpdate
    from ..models import QuoteStatus
    quote_update = QuoteUpdate(status=QuoteStatus.SUBMITTED)
    reset_quote = await update_quote(db, quote_id, quote_update)
    
    return reset_quote


@router.delete("/{quote_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quote_endpoint(
    quote_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    quote = await get_quote_by_id(db, quote_id)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Angebot nicht gefunden"
        )
    
    # Nur der Dienstleister kann sein Angebot löschen
    user_id = getattr(current_user, 'id', 0)
    service_provider_id = getattr(quote, 'service_provider_id', 0)
    
    if service_provider_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für dieses Angebot"
        )
    
    success = await delete_quote(db, quote_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Angebot konnte nicht gelöscht werden"
        )
    
    return None


@router.get("/project/{project_id}/statistics")
async def get_project_quote_statistics(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Holt Statistiken für Angebote eines Projekts"""
    stats = await get_quote_statistics(db, project_id)
    return stats


@router.get("/{quote_id}/analysis")
async def analyze_quote_endpoint(
    quote_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Analysiert ein Angebot mit KI"""
    quote = await get_quote_by_id(db, quote_id)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Angebot nicht gefunden"
        )
    
    # Nur der Projektbesitzer kann Angebote analysieren
    user_id = getattr(current_user, 'id', 0)
    project_owner_id = getattr(quote.project, 'owner_id', 0) if quote.project else 0
    
    if project_owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für dieses Angebot"
        )
    
    analysis = await analyze_quote(db, quote_id)
    return analysis 


@router.post("/{quote_id}/reject", response_model=QuoteRead)
async def reject_quote_endpoint(
    quote_id: int,
    reject_request: QuoteRejectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lehnt ein Angebot ab (mit optionalem Ablehnungsgrund)"""
    quote = await get_quote_by_id(db, quote_id)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Angebot nicht gefunden"
        )
    
    # Robuste Berechtigungsprüfung
    if not can_accept_or_reject_quote(current_user, quote):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nur Projekt-Owner, Admin oder Superuser dürfen Angebote ablehnen."
        )
    
    # Setze das Angebot auf "rejected" und speichere optionalen Ablehnungsgrund
    quote_update = QuoteUpdate(
        status=QuoteStatus.REJECTED,
        rejection_reason=reject_request.rejection_reason
    )
    rejected_quote = await update_quote(db, quote_id, quote_update)
    return rejected_quote


@router.post("/{quote_id}/withdraw", status_code=status.HTTP_204_NO_CONTENT)
async def withdraw_quote_endpoint(
    quote_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Zieht ein Angebot zurück (löscht es)"""
    quote = await get_quote_by_id(db, quote_id)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Angebot nicht gefunden"
        )
    
    # Nur der Dienstleister kann sein Angebot zurückziehen
    user_id = getattr(current_user, 'id', 0)
    service_provider_id = getattr(quote, 'service_provider_id', 0)
    
    if service_provider_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für dieses Angebot"
        )
    
    # Nur Angebote die noch nicht angenommen wurden können zurückgezogen werden
    if quote.status.value == QuoteStatus.ACCEPTED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Angenommene Angebote können nicht zurückgezogen werden"
        )
    
    success = await delete_quote(db, quote_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Angebot konnte nicht zurückgezogen werden"
        )
    
    return None


@router.post("/{quote_id}/upload-document", response_model=QuoteRead)
async def upload_quote_document(
    quote_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Lädt ein Dokument für ein Angebot hoch und speichert es im strukturierten Storage.
    Nur der Dienstleister, der das Angebot erstellt hat, kann Dokumente hochladen.
    """
    # Hole das Angebot
    quote = await get_quote_by_id(db, quote_id)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Angebot nicht gefunden"
        )
    
    # Prüfe Berechtigung - nur der Dienstleister kann Dokumente hochladen
    if quote.service_provider_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für dieses Angebot"
        )
    
    # Prüfe Dateityp
    allowed_types = ['application/pdf', 'image/jpeg', 'image/png', 'application/msword', 
                     'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nicht unterstützter Dateityp. Erlaubt sind: PDF, JPEG, PNG, DOC, DOCX"
        )
    
    # Prüfe Dateigröße (max 10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    file_content = await file.read()
    if len(file_content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Datei zu groß. Maximum: 10MB"
        )
    
    # Erstelle Storage-Struktur: /storage/projects/{project_id}/quotes/{quote_id}/
    storage_base = Path("storage")
    quote_dir = storage_base / "projects" / str(quote.project_id) / "quotes" / str(quote_id)
    quote_dir.mkdir(parents=True, exist_ok=True)
    
    # Generiere eindeutigen Dateinamen
    file_extension = Path(file.filename).suffix if file.filename else ".pdf"
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = quote_dir / unique_filename
    
    # Speichere Datei
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Speichern der Datei: {str(e)}"
        )
    
    # Relativer Pfad für Datenbank (ohne "storage/" Präfix)
    relative_path = str(file_path.relative_to(storage_base))
    
    # Aktualisiere Quote in Datenbank
    if file.content_type == 'application/pdf':
        # Hauptdokument (PDF)
        quote_update = QuoteUpdate(pdf_upload_path=f"/{relative_path}")
    else:
        # Zusätzliche Dokumente
        import json
        additional_docs = []
        if quote.additional_documents:
            try:
                additional_docs = json.loads(quote.additional_documents)
            except:
                additional_docs = []
        
        additional_docs.append({
            "name": file.filename,
            "path": f"/{relative_path}",
            "type": file.content_type,
            "size": len(file_content),
            "uploaded_at": datetime.utcnow().isoformat()
        })
        
        quote_update = QuoteUpdate(additional_documents=json.dumps(additional_docs))
    
    updated_quote = await update_quote(db, quote_id, quote_update)
    return updated_quote


@router.get("/{quote_id}/documents/{filename}")
async def download_quote_document(
    quote_id: int,
    filename: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Lädt ein Dokument eines Angebots herunter.
    Berechtigung: Dienstleister (Ersteller) oder Bauträger (Projekt-Owner).
    """
    from fastapi.responses import FileResponse
    from ..models import Project
    from sqlalchemy import select
    
    # Hole das Angebot
    quote = await get_quote_by_id(db, quote_id)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Angebot nicht gefunden"
        )
    
    # Hole Projekt für Berechtigungsprüfung
    project_result = await db.execute(
        select(Project).where(Project.id == quote.project_id)
    )
    project = project_result.scalar_one_or_none()
    
    # Prüfe Berechtigung - Dienstleister oder Bauträger
    is_service_provider = quote.service_provider_id == current_user.id
    is_project_owner = project and project.owner_id == current_user.id
    
    if not (is_service_provider or is_project_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für dieses Dokument"
        )
    
    # Baue Dateipfad
    storage_base = Path("storage")
    file_path = storage_base / "projects" / str(quote.project_id) / "quotes" / str(quote_id) / filename
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dokument nicht gefunden"
        )
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type='application/octet-stream'
    )