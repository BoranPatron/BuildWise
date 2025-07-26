#!/usr/bin/env python3
"""
Umfassendes Datenbank-Setup für BuildWise
Erstellt die Datenbank, Tabellen und führt alle Migrationen durch
"""

import asyncio
import sys
import os
import subprocess
import time
from datetime import datetime

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import text, select, func
from app.core.config import settings

async def check_postgresql_service():
    """Prüft, ob PostgreSQL als Service läuft"""
    print("🔍 Prüfe PostgreSQL Service...")
    
    try:
        # Prüfe PostgreSQL Service Status
        result = subprocess.run(
            ['sc', 'query', 'postgresql-x64-17'], 
            capture_output=True, 
            text=True
        )
        
        if "RUNNING" in result.stdout:
            print("✅ PostgreSQL Service läuft bereits")
            return True
        else:
            print("⚠️  PostgreSQL Service läuft nicht")
            return False
            
    except Exception as e:
        print(f"❌ Fehler beim Prüfen des PostgreSQL Services: {e}")
        return False

async def start_postgresql_service():
    """Startet PostgreSQL als Service"""
    print("🚀 Starte PostgreSQL Service...")
    
    try:
        # Starte PostgreSQL Service
        result = subprocess.run(
            ['sc', 'start', 'postgresql-x64-17'], 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            print("✅ PostgreSQL Service gestartet")
            return True
        else:
            print(f"❌ Fehler beim Starten: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Fehler beim Starten des PostgreSQL Services: {e}")
        return False

async def create_database():
    """Erstellt die BuildWise Datenbank"""
    print("🗄️  Erstelle BuildWise Datenbank...")
    
    try:
        # Verbinde zur Standard-Datenbank
        engine = create_async_engine(
            "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
        )
        
        async with engine.begin() as conn:
            # Prüfe, ob Datenbank bereits existiert
            check_db = text("SELECT 1 FROM pg_database WHERE datname = 'buildwise'")
            result = await conn.execute(check_db)
            
            if result.scalar():
                print("✅ Datenbank 'buildwise' existiert bereits")
            else:
                # Erstelle Datenbank
                create_db = text("CREATE DATABASE buildwise")
                await conn.execute(create_db)
                print("✅ Datenbank 'buildwise' erstellt")
            
            # Erstelle Benutzer falls nicht vorhanden
            check_user = text("SELECT 1 FROM pg_user WHERE usename = 'buildwise_user'")
            result = await conn.execute(check_user)
            
            if not result.scalar():
                create_user = text("CREATE USER buildwise_user WITH PASSWORD 'buildwise123'")
                await conn.execute(create_user)
                print("✅ Benutzer 'buildwise_user' erstellt")
            
            # Gewähre Rechte
            grant_rights = text("GRANT ALL PRIVILEGES ON DATABASE buildwise TO buildwise_user")
            await conn.execute(grant_rights)
            print("✅ Rechte für 'buildwise_user' gewährt")
        
        await engine.dispose()
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der Datenbank: {e}")
        return False

async def create_trade_status_tracking():
    """Erstellt die trade_status_tracking Tabelle"""
    print("📊 Erstelle trade_status_tracking Tabelle...")
    
    try:
        engine = create_async_engine(settings.DATABASE_URL)
        
        async with engine.begin() as conn:
            # Erstelle Tabelle
            create_table = text("""
                CREATE TABLE IF NOT EXISTS trade_status_tracking (
                    id SERIAL PRIMARY KEY,
                    milestone_id INTEGER REFERENCES milestones(id) ON DELETE CASCADE,
                    service_provider_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    quote_id INTEGER REFERENCES quotes(id) ON DELETE CASCADE,
                    status VARCHAR(50) NOT NULL DEFAULT 'available',
                    quote_submitted_at TIMESTAMP,
                    quote_accepted_at TIMESTAMP,
                    quote_rejected_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(milestone_id, service_provider_id)
                );
            """)
            
            await conn.execute(create_table)
            print("✅ trade_status_tracking Tabelle erstellt")
            
            # Erstelle Indizes
            create_indexes = text("""
                CREATE INDEX IF NOT EXISTS idx_trade_status_milestone ON trade_status_tracking(milestone_id);
                CREATE INDEX IF NOT EXISTS idx_trade_status_provider ON trade_status_tracking(service_provider_id);
                CREATE INDEX IF NOT EXISTS idx_trade_status_quote ON trade_status_tracking(quote_id);
                CREATE INDEX IF NOT EXISTS idx_trade_status_status ON trade_status_tracking(status);
            """)
            
            await conn.execute(create_indexes)
            print("✅ Indizes für trade_status_tracking erstellt")
        
        await engine.dispose()
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der trade_status_tracking Tabelle: {e}")
        return False

async def run_alembic_migrations():
    """Führt Alembic Migrationen aus"""
    print("🔄 Führe Alembic Migrationen aus...")
    
    try:
        # Führe Alembic Upgrade aus
        result = subprocess.run(
            ['alembic', 'upgrade', 'head'], 
            capture_output=True, 
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        if result.returncode == 0:
            print("✅ Alembic Migrationen erfolgreich")
            return True
        else:
            print(f"❌ Fehler bei Alembic Migrationen: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Fehler beim Ausführen der Alembic Migrationen: {e}")
        return False

async def test_database_connection():
    """Testet die Datenbankverbindung"""
    print("🔗 Teste Datenbankverbindung...")
    
    try:
        engine = create_async_engine(settings.DATABASE_URL)
        
        async with engine.begin() as conn:
            # Teste Verbindung
            result = await conn.execute(text("SELECT 1"))
            test_result = result.scalar()
            
            if test_result == 1:
                print("✅ Datenbankverbindung erfolgreich")
                
                # Prüfe Tabellen
                tables_result = await conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """))
                
                tables = [row[0] for row in tables_result.fetchall()]
                print(f"📋 Verfügbare Tabellen: {', '.join(tables)}")
                
                return True
            else:
                print("❌ Datenbankverbindung fehlgeschlagen")
                return False
        
        await engine.dispose()
        
    except Exception as e:
        print(f"❌ Fehler beim Testen der Datenbankverbindung: {e}")
        return False

async def setup_database_complete():
    """Hauptfunktion für das komplette Datenbank-Setup"""
    print("🚀 BuildWise Datenbank-Setup")
    print("=" * 50)
    
    # 1. Prüfe PostgreSQL Service
    if not await check_postgresql_service():
        if not await start_postgresql_service():
            print("❌ Konnte PostgreSQL Service nicht starten")
            return False
    
    # Warte kurz, damit PostgreSQL vollständig startet
    print("⏳ Warte auf PostgreSQL Start...")
    time.sleep(3)
    
    # 2. Erstelle Datenbank
    if not await create_database():
        print("❌ Konnte Datenbank nicht erstellen")
        return False
    
    # 3. Führe Alembic Migrationen aus
    if not await run_alembic_migrations():
        print("❌ Konnte Alembic Migrationen nicht ausführen")
        return False
    
    # 4. Erstelle trade_status_tracking Tabelle
    if not await create_trade_status_tracking():
        print("❌ Konnte trade_status_tracking Tabelle nicht erstellen")
        return False
    
    # 5. Teste Verbindung
    if not await test_database_connection():
        print("❌ Datenbankverbindung fehlgeschlagen")
        return False
    
    print("\n✅ Datenbank-Setup erfolgreich abgeschlossen!")
    print("🎉 BuildWise ist bereit für den Start!")
    
    return True

if __name__ == "__main__":
    asyncio.run(setup_database_complete()) 