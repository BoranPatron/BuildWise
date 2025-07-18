#!/usr/bin/env python3
"""
Aktualisiert Testdaten mit Geocoding-Informationen
"""

import asyncio
import sys
import os

# Pfad zum app-Verzeichnis hinzufügen
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import get_db
from app.models.project import Project
from app.services.geo_service import geo_service
from sqlalchemy import select, update
from datetime import datetime

async def update_test_data_with_geo():
    """Aktualisiert alle öffentlichen Projekte mit Geocoding-Daten"""
    
    print("🔄 Aktualisiere Projekte mit Geocoding...")
    
    async for db in get_db():
        try:
            # Lade alle öffentlichen Projekte
            result = await db.execute(
                select(Project).where(
                    Project.is_public == True,
                    Project.allow_quotes == True
                )
            )
            projects = result.scalars().all()
            
            print(f"📋 Gefundene öffentliche Projekte: {len(projects)}")
            
            updated_count = 0
            
            for project in projects:
                try:
                    print(f"🔄 Verarbeite Projekt {project.id}: {project.name}")
                    
                    # Setze Standard-Adresse für Testdaten
                    test_addresses = [
                        "Forchstrasse 6C, 8610 Uster, Schweiz",
                        "Bahnhofstrasse 15, 8001 Zürich, Schweiz", 
                        "Limmatquai 80, 8001 Zürich, Schweiz",
                        "Seestrasse 123, 8700 Küsnacht, Schweiz"
                    ]
                    
                    # Verwende eine der Test-Adressen basierend auf der Projekt-ID
                    address_index = (project.id - 1) % len(test_addresses)
                    test_address = test_addresses[address_index]
                    
                    print(f"   📍 Verwende Adresse: {test_address}")
                    
                    # Geocoding durchführen
                    geocoding_result = await geo_service.geocode_address_from_string(test_address)
                    
                    if geocoding_result:
                        # Adresse parsen
                        address_parts = geo_service.parse_address(test_address)
                        
                        # Projekt aktualisieren
                        await db.execute(
                            update(Project).where(Project.id == project.id).values(
                                address=test_address,
                                address_street=address_parts.get("street", ""),
                                address_zip=address_parts.get("zip", ""),
                                address_city=address_parts.get("city", ""),
                                address_country="Schweiz",
                                address_latitude=geocoding_result["latitude"],
                                address_longitude=geocoding_result["longitude"],
                                address_geocoded=True,
                                address_geocoding_date=datetime.utcnow()
                            )
                        )
                        
                        print(f"   ✅ Projekt {project.id} erfolgreich aktualisiert")
                        print(f"      Koordinaten: {geocoding_result['latitude']}, {geocoding_result['longitude']}")
                        updated_count += 1
                    else:
                        print(f"   ❌ Geocoding fehlgeschlagen für Projekt {project.id}")
                        
                except Exception as e:
                    print(f"   ❌ Fehler beim Aktualisieren von Projekt {project.id}: {str(e)}")
                    continue
            
            await db.commit()
            print(f"✅ Aktualisierung abgeschlossen: {updated_count} von {len(projects)} Projekten aktualisiert")
            
            break
            
        except Exception as e:
            print(f"❌ Fehler beim Aktualisieren: {str(e)}")
            await db.rollback()
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(update_test_data_with_geo()) 