"""
API Endpoints für Dienstleister-Bewertungen
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..api.deps import get_current_user
from ..models import User, UserType
from ..services.rating_service import rating_service
from ..schemas.rating import (
    ServiceProviderRatingCreate,
    ServiceProviderRatingResponse,
    ServiceProviderRatingSummary,
    ServiceProviderAggregatedRatingResponse,
    RatingCheckResponse
)

router = APIRouter(
    prefix="/ratings",
    tags=["ratings"]
)


@router.delete("/debug/delete-all-ratings")
async def delete_all_ratings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Debug-Endpoint zum Löschen aller Bewertungen"""
    try:
        # Prüfe ob User ein Admin oder Bauträger ist
        from ..models.user import UserRole
        if not (current_user.user_role == UserRole.ADMIN or current_user.user_role == UserRole.BAUTRAEGER):
            raise HTTPException(
                status_code=403,
                detail="Nur Admins und Bauträger können alle Bewertungen löschen"
            )
        
        # Lösche alle Bewertungen
        from sqlalchemy import text
        await db.execute(text("DELETE FROM service_provider_ratings"))
        await db.commit()
        
        return {"message": "Alle Bewertungen wurden gelöscht"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Löschen der Bewertungen: {str(e)}"
        )


@router.post("/", response_model=ServiceProviderRatingResponse)
async def create_rating(
    data: ServiceProviderRatingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ServiceProviderRatingResponse:
    """Erstellt eine neue Bewertung (nur Bauträger)"""
    
    # Nur Bauträger können bewerten (PRIVATE oder PROFESSIONAL, nicht SERVICE_PROVIDER)
    if current_user.user_type == UserType.SERVICE_PROVIDER:
        raise HTTPException(
            status_code=403,
            detail="Nur Bauträger können Bewertungen abgeben"
        )
    
    rating = await rating_service.create_rating(
        db=db,
        bautraeger_id=current_user.id,
        data=data
    )
    
    # Lade Relationen für Response
    await db.refresh(rating, ['bautraeger', 'service_provider', 'milestone', 'quote'])
    
    return rating


@router.get("/{rating_id}", response_model=ServiceProviderRatingResponse)
async def get_rating(
    rating_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ServiceProviderRatingResponse:
    """Holt eine einzelne Bewertung"""
    
    rating = await rating_service.get_rating(db=db, rating_id=rating_id)
    
    # Prüfe Berechtigung
    if not rating.is_public:
        # Nur Beteiligten dürfen private Bewertungen sehen
        if current_user.id not in [rating.bautraeger_id, rating.service_provider_id]:
            raise HTTPException(
                status_code=403,
                detail="Sie haben keine Berechtigung, diese Bewertung zu sehen"
            )
    
    return rating


@router.get("/service-provider/{service_provider_id}", response_model=List[ServiceProviderRatingResponse])
async def get_service_provider_ratings(
    service_provider_id: int,
    include_private: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[ServiceProviderRatingResponse]:
    """Holt alle Bewertungen für einen Dienstleister"""
    
    # Nur der Dienstleister selbst kann private Bewertungen sehen
    if include_private and current_user.id != service_provider_id:
        include_private = False
    
    ratings = await rating_service.get_service_provider_ratings(
        db=db,
        service_provider_id=service_provider_id,
        only_public=not include_private
    )
    
    return ratings


@router.get("/service-provider/{service_provider_id}/summary", response_model=ServiceProviderRatingSummary)
async def get_service_provider_rating_summary(
    service_provider_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ServiceProviderRatingSummary:
    """Holt Bewertungszusammenfassung für einen Dienstleister"""
    
    summary = await rating_service.get_service_provider_rating_summary(
        db=db,
        service_provider_id=service_provider_id
    )
    
    return summary


@router.get("/service-provider/{service_provider_id}/aggregated", response_model=ServiceProviderAggregatedRatingResponse)
async def get_service_provider_aggregated_rating(
    service_provider_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ServiceProviderAggregatedRatingResponse:
    """Holt aggregierte Bewertung für einen Service Provider (sehr performant)"""
    
    aggregated_rating = await rating_service.get_service_provider_aggregated_rating(
        db=db,
        service_provider_id=service_provider_id
    )
    
    if not aggregated_rating:
        # Fallback: Erstelle leeren Aggregat-Eintrag
        from ..models import ServiceProviderRatingAggregate
        aggregated_rating = ServiceProviderRatingAggregate(
            service_provider_id=service_provider_id,
            total_ratings=0,
            avg_quality_rating=0.0,
            avg_timeliness_rating=0.0,
            avg_communication_rating=0.0,
            avg_value_rating=0.0,
            avg_overall_rating=0.0
        )
    
    return aggregated_rating


@router.get("/milestone/{milestone_id}/invoice-check", response_model=RatingCheckResponse)
async def check_invoice_viewable(
    milestone_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> RatingCheckResponse:
    """Prüft ob Rechnung angesehen werden kann"""
    
    # Nur Bauträger können bewerten (PRIVATE oder PROFESSIONAL, nicht SERVICE_PROVIDER)
    if current_user.user_type == UserType.SERVICE_PROVIDER:
        # Dienstleister können ihre eigenen Rechnungen immer sehen
        return RatingCheckResponse(
            can_view_invoice=True,
            rating_required=False,
            rating_exists=False
        )
    
    # Prüfe ob Bewertung existiert
    can_view = await rating_service.check_invoice_viewable(
        db=db,
        milestone_id=milestone_id,
        bautraeger_id=current_user.id
    )
    
    return RatingCheckResponse(
        can_view_invoice=can_view,
        rating_required=not can_view,
        rating_exists=can_view
    )