#!/usr/bin/env python3
"""
Testet die geo-basierte Umkreissuche
"""

import asyncio
import sys
import os

# Pfad zum app-Verzeichnis hinzufügen
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import get_db
from app.services.geo_service import geo_service

async def test_geo_search():
    """Testet die geo-basierte Umkreissuche"""
    
    print("🔍 Test: Geo-basierte Umkreissuche")
    print("=" * 50)
    
    # Test-Koordinaten (Uster, Schweiz)
    test_lat = 47.3477
    test_lon = 8.7120
    test_radius = 50.0
    
    print(f"📍 Test-Koordinaten: {test_lat}, {test_lon}")
    print(f"🔍 Suchradius: {test_radius} km")
    print()
    
    async for db in get_db():
        try:
            # Teste die Umkreissuche
            print("🔍 Führe Umkreissuche durch...")
            search_results = await geo_service.search_projects_in_radius(
                db=db,
                center_lat=test_lat,
                center_lon=test_lon,
                radius_km=test_radius,
                limit=10
            )
            
            print(f"✅ Umkreissuche abgeschlossen")
            print(f"📋 Gefundene Projekte: {len(search_results)}")
            print()
            
            for i, result in enumerate(search_results):
                print(f"🏗️ Projekt {i+1}:")
                print(f"   ID: {result['id']}")
                print(f"   Name: {result['name']}")
                print(f"   Typ: {result['project_type']}")
                print(f"   Status: {result['status']}")
                print(f"   Adresse: {result['address_street']}, {result['address_zip']} {result['address_city']}")
                print(f"   Koordinaten: {result['address_latitude']}, {result['address_longitude']}")
                print(f"   Entfernung: {result['distance_km']} km")
                print(f"   Budget: {result['budget']} CHF")
                print()
            
            # Teste spezifische Entfernungen
            print("📏 Entfernungsanalyse:")
            for result in search_results:
                distance = result['distance_km']
                if distance <= 10:
                    print(f"   🟢 {result['name']}: {distance:.2f} km (sehr nah)")
                elif distance <= 25:
                    print(f"   🟡 {result['name']}: {distance:.2f} km (nah)")
                else:
                    print(f"   🔴 {result['name']}: {distance:.2f} km (weit)")
            
            break
            
        except Exception as e:
            print(f"❌ Fehler: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_geo_search()) 