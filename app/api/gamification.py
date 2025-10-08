"""
API-Endpoints für Gamification-System
Bietet Zugriff auf Rang-System und Leaderboards
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.core.database import get_db
from app.models.user import User
from app.services.gamification_service import GamificationService
from app.schemas.gamification import (
    RankInfoResponse,
    LeaderboardResponse,
    RankStatisticsResponse,
    UserRankResponse
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gamification", tags=["gamification"])


@router.get("/ranks", response_model=RankStatisticsResponse)
async def get_rank_system_info():
    """
    Gibt Informationen über das Rang-System zurück
    """
    try:
        statistics = GamificationService.get_rank_statistics()
        return RankStatisticsResponse(**statistics)
    except Exception as e:
        logger.error(f"[GAMIFICATION_API] Fehler beim Abrufen der Rang-Statistiken: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Abrufen der Rang-Statistiken")


@router.get("/user/{user_id}/rank", response_model=UserRankResponse)
async def get_user_rank(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Gibt den aktuellen Rang eines Benutzers zurück
    """
    try:
        # Lade Benutzer
        user_result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalars().first()
        
        if not user:
            raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")
        
        completed_count = user.completed_offers_count or 0
        current_rank = GamificationService.get_rank_for_count(completed_count)
        next_rank = GamificationService.get_next_rank(completed_count)
        progress = GamificationService.get_progress_to_next_rank(completed_count)
        
        return UserRankResponse(
            user_id=user_id,
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
        logger.error(f"[GAMIFICATION_API] Fehler beim Abrufen des Benutzer-Rangs: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Abrufen des Benutzer-Rangs")


@router.post("/user/{user_id}/update-rank", response_model=UserRankResponse)
async def update_user_rank(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Aktualisiert den Rang eines Benutzers manuell
    """
    try:
        rank_info = await GamificationService.update_user_rank(db, user_id)
        
        if not rank_info:
            raise HTTPException(status_code=404, detail="Benutzer nicht gefunden oder Fehler beim Aktualisieren")
        
        # Lade Benutzer für zusätzliche Informationen
        user_result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalars().first()
        
        return UserRankResponse(
            user_id=user_id,
            user_name=f"{user.first_name} {user.last_name}",
            company_name=user.company_name,
            completed_count=rank_info['completed_count'],
            current_rank=rank_info['current_rank'],
            next_rank=rank_info['next_rank'],
            progress=rank_info['progress'],
            rank_changed=rank_info['rank_changed'],
            rank_updated_at=user.rank_updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[GAMIFICATION_API] Fehler beim Aktualisieren des Benutzer-Rangs: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Aktualisieren des Benutzer-Rangs")


@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    limit: int = Query(10, ge=1, le=50, description="Anzahl Einträge in der Rangliste"),
    db: AsyncSession = Depends(get_db)
):
    """
    Gibt die Rangliste der besten Dienstleister zurück
    """
    try:
        # Lade alle Dienstleister mit completed_offers_count > 0
        users_result = await db.execute(
            select(User)
            .where(
                User.user_role == 'DIENSTLEISTER',
                User.completed_offers_count > 0
            )
            .order_by(User.completed_offers_count.desc())
            .limit(limit)
        )
        users = users_result.scalars().all()
        
        leaderboard = GamificationService.get_rank_leaderboard(users, limit)
        
        return LeaderboardResponse(
            leaderboard=leaderboard,
            total_count=len(leaderboard),
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"[GAMIFICATION_API] Fehler beim Abrufen der Rangliste: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Abrufen der Rangliste")


@router.get("/rank/{rank_key}", response_model=RankInfoResponse)
async def get_rank_info(rank_key: str):
    """
    Gibt Informationen über einen spezifischen Rang zurück
    """
    try:
        # Finde den Rang
        rank = None
        for r in GamificationService.RANKS:
            if r.key == rank_key:
                rank = r
                break
        
        if not rank:
            raise HTTPException(status_code=404, detail="Rang nicht gefunden")
        
        return RankInfoResponse(
            key=rank.key,
            title=rank.title,
            emoji=rank.emoji,
            description=rank.description,
            min_count=rank.min_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[GAMIFICATION_API] Fehler beim Abrufen der Rang-Informationen: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Abrufen der Rang-Informationen")


@router.get("/users/rank-distribution")
async def get_rank_distribution(db: AsyncSession = Depends(get_db)):
    """
    Gibt die Verteilung der Ränge über alle Dienstleister zurück
    """
    try:
        # Lade alle Dienstleister
        users_result = await db.execute(
            select(User).where(User.user_role == 'DIENSTLEISTER')
        )
        users = users_result.scalars().all()
        
        # Gruppiere nach Rängen
        rank_distribution = {}
        for rank in GamificationService.RANKS:
            rank_distribution[rank.key] = {
                'title': rank.title,
                'emoji': rank.emoji,
                'min_count': rank.min_count,
                'count': 0
            }
        
        for user in users:
            completed_count = user.completed_offers_count or 0
            current_rank = GamificationService.get_rank_for_count(completed_count)
            rank_distribution[current_rank.key]['count'] += 1
        
        return {
            'distribution': rank_distribution,
            'total_service_providers': len(users)
        }
        
    except Exception as e:
        logger.error(f"[GAMIFICATION_API] Fehler beim Abrufen der Rang-Verteilung: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Abrufen der Rang-Verteilung")
