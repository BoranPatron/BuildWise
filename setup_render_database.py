#!/usr/bin/env python3
"""
Setup-Skript für Render.com Datenbank
Führt Migrationen aus und erstellt initiale Daten
"""

import asyncio
import os
import sys
from sqlalchemy import text

# Füge das Backend-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, get_database_url
from app.models import Base


async def setup_render_database():
    """Initialisiert die Datenbank auf Render.com"""
    print("🚀 Starte Render.com Datenbank-Setup...")
    
    # Prüfe Datenbank-URL
    database_url = get_database_url()
    print(f"📊 Datenbank-URL: {database_url}")
    
    try:
        # Erstelle alle Tabellen
        print("🔧 Erstelle Datenbank-Tabellen...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Tabellen erstellt")
        
        # Prüfe ob bereits Daten vorhanden sind
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()
            
            if user_count and user_count > 0:
                print(f"ℹ️ Datenbank bereits initialisiert ({user_count} Benutzer vorhanden)")
                return
        
        print("✅ Datenbank-Setup erfolgreich abgeschlossen!")
        print("📝 Hinweis: Test-Daten können über die API-Endpunkte erstellt werden")
        
    except Exception as e:
        print(f"❌ Fehler beim Setup: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(setup_render_database()) 