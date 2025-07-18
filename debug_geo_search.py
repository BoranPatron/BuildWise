#!/usr/bin/env python3
"""
Debug-Skript für geo-basierte Umkreissuche
"""

import asyncio
import sys
import os

# Pfad zum app-Verzeichnis hinzufügen
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import get_db
from app.models.project import Project
from app.services.geo_service import geo_service
from sqlalchemy import select

async def debug_geo_search():
    """Debug-Funktion für geo-basierte Umkreissuche"""
    
    print("🔍 Debug: Geo-basierte Umkreissuche")
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
            # 1. Überprüfe alle öffentlichen Projekte
            print("📋 Schritt 1: Überprüfe öffentliche Projekte")
            result = await db.execute(
                select(Project).where(
                    Project.is_public == True,
                    Project.allow_quotes == True
                )
            )
            projects = result.scalars().all()
            
            print(f"   Gefundene öffentliche Projekte: {len(projects)}")
            
            for i, project in enumerate(projects[:5]):  # Zeige nur die ersten 5
                print(f"   Projekt {i+1}:")
                print(f"     ID: {project.id}")
                print(f"     Name: {project.name}")
                print(f"     Typ: {project.project_type.value}")
                print(f"     Status: {project.status.value}")
                print(f"     Budget: {project.budget}")
                
                # Überprüfe verfügbare Attribute
                print(f"     Verfügbare Attribute:")
                for attr in dir(project):
                    if not attr.startswith('_') and not callable(getattr(project, attr)):
                        try:
                            value = getattr(project, attr)
                            if attr in ['address', 'address_street', 'address_zip', 'address_city']:
                                print(f"       {attr}: {value}")
                        except:
                            pass
                print()
            
            # 2. Teste Geocoding für eine bekannte Adresse
            print("🌍 Schritt 2: Teste Geocoding")
            test_address = "Forchstrasse 6C, 8610 Uster, Schweiz"
            print(f"   Test-Adresse: {test_address}")
            
            geocoding_result = await geo_service.geocode_address_from_string(test_address)
            if geocoding_result:
                print(f"   ✅ Geocoding erfolgreich:")
                print(f"     Latitude: {geocoding_result['latitude']}")
                print(f"     Longitude: {geocoding_result['longitude']}")
                print(f"     Display Name: {geocoding_result['display_name']}")
                
                # Berechne Entfernung
                distance = geo_service.calculate_distance(
                    test_lat, test_lon,
                    geocoding_result['latitude'], geocoding_result['longitude']
                )
                print(f"     Entfernung zu Test-Koordinaten: {distance:.2f} km")
            else:
                print("   ❌ Geocoding fehlgeschlagen")
            
            print()
            
            # 3. Teste die Umkreissuche direkt
            print("🔍 Schritt 3: Teste Umkreissuche")
            search_results = await geo_service.search_projects_in_radius(
                db=db,
                center_lat=test_lat,
                center_lon=test_lon,
                radius_km=test_radius,
                limit=10
            )
            
            print(f"   Gefundene Projekte im Radius: {len(search_results)}")
            for i, result in enumerate(search_results):
                print(f"   Ergebnis {i+1}:")
                print(f"     ID: {result['id']}")
                print(f"     Name: {result['name']}")
                print(f"     Adresse: {result['address_street']}, {result['address_zip']} {result['address_city']}")
                print(f"     Koordinaten: {result['address_latitude']}, {result['address_longitude']}")
                print(f"     Entfernung: {result['distance_km']} km")
                print()
            
            # 4. Überprüfe Datenbank-Schema
            print("🗄️ Schritt 4: Überprüfe Datenbank-Schema")
            from sqlalchemy import inspect
            inspector = inspect(db.bind)
            
            if 'projects' in inspector.get_table_names():
                columns = inspector.get_columns('projects')
                print(f"   Projekte-Tabelle hat {len(columns)} Spalten:")
                for col in columns:
                    print(f"     {col['name']}: {col['type']}")
            else:
                print("   ❌ Projekte-Tabelle nicht gefunden")
            
            break
            
        except Exception as e:
            print(f"❌ Fehler: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_geo_search()) 