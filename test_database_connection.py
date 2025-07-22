#!/usr/bin/env python3
"""
Testet die Datenbank-Verbindung und alle Tabellen
"""

import asyncio
import sqlite3
import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine

def test_database_connection():
    """Testet die Datenbank-Verbindung"""
    print("🔍 TESTE DATENBANK-VERBINDUNG")
    print("=" * 40)
    
    db_path = "buildwise.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Datenbank nicht gefunden: {db_path}")
        return False
    
    print(f"📁 Datenbank gefunden: {os.path.abspath(db_path)}")
    print(f"📊 Größe: {os.path.getsize(db_path)} Bytes")
    
    # SQLite-Verbindung testen
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Teste Verbindung
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print(f"✅ SQLite-Verbindung erfolgreich: {result}")
        
        # Tabellen auflisten
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"📋 Gefundene Tabellen: {len(tables)}")
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"   - {table_name}: {count} Einträge")
            
            # Erste 3 Einträge zeigen
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                rows = cursor.fetchall()
                for i, row in enumerate(rows, 1):
                    print(f"     {i}. {row}")
        
        conn.close()
        print("✅ Datenbank-Test erfolgreich")
        return True
        
    except Exception as e:
        print(f"❌ Datenbank-Test fehlgeschlagen: {e}")
        return False

async def test_async_database_connection():
    """Testet die asynchrone Datenbank-Verbindung"""
    print("\n🔍 TESTE ASYNC DATENBANK-VERBINDUNG")
    print("=" * 40)
    
    db_path = "buildwise.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Datenbank nicht gefunden: {db_path}")
        return False
    
    # Async SQLite-Engine erstellen
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
    
    try:
        # Teste Verbindung
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            row = result.fetchone()
            print(f"✅ Async SQLite-Verbindung erfolgreich: {row}")
            
            # Tabellen auflisten
            result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result]
            print(f"📋 Gefundene Tabellen: {tables}")
            
            for table in tables:
                result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"   - {table}: {count} Einträge")
        
        await engine.dispose()
        print("✅ Async Datenbank-Test erfolgreich")
        return True
        
    except Exception as e:
        print(f"❌ Async Datenbank-Test fehlgeschlagen: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starte Datenbank-Tests...")
    
    # Synchron testen
    sync_ok = test_database_connection()
    
    # Async testen
    async_ok = asyncio.run(test_async_database_connection())
    
    if sync_ok and async_ok:
        print("\n✅ Alle Datenbank-Tests erfolgreich")
    else:
        print("\n❌ Einige Datenbank-Tests fehlgeschlagen") 