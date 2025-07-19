#!/usr/bin/env python3
"""
Einfaches Skript zur Bereinigung der Milestone-Daten
"""

import asyncio
import os
from datetime import datetime, date
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv

load_dotenv()

# Verwende SQLite für einfacheren Zugriff
DATABASE_URL = "sqlite+aiosqlite:///buildwise.db"

async def fix_milestone_dates():
    """Bereinigt ungültige Datumsformate in der Milestone-Tabelle"""
    engine = create_async_engine(DATABASE_URL)
    
    try:
        async with engine.begin() as conn:
            print("🔧 Starte Milestone-Datenbereinigung...")
            
            # Setze nur die optionalen Datumsfelder auf NULL
            await conn.execute(text("""
                UPDATE milestones 
                SET actual_date = NULL, 
                    start_date = NULL, 
                    end_date = NULL
                WHERE actual_date IS NOT NULL 
                   OR start_date IS NOT NULL 
                   OR end_date IS NOT NULL
            """))
            
            # Setze planned_date auf heutiges Datum falls es ungültig ist
            await conn.execute(text("""
                UPDATE milestones 
                SET planned_date = date('now')
                WHERE planned_date IS NULL OR planned_date = ''
            """))
            
            print("✅ Milestone-Daten bereinigt!")
            
    except Exception as e:
        print(f"❌ Fehler bei der Datenbereinigung: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_milestone_dates()) 