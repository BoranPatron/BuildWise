"""
Background Task für automatische Archivierung von completed Tasks
Läuft täglich und archiviert Tasks die seit 14 Tagen completed sind
"""

import asyncio
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db_session
from ..services.task_archiving_service import archive_completed_tasks

logger = logging.getLogger(__name__)


async def run_task_archiver():
    """Führe die Task-Archivierung aus"""
    try:
        logger.info("🗂️ Starte automatische Task-Archivierung...")
        
        async with get_db_session() as db:
            archived_count = await archive_completed_tasks(db)
            
        if archived_count > 0:
            logger.info(f"[SUCCESS] {archived_count} Tasks automatisch archiviert")
        else:
            logger.info("ℹ️ Keine Tasks zum Archivieren gefunden")
            
        return archived_count
        
    except Exception as e:
        logger.error(f"[ERROR] Fehler bei Task-Archivierung: {e}")
        return 0


async def schedule_task_archiver():
    """Plane die tägliche Ausführung der Task-Archivierung"""
    while True:
        try:
            # Führe Archivierung aus
            await run_task_archiver()
            
            # Warte 24 Stunden bis zur nächsten Ausführung
            await asyncio.sleep(24 * 60 * 60)  # 24 Stunden
            
        except Exception as e:
            logger.error(f"[ERROR] Fehler im Task-Archiver Scheduler: {e}")
            # Warte 1 Stunde bei Fehler, dann versuche es erneut
            await asyncio.sleep(60 * 60)


def start_task_archiver_background():
    """Starte den Task-Archiver als Background-Task"""
    logger.info("[INFO] Starte Task-Archiver Background-Service...")
    
    # Erstelle und starte den Background-Task
    loop = asyncio.get_event_loop()
    loop.create_task(schedule_task_archiver())
    
    logger.info("[SUCCESS] Task-Archiver Background-Service gestartet")


if __name__ == "__main__":
    # Für manuellen Test
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_task_archiver())