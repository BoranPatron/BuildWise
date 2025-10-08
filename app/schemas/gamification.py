"""
Pydantic-Schemas für Gamification-System
Definiert die Datenstrukturen für API-Requests und -Responses
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class RankInfo(BaseModel):
    """Informationen über einen Rang"""
    key: str
    title: str
    emoji: str
    description: str
    min_count: int


class ProgressInfo(BaseModel):
    """Fortschrittsinformationen zum nächsten Rang"""
    current: int
    needed: int
    progress_percentage: int


class UserRankResponse(BaseModel):
    """Response für Benutzer-Rang-Informationen"""
    user_id: int
    user_name: str
    company_name: Optional[str] = None
    completed_count: int
    current_rank: RankInfo
    next_rank: Optional[RankInfo] = None
    progress: ProgressInfo
    rank_changed: Optional[bool] = None
    rank_updated_at: Optional[datetime] = None


class LeaderboardEntry(BaseModel):
    """Eintrag in der Rangliste"""
    user_id: int
    name: str
    company_name: str
    completed_count: int
    rank: RankInfo


class LeaderboardResponse(BaseModel):
    """Response für Rangliste"""
    leaderboard: List[LeaderboardEntry]
    total_count: int
    limit: int


class RankStatisticsResponse(BaseModel):
    """Response für Rang-System-Statistiken"""
    total_ranks: int
    highest_rank: RankInfo
    rank_progression: List[RankInfo]


class RankInfoResponse(BaseModel):
    """Response für spezifische Rang-Informationen"""
    key: str
    title: str
    emoji: str
    description: str
    min_count: int


class RankDistributionResponse(BaseModel):
    """Response für Rang-Verteilung"""
    distribution: Dict[str, Dict[str, Any]]
    total_service_providers: int
