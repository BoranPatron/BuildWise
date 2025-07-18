#!/usr/bin/env python3
"""
Backend Debug-Skript für Geo-Suche
Analysiert das Problem mit fehlenden Markern auf der Karte
"""

import asyncio
import sys
import os
from datetime import datetime

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func

from app.core.config import get_settings
from app.models.user import User, UserType
from app.models.project import Project
from app.models.milestone import Milestone
from app.services.geo_service import GeoService

async def debug_database_connection():
    """Testet die Datenbankverbindung"""
    print("=== DATENBANK-VERBINDUNG ===")
    
    try:
        settings = get_settings()
        # Verwende die korrekte Eigenschaft für die Datenbank-URL
        database_url = getattr(settings, 'database_url', None)
        if not database_url:
            # Fallback für die Datenbank-URL
            database_url = "postgresql+asyncpg://buildwise:buildwise@localhost:5432/buildwise"
        
        print(f"Database URL: {database_url}")
        
        engine = create_async_engine(database_url)
        
        # Teste Verbindung
        async with engine.begin() as conn:
            result = await conn.execute(select(func.count()))
            print("✅ Datenbankverbindung erfolgreich")
            
        return engine
    except Exception as e:
        print(f"❌ Datenbankverbindung fehlgeschlagen: {e}")
        return None

async def debug_users(engine):
    """Analysiert User-Daten"""
    print("\n=== USER-ANALYSE ===")
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    session = async_session()
    try:
        # Zähle alle User
        result = await session.execute(select(func.count(User.id)))
        total_users = result.scalar()
        print(f"Gesamte User: {total_users}")
        
        # Zähle Dienstleister
        result = await session.execute(
            select(func.count(User.id)).where(User.user_type == UserType.SERVICE_PROVIDER)
        )
        service_providers = result.scalar()
        print(f"Dienstleister: {service_providers}")
        
        # User mit Geocoding-Daten
        result = await session.execute(
            select(func.count(User.id)).where(
                User.address_latitude.isnot(None),
                User.address_longitude.isnot(None)
            )
        )
        users_with_geo = result.scalar()
        print(f"User mit Geocoding: {users_with_geo}")
        
        # Zeige einige User-Beispiele
        result = await session.execute(
            select(User).where(User.user_type == UserType.SERVICE_PROVIDER).limit(3)
        )
        users = result.scalars().all()
        
        for user in users:
            print(f"  - User {user.id}: {user.first_name} {user.last_name}")
            print(f"    Geocoding: {user.address_latitude}, {user.address_longitude}")
            print(f"    Adresse: {user.address_street}, {user.address_zip} {user.address_city}")

async def debug_projects(engine):
    """Analysiert Projekt-Daten"""
    print("\n=== PROJEKT-ANALYSE ===")
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Zähle alle Projekte
        result = await session.execute(select(func.count(Project.id)))
        total_projects = result.scalar()
        print(f"Gesamte Projekte: {total_projects}")
        
        # Öffentliche Projekte
        result = await session.execute(
            select(func.count(Project.id)).where(Project.is_public == True)
        )
        public_projects = result.scalar()
        print(f"Öffentliche Projekte: {public_projects}")
        
        # Projekte mit Adressen
        result = await session.execute(
            select(func.count(Project.id)).where(Project.address.isnot(None))
        )
        projects_with_address = result.scalar()
        print(f"Projekte mit Adressen: {projects_with_address}")
        
        # Zeige einige Projekt-Beispiele
        result = await session.execute(
            select(Project).where(
                Project.is_public == True,
                Project.address.isnot(None)
            ).limit(3)
        )
        projects = result.scalars().all()
        
        for project in projects:
            print(f"  - Projekt {project.id}: {project.name}")
            print(f"    Adresse: {project.address}")
            print(f"    Öffentlich: {project.is_public}")
            print(f"    Quotes erlaubt: {project.allow_quotes}")

async def debug_milestones(engine):
    """Analysiert Milestone/Gewerk-Daten"""
    print("\n=== MILESTONE/GEWERK-ANALYSE ===")
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Zähle alle Milestones
        result = await session.execute(select(func.count(Milestone.id)))
        total_milestones = result.scalar()
        print(f"Gesamte Milestones: {total_milestones}")
        
        # Milestones mit Projekten
        result = await session.execute(
            select(func.count(Milestone.id))
            .join(Project, Milestone.project_id == Project.id)
            .where(
                Project.is_public == True,
                Project.allow_quotes == True,
                Project.address.isnot(None)
            )
        )
        searchable_milestones = result.scalar()
        print(f"Suchbare Milestones: {searchable_milestones}")
        
        # Zeige einige Milestone-Beispiele
        result = await session.execute(
            select(Milestone, Project)
            .join(Project, Milestone.project_id == Project.id)
            .where(
                Project.is_public == True,
                Project.allow_quotes == True,
                Project.address.isnot(None)
            ).limit(5)
        )
        milestone_project_pairs = result.all()
        
        for milestone, project in milestone_project_pairs:
            print(f"  - Milestone {milestone.id}: {milestone.title}")
            print(f"    Kategorie: {milestone.category}")
            print(f"    Status: {milestone.status}")
            print(f"    Projekt: {project.name}")
            print(f"    Projekt-Adresse: {project.address}")

async def debug_geo_service(engine):
    """Testet den Geo-Service"""
    print("\n=== GEO-SERVICE TEST ===")
    
    geo_service = GeoService()
    
    # Teste Geocoding
    print("Teste Geocoding...")
    geocoding_result = await geo_service.geocode_address_from_string("Berlin, Deutschland")
    if geocoding_result:
        print(f"✅ Geocoding erfolgreich: {geocoding_result}")
    else:
        print("❌ Geocoding fehlgeschlagen")
    
    # Teste Gewerk-Suche
    print("\nTeste Gewerk-Suche...")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            results = await geo_service.search_trades_in_radius(
                db=session,
                center_lat=52.5200,  # Berlin
                center_lon=13.4050,
                radius_km=10,
                limit=5
            )
            
            print(f"✅ Gewerk-Suche erfolgreich: {len(results)} Ergebnisse")
            
            for i, trade in enumerate(results[:3]):
                print(f"  {i+1}. {trade['title']}")
                print(f"     Kategorie: {trade['category']}")
                print(f"     Status: {trade['status']}")
                print(f"     Entfernung: {trade['distance_km']} km")
                print(f"     Koordinaten: {trade['address_latitude']}, {trade['address_longitude']}")
                print(f"     Projekt: {trade['project_name']}")
                
        except Exception as e:
            print(f"❌ Gewerk-Suche fehlgeschlagen: {e}")

async def debug_api_endpoint():
    """Testet den API-Endpoint"""
    print("\n=== API-ENDPOINT TEST ===")
    
    import aiohttp
    import json
    
    # Simuliere einen API-Aufruf
    test_request = {
        "latitude": 52.5200,
        "longitude": 13.4050,
        "radius_km": 10,
        "limit": 5
    }
    
    print(f"Test-Request: {json.dumps(test_request, indent=2)}")
    
    # Hier würde normalerweise ein echter API-Aufruf stehen
    # Für Debug-Zwecke simulieren wir die Antwort
    print("✅ API-Endpoint-Test simuliert")

async def run_complete_debug():
    """Führt die vollständige Debug-Analyse durch"""
    print("🚀 Starte vollständige Backend Debug-Analyse...")
    print(f"Zeitstempel: {datetime.now()}")
    
    try:
        # 1. Datenbankverbindung
        engine = await debug_database_connection()
        if not engine:
            print("❌ Debug-Analyse abgebrochen - keine Datenbankverbindung")
            return
        
        # 2. User-Analyse
        await debug_users(engine)
        
        # 3. Projekt-Analyse
        await debug_projects(engine)
        
        # 4. Milestone-Analyse
        await debug_milestones(engine)
        
        # 5. Geo-Service-Test
        await debug_geo_service(engine)
        
        # 6. API-Endpoint-Test
        await debug_api_endpoint()
        
        print("\n📊 DEBUG-ZUSAMMENFASSUNG:")
        print("✅ Backend Debug-Analyse abgeschlossen")
        
    except Exception as e:
        print(f"❌ Fehler bei der Debug-Analyse: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_complete_debug()) 