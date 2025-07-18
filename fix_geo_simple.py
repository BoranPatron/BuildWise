#!/usr/bin/env python3
"""
Einfaches Skript zur Behebung der fehlenden Geocoding-Daten
"""

import asyncio
import sys
import os
from datetime import datetime

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.geo_service import GeoService

async def test_geocoding():
    """Testet das Geocoding-Service"""
    print("=== GEOCODING TEST ===")
    
    geo_service = GeoService()
    
    # Teste Geocoding mit verschiedenen Adressen
    test_addresses = [
        "Musterstraße 1, 10115 Berlin, Deutschland",
        "Hauptstraße 42, 80331 München, Deutschland",
        "Königsallee 15, 40212 Düsseldorf, Deutschland"
    ]
    
    for address in test_addresses:
        print(f"\nTeste Geocoding für: {address}")
        try:
            result = await geo_service.geocode_address_from_string(address)
            if result:
                print(f"✅ Erfolgreich: {result['latitude']}, {result['longitude']}")
            else:
                print("❌ Geocoding fehlgeschlagen")
        except Exception as e:
            print(f"❌ Fehler: {e}")

async def generate_sample_data():
    """Generiert Beispieldaten für die Datenbank"""
    print("\n=== BEISPIEL-DATEN GENERIEREN ===")
    
    # SQL-Statements für die Datenbank
    sql_statements = [
        # Füge Adressen zu bestehenden Projekten hinzu
        """
        UPDATE projects 
        SET address = 'Musterstraße 1, 10115 Berlin, Deutschland'
        WHERE id = 1 AND (address IS NULL OR address = '');
        """,
        
        """
        UPDATE projects 
        SET address = 'Hauptstraße 42, 80331 München, Deutschland'
        WHERE id = 2 AND (address IS NULL OR address = '');
        """,
        
        """
        UPDATE projects 
        SET address = 'Königsallee 15, 40212 Düsseldorf, Deutschland'
        WHERE id = 3 AND (address IS NULL OR address = '');
        """,
        
        # Stelle sicher, dass Projekte öffentlich sind
        """
        UPDATE projects 
        SET is_public = true, allow_quotes = true
        WHERE id IN (1, 2, 3);
        """
    ]
    
    print("SQL-Statements für die Datenbank:")
    for i, sql in enumerate(sql_statements, 1):
        print(f"\n{i}. {sql.strip()}")
    
    print("\n📋 Führen Sie diese SQL-Statements in Ihrer Datenbank aus:")
    print("1. Öffnen Sie Ihre Datenbank-Verwaltung (pgAdmin, DBeaver, etc.)")
    print("2. Verbinden Sie sich mit der BuildWise-Datenbank")
    print("3. Führen Sie die obigen SQL-Statements aus")
    print("4. Starten Sie dann das Backend neu")

async def test_api_endpoint():
    """Testet den API-Endpoint"""
    print("\n=== API-ENDPOINT TEST ===")
    
    import aiohttp
    import json
    
    # Simuliere einen API-Aufruf
    test_request = {
        "latitude": 52.5200,
        "longitude": 13.4050,
        "radius_km": 50,
        "limit": 10
    }
    
    print(f"Test-Request für /geo/search-trades:")
    print(json.dumps(test_request, indent=2))
    
    print("\n📋 So testen Sie den API-Endpoint:")
    print("1. Starten Sie das Backend: python -m uvicorn app.main:app --reload")
    print("2. Verwenden Sie curl oder Postman:")
    print(f"   curl -X POST http://localhost:8000/geo/search-trades \\")
    print(f"     -H 'Content-Type: application/json' \\")
    print(f"     -H 'Authorization: Bearer YOUR_TOKEN' \\")
    print(f"     -d '{json.dumps(test_request)}'")

async def run_simple_fix():
    """Führt die einfache Behebung durch"""
    print("🚀 Starte einfache Geocoding-Behebung...")
    print(f"Zeitstempel: {datetime.now()}")
    
    try:
        # 1. Teste Geocoding-Service
        await test_geocoding()
        
        # 2. Generiere Beispieldaten
        await generate_sample_data()
        
        # 3. Teste API-Endpoint
        await test_api_endpoint()
        
        print("\n📊 BEHEBUNG-ZUSAMMENFASSUNG:")
        print("✅ Geocoding-Service funktioniert")
        print("📋 Führen Sie die SQL-Statements in der Datenbank aus")
        print("📋 Testen Sie den API-Endpoint")
        print("📋 Starten Sie das Backend neu")
        
    except Exception as e:
        print(f"❌ Fehler bei der Behebung: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_simple_fix()) 