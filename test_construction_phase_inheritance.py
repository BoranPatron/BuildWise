#!/usr/bin/env python3
"""
Test-Skript für Bauphasen-Vererbung bei Gewerken
"""

import asyncio
import sqlite3
from datetime import datetime, date
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

# Import der Modelle
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.milestone import Milestone, MilestoneStatus, MilestonePriority
from app.models.project import Project
from app.schemas.milestone import MilestoneCreate
from app.services.milestone_service import create_milestone

async def test_construction_phase_inheritance():
    """Testet die Bauphasen-Vererbung für Gewerke"""
    
    # SQLite-Verbindung
    engine = create_engine("sqlite:///buildwise.db")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    with SessionLocal() as db:
        try:
            print("🔧 Teste Bauphasen-Vererbung für Gewerke...")
            
            # 1. Zeige alle Projekte mit ihren Bauphasen
            print("\n📋 Projekte und ihre Bauphasen:")
            projects_result = db.execute(select(Project))
            projects = projects_result.scalars().all()
            
            for project in projects:
                print(f"  • Projekt {project.id}: '{project.name}' (Bauphase: {project.construction_phase or 'Nicht gesetzt'})")
            
            # 2. Zeige bestehende Gewerke
            print("\n📋 Bestehende Gewerke:")
            milestones_result = db.execute(select(Milestone))
            milestones = milestones_result.scalars().all()
            
            for milestone in milestones:
                print(f"  • Gewerk {milestone.id}: '{milestone.title}' (Projekt: {milestone.project_id}, Bauphase: {milestone.construction_phase or 'Nicht gesetzt'})")
            
            # 3. Teste Erstellung neuer Gewerke
            print("\n🏗️ Teste Erstellung neuer Gewerke...")
            
            # Finde ein Projekt mit Bauphase
            project_with_phase = None
            for project in projects:
                if project.construction_phase:
                    project_with_phase = project
                    break
            
            if project_with_phase:
                print(f"✅ Teste mit Projekt: {project_with_phase.name} (Bauphase: {project_with_phase.construction_phase})")
                
                # Erstelle ein Test-Gewerk
                test_milestone_data = MilestoneCreate(
                    project_id=project_with_phase.id,
                    title=f"Test Gewerk - {datetime.now().strftime('%H:%M:%S')}",
                    description="Test-Beschreibung für Bauphasen-Vererbung",
                    status=MilestoneStatus.PLANNED,
                    priority=MilestonePriority.MEDIUM,
                    category="test",
                    planned_date=date(2024, 8, 15),
                    budget=5000.00
                )
                
                # Erstelle das Gewerk (simuliere den Service-Aufruf)
                milestone_data = {
                    'project_id': test_milestone_data.project_id,
                    'created_by': 1,  # Test-User
                    'title': test_milestone_data.title,
                    'description': test_milestone_data.description,
                    'status': test_milestone_data.status,
                    'priority': test_milestone_data.priority,
                    'category': test_milestone_data.category,
                    'planned_date': test_milestone_data.planned_date,
                    'start_date': test_milestone_data.start_date,
                    'end_date': test_milestone_data.end_date,
                    'budget': test_milestone_data.budget,
                    'actual_costs': test_milestone_data.actual_costs,
                    'contractor': test_milestone_data.contractor,
                    'is_critical': test_milestone_data.is_critical,
                    'notify_on_completion': test_milestone_data.notify_on_completion,
                    'notes': test_milestone_data.notes
                }
                
                # Setze automatisch die aktuelle Bauphase des Projekts
                if project_with_phase.construction_phase:
                    milestone_data['construction_phase'] = project_with_phase.construction_phase
                    print(f"🏗️ Gewerk erstellt mit Bauphase: {project_with_phase.construction_phase}")
                else:
                    print(f"⚠️ Projekt hat keine Bauphase gesetzt")
                
                # Erstelle das Gewerk in der Datenbank
                milestone = Milestone(**milestone_data)
                db.add(milestone)
                db.commit()
                db.refresh(milestone)
                
                print(f"✅ Test-Gewerk erstellt:")
                print(f"  • ID: {milestone.id}")
                print(f"  • Titel: {milestone.title}")
                print(f"  • Projekt: {milestone.project_id}")
                print(f"  • Bauphase: {milestone.construction_phase}")
                print(f"  • Status: {milestone.status}")
                print(f"  • Priority: {milestone.priority}")
                
                # Lösche das Test-Gewerk
                db.delete(milestone)
                db.commit()
                print(f"🗑️ Test-Gewerk gelöscht")
                
            else:
                print("⚠️ Kein Projekt mit Bauphase gefunden")
            
            # 4. Teste mit Projekt ohne Bauphase
            print("\n🏗️ Teste mit Projekt ohne Bauphase...")
            
            project_without_phase = None
            for project in projects:
                if not project.construction_phase:
                    project_without_phase = project
                    break
            
            if project_without_phase:
                print(f"✅ Teste mit Projekt: {project_without_phase.name} (Bauphase: Nicht gesetzt)")
                
                # Erstelle ein Test-Gewerk
                test_milestone_data = MilestoneCreate(
                    project_id=project_without_phase.id,
                    title=f"Test Gewerk ohne Phase - {datetime.now().strftime('%H:%M:%S')}",
                    description="Test-Beschreibung für Projekt ohne Bauphase",
                    status=MilestoneStatus.PLANNED,
                    priority=MilestonePriority.LOW,
                    category="test",
                    planned_date=date(2024, 8, 20),
                    budget=3000.00
                )
                
                # Erstelle das Gewerk (simuliere den Service-Aufruf)
                milestone_data = {
                    'project_id': test_milestone_data.project_id,
                    'created_by': 1,  # Test-User
                    'title': test_milestone_data.title,
                    'description': test_milestone_data.description,
                    'status': test_milestone_data.status,
                    'priority': test_milestone_data.priority,
                    'category': test_milestone_data.category,
                    'planned_date': test_milestone_data.planned_date,
                    'start_date': test_milestone_data.start_date,
                    'end_date': test_milestone_data.end_date,
                    'budget': test_milestone_data.budget,
                    'actual_costs': test_milestone_data.actual_costs,
                    'contractor': test_milestone_data.contractor,
                    'is_critical': test_milestone_data.is_critical,
                    'notify_on_completion': test_milestone_data.notify_on_completion,
                    'notes': test_milestone_data.notes
                }
                
                # Setze automatisch die aktuelle Bauphase des Projekts
                if project_without_phase.construction_phase:
                    milestone_data['construction_phase'] = project_without_phase.construction_phase
                    print(f"🏗️ Gewerk erstellt mit Bauphase: {project_without_phase.construction_phase}")
                else:
                    print(f"⚠️ Projekt hat keine Bauphase gesetzt")
                
                # Erstelle das Gewerk in der Datenbank
                milestone = Milestone(**milestone_data)
                db.add(milestone)
                db.commit()
                db.refresh(milestone)
                
                print(f"✅ Test-Gewerk erstellt:")
                print(f"  • ID: {milestone.id}")
                print(f"  • Titel: {milestone.title}")
                print(f"  • Projekt: {milestone.project_id}")
                print(f"  • Bauphase: {milestone.construction_phase}")
                print(f"  • Status: {milestone.status}")
                print(f"  • Priority: {milestone.priority}")
                
                # Lösche das Test-Gewerk
                db.delete(milestone)
                db.commit()
                print(f"🗑️ Test-Gewerk gelöscht")
                
            else:
                print("⚠️ Kein Projekt ohne Bauphase gefunden")
            
            print("\n✅ Bauphasen-Vererbung Test abgeschlossen!")
            
        except Exception as e:
            print(f"❌ Fehler beim Test: {e}")
            import traceback
            traceback.print_exc()


def show_construction_phase_statistics():
    """Zeigt Statistiken zur Bauphasen-Verteilung"""
    print("\n📊 Bauphasen-Statistiken:")
    print("-" * 40)
    
    # SQLite-Verbindung
    conn = sqlite3.connect("buildwise.db")
    cursor = conn.cursor()
    
    try:
        # Projekte nach Bauphasen
        cursor.execute("""
            SELECT construction_phase, COUNT(*) 
            FROM projects 
            WHERE construction_phase IS NOT NULL AND construction_phase != ''
            GROUP BY construction_phase
        """)
        project_phases = cursor.fetchall()
        
        if project_phases:
            print("📋 Projekte nach Bauphasen:")
            for phase, count in project_phases:
                print(f"  • {phase}: {count} Projekte")
        else:
            print("📋 Keine Projekte mit Bauphasen gefunden")
        
        # Gewerke nach Bauphasen
        cursor.execute("""
            SELECT construction_phase, COUNT(*) 
            FROM milestones 
            WHERE construction_phase IS NOT NULL AND construction_phase != ''
            GROUP BY construction_phase
        """)
        milestone_phases = cursor.fetchall()
        
        if milestone_phases:
            print("\n📋 Gewerke nach Bauphasen:")
            for phase, count in milestone_phases:
                print(f"  • {phase}: {count} Gewerke")
        else:
            print("\n📋 Keine Gewerke mit Bauphasen gefunden")
        
        # Gewerke ohne Bauphase
        cursor.execute("""
            SELECT COUNT(*) 
            FROM milestones 
            WHERE construction_phase IS NULL OR construction_phase = ''
        """)
        milestones_without_phase = cursor.fetchone()[0]
        
        print(f"\n📋 Gewerke ohne Bauphase: {milestones_without_phase}")
        
    except Exception as e:
        print(f"❌ Fehler bei Statistiken: {e}")
    finally:
        conn.close()


async def main():
    """Hauptfunktion"""
    print("🏗️ Test Bauphasen-Vererbung für Gewerke")
    print("=" * 60)
    
    # Zeige Statistiken
    show_construction_phase_statistics()
    
    # Teste Vererbung
    await test_construction_phase_inheritance()


if __name__ == "__main__":
    asyncio.run(main()) 