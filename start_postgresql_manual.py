#!/usr/bin/env python3
"""
Manueller PostgreSQL Start und Datenbank-Setup für BuildWise
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

async def start_postgresql_manual():
    """Startet PostgreSQL manuell und führt Datenbank-Setup durch"""
    print("🚀 Manueller PostgreSQL Start für BuildWise")
    print("=" * 50)
    
    try:
        # 1. Prüfe ob PostgreSQL läuft
        print("\n1. 🔍 Prüfe PostgreSQL Status...")
        
        # Versuche Verbindung zur Standard-Datenbank
        test_engine = create_async_engine(
            "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
        )
        
        try:
            async with test_engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                if result.scalar() == 1:
                    print("✅ PostgreSQL läuft bereits")
                    await test_engine.dispose()
                    return await setup_buildwise_database()
        except Exception as e:
            print(f"⚠️  PostgreSQL nicht erreichbar: {e}")
            await test_engine.dispose()
        
        # 2. Versuche PostgreSQL zu starten
        print("\n2. 🚀 Versuche PostgreSQL zu starten...")
        
        # Versuche verschiedene Start-Methoden
        start_methods = [
            ["sc", "start", "postgresql-x64-17"],
            ["net", "start", "postgresql-x64-17"],
            ["pg_ctl", "start", "-D", "C:\\Program Files\\PostgreSQL\\17\\data"],
            ["C:\\Program Files\\PostgreSQL\\17\\bin\\pg_ctl.exe", "start", "-D", "C:\\Program Files\\PostgreSQL\\17\\data"]
        ]
        
        for method in start_methods:
            try:
                print(f"   Versuche: {' '.join(method)}")
                result = subprocess.run(method, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    print(f"✅ PostgreSQL gestartet mit: {' '.join(method)}")
                    time.sleep(5)  # Warte auf vollständigen Start
                    break
                else:
                    print(f"   Fehler: {result.stderr}")
            except Exception as e:
                print(f"   Fehler: {e}")
                continue
        else:
            print("❌ Konnte PostgreSQL nicht starten")
            print("💡 Bitte starten Sie PostgreSQL manuell:")
            print("   1. Öffnen Sie 'Dienste' (services.msc)")
            print("   2. Suchen Sie 'postgresql-x64-17'")
            print("   3. Klicken Sie 'Start'")
            return False
        
        # 3. Teste Verbindung erneut
        print("\n3. 🔗 Teste PostgreSQL Verbindung...")
        
        try:
            async with test_engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                if result.scalar() == 1:
                    print("✅ PostgreSQL Verbindung erfolgreich")
                    await test_engine.dispose()
                    return await setup_buildwise_database()
                else:
                    print("❌ PostgreSQL Verbindung fehlgeschlagen")
                    return False
        except Exception as e:
            print(f"❌ PostgreSQL Verbindung fehlgeschlagen: {e}")
            await test_engine.dispose()
            return False
            
    except Exception as e:
        print(f"❌ Kritischer Fehler: {e}")
        return False

async def setup_buildwise_database():
    """Erstellt die BuildWise Datenbank und Tabellen"""
    print("\n4. 🗄️  Erstelle BuildWise Datenbank...")
    
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
        
        # 5. Erstelle Tabellen in BuildWise Datenbank
        print("\n5. 📊 Erstelle Tabellen...")
        
        buildwise_engine = create_async_engine(settings.DATABASE_URL)
        
        async with buildwise_engine.begin() as conn:
            # Erstelle trade_status_tracking Tabelle
            create_table = text("""
                CREATE TABLE IF NOT EXISTS trade_status_tracking (
                    id SERIAL PRIMARY KEY,
                    milestone_id INTEGER,
                    service_provider_id INTEGER,
                    quote_id INTEGER,
                    status VARCHAR(50) NOT NULL DEFAULT 'available',
                    quote_submitted_at TIMESTAMP,
                    quote_accepted_at TIMESTAMP,
                    quote_rejected_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        
        await buildwise_engine.dispose()
        
        # 6. Führe Alembic Migrationen aus
        print("\n6. 🔄 Führe Alembic Migrationen aus...")
        
        try:
            result = subprocess.run(
                ['alembic', 'upgrade', 'head'], 
                capture_output=True, 
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            if result.returncode == 0:
                print("✅ Alembic Migrationen erfolgreich")
            else:
                print(f"⚠️  Alembic Fehler: {result.stderr}")
                print("   Versuche trotzdem fortzufahren...")
                
        except Exception as e:
            print(f"⚠️  Fehler bei Alembic Migrationen: {e}")
            print("   Versuche trotzdem fortzufahren...")
        
        # 7. Finale Prüfung
        print("\n7. ✅ Finale Prüfung...")
        
        try:
            async with buildwise_engine.begin() as conn:
                # Teste Verbindung
                result = await conn.execute(text("SELECT 1"))
                if result.scalar() == 1:
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
                    
                    if 'trade_status_tracking' in tables:
                        count_result = await conn.execute(text("SELECT COUNT(*) FROM trade_status_tracking"))
                        count = count_result.scalar()
                        print(f"📊 trade_status_tracking Einträge: {count}")
                        print("✅ BuildWise Datenbank ist bereit!")
                        return True
                    else:
                        print("❌ trade_status_tracking Tabelle fehlt")
                        return False
                else:
                    print("❌ Datenbankverbindung fehlgeschlagen")
                    return False
                    
        except Exception as e:
            print(f"❌ Fehler bei der finalen Prüfung: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der Datenbank: {e}")
        return False

async def main():
    """Hauptfunktion"""
    print("🚀 Starte manuelles PostgreSQL Setup...")
    
    success = await start_postgresql_manual()
    
    if success:
        print("\n🎉 BuildWise ist bereit für den Start!")
        print("💡 Tipp: Starten Sie den Server mit: python -m uvicorn app.main:app --reload")
    else:
        print("\n❌ Setup fehlgeschlagen")
        print("💡 Bitte überprüfen Sie die PostgreSQL-Installation")

if __name__ == "__main__":
    asyncio.run(main()) 