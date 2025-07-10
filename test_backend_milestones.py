#!/usr/bin/env python3
"""
Test-Skript für Backend-Milestone-Funktion
"""

import asyncio
import sys
import os

# Füge das app-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.services.milestone_service import get_all_active_milestones

async def test_backend_milestones():
    """Testet die Backend-Milestone-Funktion direkt"""
    
    print("🔧 Teste Backend-Milestone-Funktion direkt")
    print("=" * 50)
    
    try:
        # Datenbankverbindung herstellen
        async for db in get_db():
            print("✅ Datenbankverbindung hergestellt")
            
            # Rufe alle aktiven Milestones ab
            print("\n📋 Rufe get_all_active_milestones() auf...")
            milestones = await get_all_active_milestones(db)
            
            print(f"✅ Funktion zurückgegeben: {len(milestones)} Milestones")
            
            if len(milestones) > 0:
                print("\n📋 Gefundene Milestones:")
                for i, milestone in enumerate(milestones, 1):
                    print(f"  {i}. ID: {milestone.id}")
                    print(f"     Titel: {milestone.title}")
                    print(f"     Status: {milestone.status}")
                    print(f"     Projekt-ID: {milestone.project_id}")
                    print(f"     Kategorie: {milestone.category}")
                    print(f"     Priorität: {milestone.priority}")
                    print()
            else:
                print("⚠️  Keine Milestones gefunden")
                
                # Debug: Prüfe alle Milestones ohne Filter
                print("\n🔍 Debug: Alle Milestones ohne Filter...")
                from sqlalchemy import select
                from app.models import Milestone, Project
                
                # Alle Milestones
                result = await db.execute(select(Milestone))
                all_milestones = result.scalars().all()
                print(f"  Alle Milestones: {len(all_milestones)}")
                
                for m in all_milestones:
                    print(f"    - ID: {m.id}, Status: '{m.status}', Projekt: {m.project_id}")
                
                # Alle Projekte
                result = await db.execute(select(Project))
                all_projects = result.scalars().all()
                print(f"\n  Alle Projekte: {len(all_projects)}")
                
                for p in all_projects:
                    print(f"    - ID: {p.id}, Name: '{p.name}', Öffentlich: {p.is_public}, Angebote: {p.allow_quotes}")
                
                # Milestones mit Projekt-Join
                print(f"\n  Milestones mit Projekt-Join:")
                result = await db.execute(
                    select(Milestone, Project)
                    .join(Project, Milestone.project_id == Project.id)
                )
                joined_milestones = result.fetchall()
                print(f"    Gefunden: {len(joined_milestones)}")
                
                for m, p in joined_milestones:
                    print(f"    - Milestone ID: {m.id}, Status: '{m.status}', Projekt: {p.name}, Öffentlich: {p.is_public}")
            
            break
            
    except Exception as e:
        print(f"❌ Fehler beim Testen: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Hauptfunktion"""
    print("🧪 Backend-Milestone-Test")
    print("=" * 60)
    
    # Führe den asynchronen Test aus
    asyncio.run(test_backend_milestones())
    
    print("\n✅ Test abgeschlossen")

if __name__ == "__main__":
    main() 