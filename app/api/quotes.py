from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

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
    user_id = getattr(current_user, 'id', 0)
    quote = await create_quote(db, quote_in, user_id)
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