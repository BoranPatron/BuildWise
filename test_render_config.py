#!/usr/bin/env python3
"""
Test-Skript für Render.com-Konfiguration
Führt grundlegende Tests der Umgebungsvariablen und Datenbankverbindung durch
"""

import os
import sys
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

def test_environment_variables():
    """Teste alle wichtigen Umgebungsvariablen"""
    print("🔍 Teste Umgebungsvariablen...")
    
    required_vars = [
        "DATABASE_URL",
        "JWT_SECRET_KEY",
        "ENVIRONMENT"
    ]
    
    optional_vars = [
        "DEBUG",
        "PORT",
        "HOST",
        "ALLOWED_ORIGINS"
    ]
    
    print("\n📋 Erforderliche Variablen:")
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            print(f"✅ {var}: {'*' * len(value)} (Länge: {len(value)})")
        else:
            print(f"❌ {var}: NICHT GESETZT")
    
    print("\n📋 Optionale Variablen:")
    for var in optional_vars:
        value = os.environ.get(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"⚠️  {var}: NICHT GESETZT (verwendet Standard)")
    
    return True

def test_database_url():
    """Teste die Datenbank-URL-Konfiguration"""
    print("\n🔍 Teste Datenbank-URL...")
    
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL nicht gesetzt")
        return False
    
    print(f"📋 DATABASE_URL: {database_url}")
    
    # Prüfe URL-Format
    if database_url.startswith("postgres://"):
        print("✅ PostgreSQL-URL erkannt (postgres://)")
        # Konvertiere für SQLAlchemy
        converted_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
        print(f"🔄 Konvertiert zu: {converted_url}")
    elif database_url.startswith("postgresql://"):
        print("✅ PostgreSQL-URL erkannt (postgresql://)")
        converted_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        print(f"🔄 Konvertiert zu: {converted_url}")
    elif database_url.startswith("sqlite"):
        print("✅ SQLite-URL erkannt")
        converted_url = database_url
    else:
        print("❌ Unbekanntes URL-Format")
        return False
    
    return True

async def test_database_connection():
    """Teste die tatsächliche Datenbankverbindung"""
    print("\n🔍 Teste Datenbankverbindung...")
    
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL nicht gesetzt")
        return False
    
    # Konvertiere URL für SQLAlchemy
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    try:
        print(f"🔗 Verbinde mit: {database_url.split('@')[1] if '@' in database_url else database_url}")
        
        engine = create_async_engine(
            database_url,
            echo=False,
            future=True,
            pool_pre_ping=True
        )
        
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("✅ Datenbankverbindung erfolgreich!")
            
            # Teste Tabellen-Liste
            if database_url.startswith("postgresql"):
                result = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
                tables = [row[0] for row in result.fetchall()]
                print(f"📋 Verfügbare Tabellen: {len(tables)}")
                if tables:
                    print(f"   Erste 5 Tabellen: {tables[:5]}")
                else:
                    print("   ⚠️  Keine Tabellen gefunden - Migrationen müssen ausgeführt werden")
        
        await engine.dispose()
        return True
        
    except Exception as e:
        print(f"❌ Datenbankverbindung fehlgeschlagen: {str(e)}")
        return False

def test_imports():
    """Teste alle wichtigen Imports"""
    print("\n🔍 Teste Imports...")
    
    try:
        import fastapi
        print(f"✅ FastAPI: {fastapi.__version__}")
    except ImportError as e:
        print(f"❌ FastAPI Import fehlgeschlagen: {e}")
        return False
    
    try:
        import sqlalchemy
        print(f"✅ SQLAlchemy: {sqlalchemy.__version__}")
    except ImportError as e:
        print(f"❌ SQLAlchemy Import fehlgeschlagen: {e}")
        return False
    
    try:
        import asyncpg
        print("✅ asyncpg verfügbar")
    except ImportError as e:
        print(f"❌ asyncpg Import fehlgeschlagen: {e}")
        return False
    
    try:
        import pydantic
        print(f"✅ Pydantic: {pydantic.__version__}")
    except ImportError as e:
        print(f"❌ Pydantic Import fehlgeschlagen: {e}")
        return False
    
    return True

async def main():
    """Hauptfunktion für alle Tests"""
    print("🚀 Starte Render.com-Konfigurationstests...")
    print("=" * 50)
    
    results = []
    
    # Teste Imports
    results.append(test_imports())
    
    # Teste Umgebungsvariablen
    results.append(test_environment_variables())
    
    # Teste Datenbank-URL
    results.append(test_database_url())
    
    # Teste Datenbankverbindung
    results.append(await test_database_connection())
    
    print("\n" + "=" * 50)
    print("📊 Test-Zusammenfassung:")
    
    if all(results):
        print("✅ Alle Tests erfolgreich!")
        print("🎉 Das Backend sollte auf Render.com funktionieren")
        return 0
    else:
        print("❌ Einige Tests fehlgeschlagen")
        print("🔧 Überprüfe die Konfiguration und versuche es erneut")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 