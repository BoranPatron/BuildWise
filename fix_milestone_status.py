#!/usr/bin/env python3
"""
Skript um den Milestone-Status zu korrigieren
"""

import asyncio
import sys
import os

# Füge das aktuelle Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.milestone import Milestone, MilestoneStatus
from sqlalchemy import text

async def fix_milestone_status():
    """Korrigiert den Milestone-Status in der Datenbank"""
    try:
        async for db in get_db():
            print("🔧 Korrigiere Milestone-Status...")
            
            # Zuerst alle aktuellen Milestones anzeigen
            stmt = text("SELECT id, title, status FROM milestones ORDER BY id")
            result = await db.execute(stmt)
            milestones = result.fetchall()
            
            print(f"📋 Gefundene Milestones: {len(milestones)}")
            for milestone in milestones:
                print(f"   Milestone {milestone.id}: {milestone.title} (Status: {milestone.status})")
            
            # Korrigiere den Status von Milestone 1
            print("\n🔧 Korrigiere Status von Milestone 1...")
            update_stmt = text("UPDATE milestones SET status = 'PLANNED' WHERE id = 1")
            await db.execute(update_stmt)
            
            # Commit der Änderungen
            await db.commit()
            print("✅ Status korrigiert")
            
            # Prüfe das Ergebnis
            stmt = text("SELECT id, title, status FROM milestones WHERE id = 1")
            result = await db.execute(stmt)
            milestone = result.fetchone()
            
            if milestone:
                print(f"✅ Milestone {milestone.id}: {milestone.title} (Status: {milestone.status})")
            else:
                print("❌ Milestone nicht gefunden")
            
            print("\n✅ Milestone-Status-Korrektur abgeschlossen")
            
    except Exception as e:
        print(f"❌ Fehler beim Korrigieren des Milestone-Status: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(fix_milestone_status()) 