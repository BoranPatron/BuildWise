#!/usr/bin/env python3
"""
Skript zum Löschen aller bestehenden Kostenpositionen
"""

import asyncio
import sys
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Füge das BuildWise-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def clear_cost_positions():
    """Löscht alle bestehenden Kostenpositionen"""
    
    # Erstelle Engine für SQLite
    DATABASE_URL = "sqlite+aiosqlite:///./buildwise.db"
    engine = create_async_engine(DATABASE_URL, echo=False, future=True)
    
    async with engine.begin() as conn:
        print("🗑️ Lösche alle bestehenden Kostenpositionen...")
        
        # Prüfe ob die Tabelle existiert
        result = await conn.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='cost_positions'
        """))
        
        if not result.fetchone():
            print("✅ Tabelle 'cost_positions' existiert nicht - nichts zu löschen")
            return
        
        # Zähle bestehende Kostenpositionen
        count_result = await conn.execute(text("SELECT COUNT(*) FROM cost_positions"))
        count = count_result.scalar()
        
        if count == 0:
            print("✅ Keine Kostenpositionen vorhanden - nichts zu löschen")
            return
        
        print(f"📊 Gefunden: {count} Kostenpositionen")
        
        # Lösche alle Kostenpositionen
        await conn.execute(text("DELETE FROM cost_positions"))
        
        print(f"✅ {count} Kostenpositionen erfolgreich gelöscht")


async def main():
    """Hauptfunktion"""
    try:
        await clear_cost_positions()
        print("🎉 Alle Kostenpositionen erfolgreich gelöscht!")
    except Exception as e:
        print(f"❌ Fehler beim Löschen der Kostenpositionen: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 