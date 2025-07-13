#!/usr/bin/env python3
"""
Einfaches Test-Skript für Datenbankverbindung
"""

import asyncio
import os
import sys
from pathlib import Path

# Füge das Projektverzeichnis zum Python-Pfad hinzu
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.database import get_database_url

async def test_database():
    """Teste die Datenbankverbindung und das Schema"""
    print("🔍 Teste Datenbankverbindung...")
    
    # Hole die Datenbank-URL
    database_url = get_database_url()
    print(f"📊 Datenbank-URL: {database_url}")
    
    # Erstelle Engine
    engine = create_async_engine(database_url, echo=False)
    
    try:
        # Teste Verbindung
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("✅ Datenbankverbindung erfolgreich")
        
        # Teste Tabellen-Liste
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result.fetchall()]
            print(f"📋 Verfügbare Tabellen: {tables}")
        
        # Teste users-Tabelle
        if 'users' in tables:
            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT COUNT(*) FROM users"))
                user_count_result = result.fetchone()
                user_count = user_count_result[0] if user_count_result else 0
                print(f"👥 Anzahl Benutzer: {user_count}")
                
                # Prüfe Spalten der users-Tabelle
                result = await conn.execute(text("PRAGMA table_info(users)"))
                columns = [row[1] for row in result.fetchall()]
                print(f"📊 Spalten der users-Tabelle: {columns}")
        
        # Teste projects-Tabelle
        if 'projects' in tables:
            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT COUNT(*) FROM projects"))
                project_count_result = result.fetchone()
                project_count = project_count_result[0] if project_count_result else 0
                print(f"🏗️ Anzahl Projekte: {project_count}")
        
        print("✅ Datenbank-Test erfolgreich abgeschlossen!")
        
    except Exception as e:
        print(f"❌ Fehler beim Datenbank-Test: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_database()) 