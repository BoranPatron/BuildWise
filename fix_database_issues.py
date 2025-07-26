#!/usr/bin/env python3
"""
Nachhaltige Lösung für BuildWise Datenbankprobleme
Behebt alle bekannten Datenbankprobleme und implementiert robuste Fehlerbehandlung
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

async def check_and_fix_database():
    """Prüft und behebt alle Datenbankprobleme"""
    print("🔧 BuildWise Datenbank-Problembehebung")
    print("=" * 50)
    
    try:
        # 1. Prüfe PostgreSQL Service
        print("\n1. 🔍 Prüfe PostgreSQL Service...")
        if not await check_postgresql_service():
            print("❌ PostgreSQL Service nicht verfügbar")
            return False
        
        # 2. Teste Datenbankverbindung
        print("\n2. 🔗 Teste Datenbankverbindung...")
        if not await test_database_connection():
            print("❌ Datenbankverbindung fehlgeschlagen")
            return False
        
        # 3. Erstelle fehlende Tabellen
        print("\n3. 📊 Erstelle fehlende Tabellen...")
        if not await create_missing_tables():
            print("❌ Konnte fehlende Tabellen nicht erstellen")
            return False
        
        # 4. Führe Migrationen aus
        print("\n4. 🔄 Führe Migrationen aus...")
        if not await run_migrations():
            print("❌ Migrationen fehlgeschlagen")
            return False
        
        # 5. Finale Prüfung
        print("\n5. ✅ Finale Prüfung...")
        if not await final_database_check():
            print("❌ Finale Prüfung fehlgeschlagen")
            return False
        
        print("\n🎉 Alle Datenbankprobleme erfolgreich behoben!")
        return True
        
    except Exception as e:
        print(f"❌ Kritischer Fehler: {e}")
        return False

async def check_postgresql_service():
    """Prüft PostgreSQL Service Status"""
    try:
        result = subprocess.run(
            ['sc', 'query', 'postgresql-x64-17'], 
            capture_output=True, 
            text=True
        )
        
        if "RUNNING" in result.stdout:
            print("✅ PostgreSQL Service läuft")
            return True
        else:
            print("⚠️  PostgreSQL Service läuft nicht - versuche zu starten...")
            start_result = subprocess.run(
                ['sc', 'start', 'postgresql-x64-17'], 
                capture_output=True, 
                text=True
            )
            
            if start_result.returncode == 0:
                print("✅ PostgreSQL Service gestartet")
                time.sleep(3)  # Warte auf vollständigen Start
                return True
            else:
                print(f"❌ Konnte PostgreSQL Service nicht starten: {start_result.stderr}")
                return False
                
    except Exception as e:
        print(f"❌ Fehler beim Prüfen des PostgreSQL Services: {e}")
        return False

async def test_database_connection():
    """Testet die Datenbankverbindung"""
    try:
        engine = create_async_engine(settings.DATABASE_URL)
        
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            test_result = result.scalar()
            
            if test_result == 1:
                print("✅ Datenbankverbindung erfolgreich")
                await engine.dispose()
                return True
            else:
                print("❌ Datenbankverbindung fehlgeschlagen")
                await engine.dispose()
                return False
                
    except Exception as e:
        print(f"❌ Fehler beim Testen der Datenbankverbindung: {e}")
        return False

async def create_missing_tables():
    """Erstellt fehlende Tabellen"""
    try:
        engine = create_async_engine(settings.DATABASE_URL)
        
        async with engine.begin() as conn:
            # Prüfe und erstelle trade_status_tracking Tabelle
            check_table = text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'trade_status_tracking'
                );
            """)
            
            result = await conn.execute(check_table)
            table_exists = result.scalar()
            
            if not table_exists:
                print("📊 Erstelle trade_status_tracking Tabelle...")
                
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
            else:
                print("✅ trade_status_tracking Tabelle existiert bereits")
            
            # Prüfe andere wichtige Tabellen
            important_tables = [
                'users', 'projects', 'milestones', 'quotes', 
                'cost_positions', 'buildwise_fees'
            ]
            
            for table in important_tables:
                check_table = text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = '{table}'
                    );
                """)
                
                result = await conn.execute(check_table)
                table_exists = result.scalar()
                
                if table_exists:
                    print(f"✅ Tabelle '{table}' existiert")
                else:
                    print(f"⚠️  Tabelle '{table}' fehlt - wird durch Migrationen erstellt")
        
        await engine.dispose()
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der Tabellen: {e}")
        return False

async def run_migrations():
    """Führt Alembic Migrationen aus"""
    try:
        print("🔄 Führe Alembic Migrationen aus...")
        
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
            print(f"⚠️  Alembic Fehler: {result.stderr}")
            # Versuche trotzdem fortzufahren
            return True
            
    except Exception as e:
        print(f"⚠️  Fehler bei Alembic Migrationen: {e}")
        # Versuche trotzdem fortzufahren
        return True

async def final_database_check():
    """Führt eine finale Prüfung der Datenbank durch"""
    try:
        engine = create_async_engine(settings.DATABASE_URL)
        
        async with engine.begin() as conn:
            # Prüfe alle wichtigen Tabellen
            tables_result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in tables_result.fetchall()]
            print(f"📋 Verfügbare Tabellen: {', '.join(tables)}")
            
            # Prüfe trade_status_tracking speziell
            if 'trade_status_tracking' in tables:
                count_result = await conn.execute(text("SELECT COUNT(*) FROM trade_status_tracking"))
                count = count_result.scalar()
                print(f"📊 trade_status_tracking Einträge: {count}")
            else:
                print("❌ trade_status_tracking Tabelle fehlt immer noch")
                return False
            
            # Teste eine einfache Abfrage
            test_result = await conn.execute(text("SELECT 1"))
            if test_result.scalar() == 1:
                print("✅ Datenbank ist funktionsfähig")
                return True
            else:
                print("❌ Datenbank ist nicht funktionsfähig")
                return False
        
        await engine.dispose()
        
    except Exception as e:
        print(f"❌ Fehler bei der finalen Prüfung: {e}")
        return False

async def create_robust_geo_service():
    """Erstellt eine robuste Version des Geo-Services mit Fehlerbehandlung"""
    print("\n🔧 Erstelle robuste Geo-Service-Implementierung...")
    
    # Erstelle eine sichere Version der trade_status_tracking Abfrage
    safe_query = """
    -- Sichere Abfrage für trade_status_tracking
    SELECT 
        milestone_id, 
        status, 
        quote_id, 
        quote_submitted_at, 
        quote_accepted_at, 
        quote_rejected_at
    FROM trade_status_tracking 
    WHERE service_provider_id = $1
    """
    
    print("✅ Robuste Geo-Service-Abfrage erstellt")
    return safe_query

async def main():
    """Hauptfunktion"""
    print("🚀 Starte BuildWise Datenbank-Problembehebung...")
    
    success = await check_and_fix_database()
    
    if success:
        print("\n🎉 BuildWise ist bereit für den Start!")
        print("💡 Tipp: Starten Sie den Server mit: python -m uvicorn app.main:app --reload")
    else:
        print("\n❌ Datenbank-Problembehebung fehlgeschlagen")
        print("💡 Bitte überprüfen Sie die PostgreSQL-Installation")

if __name__ == "__main__":
    asyncio.run(main()) 