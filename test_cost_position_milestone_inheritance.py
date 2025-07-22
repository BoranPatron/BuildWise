#!/usr/bin/env python3
"""
Test-Skript für Bauphasen-Vererbung von Gewerken zu Kostenpositionen
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
from app.models.cost_position import CostPosition, CostCategory, CostType, CostStatus
from app.models.project import Project
from app.schemas.cost_position import CostPositionCreate
from app.services.cost_position_service import create_cost_position

async def test_cost_position_milestone_inheritance():
    """Testet die Bauphasen-Vererbung von Gewerken zu Kostenpositionen"""
    
    # SQLite-Verbindung
    engine = create_engine("sqlite:///buildwise.db")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    with SessionLocal() as db:
        try:
            print("🔧 Teste Bauphasen-Vererbung von Gewerken zu Kostenpositionen...")
            
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
            
            # 3. Teste Erstellung von Kostenpositionen mit Gewerk-Verknüpfung
            print("\n🏗️ Teste Erstellung von Kostenpositionen mit Gewerk-Verknüpfung...")
            
            # Finde ein Gewerk mit Bauphase
            milestone_with_phase = None
            for milestone in milestones:
                if milestone.construction_phase:
                    milestone_with_phase = milestone
                    break
            
            if milestone_with_phase:
                print(f"✅ Teste mit Gewerk: {milestone_with_phase.title} (Bauphase: {milestone_with_phase.construction_phase})")
                
                # Erstelle eine Test-Kostenposition mit Gewerk-Verknüpfung
                test_cost_position_data = CostPositionCreate(
                    project_id=milestone_with_phase.project_id,
                    milestone_id=milestone_with_phase.id,  # Verknüpfung zum Gewerk
                    title=f"Test Kostenposition - {datetime.now().strftime('%H:%M:%S')}",
                    description="Test-Beschreibung für Bauphasen-Vererbung vom Gewerk",
                    amount=5000.00,
                    category=CostCategory.ELECTRICAL,
                    cost_type=CostType.MANUAL,
                    status=CostStatus.ACTIVE
                )
                
                # Erstelle die Kostenposition (simuliere den Service-Aufruf)
                cost_position_data = {
                    'project_id': test_cost_position_data.project_id,
                    'milestone_id': test_cost_position_data.milestone_id,
                    'title': test_cost_position_data.title,
                    'description': test_cost_position_data.description,
                    'amount': test_cost_position_data.amount,
                    'currency': test_cost_position_data.currency,
                    'category': test_cost_position_data.category,
                    'cost_type': test_cost_position_data.cost_type,
                    'status': test_cost_position_data.status,
                    'payment_terms': test_cost_position_data.payment_terms,
                    'warranty_period': test_cost_position_data.warranty_period,
                    'estimated_duration': test_cost_position_data.estimated_duration,
                    'start_date': test_cost_position_data.start_date,
                    'completion_date': test_cost_position_data.completion_date,
                    'contractor_name': test_cost_position_data.contractor_name,
                    'contractor_contact': test_cost_position_data.contractor_contact,
                    'contractor_phone': test_cost_position_data.contractor_phone,
                    'contractor_email': test_cost_position_data.contractor_email,
                    'contractor_website': test_cost_position_data.contractor_website,
                    'labor_cost': test_cost_position_data.labor_cost,
                    'material_cost': test_cost_position_data.material_cost,
                    'overhead_cost': test_cost_position_data.overhead_cost,
                    'notes': test_cost_position_data.notes
                }
                
                # Priorität 1: Bauphase vom verknüpften Gewerk (Milestone) erben
                if test_cost_position_data.milestone_id:
                    milestone_result = db.execute(
                        select(Milestone).where(Milestone.id == test_cost_position_data.milestone_id)
                    )
                    milestone = milestone_result.scalar_one_or_none()
                    
                    if milestone and milestone.construction_phase:
                        cost_position_data['construction_phase'] = milestone.construction_phase
                        print(f"🏗️ Kostenposition erstellt mit Bauphase vom Gewerk: {milestone.construction_phase}")
                    else:
                        print(f"⚠️ Verknüpftes Gewerk hat keine Bauphase gesetzt")
                
                # Priorität 2: Falls kein Gewerk verknüpft, Bauphase vom Projekt erben
                else:
                    project_result = db.execute(
                        select(Project).where(Project.id == test_cost_position_data.project_id)
                    )
                    project = project_result.scalar_one_or_none()
                    
                    if project and project.construction_phase:
                        cost_position_data['construction_phase'] = project.construction_phase
                        print(f"🏗️ Kostenposition erstellt mit Bauphase vom Projekt: {project.construction_phase}")
                    else:
                        print(f"⚠️ Projekt hat keine Bauphase gesetzt")
                
                # Erstelle die Kostenposition in der Datenbank
                cost_position = CostPosition(**cost_position_data)
                db.add(cost_position)
                db.commit()
                db.refresh(cost_position)
                
                print(f"✅ Test-Kostenposition erstellt:")
                print(f"  • ID: {cost_position.id}")
                print(f"  • Titel: {cost_position.title}")
                print(f"  • Projekt: {cost_position.project_id}")
                print(f"  • Gewerk: {cost_position.milestone_id}")
                print(f"  • Bauphase: {cost_position.construction_phase}")
                print(f"  • Betrag: {cost_position.amount} {cost_position.currency}")
                print(f"  • Kategorie: {cost_position.category}")
                
                # Lösche die Test-Kostenposition
                db.delete(cost_position)
                db.commit()
                print(f"🗑️ Test-Kostenposition gelöscht")
                
            else:
                print("⚠️ Kein Gewerk mit Bauphase gefunden")
            
            # 4. Teste Erstellung von Kostenpositionen ohne Gewerk-Verknüpfung
            print("\n🏗️ Teste Erstellung von Kostenpositionen ohne Gewerk-Verknüpfung...")
            
            # Finde ein Projekt mit Bauphase
            project_with_phase = None
            for project in projects:
                if project.construction_phase:
                    project_with_phase = project
                    break
            
            if project_with_phase:
                print(f"✅ Teste mit Projekt: {project_with_phase.name} (Bauphase: {project_with_phase.construction_phase})")
                
                # Erstelle eine Test-Kostenposition ohne Gewerk-Verknüpfung
                test_cost_position_data = CostPositionCreate(
                    project_id=project_with_phase.id,
                    # milestone_id=None  # Keine Gewerk-Verknüpfung
                    title=f"Test Kostenposition ohne Gewerk - {datetime.now().strftime('%H:%M:%S')}",
                    description="Test-Beschreibung für Bauphasen-Vererbung vom Projekt",
                    amount=3000.00,
                    category=CostCategory.MASONRY,
                    cost_type=CostType.MANUAL,
                    status=CostStatus.ACTIVE
                )
                
                # Erstelle die Kostenposition (simuliere den Service-Aufruf)
                cost_position_data = {
                    'project_id': test_cost_position_data.project_id,
                    'milestone_id': test_cost_position_data.milestone_id,
                    'title': test_cost_position_data.title,
                    'description': test_cost_position_data.description,
                    'amount': test_cost_position_data.amount,
                    'currency': test_cost_position_data.currency,
                    'category': test_cost_position_data.category,
                    'cost_type': test_cost_position_data.cost_type,
                    'status': test_cost_position_data.status,
                    'payment_terms': test_cost_position_data.payment_terms,
                    'warranty_period': test_cost_position_data.warranty_period,
                    'estimated_duration': test_cost_position_data.estimated_duration,
                    'start_date': test_cost_position_data.start_date,
                    'completion_date': test_cost_position_data.completion_date,
                    'contractor_name': test_cost_position_data.contractor_name,
                    'contractor_contact': test_cost_position_data.contractor_contact,
                    'contractor_phone': test_cost_position_data.contractor_phone,
                    'contractor_email': test_cost_position_data.contractor_email,
                    'contractor_website': test_cost_position_data.contractor_website,
                    'labor_cost': test_cost_position_data.labor_cost,
                    'material_cost': test_cost_position_data.material_cost,
                    'overhead_cost': test_cost_position_data.overhead_cost,
                    'notes': test_cost_position_data.notes
                }
                
                # Priorität 1: Bauphase vom verknüpften Gewerk (Milestone) erben
                if test_cost_position_data.milestone_id:
                    milestone_result = db.execute(
                        select(Milestone).where(Milestone.id == test_cost_position_data.milestone_id)
                    )
                    milestone = milestone_result.scalar_one_or_none()
                    
                    if milestone and milestone.construction_phase:
                        cost_position_data['construction_phase'] = milestone.construction_phase
                        print(f"🏗️ Kostenposition erstellt mit Bauphase vom Gewerk: {milestone.construction_phase}")
                    else:
                        print(f"⚠️ Verknüpftes Gewerk hat keine Bauphase gesetzt")
                
                # Priorität 2: Falls kein Gewerk verknüpft, Bauphase vom Projekt erben
                else:
                    project_result = db.execute(
                        select(Project).where(Project.id == test_cost_position_data.project_id)
                    )
                    project = project_result.scalar_one_or_none()
                    
                    if project and project.construction_phase:
                        cost_position_data['construction_phase'] = project.construction_phase
                        print(f"🏗️ Kostenposition erstellt mit Bauphase vom Projekt: {project.construction_phase}")
                    else:
                        print(f"⚠️ Projekt hat keine Bauphase gesetzt")
                
                # Erstelle die Kostenposition in der Datenbank
                cost_position = CostPosition(**cost_position_data)
                db.add(cost_position)
                db.commit()
                db.refresh(cost_position)
                
                print(f"✅ Test-Kostenposition erstellt:")
                print(f"  • ID: {cost_position.id}")
                print(f"  • Titel: {cost_position.title}")
                print(f"  • Projekt: {cost_position.project_id}")
                print(f"  • Gewerk: {cost_position.milestone_id}")
                print(f"  • Bauphase: {cost_position.construction_phase}")
                print(f"  • Betrag: {cost_position.amount} {cost_position.currency}")
                print(f"  • Kategorie: {cost_position.category}")
                
                # Lösche die Test-Kostenposition
                db.delete(cost_position)
                db.commit()
                print(f"🗑️ Test-Kostenposition gelöscht")
                
            else:
                print("⚠️ Kein Projekt mit Bauphase gefunden")
            
            print("\n✅ Bauphasen-Vererbung Test abgeschlossen!")
            
        except Exception as e:
            print(f"❌ Fehler beim Test: {e}")
            import traceback
            traceback.print_exc()


def show_cost_position_milestone_statistics():
    """Zeigt Statistiken zur Bauphasen-Verteilung von Kostenpositionen"""
    print("\n📊 Kostenpositionen Bauphasen-Statistiken:")
    print("-" * 50)
    
    # SQLite-Verbindung
    conn = sqlite3.connect("buildwise.db")
    cursor = conn.cursor()
    
    try:
        # Kostenpositionen nach Bauphasen
        cursor.execute("""
            SELECT construction_phase, COUNT(*) 
            FROM cost_positions 
            WHERE construction_phase IS NOT NULL AND construction_phase != ''
            GROUP BY construction_phase
        """)
        cost_position_phases = cursor.fetchall()
        
        if cost_position_phases:
            print("📋 Kostenpositionen nach Bauphasen:")
            for phase, count in cost_position_phases:
                print(f"  • {phase}: {count} Kostenpositionen")
        else:
            print("📋 Keine Kostenpositionen mit Bauphasen gefunden")
        
        # Kostenpositionen ohne Bauphase
        cursor.execute("""
            SELECT COUNT(*) 
            FROM cost_positions 
            WHERE construction_phase IS NULL OR construction_phase = ''
        """)
        cost_positions_without_phase = cursor.fetchone()[0]
        
        print(f"\n📋 Kostenpositionen ohne Bauphase: {cost_positions_without_phase}")
        
        # Kostenpositionen mit Gewerk-Verknüpfung
        cursor.execute("""
            SELECT COUNT(*) 
            FROM cost_positions 
            WHERE milestone_id IS NOT NULL
        """)
        cost_positions_with_milestone = cursor.fetchone()[0]
        
        print(f"📋 Kostenpositionen mit Gewerk-Verknüpfung: {cost_positions_with_milestone}")
        
        # Kostenpositionen ohne Gewerk-Verknüpfung
        cursor.execute("""
            SELECT COUNT(*) 
            FROM cost_positions 
            WHERE milestone_id IS NULL
        """)
        cost_positions_without_milestone = cursor.fetchone()[0]
        
        print(f"📋 Kostenpositionen ohne Gewerk-Verknüpfung: {cost_positions_without_milestone}")
        
    except Exception as e:
        print(f"❌ Fehler bei Statistiken: {e}")
    finally:
        conn.close()


async def main():
    """Hauptfunktion"""
    print("🏗️ Test Bauphasen-Vererbung von Gewerken zu Kostenpositionen")
    print("=" * 70)
    
    # Zeige Statistiken
    show_cost_position_milestone_statistics()
    
    # Teste Vererbung
    await test_cost_position_milestone_inheritance()


if __name__ == "__main__":
    asyncio.run(main()) 