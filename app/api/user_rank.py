"""
API-Endpoint für aktuellen Benutzer-Rang
Bietet einfachen Zugriff auf den Rang des eingeloggten Benutzers
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.user import User
from app.services.gamification_service import GamificationService
from app.schemas.gamification import UserRankResponse
from app.api.deps import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/my-rank", response_model=UserRankResponse)
async def get_my_rank(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Gibt den aktuellen Rang des eingeloggten Benutzers zurück
    """
    try:
        # Lade Benutzer mit aktuellen Daten
        user_result = await db.execute(
            select(User).where(User.id == current_user.id)
        )
        user = user_result.scalars().first()
        
        if not user:
            raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")
        
        completed_count = user.completed_offers_count or 0
        current_rank = GamificationService.get_rank_for_count(completed_count)
        next_rank = GamificationService.get_next_rank(completed_count)
        progress = GamificationService.get_progress_to_next_rank(completed_count)
        
        return UserRankResponse(
            user_id=user.id,
            user_name=f"{user.first_name} {user.last_name}",
            company_name=user.company_name,
            completed_count=completed_count,
            current_rank={
                'key': current_rank.key,
                'title': current_rank.title,
                'emoji': current_rank.emoji,
                'description': current_rank.description,
                'min_count': current_rank.min_count
            },
            next_rank={
                'key': next_rank.key,
                'title': next_rank.title,
                'emoji': next_rank.emoji,
                'description': next_rank.description,
                'min_count': next_rank.min_count
            } if next_rank else None,
            progress=progress,
            rank_updated_at=user.rank_updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[USER_RANK_API] Fehler beim Abrufen des Benutzer-Rangs: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Abrufen des Benutzer-Rangs")
