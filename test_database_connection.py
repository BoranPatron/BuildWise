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
            print("✅ Datenbankverbindung erfolgreich")
            
            # Prüfe ob users-Tabelle existiert
            result = await conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='users'
            """))
            table_exists = result.fetchone()
            
            if table_exists:
                print("✅ users-Tabelle existiert")
                
                # Prüfe Spalten der users-Tabelle
                result = await conn.execute(text("PRAGMA table_info(users)"))
                columns = result.fetchall()
                print(f"📋 Spalten in users-Tabelle: {[col[1] for col in columns]}")
                
                # Prüfe ob hashed_password-Spalte existiert
                hashed_password_exists = any(col[1] == 'hashed_password' for col in columns)
                if hashed_password_exists:
                    print("✅ hashed_password-Spalte existiert")
                else:
                    print("❌ hashed_password-Spalte fehlt!")
                    
                # Prüfe Anzahl Benutzer
                result = await conn.execute(text("SELECT COUNT(*) FROM users"))
                user_count = result.scalar()
                print(f"👥 Anzahl Benutzer: {user_count}")
                
            else:
                print("❌ users-Tabelle existiert nicht!")
                
    except Exception as e:
        print(f"❌ Fehler beim Datenbank-Test: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_database()) 