"""
Gamification Service für BuildWise
Implementiert Rang-System basierend auf completed_offers_count
"""
import enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.user import User
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ServiceProviderRank(enum.Enum):
    """Ränge für Dienstleister basierend auf completed_offers_count"""
    
    # 0-9: Anfänger-Ränge
    NEULING = ("neuling", 0, "Neuling", "🏗️", "Erste Schritte im Bauwesen")
    LEHRJUNGE = ("lehrjunge", 10, "Lehrjunge", "🔨", "Lernt die Grundlagen")
    
    # 10-19: Fortgeschrittene Anfänger
    NACHBARSCHAFTSHELD = ("nachbarschaftsheld", 20, "Nachbarschaftsheld", "🏘️", "Vertrauenswürdig in der Nachbarschaft")
    HANDWERKER = ("handwerker", 30, "Handwerker", "⚒️", "Solide handwerkliche Fähigkeiten")
    
    # 20-29: Erfahrene Praktiker
    BAUPROFI = ("bauprofi", 40, "Bau-Profi", "🔧", "Professionelle Bauausführung")
    BAUSPEZIALIST = ("bauspezialist", 50, "Bau-Spezialist", "⚡", "Spezialist für komplexe Projekte")
    
    # 30-39: Experten
    BAUVISIONAER = ("bauvisionaer", 60, "Bau-Visionär", "🚀", "Visionär der Baubranche")
    BAUKOENIG = ("baukoenig", 70, "Baukönig", "👑", "Herrscht über das Bauwesen")
    
    # 40-49: Legenden
    BAULEGENDE = ("baulegende", 80, "Baulegende", "🌟", "Legende im Bauwesen")
    BAUMAGIER = ("baumagier", 90, "Bau-Magier", "✨", "Magische Baukunst")
    
    # 50+: Mythos
    BAUMYTHOS = ("baumythos", 100, "Bau-Mythos", "⚡", "Mythos des Bauwesens")
    
    def __init__(self, key: str, min_count: int, title: str, emoji: str, description: str):
        self.key = key
        self.min_count = min_count
        self.title = title
        self.emoji = emoji
        self.description = description


class GamificationService:
    """Service für Gamification und Rang-System"""
    
    # Rang-Definitionen
    RANKS = [
        ServiceProviderRank.NEULING,
        ServiceProviderRank.LEHRJUNGE,
        ServiceProviderRank.NACHBARSCHAFTSHELD,
        ServiceProviderRank.HANDWERKER,
        ServiceProviderRank.BAUPROFI,
        ServiceProviderRank.BAUSPEZIALIST,
        ServiceProviderRank.BAUVISIONAER,
        ServiceProviderRank.BAUKOENIG,
        ServiceProviderRank.BAULEGENDE,
        ServiceProviderRank.BAUMAGIER,
        ServiceProviderRank.BAUMYTHOS,
    ]
    
    @staticmethod
    def get_rank_for_count(completed_count: int) -> ServiceProviderRank:
        """
        Ermittelt den aktuellen Rang basierend auf completed_offers_count
        
        Args:
            completed_count: Anzahl abgeschlossener Angebote
            
        Returns:
            ServiceProviderRank: Aktueller Rang
        """
        # Finde den höchsten Rang, den der Benutzer erreicht hat
        current_rank = ServiceProviderRank.NEULING
        
        for rank in GamificationService.RANKS:
            if completed_count >= rank.min_count:
                current_rank = rank
            else:
                break
        
        return current_rank
    
    @staticmethod
    def get_next_rank(completed_count: int) -> Optional[ServiceProviderRank]:
        """
        Ermittelt den nächsten erreichbaren Rang
        
        Args:
            completed_count: Aktuelle Anzahl abgeschlossener Angebote
            
        Returns:
            ServiceProviderRank oder None wenn bereits höchster Rang erreicht
        """
        current_rank = GamificationService.get_rank_for_count(completed_count)
        
        # Finde den nächsten Rang
        for i, rank in enumerate(GamificationService.RANKS):
            if rank == current_rank and i + 1 < len(GamificationService.RANKS):
                return GamificationService.RANKS[i + 1]
        
        return None  # Bereits höchster Rang erreicht
    
    @staticmethod
    def get_progress_to_next_rank(completed_count: int) -> Dict[str, int]:
        """
        Berechnet den Fortschritt zum nächsten Rang
        
        Args:
            completed_count: Aktuelle Anzahl abgeschlossener Angebote
            
        Returns:
            Dict mit 'current', 'needed', 'progress_percentage'
        """
        next_rank = GamificationService.get_next_rank(completed_count)
        
        if not next_rank:
            return {
                'current': completed_count,
                'needed': 0,
                'progress_percentage': 100
            }
        
        current_rank = GamificationService.get_rank_for_count(completed_count)
        
        # Berechne Fortschritt zwischen aktuellem und nächstem Rang
        progress_needed = next_rank.min_count - current_rank.min_count
        progress_made = completed_count - current_rank.min_count
        
        progress_percentage = int((progress_made / progress_needed) * 100) if progress_needed > 0 else 100
        
        return {
            'current': completed_count,
            'needed': next_rank.min_count,
            'progress_percentage': min(progress_percentage, 100)
        }
    
    @staticmethod
    async def update_user_rank(db: AsyncSession, user_id: int) -> Dict[str, any]:
        """
        Aktualisiert den Rang eines Benutzers basierend auf completed_offers_count
        
        Args:
            db: Datenbank-Session
            user_id: ID des Benutzers
            
        Returns:
            Dict mit Rang-Informationen
        """
        try:
            # Lade Benutzer
            user_result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalars().first()
            
            if not user:
                logger.error(f"[GAMIFICATION] Benutzer {user_id} nicht gefunden")
                return {}
            
            completed_count = user.completed_offers_count or 0
            current_rank = GamificationService.get_rank_for_count(completed_count)
            next_rank = GamificationService.get_next_rank(completed_count)
            progress = GamificationService.get_progress_to_next_rank(completed_count)
            
            # Prüfe ob Rang sich geändert hat
            old_rank_key = user.current_rank_key if hasattr(user, 'current_rank_key') else None
            rank_changed = old_rank_key != current_rank.key
            
            # Aktualisiere Benutzer-Rang
            await db.execute(
                update(User)
                .where(User.id == user_id)
                .values(
                    current_rank_key=current_rank.key,
                    current_rank_title=current_rank.title,
                    rank_updated_at=datetime.now()
                )
            )
            
            await db.commit()
            
            rank_info = {
                'user_id': user_id,
                'completed_count': completed_count,
                'current_rank': {
                    'key': current_rank.key,
                    'title': current_rank.title,
                    'emoji': current_rank.emoji,
                    'description': current_rank.description,
                    'min_count': current_rank.min_count
                },
                'next_rank': {
                    'key': next_rank.key,
                    'title': next_rank.title,
                    'emoji': next_rank.emoji,
                    'description': next_rank.description,
                    'min_count': next_rank.min_count
                } if next_rank else None,
                'progress': progress,
                'rank_changed': rank_changed
            }
            
            if rank_changed:
                logger.info(f"[GAMIFICATION] Rang-Update für Benutzer {user_id}: {old_rank_key} -> {current_rank.key}")
            
            return rank_info
            
        except Exception as e:
            logger.error(f"[GAMIFICATION] Fehler beim Aktualisieren des Rangs für Benutzer {user_id}: {e}")
            await db.rollback()
            return {}
    
    @staticmethod
    def get_rank_leaderboard(users: List[User], limit: int = 10) -> List[Dict[str, any]]:
        """
        Erstellt eine Rangliste der besten Dienstleister
        
        Args:
            users: Liste der Benutzer
            limit: Maximale Anzahl Einträge
            
        Returns:
            List von Rang-Informationen sortiert nach completed_offers_count
        """
        leaderboard = []
        
        for user in users:
            if user.user_role == 'DIENSTLEISTER' and user.completed_offers_count:
                completed_count = user.completed_offers_count or 0
                current_rank = GamificationService.get_rank_for_count(completed_count)
                
                leaderboard.append({
                    'user_id': user.id,
                    'name': f"{user.first_name} {user.last_name}",
                    'company_name': user.company_name or "Freiberufler",
                    'completed_count': completed_count,
                    'rank': {
                        'key': current_rank.key,
                        'title': current_rank.title,
                        'emoji': current_rank.emoji,
                        'description': current_rank.description
                    }
                })
        
        # Sortiere nach completed_offers_count (absteigend)
        leaderboard.sort(key=lambda x: x['completed_count'], reverse=True)
        
        return leaderboard[:limit]
    
    @staticmethod
    def get_rank_statistics() -> Dict[str, any]:
        """
        Gibt Statistiken über das Rang-System zurück
        
        Returns:
            Dict mit Rang-Statistiken
        """
        return {
            'total_ranks': len(GamificationService.RANKS),
            'highest_rank': {
                'key': ServiceProviderRank.BAUMYTHOS.key,
                'title': ServiceProviderRank.BAUMYTHOS.title,
                'min_count': ServiceProviderRank.BAUMYTHOS.min_count
            },
            'rank_progression': [
                {
                    'rank': rank.title,
                    'emoji': rank.emoji,
                    'min_count': rank.min_count,
                    'description': rank.description
                }
                for rank in GamificationService.RANKS
            ]
        }


