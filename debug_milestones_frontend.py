#!/usr/bin/env python3
"""
Skript um zu prüfen, welche Milestones für den Dienstleister verfügbar sind
"""

import asyncio
import sys
import os

# Füge das aktuelle Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.milestone import Milestone
from app.models.project import Project
from sqlalchemy import select

async def debug_milestones_frontend():
    """Prüfe welche Milestones für den Dienstleister verfügbar sind"""
    try:
        async for db in get_db():
            print("🔍 Debugging Milestones für Frontend...")
            
            # Alle Projekte anzeigen
            stmt = select(Project)
            result = await db.execute(stmt)
            projects = result.scalars().all()
            
            print(f"📋 Gefundene Projekte: {len(projects)}")
            for project in projects:
                print(f"   Projekt {project.id}: {project.name} (Status: {project.status})")
            
            # Alle Milestones anzeigen
            stmt = select(Milestone)
            result = await db.execute(stmt)
            milestones = result.scalars().all()
            
            print(f"\n📋 Gefundene Milestones: {len(milestones)}")
            for milestone in milestones:
                print(f"   Milestone {milestone.id}: {milestone.title}")
                print(f"     Projekt: {milestone.project_id}")
                print(f"     Status: {milestone.status}")
                print(f"     Beschreibung: {milestone.description}")
                print()
            
            # Prüfe welche Milestones für Dienstleister sichtbar sein sollten
            print("🔍 Milestones die für Dienstleister sichtbar sein sollten:")
            active_milestones = [m for m in milestones if m.status in ['PLANNED', 'IN_PROGRESS']]
            print(f"   Aktive Milestones (PLANNED/IN_PROGRESS): {len(active_milestones)}")
            
            for milestone in active_milestones:
                print(f"   ✅ {milestone.title} (Projekt {milestone.project_id}, Status: {milestone.status})")
            
            # Prüfe ob es Milestones ohne Projekt gibt
            milestones_without_project = [m for m in milestones if m.project_id is None]
            if milestones_without_project:
                print(f"\n⚠️ Milestones ohne Projekt: {len(milestones_without_project)}")
                for milestone in milestones_without_project:
                    print(f"   {milestone.title} (ID: {milestone.id})")
            
            # Prüfe ob es Projekte ohne Milestones gibt
            project_ids = {p.id for p in projects}
            milestone_project_ids = {m.project_id for m in milestones if m.project_id is not None}
            projects_without_milestones = project_ids - milestone_project_ids
            
            if projects_without_milestones:
                print(f"\n⚠️ Projekte ohne Milestones: {projects_without_milestones}")
            
            print("\n✅ Debug abgeschlossen")
            
    except Exception as e:
        print(f"❌ Fehler beim Debugging: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_milestones_frontend()) 