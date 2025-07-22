#!/usr/bin/env python3
"""
Debug-Skript für Finance-Analytics
Prüft die Datenherkunft und Logik der Diagramme
"""

import asyncio
import sys
import os

# Füge das app-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select, func, and_, extract
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date, timedelta

from app.core.database import get_db
from app.models.cost_position import CostPosition, CostCategory, CostStatus
from app.models.milestone import Milestone
from app.models.project import Project
from app.models.user import User


async def check_database_data():
    """Prüft die verfügbaren Daten in der Datenbank"""
    print("🔍 FINANCE-ANALYTICS DATEN-ÜBERPRÜFUNG")
    print("=" * 50)
    
    async for db in get_db():
        try:
            # Prüfe Projekte
            projects_result = await db.execute(select(Project))
            projects = projects_result.scalars().all()
            print(f"📊 Projekte gefunden: {len(projects)}")
            for project in projects:
                print(f"   - ID {project.id}: {project.name}")
            
            # Prüfe Kostenpositionen
            cost_positions_result = await db.execute(select(CostPosition))
            cost_positions = cost_positions_result.scalars().all()
            print(f"\n💰 Kostenpositionen gefunden: {len(cost_positions)}")
            
            if cost_positions:
                for cp in cost_positions:
                    print(f"   - ID {cp.id}: {cp.title}")
                    print(f"     Projekt: {cp.project_id}, Betrag: {cp.amount}€")
                    print(f"     Status: {cp.status}, Kategorie: {cp.category}")
                    print(f"     Bauphase: {cp.construction_phase}")
                    print(f"     Bezahlt: {cp.paid_amount}€, Fortschritt: {cp.progress_percentage}%")
                    print()
            else:
                print("   ⚠️  Keine Kostenpositionen gefunden!")
            
            # Prüfe Milestones
            milestones_result = await db.execute(select(Milestone))
            milestones = milestones_result.scalars().all()
            print(f"\n🎯 Milestones gefunden: {len(milestones)}")
            for milestone in milestones:
                print(f"   - ID {milestone.id}: {milestone.title}")
                print(f"     Projekt: {milestone.project_id}, Bauphase: {milestone.construction_phase}")
                print(f"     Budget: {milestone.budget}€, Aktuelle Kosten: {milestone.actual_costs}€")
                print()
            
            # Prüfe Daten für Projekt 1
            print("\n🔍 DETAIL-ANALYSE FÜR PROJEKT 1:")
            project_1_costs = await db.execute(
                select(CostPosition).where(CostPosition.project_id == 1)
            )
            project_1_costs = project_1_costs.scalars().all()
            print(f"   Kostenpositionen für Projekt 1: {len(project_1_costs)}")
            
            if project_1_costs:
                total_amount = sum(cp.amount for cp in project_1_costs)
                total_paid = sum(cp.paid_amount for cp in project_1_costs)
                print(f"   Gesamtbetrag: {total_amount}€")
                print(f"   Bezahlt: {total_paid}€")
                print(f"   Verbleibend: {total_amount - total_paid}€")
                
                # Prüfe Bauphasen
                phases = {}
                for cp in project_1_costs:
                    phase = cp.construction_phase or "Unbekannt"
                    if phase not in phases:
                        phases[phase] = {"count": 0, "amount": 0, "paid": 0}
                    phases[phase]["count"] += 1
                    phases[phase]["amount"] += cp.amount
                    phases[phase]["paid"] += cp.paid_amount
                
                print(f"\n   Bauphasen-Verteilung:")
                for phase, data in phases.items():
                    print(f"     {phase}: {data['count']} Positionen, {data['amount']}€, {data['paid']}€ bezahlt")
            
            # Prüfe API-Endpunkte
            print("\n🔍 API-ENDPUNKT-TEST:")
            
            # Teste Summary-Endpunkt
            from app.api.finance_analytics import get_finance_summary
            try:
                # Erstelle einen Mock-User für den Test
                mock_user = User(id=1, email="test@test.com", user_type="PRIVATE")
                summary_data = await get_finance_summary(1, db, mock_user)
                print("   ✅ Summary-Endpunkt funktioniert")
                print(f"   Gesamtbetrag: {summary_data['summary']['total_amount']}€")
                print(f"   Bezahlt: {summary_data['summary']['total_paid']}€")
                print(f"   Fortschritt: {summary_data['summary']['completion_percentage']}%")
            except Exception as e:
                print(f"   ❌ Summary-Endpunkt Fehler: {e}")
            
            # Teste Phasen-Endpunkt
            from app.api.finance_analytics import get_costs_by_construction_phase
            try:
                phases_data = await get_costs_by_construction_phase(1, db, mock_user)
                print("   ✅ Phasen-Endpunkt funktioniert")
                print(f"   Anzahl Phasen: {len(phases_data['phases'])}")
                for phase in phases_data['phases']:
                    print(f"     {phase['phase']}: {phase['total_amount']}€")
            except Exception as e:
                print(f"   ❌ Phasen-Endpunkt Fehler: {e}")
            
            # Teste Zeit-Endpunkt
            from app.api.finance_analytics import get_costs_over_time
            try:
                time_data = await get_costs_over_time(1, "monthly", 12, db, mock_user)
                print("   ✅ Zeit-Endpunkt funktioniert")
                print(f"   Anzahl Zeitpunkte: {len(time_data['time_data'])}")
            except Exception as e:
                print(f"   ❌ Zeit-Endpunkt Fehler: {e}")
            
            break
        except Exception as e:
            print(f"❌ Fehler bei der Datenbankabfrage: {e}")
            break


async def create_test_data():
    """Erstellt Testdaten für Finance-Analytics"""
    print("\n🔧 ERSTELLE TEST-DATEN FÜR FINANCE-ANALYTICS")
    print("=" * 50)
    
    async for db in get_db():
        try:
            # Prüfe ob Projekt 1 existiert
            project_result = await db.execute(select(Project).where(Project.id == 1))
            project = project_result.scalar_one_or_none()
            
            if not project:
                print("❌ Projekt 1 nicht gefunden!")
                return
            
            # Erstelle Test-Kostenpositionen für verschiedene Bauphasen
            test_cost_positions = [
                {
                    "title": "Fundamentarbeiten",
                    "amount": 25000.0,
                    "paid_amount": 15000.0,
                    "construction_phase": "Fundament",
                    "category": CostCategory.MASONRY,
                    "status": CostStatus.ACTIVE,
                    "progress_percentage": 60.0
                },
                {
                    "title": "Rohbau Wände",
                    "amount": 45000.0,
                    "paid_amount": 30000.0,
                    "construction_phase": "Rohbau",
                    "category": CostCategory.MASONRY,
                    "status": CostStatus.ACTIVE,
                    "progress_percentage": 70.0
                },
                {
                    "title": "Dachkonstruktion",
                    "amount": 35000.0,
                    "paid_amount": 20000.0,
                    "construction_phase": "Dach",
                    "category": CostCategory.ROOFING,
                    "status": CostStatus.ACTIVE,
                    "progress_percentage": 55.0
                },
                {
                    "title": "Elektroinstallation",
                    "amount": 28000.0,
                    "paid_amount": 15000.0,
                    "construction_phase": "Elektrik",
                    "category": CostCategory.ELECTRICAL,
                    "status": CostStatus.ACTIVE,
                    "progress_percentage": 50.0
                },
                {
                    "title": "Sanitäranlagen",
                    "amount": 22000.0,
                    "paid_amount": 10000.0,
                    "construction_phase": "Sanitär",
                    "category": CostCategory.PLUMBING,
                    "status": CostStatus.ACTIVE,
                    "progress_percentage": 45.0
                },
                {
                    "title": "Innenausbau Wände",
                    "amount": 18000.0,
                    "paid_amount": 8000.0,
                    "construction_phase": "Innenausbau",
                    "category": CostCategory.DRYWALL,
                    "status": CostStatus.ACTIVE,
                    "progress_percentage": 40.0
                },
                {
                    "title": "Fenster und Türen",
                    "amount": 32000.0,
                    "paid_amount": 25000.0,
                    "construction_phase": "Fenster",
                    "category": CostCategory.OTHER,
                    "status": CostStatus.COMPLETED,
                    "progress_percentage": 100.0
                },
                {
                    "title": "Außenanlagen",
                    "amount": 15000.0,
                    "paid_amount": 5000.0,
                    "construction_phase": "Außenanlagen",
                    "category": CostCategory.LANDSCAPING,
                    "status": CostStatus.ACTIVE,
                    "progress_percentage": 30.0
                }
            ]
            
            # Lösche existierende Kostenpositionen für Projekt 1
            await db.execute(
                select(CostPosition).where(CostPosition.project_id == 1)
            )
            
            # Erstelle neue Test-Kostenpositionen
            for i, test_data in enumerate(test_cost_positions):
                cost_position = CostPosition(
                    project_id=1,
                    title=test_data["title"],
                    amount=test_data["amount"],
                    paid_amount=test_data["paid_amount"],
                    construction_phase=test_data["construction_phase"],
                    category=test_data["category"],
                    status=test_data["status"],
                    progress_percentage=test_data["progress_percentage"],
                    created_at=datetime.now() - timedelta(days=30 - i * 3)  # Verschiedene Erstellungsdaten
                )
                db.add(cost_position)
            
            await db.commit()
            print("✅ Test-Kostenpositionen erstellt!")
            
            # Zeige die erstellten Daten
            print("\n📊 ERSTELLTE TEST-DATEN:")
            cost_positions_result = await db.execute(
                select(CostPosition).where(CostPosition.project_id == 1)
            )
            cost_positions = cost_positions_result.scalars().all()
            
            total_amount = sum(cp.amount for cp in cost_positions)
            total_paid = sum(cp.paid_amount for cp in cost_positions)
            
            print(f"   Gesamtbetrag: {total_amount:,.2f}€")
            print(f"   Bezahlt: {total_paid:,.2f}€")
            print(f"   Verbleibend: {total_amount - total_paid:,.2f}€")
            print(f"   Fortschritt: {(total_paid / total_amount * 100):.1f}%")
            
            # Zeige Bauphasen-Verteilung
            phases = {}
            for cp in cost_positions:
                phase = cp.construction_phase
                if phase not in phases:
                    phases[phase] = {"count": 0, "amount": 0, "paid": 0}
                phases[phase]["count"] += 1
                phases[phase]["amount"] += cp.amount
                phases[phase]["paid"] += cp.paid_amount
            
            print(f"\n   Bauphasen-Verteilung:")
            for phase, data in phases.items():
                print(f"     {phase}: {data['count']} Positionen, {data['amount']:,.2f}€, {data['paid']:,.2f}€ bezahlt")
            
            break
        except Exception as e:
            print(f"❌ Fehler beim Erstellen der Testdaten: {e}")
            await db.rollback()
            break


async def main():
    """Hauptfunktion"""
    print("🚀 FINANCE-ANALYTICS DEBUG TOOL")
    print("=" * 50)
    
    # Prüfe aktuelle Daten
    await check_database_data()
    
    # Frage nach Testdaten-Erstellung
    response = input("\n🤔 Möchten Sie Testdaten für Finance-Analytics erstellen? (j/n): ")
    if response.lower() in ['j', 'ja', 'y', 'yes']:
        await create_test_data()
        print("\n✅ Testdaten erstellt! Sie können jetzt die Finance-Analytics testen.")
    else:
        print("\nℹ️  Keine Testdaten erstellt. Verwenden Sie die vorhandenen Daten.")


if __name__ == "__main__":
    asyncio.run(main()) 