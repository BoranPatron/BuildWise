import asyncio
import logging
from datetime import datetime, time
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ..core.database import get_db
from ..services.credit_service import CreditService
from ..services.geo_service import geo_service
from ..models.project import Project
from sqlalchemy import select

logger = logging.getLogger(__name__)


class CreditScheduler:
    """Scheduler für tägliche Credit-Abzüge"""
    
    def __init__(self):
        self.is_running = False
        self.task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Startet den Scheduler"""
        if self.is_running:
            logger.warning("Credit-Scheduler läuft bereits")
            return
        
        self.is_running = True
        self.task = asyncio.create_task(self._run_scheduler())
        logger.info("Credit-Scheduler gestartet")
    
    async def stop(self):
        """Stoppt den Scheduler mit verbesserter Fehlerbehandlung"""
        if not self.is_running:
            logger.info("Credit-Scheduler war bereits gestoppt")
            return
        
        logger.info("Stoppe Credit-Scheduler...")
        self.is_running = False
        
        if self.task and not self.task.done():
            logger.info("Cancelling Scheduler-Task...")
            self.task.cancel()
            
            try:
                # Warte auf Task-Completion mit Timeout
                await asyncio.wait_for(self.task, timeout=3.0)
                logger.info("Scheduler-Task erfolgreich beendet")
            except asyncio.CancelledError:
                logger.info("Scheduler-Task wurde abgebrochen (erwartet)")
            except asyncio.TimeoutError:
                logger.warning("Scheduler-Task Shutdown-Timeout erreicht")
            except Exception as e:
                logger.warning(f"Unerwarteter Fehler beim Scheduler-Shutdown: {e}")
        
        logger.info("Credit-Scheduler gestoppt")
    
    async def _run_scheduler(self):
        """Hauptschleife des Schedulers mit verbesserter Cancellation-Behandlung"""
        try:
            while self.is_running:
                try:
                    # Warte bis zur nächsten Ausführungszeit (täglich um 02:00 Uhr)
                    now = datetime.now()
                    next_run = now.replace(hour=2, minute=0, second=0, microsecond=0)
                    
                    if now >= next_run:
                        next_run = next_run.replace(day=next_run.day + 1)
                    
                    wait_seconds = (next_run - now).total_seconds()
                    logger.info(f"Nächste Credit-Abzug-Ausführung: {next_run} (in {wait_seconds:.0f} Sekunden)")
                    
                    # Verwende asyncio.sleep mit regelmäßiger Prüfung auf Cancellation
                    await asyncio.sleep(min(wait_seconds, 300))  # Max 5 Minuten Sleep
                    
                    # Prüfe ob wir noch laufen sollen (nach dem Sleep)
                    if not self.is_running:
                        logger.info("Scheduler wurde gestoppt während Sleep")
                        break
                    
                    # Führe tägliche Credit-Abzüge aus
                    await self._process_daily_deductions()

                    # Ergänzung: Periodisches Geocoding-Update für Projekte ohne Koordinaten
                    await self._update_project_geocoding_batch()
                    
                except asyncio.CancelledError:
                    logger.info("Credit-Scheduler wurde abgebrochen")
                    break
                except Exception as e:
                    if self.is_running:  # Nur loggen wenn wir noch laufen sollen
                        logger.error(f"Fehler im Credit-Scheduler: {e}")
                        # Warte 1 Stunde bei Fehlern, aber prüfe regelmäßig ob wir stoppen sollen
                        for _ in range(360):  # 360 * 10 = 3600 Sekunden = 1 Stunde
                            if not self.is_running:
                                break
                            try:
                                await asyncio.sleep(10)
                            except asyncio.CancelledError:
                                logger.info("Scheduler wurde während Fehler-Wartezeit abgebrochen")
                                break
                    else:
                        break
        except asyncio.CancelledError:
            logger.info("Credit-Scheduler Hauptschleife wurde abgebrochen")
        except Exception as e:
            logger.error(f"Unerwarteter Fehler in Credit-Scheduler Hauptschleife: {e}")
        finally:
            logger.info("Credit-Scheduler Hauptschleife beendet")
    
    async def _process_daily_deductions(self):
        """Verarbeitet tägliche Credit-Abzüge"""
        try:
            logger.info("Starte tägliche Credit-Abzüge...")
            
            # Erstelle neue Datenbank-Session
            async for db in get_db():
                try:
                    result = await CreditService.process_all_daily_deductions(db)
                    
                    logger.info(
                        f"Tägliche Credit-Abzüge abgeschlossen: "
                        f"{result['processed_users']} User verarbeitet, "
                        f"{result['downgraded_users']} downgraded"
                    )
                    
                except Exception as e:
                    logger.error(f"Fehler bei täglichen Credit-Abzügen: {e}")
                finally:
                    await db.close()
                    
        except Exception as e:
            logger.error(f"Fehler beim Verarbeiten der täglichen Credit-Abzüge: {e}")

    async def _update_project_geocoding_batch(self):
        """Aktualisiert Geocoding-Daten für Projekte ohne gespeicherte Koordinaten.
        Läuft täglich im Scheduler nach den Credit-Abzügen.
        """
        try:
            logger.info("Starte tägliches Projekt-Geocoding-Update (Batch)...")
            async for db in get_db():
                try:
                    # Wähle eine überschaubare Menge pro Lauf, z. B. 100 Projekte ohne Koordinaten
                    result = await db.execute(
                        select(Project).where(
                            (getattr(Project, 'address_latitude') == None) |
                            (getattr(Project, 'address_longitude') == None)
                        ).limit(100)
                    )
                    projects = result.scalars().all()

                    updated = 0
                    for project in projects:
                        if await geo_service.update_project_geocoding(db, project.id):
                            updated += 1

                    logger.info(f"Projekt-Geocoding-Update abgeschlossen: {updated} Projekte aktualisiert")
                except Exception as e:
                    logger.error(f"Fehler beim Projekt-Geocoding-Update: {e}")
                finally:
                    await db.close()
        except Exception as e:
            logger.error(f"Fehler im Geocoding-Batch: {e}")


# Globaler Scheduler-Instance
credit_scheduler = CreditScheduler()


async def start_credit_scheduler():
    """Startet den Credit-Scheduler (für FastAPI Startup Event)"""
    await credit_scheduler.start()


async def stop_credit_scheduler():
    """Stoppt den Credit-Scheduler (für FastAPI Shutdown Event)"""
    await credit_scheduler.stop()


# Manuelle Ausführung für Tests
async def run_daily_deductions_manual():
    """Manuelle Ausführung der täglichen Credit-Abzüge (für Tests/Admin)"""
    try:
        logger.info("Manuelle Ausführung der täglichen Credit-Abzüge...")
        
        async for db in get_db():
            try:
                result = await CreditService.process_all_daily_deductions(db)
                
                logger.info(
                    f"Manuelle Credit-Abzüge abgeschlossen: "
                    f"{result['processed_users']} User verarbeitet, "
                    f"{result['downgraded_users']} downgraded"
                )
                
                return result
                
            except Exception as e:
                logger.error(f"Fehler bei manuellen Credit-Abzügen: {e}")
                raise
            finally:
                await db.close()
                
    except Exception as e:
        logger.error(f"Fehler bei manueller Ausführung der Credit-Abzüge: {e}")
        raise 