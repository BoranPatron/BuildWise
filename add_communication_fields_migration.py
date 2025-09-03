#!/usr/bin/env python3
"""
Migration: Fügt neue Felder für Ausschreibungs-Kommunikation zur milestone_progress Tabelle hinzu
"""

import asyncio
import sys
import os

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.core.config import get_settings

async def run_migration():
    """Führt die Migration aus"""
    settings = get_settings()
    
    # Erstelle Engine für SQLite
    engine = create_async_engine(
        settings.database_url,
        echo=True
    )
    
    # Erstelle Session
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            print("🔄 Starte Migration: Kommunikations-Felder für milestone_progress")
            
            # 1. Prüfe ob Spalten bereits existieren
            result = await session.execute(text("PRAGMA table_info(milestone_progress)"))
            columns = [row[1] for row in result]
            
            # 2. Füge is_tender_communication Feld hinzu (falls nicht vorhanden)
            if 'is_tender_communication' not in columns:
                await session.execute(text("""
                    ALTER TABLE milestone_progress 
                    ADD COLUMN is_tender_communication BOOLEAN DEFAULT 0
                """))
                print("✅ Spalte 'is_tender_communication' zu milestone_progress hinzugefügt")
            else:
                print("ℹ️ Spalte 'is_tender_communication' bereits vorhanden")
            
            # 3. Füge visible_to_all_bidders Feld hinzu (falls nicht vorhanden)
            if 'visible_to_all_bidders' not in columns:
                await session.execute(text("""
                    ALTER TABLE milestone_progress 
                    ADD COLUMN visible_to_all_bidders BOOLEAN DEFAULT 1
                """))
                print("✅ Spalte 'visible_to_all_bidders' zu milestone_progress hinzugefügt")
            else:
                print("ℹ️ Spalte 'visible_to_all_bidders' bereits vorhanden")
            
            # 4. Aktualisiere bestehende Einträge
            await session.execute(text("""
                UPDATE milestone_progress 
                SET is_tender_communication = 0, visible_to_all_bidders = 1 
                WHERE is_tender_communication IS NULL OR visible_to_all_bidders IS NULL
            """))
            
            await session.commit()
            print("✅ Migration erfolgreich abgeschlossen")
            
    except Exception as e:
        print(f"❌ Fehler bei der Migration: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    print("🚀 Starte Kommunikations-Migration für BuildWise")
    asyncio.run(run_migration())
    print("🎉 Migration abgeschlossen!")
