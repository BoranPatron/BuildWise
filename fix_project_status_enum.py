#!/usr/bin/env python3
"""
Fix Project Status Enum Script
Korrigiert alle Projekte mit ungültigem Status 'active' auf 'PLANNING'
"""

import asyncio
import sys
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_database_url
from app.models.project import Project

async def fix_project_status_enum():
    """Korrigiert alle Projekte mit ungültigem Status 'active'"""
    
    print("🔧 Starte Projekt-Status-Enum-Korrektur...")
    
    # Erstelle Datenbankverbindung
    database_url = get_database_url()
    engine = create_async_engine(database_url, echo=False)
    
    async_session = sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    
    try:
        async with async_session() as session:
            # Finde alle Projekte mit ungültigem Status 'active'
            result = await session.execute(
                text("SELECT id, name, status FROM projects WHERE status = 'active'")
            )
            projects_with_active_status = result.fetchall()
            
            if not projects_with_active_status:
                print("✅ Keine Projekte mit ungültigem Status 'active' gefunden.")
                return
            
            print(f"⚠️  Gefunden: {len(projects_with_active_status)} Projekte mit ungültigem Status 'active'")
            
            # Zeige betroffene Projekte
            for project in projects_with_active_status:
                print(f"   - Projekt {project.id}: '{project.name}' (Status: {project.status})")
            
            # Korrigiere alle Projekte auf 'PLANNING'
            await session.execute(
                text("UPDATE projects SET status = 'PLANNING' WHERE status = 'active'")
            )
            
            await session.commit()
            
            print("✅ Alle Projekte erfolgreich auf Status 'PLANNING' korrigiert!")
            
            # Bestätige die Änderungen
            result = await session.execute(
                text("SELECT id, name, status FROM projects WHERE status = 'PLANNING'")
            )
            updated_projects = result.fetchall()
            
            print(f"📊 Aktualisierte Projekte:")
            for project in updated_projects:
                print(f"   - Projekt {project.id}: '{project.name}' (Status: {project.status})")
                
    except Exception as e:
        print(f"❌ Fehler beim Korrigieren der Projekt-Status: {e}")
        raise
    finally:
        await engine.dispose()

async def check_project_statuses():
    """Prüft alle Projekt-Status in der Datenbank"""
    
    print("🔍 Prüfe alle Projekt-Status...")
    
    database_url = get_database_url()
    engine = create_async_engine(database_url, echo=False)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    try:
        async with async_session() as session:
            result = await session.execute(
                text("SELECT id, name, status FROM projects ORDER BY id")
            )
            projects = result.fetchall()
            
            if not projects:
                print("ℹ️  Keine Projekte in der Datenbank gefunden.")
                return
            
            print(f"📊 Gefunden: {len(projects)} Projekte")
            print("Status-Übersicht:")
            
            status_count = {}
            for project in projects:
                status = project.status
                status_count[status] = status_count.get(status, 0) + 1
                print(f"   - Projekt {project.id}: '{project.name}' (Status: {status})")
            
            print("\n📈 Status-Verteilung:")
            for status, count in status_count.items():
                print(f"   - {status}: {count} Projekte")
                
    except Exception as e:
        print(f"❌ Fehler beim Prüfen der Projekt-Status: {e}")
        raise
    finally:
        await engine.dispose()

async def main():
    """Hauptfunktion"""
    print("🚀 BuildWise - Projekt-Status-Enum-Korrektur")
    print("=" * 50)
    
    try:
        # Prüfe aktuelle Status
        await check_project_statuses()
        print("\n" + "=" * 50)
        
        # Korrigiere ungültige Status
        await fix_project_status_enum()
        print("\n" + "=" * 50)
        
        # Prüfe Status nach Korrektur
        await check_project_statuses()
        
        print("\n✅ Projekt-Status-Enum-Korrektur erfolgreich abgeschlossen!")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 