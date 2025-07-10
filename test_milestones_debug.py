#!/usr/bin/env python3
"""
Debug-Skript für Milestones/Ausschreibungen
Testet die get_all_active_milestones Funktion für Dienstleister
"""

import asyncio
import sys
import os

# Füge das BuildWise-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.services.milestone_service import get_all_active_milestones
from app.models import Milestone, Project
from sqlalchemy import select

async def test_milestones():
    """Testet die get_all_active_milestones Funktion"""
    print("🔍 Teste get_all_active_milestones Funktion...")
    
    async for db in get_db():
        try:
            # Debug: Zeige alle Projekte
            print("\n📋 Alle Projekte:")
            projects_result = await db.execute(select(Project))
            all_projects = list(projects_result.scalars().all())
            for p in all_projects:
                print(f"  - Projekt {p.id}: {p.name} (öffentlich: {p.is_public}, Quotes erlaubt: {p.allow_quotes})")
            
            # Debug: Zeige alle Milestones
            print("\n📋 Alle Milestones:")
            milestones_result = await db.execute(select(Milestone))
            all_milestones = list(milestones_result.scalars().all())
            for m in all_milestones:
                print(f"  - Milestone {m.id}: {m.title} (Status: {m.status}, Projekt: {m.project_id})")
            
            # Teste get_all_active_milestones
            print("\n🚀 Teste get_all_active_milestones...")
            active_milestones = await get_all_active_milestones(db)
            
            print(f"\n✅ Ergebnis: {len(active_milestones)} aktive Milestones gefunden")
            
            if active_milestones:
                print("\n📋 Gefundene aktive Milestones:")
                for milestone in active_milestones:
                    print(f"  - ID: {milestone.id}")
                    print(f"    Titel: {milestone.title}")
                    print(f"    Status: {milestone.status}")
                    print(f"    Projekt-ID: {milestone.project_id}")
                    print(f"    Geplantes Datum: {milestone.planned_date}")
                    print(f"    Beschreibung: {milestone.description}")
                    print("    ---")
            else:
                print("❌ Keine aktiven Milestones gefunden!")
                
        except Exception as e:
            print(f"❌ Fehler beim Testen: {e}")
            import traceback
            traceback.print_exc()
        finally:
            break

if __name__ == "__main__":
    asyncio.run(test_milestones()) 