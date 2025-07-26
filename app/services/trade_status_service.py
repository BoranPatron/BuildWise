"""
Trade Status Service für BuildWise
Handhabt Status-Tracking für Gewerke und Angebote in der Dienstleister-Ansicht
"""

import logging
from typing import Optional, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from datetime import datetime

from ..models.quote import Quote, QuoteStatus
from ..models.milestone import Milestone
from ..models.cost_position import CostPosition

logger = logging.getLogger(__name__)


class TradeStatusService:
    """Service für Trade Status Tracking"""
    
    @staticmethod
    async def check_table_exists(db: AsyncSession, table_name: str) -> bool:
        """Prüft, ob eine Tabelle existiert"""
        try:
            check_query = text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = '{table_name}'
                );
            """)
            
            result = await db.execute(check_query)
            return result.scalar()
            
        except Exception as e:
            logger.error(f"Fehler beim Prüfen der Tabelle {table_name}: {e}")
            return False
    
    @staticmethod
    async def create_trade_status_table(db: AsyncSession) -> bool:
        """Erstellt die trade_status_tracking Tabelle falls sie nicht existiert"""
        try:
            # Prüfe ob Tabelle existiert
            if await TradeStatusService.check_table_exists(db, 'trade_status_tracking'):
                logger.info("trade_status_tracking Tabelle existiert bereits")
                return True
            
            # Erstelle Tabelle
            create_table = text("""
                CREATE TABLE IF NOT EXISTS trade_status_tracking (
                    id SERIAL PRIMARY KEY,
                    milestone_id INTEGER,
                    service_provider_id INTEGER,
                    quote_id INTEGER,
                    status VARCHAR(50) NOT NULL DEFAULT 'available',
                    quote_submitted_at TIMESTAMP,
                    quote_accepted_at TIMESTAMP,
                    quote_rejected_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            await db.execute(create_table)
            
            # Erstelle Indizes
            create_indexes = text("""
                CREATE INDEX IF NOT EXISTS idx_trade_status_milestone ON trade_status_tracking(milestone_id);
                CREATE INDEX IF NOT EXISTS idx_trade_status_provider ON trade_status_tracking(service_provider_id);
                CREATE INDEX IF NOT EXISTS idx_trade_status_quote ON trade_status_tracking(quote_id);
                CREATE INDEX IF NOT EXISTS idx_trade_status_status ON trade_status_tracking(status);
            """)
            
            await db.execute(create_indexes)
            await db.commit()
            
            logger.info("trade_status_tracking Tabelle erfolgreich erstellt")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Erstellen der trade_status_tracking Tabelle: {e}")
            await db.rollback()
            return False
    
    @staticmethod
    async def get_trade_status_for_user_safe(
        db: AsyncSession,
        service_provider_id: int
    ) -> List[Dict]:
        """
        Sichere Version: Holt den Trade Status für einen Dienstleister
        
        Args:
            db: Datenbank-Session
            service_provider_id: ID des Dienstleisters
            
        Returns:
            Liste der Trade Status Einträge oder leere Liste bei Fehler
        """
        try:
            # Prüfe ob Tabelle existiert
            if not await TradeStatusService.check_table_exists(db, 'trade_status_tracking'):
                logger.warning("trade_status_tracking Tabelle existiert nicht - erstelle sie...")
                if not await TradeStatusService.create_trade_status_table(db):
                    logger.error("Konnte trade_status_tracking Tabelle nicht erstellen")
                    return []
            
            # Sichere Abfrage mit Fehlerbehandlung
            query = text("""
                SELECT 
                    milestone_id, 
                    status, 
                    quote_id, 
                    quote_submitted_at, 
                    quote_accepted_at, 
                    quote_rejected_at
                FROM trade_status_tracking 
                WHERE service_provider_id = :service_provider_id
            """)
            
            result = await db.execute(query, {'service_provider_id': service_provider_id})
            rows = result.fetchall()
            
            # Konvertiere zu Dictionary-Liste
            status_list = []
            for row in rows:
                status_dict = {
                    'milestone_id': row[0],
                    'status': row[1],
                    'quote_id': row[2],
                    'quote_submitted_at': row[3].isoformat() if row[3] else None,
                    'quote_accepted_at': row[4].isoformat() if row[4] else None,
                    'quote_rejected_at': row[5].isoformat() if row[5] else None
                }
                status_list.append(status_dict)
            
            logger.info(f"Trade Status für Dienstleister {service_provider_id} abgerufen: {len(status_list)} Einträge")
            return status_list
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen des Trade Status für Dienstleister {service_provider_id}: {e}")
            return []
    
    @staticmethod
    async def update_trade_status(
        db: AsyncSession,
        milestone_id: int,
        service_provider_id: int,
        quote_id: int,
        status: str
    ) -> bool:
        """
        Aktualisiert den Status eines Gewerks für einen Dienstleister
        
        Args:
            db: Datenbank-Session
            milestone_id: ID des Gewerks
            service_provider_id: ID des Dienstleisters
            quote_id: ID des Angebots
            status: Neuer Status (available, submitted, accepted, rejected)
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            # Prüfe ob Tabelle existiert
            if not await TradeStatusService.check_table_exists(db, 'trade_status_tracking'):
                logger.warning("trade_status_tracking Tabelle existiert nicht - erstelle sie...")
                if not await TradeStatusService.create_trade_status_table(db):
                    logger.error("Konnte trade_status_tracking Tabelle nicht erstellen")
                    return False
            
            # Prüfe ob bereits ein Eintrag existiert
            check_query = text("""
                SELECT id FROM trade_status_tracking 
                WHERE milestone_id = :milestone_id AND service_provider_id = :service_provider_id
            """)
            
            result = await db.execute(check_query, {
                'milestone_id': milestone_id,
                'service_provider_id': service_provider_id
            })
            existing = result.fetchone()
            
            if existing:
                # Update bestehenden Eintrag
                update_query = text("""
                    UPDATE trade_status_tracking 
                    SET status = :status, quote_id = :quote_id, updated_at = CURRENT_TIMESTAMP
                    WHERE milestone_id = :milestone_id AND service_provider_id = :service_provider_id
                """)
                
                await db.execute(update_query, {
                    'status': status,
                    'quote_id': quote_id,
                    'milestone_id': milestone_id,
                    'service_provider_id': service_provider_id
                })
            else:
                # Erstelle neuen Eintrag
                insert_query = text("""
                    INSERT INTO trade_status_tracking 
                    (milestone_id, service_provider_id, quote_id, status, created_at, updated_at)
                    VALUES (:milestone_id, :service_provider_id, :quote_id, :status, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """)
                
                await db.execute(insert_query, {
                    'milestone_id': milestone_id,
                    'service_provider_id': service_provider_id,
                    'quote_id': quote_id,
                    'status': status
                })
            
            await db.commit()
            logger.info(f"Trade Status aktualisiert: Milestone {milestone_id}, Provider {service_provider_id}, Status {status}")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren des Trade Status: {str(e)}")
            await db.rollback()
            return False
    
    @staticmethod
    async def get_trade_status_for_user(
        db: AsyncSession,
        milestone_id: int,
        service_provider_id: int
    ) -> Optional[Dict]:
        """
        Holt den Trade Status für einen spezifischen Dienstleister und Gewerk
        
        Args:
            db: Datenbank-Session
            milestone_id: ID des Gewerks
            service_provider_id: ID des Dienstleisters
            
        Returns:
            Trade Status Dictionary oder None
        """
        try:
            # Prüfe ob Tabelle existiert
            if not await TradeStatusService.check_table_exists(db, 'trade_status_tracking'):
                logger.warning("trade_status_tracking Tabelle existiert nicht")
                return None
            
            query = text("""
                SELECT 
                    milestone_id, 
                    status, 
                    quote_id, 
                    quote_submitted_at, 
                    quote_accepted_at, 
                    quote_rejected_at
                FROM trade_status_tracking 
                WHERE milestone_id = :milestone_id AND service_provider_id = :service_provider_id
            """)
            
            result = await db.execute(query, {
                'milestone_id': milestone_id,
                'service_provider_id': service_provider_id
            })
            row = result.fetchone()
            
            if row:
                return {
                    'milestone_id': row[0],
                    'status': row[1],
                    'quote_id': row[2],
                    'quote_submitted_at': row[3].isoformat() if row[3] else None,
                    'quote_accepted_at': row[4].isoformat() if row[4] else None,
                    'quote_rejected_at': row[5].isoformat() if row[5] else None
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen des Trade Status: {str(e)}")
            return None

    @staticmethod
    async def get_accepted_trades_for_milestone(
        db: AsyncSession,
        milestone_id: int
    ) -> List[Dict]:
        """
        Holt alle akzeptierten Trades für ein Gewerk
        
        Args:
            db: Datenbank-Session
            milestone_id: ID des Gewerks
            
        Returns:
            Liste der akzeptierten Trades
        """
        try:
            # Prüfe ob Tabelle existiert
            if not await TradeStatusService.check_table_exists(db, 'trade_status_tracking'):
                logger.warning("trade_status_tracking Tabelle existiert nicht")
                return []
            
            query = text("""
                SELECT 
                    service_provider_id, 
                    quote_id, 
                    quote_accepted_at
                FROM trade_status_tracking 
                WHERE milestone_id = :milestone_id AND status = 'accepted'
            """)
            
            result = await db.execute(query, {'milestone_id': milestone_id})
            rows = result.fetchall()
            
            accepted_trades = []
            for row in rows:
                accepted_trades.append({
                    'service_provider_id': row[0],
                    'quote_id': row[1],
                    'accepted_at': row[2].isoformat() if row[2] else None
                })
            
            return accepted_trades
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der akzeptierten Trades: {str(e)}")
            return []

    @staticmethod
    async def sync_quote_status(
        db: AsyncSession,
        quote_id: int
    ) -> bool:
        """
        Synchronisiert den Quote Status mit dem Trade Status Tracking
        
        Args:
            db: Datenbank-Session
            quote_id: ID des Angebots
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            # Hole Quote Information
            quote_result = await db.execute(select(Quote).where(Quote.id == quote_id))
            quote = quote_result.scalar_one_or_none()
            
            if not quote:
                logger.warning(f"Quote {quote_id} nicht gefunden")
                return False
            
            # Bestimme Status basierend auf Quote Status
            status_mapping = {
                QuoteStatus.SUBMITTED: 'submitted',
                QuoteStatus.ACCEPTED: 'accepted',
                QuoteStatus.REJECTED: 'rejected',
                QuoteStatus.DRAFT: 'draft'
            }
            
            status = status_mapping.get(quote.status, 'available')
            
            # Aktualisiere Trade Status
            success = await TradeStatusService.update_trade_status(
                db=db,
                milestone_id=quote.milestone_id,
                service_provider_id=quote.service_provider_id,
                quote_id=quote.id,
                status=status
            )
            
            if success:
                logger.info(f"Quote Status für Quote {quote_id} synchronisiert")
            else:
                logger.error(f"Fehler beim Synchronisieren des Quote Status für Quote {quote_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Fehler beim Synchronisieren des Quote Status: {str(e)}")
            return False

    @staticmethod
    async def cleanup_old_status_entries(
        db: AsyncSession,
        days_old: int = 365
    ) -> int:
        """
        Bereinigt alte Status-Einträge
        
        Args:
            db: Datenbank-Session
            days_old: Anzahl Tage für Bereinigung
            
        Returns:
            Anzahl gelöschter Einträge
        """
        try:
            # Prüfe ob Tabelle existiert
            if not await TradeStatusService.check_table_exists(db, 'trade_status_tracking'):
                logger.warning("trade_status_tracking Tabelle existiert nicht")
                return 0
            
            delete_query = text("""
                DELETE FROM trade_status_tracking 
                WHERE updated_at < CURRENT_TIMESTAMP - INTERVAL ':days_old days'
            """)
            
            result = await db.execute(delete_query, {'days_old': days_old})
            deleted_count = result.rowcount
            
            await db.commit()
            logger.info(f"{deleted_count} alte Status-Einträge bereinigt")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Fehler beim Bereinigen alter Status-Einträge: {str(e)}")
            await db.rollback()
            return 0 