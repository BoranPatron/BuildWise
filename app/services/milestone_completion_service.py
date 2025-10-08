"""
Service für Milestone-Completion-Logik
Inkrementiert completed_offers_count für alle betroffenen Dienstleister
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from app.models.milestone import Milestone
from app.models.quote import Quote, QuoteStatus
from app.models.user import User
from typing import List, Set
import logging

logger = logging.getLogger(__name__)


class MilestoneCompletionService:
    """Service für Milestone-Completion-Logik"""
    
    @staticmethod
    async def increment_completed_offers_count(db: AsyncSession, milestone_id: int) -> bool:
        """
        Inkrementiert completed_offers_count für alle Dienstleister, die an diesem Milestone beteiligt waren
        
        Args:
            db: Datenbank-Session
            milestone_id: ID des abgeschlossenen Milestones
            
        Returns:
            bool: True wenn erfolgreich, False bei Fehler
        """
        try:
            logger.info(f"[MILESTONE_COMPLETION] Starte completed_offers_count Inkrementierung für Milestone {milestone_id}")
            
            # 1. Lade das Milestone mit allen relevanten Daten
            milestone_result = await db.execute(
                select(Milestone)
                .options(selectinload(Milestone.quotes))
                .where(Milestone.id == milestone_id)
            )
            milestone = milestone_result.scalars().first()
            
            if not milestone:
                logger.error(f"[MILESTONE_COMPLETION] Milestone {milestone_id} nicht gefunden")
                return False
            
            # 2. Sammle alle betroffenen Dienstleister
            affected_service_providers: Set[int] = set()
            
            # Dienstleister der akzeptierte Angebote hat
            if milestone.accepted_by:
                affected_service_providers.add(milestone.accepted_by)
                logger.info(f"[MILESTONE_COMPLETION] Akzeptierter Dienstleister gefunden: {milestone.accepted_by}")
            
            # Alle Dienstleister mit eingereichten Angeboten für dieses Milestone
            quotes_result = await db.execute(
                select(Quote.service_provider_id)
                .where(
                    Quote.milestone_id == milestone_id,
                    Quote.status.in_([QuoteStatus.SUBMITTED.value, QuoteStatus.ACCEPTED.value])
                )
            )
            quote_service_providers = quotes_result.scalars().all()
            
            for service_provider_id in quote_service_providers:
                affected_service_providers.add(service_provider_id)
                logger.info(f"[MILESTONE_COMPLETION] Dienstleister mit Angebot gefunden: {service_provider_id}")
            
            if not affected_service_providers:
                logger.warning(f"[MILESTONE_COMPLETION] Keine betroffenen Dienstleister für Milestone {milestone_id} gefunden")
                return True  # Nicht unbedingt ein Fehler, könnte ein Milestone ohne Angebote sein
            
            # 3. Inkrementiere completed_offers_count für alle betroffenen Dienstleister
            updated_count = 0
            for service_provider_id in affected_service_providers:
                try:
                    # Prüfe ob der Dienstleister existiert
                    user_result = await db.execute(
                        select(User).where(User.id == service_provider_id)
                    )
                    user = user_result.scalars().first()
                    
                    if not user:
                        logger.warning(f"[MILESTONE_COMPLETION] Dienstleister {service_provider_id} nicht gefunden, überspringe")
                        continue
                    
                    # Inkrementiere completed_offers_count
                    # Verwende COALESCE um NULL-Werte zu behandeln
                    await db.execute(
                        update(User)
                        .where(User.id == service_provider_id)
                        .values(
                            completed_offers_count=User.completed_offers_count + 1
                        )
                    )
                    
                    updated_count += 1
                    logger.info(f"[MILESTONE_COMPLETION] completed_offers_count für Dienstleister {service_provider_id} inkrementiert")
                    
                    # Aktualisiere Rang des Dienstleisters
                    try:
                        from .gamification_service import GamificationService
                        rank_info = await GamificationService.update_user_rank(db, service_provider_id)
                        if rank_info.get('rank_changed'):
                            logger.info(f"[MILESTONE_COMPLETION] Rang-Update für Dienstleister {service_provider_id}: {rank_info['current_rank']['title']}")
                    except Exception as rank_error:
                        logger.warning(f"[MILESTONE_COMPLETION] Fehler beim Rang-Update für Dienstleister {service_provider_id}: {rank_error}")
                        # Rang-Update-Fehler ist nicht kritisch
                    
                except Exception as e:
                    logger.error(f"[MILESTONE_COMPLETION] Fehler beim Inkrementieren für Dienstleister {service_provider_id}: {e}")
                    continue
            
            # 4. Commit der Änderungen
            await db.commit()
            
            logger.info(f"[MILESTONE_COMPLETION] Erfolgreich abgeschlossen: {updated_count} Dienstleister aktualisiert für Milestone {milestone_id}")
            return True
            
        except Exception as e:
            logger.error(f"[MILESTONE_COMPLETION] Fehler beim Inkrementieren der completed_offers_count: {e}")
            await db.rollback()
            return False
    
    @staticmethod
    async def get_affected_service_providers(db: AsyncSession, milestone_id: int) -> List[int]:
        """
        Ermittelt alle Dienstleister, die von einem Milestone-Completion betroffen sind
        
        Args:
            db: Datenbank-Session
            milestone_id: ID des Milestones
            
        Returns:
            List[int]: Liste der betroffenen Dienstleister-IDs
        """
        try:
            affected_service_providers: Set[int] = set()
            
            # Lade Milestone
            milestone_result = await db.execute(
                select(Milestone).where(Milestone.id == milestone_id)
            )
            milestone = milestone_result.scalars().first()
            
            if milestone and milestone.accepted_by:
                affected_service_providers.add(milestone.accepted_by)
            
            # Lade alle Dienstleister mit Angeboten
            quotes_result = await db.execute(
                select(Quote.service_provider_id)
                .where(
                    Quote.milestone_id == milestone_id,
                    Quote.status.in_([QuoteStatus.SUBMITTED.value, QuoteStatus.ACCEPTED.value])
                )
            )
            quote_service_providers = quotes_result.scalars().all()
            
            for service_provider_id in quote_service_providers:
                affected_service_providers.add(service_provider_id)
            
            return list(affected_service_providers)
            
        except Exception as e:
            logger.error(f"[MILESTONE_COMPLETION] Fehler beim Ermitteln der betroffenen Dienstleister: {e}")
            return []
    
    @staticmethod
    async def reset_completed_offers_count(db: AsyncSession, user_id: int) -> bool:
        """
        Setzt completed_offers_count für einen Benutzer auf 0 zurück
        
        Args:
            db: Datenbank-Session
            user_id: ID des Benutzers
            
        Returns:
            bool: True wenn erfolgreich
        """
        try:
            await db.execute(
                update(User)
                .where(User.id == user_id)
                .values(completed_offers_count=0)
            )
            await db.commit()
            
            logger.info(f"[MILESTONE_COMPLETION] completed_offers_count für Benutzer {user_id} auf 0 zurückgesetzt")
            return True
            
        except Exception as e:
            logger.error(f"[MILESTONE_COMPLETION] Fehler beim Zurücksetzen für Benutzer {user_id}: {e}")
            await db.rollback()
            return False
