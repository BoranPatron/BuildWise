#!/usr/bin/env python3
"""
Initialisiert die BuildWise-Datenbank mit allen Tabellen
"""

import asyncio
import sqlite3
import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine

def initialize_database_sync():
    """Initialisiert die Datenbank synchron"""
    print("🗄️ INITIALISIERE BUILDWISE-DATENBANK")
    print("=" * 40)
    
    db_path = "buildwise.db"
    
    # Prüfe ob Datenbank existiert
    if os.path.exists(db_path):
        print(f"📁 Datenbank existiert bereits: {os.path.abspath(db_path)}")
        
        # Prüfe Datenbank-Inhalt
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Tabellen auflisten
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"📋 Gefundene Tabellen: {len(tables)}")
            
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"   - {table_name}: {count} Einträge")
                
        except Exception as e:
            print(f"❌ Fehler beim Prüfen der Datenbank: {e}")
        finally:
            conn.close()
    else:
        print(f"📁 Erstelle neue Datenbank: {os.path.abspath(db_path)}")
    
    # SQLite-Engine erstellen
    engine = create_engine(f"sqlite:///{db_path}")
    
    try:
        # Tabellen erstellen
        from app.models import Base
        Base.metadata.create_all(engine)
        print("✅ Tabellen erfolgreich erstellt")
        
        # Prüfe erstellte Tabellen
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result]
            print(f"📋 Erstellte Tabellen: {tables}")
            
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der Tabellen: {e}")
        return False
    
    print("✅ Datenbank-Initialisierung abgeschlossen")
    return True

async def initialize_database_async():
    """Initialisiert die Datenbank asynchron"""
    print("🗄️ INITIALISIERE BUILDWISE-DATENBANK (ASYNC)")
    print("=" * 40)
    
    db_path = "buildwise.db"
    
    # Async SQLite-Engine erstellen
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
    
    try:
        # Tabellen erstellen
        from app.models import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Tabellen erfolgreich erstellt (Async)")
        
        # Prüfe erstellte Tabellen
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result]
            print(f"📋 Erstellte Tabellen: {tables}")
            
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der Tabellen: {e}")
        return False
    finally:
        await engine.dispose()
    
    print("✅ Datenbank-Initialisierung abgeschlossen (Async)")
    return True

if __name__ == "__main__":
    print("🚀 Starte Datenbank-Initialisierung...")
    
    # Synchron initialisieren
    success = initialize_database_sync()
    
    if success:
        print("✅ Datenbank-Initialisierung erfolgreich")
    else:
        print("❌ Datenbank-Initialisierung fehlgeschlagen") 