#!/usr/bin/env python3
"""
Skript zur Migration der Datenbank: Fügt das phase-Feld zu Projekten hinzu
"""

import asyncio
import sys
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Füge das BuildWise-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.project import ProjectPhase


async def add_phase_column():
    """Fügt das phase-Feld zur projects-Tabelle hinzu"""
    
    # Erstelle Engine für SQLite
    DATABASE_URL = "sqlite+aiosqlite:///./buildwise.db"
    engine = create_async_engine(DATABASE_URL, echo=False, future=True)
    
    async with engine.begin() as conn:
        print("🔧 Füge phase-Spalte zur projects-Tabelle hinzu...")
        
        # Prüfe ob die Spalte bereits existiert
        result = await conn.execute(text("""
            SELECT name FROM pragma_table_info('projects') 
            WHERE name = 'phase'
        """))
        
        if result.fetchone():
            print("✅ phase-Spalte existiert bereits")
            return
        
        # Füge die Spalte hinzu
        await conn.execute(text("""
            ALTER TABLE projects 
            ADD COLUMN phase VARCHAR(20) NOT NULL DEFAULT 'preparation'
        """))
        
        print("✅ phase-Spalte erfolgreich hinzugefügt")
        
        # Aktualisiere bestehende Projekte mit Standard-Phase
        await conn.execute(text("""
            UPDATE projects 
            SET phase = 'preparation' 
            WHERE phase IS NULL OR phase = ''
        """))
        
        print("✅ Bestehende Projekte mit Standard-Phase aktualisiert")


async def main():
    """Hauptfunktion"""
    try:
        await add_phase_column()
        print("🎉 Migration erfolgreich abgeschlossen!")
    except Exception as e:
        print(f"❌ Fehler bei der Migration: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 