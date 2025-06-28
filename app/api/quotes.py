from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..api.deps import get_current_user
from ..models import User, QuoteStatus
from ..schemas.quote import QuoteCreate, QuoteRead, QuoteUpdate, QuoteSummary
from ..services.quote_service import (
    create_quote, get_quote_by_id, get_quotes_for_project,
    update_quote, delete_quote, submit_quote, accept_quote,
    get_quote_statistics, analyze_quote, get_quotes_for_service_provider
)

router = APIRouter(prefix="/quotes", tags=["quotes"])


@router.post("/", response_model=QuoteRead, status_code=status.HTTP_201_CREATED)
async def create_new_quote(
    quote_in: QuoteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    quote = await create_quote(db, quote_in, current_user.id)
    return quote


@router.get("/", response_model=List[QuoteSummary])
async def read_quotes(
    project_id: int = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if project_id:
        quotes = await get_quotes_for_project(db, project_id)
    else:
        # Für Dienstleister: eigene Angebote
        quotes = await get_quotes_for_service_provider(db, current_user.id)
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
    if quote.service_provider_id != current_user.id and quote.project.owner_id != current_user.id:
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
    if quote.service_provider_id != current_user.id:
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
    
    if quote.service_provider_id != current_user.id:
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
    """Akzeptiert ein Angebot"""
    quote = await get_quote_by_id(db, quote_id)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Angebot nicht gefunden"
        )
    
    if quote.project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für dieses Angebot"
        )
    
    accepted_quote = await accept_quote(db, quote_id)
    return accepted_quote


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
    if quote.service_provider_id != current_user.id:
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
    if quote.project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für dieses Angebot"
        )
    
    analysis = await analyze_quote(db, quote_id)
    return analysis 