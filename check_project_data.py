#!/usr/bin/env python3
"""
Überprüft die Projektdaten in der Datenbank
"""

import asyncio
import sys
import os

# Pfad zum app-Verzeichnis hinzufügen
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import get_db
from app.models.project import Project
from sqlalchemy import select, text

async def check_project_data():
    """Überprüft die Projektdaten in der Datenbank"""
    
    print("📋 Überprüfe Projektdaten")
    print("=" * 50)
    
    async for db in get_db():
        try:
            # 1. Überprüfe alle Projekte
            print("📋 Schritt 1: Alle Projekte")
            result = await db.execute(select(Project))
            projects = result.scalars().all()
            
            print(f"   Gesamte Projekte: {len(projects)}")
            
            for i, project in enumerate(projects[:3]):  # Zeige nur die ersten 3
                print(f"   Projekt {i+1}:")
                print(f"     ID: {project.id}")
                print(f"     Name: {project.name}")
                print(f"     Typ: {project.project_type.value}")
                print(f"     Status: {project.status.value}")
                print(f"     Öffentlich: {project.is_public}")
                print(f"     Quotes erlaubt: {project.allow_quotes}")
                print(f"     Budget: {project.budget}")
                
                # Überprüfe alle Attribute
                print(f"     Alle Attribute:")
                for attr in dir(project):
                    if not attr.startswith('_') and not callable(getattr(project, attr)):
                        try:
                            value = getattr(project, attr)
                            if isinstance(value, (str, int, float, bool)) or value is None:
                                print(f"       {attr}: {value}")
                        except:
                            pass
                print()
            
            # 2. Überprüfe öffentliche Projekte
            print("🌍 Schritt 2: Öffentliche Projekte")
            result = await db.execute(
                select(Project).where(
                    Project.is_public == True,
                    Project.allow_quotes == True
                )
            )
            public_projects = result.scalars().all()
            
            print(f"   Öffentliche Projekte: {len(public_projects)}")
            
            for i, project in enumerate(public_projects):
                print(f"   Öffentliches Projekt {i+1}:")
                print(f"     ID: {project.id}")
                print(f"     Name: {project.name}")
                print(f"     Typ: {project.project_type.value}")
                print(f"     Status: {project.status.value}")
                print(f"     Budget: {project.budget}")
                print()
            
            # 3. Überprüfe Datenbank-Schema direkt
            print("🗄️ Schritt 3: Datenbank-Schema")
            result = await db.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'projects'
                ORDER BY ordinal_position
            """))
            
            columns = result.fetchall()
            print(f"   Projekte-Tabelle Spalten:")
            for col in columns:
                print(f"     {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
            
            # Überprüfe spezifisch nach address-Spalten
            address_columns = [col[0] for col in columns if 'address' in col[0].lower()]
            if address_columns:
                print(f"   📍 Address-bezogene Spalten: {address_columns}")
            else:
                print("   ❌ Keine address-bezogenen Spalten gefunden")
            
            break
            
        except Exception as e:
            print(f"❌ Fehler: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_project_data()) 