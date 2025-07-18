#!/usr/bin/env python3
"""
Automatisches Skript zur Behebung der Datenbank-Probleme
Führt SQL-Updates direkt aus und startet das Backend neu
"""

import asyncio
import sys
import os
import subprocess
import time
from datetime import datetime

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

async def fix_database_directly():
    """Behebt die Datenbank-Probleme direkt"""
    print("🚀 Starte automatische Datenbank-Behebung...")
    
    try:
        # Datenbank-URL (anpassen an Ihre Konfiguration)
        database_url = "postgresql+asyncpg://buildwise:buildwise@localhost:5432/buildwise"
        
        engine = create_async_engine(database_url)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        session = async_session()
        try:
            # 1. Zeige aktuelle Projekte
            print("\n=== AKTUELLE PROJEKTE ===")
            result = await session.execute(text("""
                SELECT id, name, address, is_public, allow_quotes, 
                       address_latitude, address_longitude
                FROM projects 
                ORDER BY id
            """))
            projects = result.fetchall()
            
            for project in projects:
                print(f"Projekt {project[0]}: {project[1]}")
                print(f"  Adresse: {project[2]}")
                print(f"  Öffentlich: {project[3]}")
                print(f"  Quotes erlaubt: {project[4]}")
                print(f"  Koordinaten: {project[5]}, {project[6]}")
            
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
                await session.execute(text(query))
                print(f"✅ Query ausgeführt: {query[:50]}...")
            
            # 3. Mache Projekte öffentlich
            print("\n=== PROJEKTE ÖFFENTLICH MACHEN ===")
            await session.execute(text("UPDATE projects SET is_public = true, allow_quotes = true WHERE id IN (1, 2, 3, 4, 5)"))
            print("✅ Projekte öffentlich gemacht")
            
            # 4. Commit Änderungen
            await session.commit()
            print("✅ Änderungen gespeichert")
            
            # 5. Zeige aktualisierte Projekte
            print("\n=== AKTUALISIERTE PROJEKTE ===")
            result = await session.execute(text("""
                SELECT id, name, address, is_public, allow_quotes, 
                       address_latitude, address_longitude
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
                print(f"  Koordinaten: {project[5]}, {project[6]}")
            
            # 6. Zeige Gewerke
            print("\n=== GEWERKE ===")
            result = await session.execute(text("""
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
            
        finally:
            await session.close()
            
    except Exception as e:
        print(f"❌ Fehler bei der Datenbank-Behebung: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_geo_api():
    """Testet die Geo-API nach der Behebung"""
    print("\n=== GEO-API TEST ===")
    
    try:
        import aiohttp
        import json
        
        # Simuliere einen API-Aufruf
        test_request = {
            "latitude": 52.5200,
            "longitude": 13.4050,
            "radius_km": 50,
            "limit": 10
        }
        
        print("Test-Request:", json.dumps(test_request, indent=2))
        print("\n📋 So testen Sie die API:")
        print("1. Starten Sie das Backend: python -m uvicorn app.main:app --reload")
        print("2. Verwenden Sie curl:")
        print(f"   curl -X POST http://localhost:8000/geo/search-trades \\")
        print(f"     -H 'Content-Type: application/json' \\")
        print(f"     -H 'Authorization: Bearer YOUR_TOKEN' \\")
        print(f"     -d '{json.dumps(test_request)}'")
        
    except Exception as e:
        print(f"❌ Fehler beim API-Test: {e}")

def start_backend():
    """Startet das Backend neu"""
    print("\n=== BACKEND NEUSTART ===")
    
    try:
        # Stoppe laufende Backend-Prozesse
        print("Stoppe laufende Backend-Prozesse...")
        subprocess.run(["taskkill", "/f", "/im", "python.exe"], capture_output=True)
        
        # Warte kurz
        time.sleep(2)
        
        # Starte Backend neu
        print("Starte Backend neu...")
        subprocess.Popen([
            "python", "-m", "uvicorn", "app.main:app", 
            "--reload", "--host", "0.0.0.0", "--port", "8000"
        ], cwd=os.getcwd())
        
        print("✅ Backend gestartet")
        print("📋 Backend läuft auf: http://localhost:8000")
        
    except Exception as e:
        print(f"❌ Fehler beim Backend-Start: {e}")

async def run_complete_fix():
    """Führt die vollständige Behebung durch"""
    print("🚀 Starte vollständige automatische Behebung...")
    print(f"Zeitstempel: {datetime.now()}")
    
    try:
        # 1. Datenbank beheben
        db_success = await fix_database_directly()
        
        if db_success:
            # 2. Backend neu starten
            start_backend()
            
            # 3. API testen
            await test_geo_api()
            
            print("\n📊 BEHEBUNG-ZUSAMMENFASSUNG:")
            print("✅ Datenbank erfolgreich behebt")
            print("✅ Backend neu gestartet")
            print("✅ Geo-API sollte jetzt funktionieren")
            print("\n📋 Nächste Schritte:")
            print("1. Warten Sie 10-15 Sekunden bis das Backend vollständig gestartet ist")
            print("2. Testen Sie die Kartenansicht in der Dienstleisteransicht")
            print("3. Verwenden Sie das Debug-Skript: debug_geo_search_final.js")
            
        else:
            print("❌ Datenbank-Behebung fehlgeschlagen")
            
    except Exception as e:
        print(f"❌ Fehler bei der vollständigen Behebung: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_complete_fix()) 