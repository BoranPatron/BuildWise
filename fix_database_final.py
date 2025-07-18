#!/usr/bin/env python3
"""
Finales Skript zur Datenbank-Behebung mit korrekten Credentials
"""

import asyncio
import sys
import os
from datetime import datetime

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def fix_database_with_correct_credentials():
    """Behebt die Datenbank mit korrekten Credentials"""
    print("🚀 Starte finale Datenbank-Behebung...")
    
    try:
        # Importiere SQLAlchemy-Komponenten
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text
        
        # Verwende die korrekten Credentials aus .env_original
        database_url = "postgresql+asyncpg://postgres:your_secure_password@localhost:5432/buildwise"
        
        print("Verwende Datenbank-URL:", database_url.replace("your_secure_password", "***"))
        
        # Erstelle Engine
        engine = create_async_engine(database_url)
        
        async with engine.begin() as conn:
            # 1. Zeige aktuelle Projekte
            print("\n=== AKTUELLE PROJEKTE ===")
            result = await conn.execute(text("""
                SELECT id, name, address, is_public, allow_quotes 
                FROM projects 
                ORDER BY id
            """))
            projects = result.fetchall()
            
            for project in projects:
                print(f"Projekt {project[0]}: {project[1]}")
                print(f"  Adresse: {project[2]}")
                print(f"  Öffentlich: {project[3]}")
                print(f"  Quotes erlaubt: {project[4]}")
            
            # 2. Füge Adressen hinzu
            print("\n=== ADRESSEN HINZUFÜGEN ===")
            
            update_queries = [
                "UPDATE projects SET address = 'Hauptstraße 42, 80331 München, Deutschland' WHERE id = 1 AND (address IS NULL OR address = '')",
                "UPDATE projects SET address = 'Königsallee 15, 40212 Düsseldorf, Deutschland' WHERE id = 2 AND (address IS NULL OR address = '')",
                "UPDATE projects SET address = 'Neuer Wall 80, 20354 Hamburg, Deutschland' WHERE id = 3 AND (address IS NULL OR address = '')",
                "UPDATE projects SET address = 'Zeil 106, 60313 Frankfurt am Main, Deutschland' WHERE id = 4 AND (address IS NULL OR address = '')",
                "UPDATE projects SET address = 'Friedrichstraße 123, 10117 Berlin, Deutschland' WHERE id = 5 AND (address IS NULL OR address = '')"
            ]
            
            for query in update_queries:
                await conn.execute(text(query))
                print(f"✅ Query ausgeführt: {query[:50]}...")
            
            # 3. Mache Projekte öffentlich
            print("\n=== PROJEKTE ÖFFENTLICH MACHEN ===")
            await conn.execute(text("UPDATE projects SET is_public = true, allow_quotes = true WHERE id IN (1, 2, 3, 4, 5)"))
            print("✅ Projekte öffentlich gemacht")
            
            # 4. Zeige aktualisierte Projekte
            print("\n=== AKTUALISIERTE PROJEKTE ===")
            result = await conn.execute(text("""
                SELECT id, name, address, is_public, allow_quotes 
                FROM projects 
                WHERE id IN (1, 2, 3, 4, 5)
                ORDER BY id
            """))
            updated_projects = result.fetchall()
            
            for project in updated_projects:
                print(f"Projekt {project[0]}: {project[1]}")
                print(f"  Adresse: {project[2]}")
                print(f"  Öffentlich: {project[3]}")
                print(f"  Quotes erlaubt: {project[4]}")
            
            # 5. Zeige Gewerke
            print("\n=== GEWERKE ===")
            result = await conn.execute(text("""
                SELECT m.id, m.title, m.category, m.status,
                       p.name as project_name, p.address as project_address,
                       p.is_public, p.allow_quotes
                FROM milestones m
                JOIN projects p ON m.project_id = p.id
                ORDER BY m.id
            """))
            trades = result.fetchall()
            
            for trade in trades:
                print(f"Gewerk {trade[0]}: {trade[1]}")
                print(f"  Kategorie: {trade[2]}")
                print(f"  Status: {trade[3]}")
                print(f"  Projekt: {trade[4]}")
                print(f"  Adresse: {trade[5]}")
                print(f"  Öffentlich: {trade[6]}")
                print(f"  Quotes erlaubt: {trade[7]}")
            
            print("\n✅ Datenbank-Behebung erfolgreich abgeschlossen!")
            return True
            
    except Exception as e:
        print(f"❌ Fehler bei der Datenbank-Behebung: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_manual_instructions():
    """Erstellt manuelle Anweisungen"""
    print("\n=== MANUELLE ANWEISUNGEN ===")
    print("Falls das automatische Skript nicht funktioniert:")
    print("\n1. Öffnen Sie Ihre Datenbank-Verwaltung (pgAdmin, DBeaver, etc.)")
    print("2. Verbinden Sie sich mit der BuildWise-Datenbank")
    print("   - Host: localhost")
    print("   - Port: 5432")
    print("   - Database: buildwise")
    print("   - Username: postgres")
    print("   - Password: your_secure_password")
    print("\n3. Führen Sie diese SQL-Befehle aus:")
    print("\n-- Füge Adressen hinzu")
    print("UPDATE projects SET address = 'Hauptstraße 42, 80331 München, Deutschland' WHERE id = 1;")
    print("UPDATE projects SET address = 'Königsallee 15, 40212 Düsseldorf, Deutschland' WHERE id = 2;")
    print("UPDATE projects SET address = 'Neuer Wall 80, 20354 Hamburg, Deutschland' WHERE id = 3;")
    print("UPDATE projects SET address = 'Zeil 106, 60313 Frankfurt am Main, Deutschland' WHERE id = 4;")
    print("UPDATE projects SET address = 'Friedrichstraße 123, 10117 Berlin, Deutschland' WHERE id = 5;")
    print("\n-- Mache Projekte öffentlich")
    print("UPDATE projects SET is_public = true, allow_quotes = true WHERE id IN (1, 2, 3, 4, 5);")
    print("\n4. Starten Sie das Backend neu:")
    print("   python -m uvicorn app.main:app --reload")

async def main():
    """Hauptfunktion"""
    print("🚀 Starte finale Datenbank-Behebung...")
    print(f"Zeitstempel: {datetime.now()}")
    
    try:
        # 1. Datenbank beheben
        db_success = await fix_database_with_correct_credentials()
        
        if db_success:
            print("\n📊 BEHEBUNG-ZUSAMMENFASSUNG:")
            print("✅ Datenbank erfolgreich behebt")
            print("✅ Projekte haben jetzt Adressen")
            print("✅ Projekte sind öffentlich")
            print("\n📋 Nächste Schritte:")
            print("1. Starten Sie das Backend neu: python -m uvicorn app.main:app --reload")
            print("2. Warten Sie 10-15 Sekunden bis das Backend vollständig gestartet ist")
            print("3. Testen Sie die Kartenansicht in der Dienstleisteransicht")
            print("4. Verwenden Sie das Debug-Skript: debug_geo_search_final.js")
            
        else:
            print("❌ Datenbank-Behebung fehlgeschlagen")
            create_manual_instructions()
            
    except Exception as e:
        print(f"❌ Fehler bei der Behebung: {e}")
        create_manual_instructions()

if __name__ == "__main__":
    asyncio.run(main()) 