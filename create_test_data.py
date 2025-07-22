#!/usr/bin/env python3
"""
Skript zum Erstellen von Testdaten für BuildWise
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(str(Path(__file__).parent))

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.project import Project
from app.models.milestone import Milestone
from app.models.quote import Quote
from app.models.task import Task
from app.models.user import UserType, UserStatus
from sqlalchemy import select

async def create_test_data():
    """Erstellt Testdaten für BuildWise"""
    
    async with AsyncSessionLocal() as db:
        try:
            # Benutzer finden
            stmt = select(User).where(User.email == "admin@buildwise.de")
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                print("❌ Benutzer admin@buildwise.de nicht gefunden!")
                return None
            
            print(f"✅ Benutzer gefunden: {user.email}")
            
            # Test-Projekt erstellen
            project = Project(
                name="Test-Projekt Zürich",
                description="Ein Testprojekt für die Entwicklung",
                project_type="renovation",
                status="active",
                budget=50000,
                current_costs=15000,
                start_date=datetime.now().date(),
                end_date=(datetime.now() + timedelta(days=90)).date(),
                address="Bahnhofstrasse 1, 8001 Zürich",
                property_size=120,
                construction_area=80,
                estimated_duration=90,
                is_public=True,
                allow_quotes=True,
                owner_id=user.id,
                created_by=user.id
            )
            db.add(project)
            await db.commit()
            await db.refresh(project)
            
            print(f"✅ Projekt erstellt: {project.name}")
            
            # Test-Milestone erstellen
            milestone = Milestone(
                title="Grundausstattung",
                description="Installation der Grundausstattung",
                project_id=project.id,
                status="active",
                priority="high",
                planned_date=datetime.now().date(),
                start_date=datetime.now().date(),
                end_date=(datetime.now() + timedelta(days=30)).date(),
                category="installation",
                budget=20000,
                contractor="Test AG",
                is_critical=True,
                notify_on_completion=True,
                notes="Wichtiger Meilenstein",
                created_by=user.id
            )
            db.add(milestone)
            await db.commit()
            await db.refresh(milestone)
            
            print(f"✅ Milestone erstellt: {milestone.title}")
            
            # Test-Quote erstellen
            quote = Quote(
                title="Grundausstattung Angebot",
                description="Angebot für die Grundausstattung",
                project_id=project.id,
                milestone_id=milestone.id,
                service_provider_id=user.id,
                total_amount=18000,
                currency="EUR",
                valid_until=(datetime.now() + timedelta(days=30)).date(),
                labor_cost=12000,
                material_cost=5000,
                overhead_cost=1000,
                estimated_duration=25,
                start_date=datetime.now().date(),
                completion_date=(datetime.now() + timedelta(days=25)).date(),
                payment_terms="30 Tage netto",
                warranty_period=24,
                company_name="Test AG",
                contact_person="Max Mustermann",
                phone="+41 44 123 45 67",
                email="max@testag.ch",
                website="https://testag.ch",
                status="submitted",
                created_by=user.id
            )
            db.add(quote)
            await db.commit()
            await db.refresh(quote)
            
            print(f"✅ Quote erstellt: {quote.title}")
            
            # Test-Task erstellen
            task = Task(
                title="Elektroinstallation planen",
                description="Planung der Elektroinstallation",
                project_id=project.id,
                milestone_id=milestone.id,
                assigned_to=user.id,
                status="in_progress",
                priority="high",
                progress_percentage=30,
                due_date=(datetime.now() + timedelta(days=14)).date(),
                estimated_hours=16,
                actual_hours=5,
                category="planning",
                tags="elektro,planung",
                notes="Wichtige Aufgabe für das Projekt",
                created_by=user.id
            )
            db.add(task)
            await db.commit()
            await db.refresh(task)
            
            print(f"✅ Task erstellt: {task.title}")
            
            print(f"\n🎉 Testdaten erfolgreich erstellt!")
            print(f"📊 Erstellte Daten:")
            print(f"   - Projekt: {project.name}")
            print(f"   - Milestone: {milestone.title}")
            print(f"   - Quote: {quote.title}")
            print(f"   - Task: {task.title}")
            
            return {
                "project": project,
                "milestone": milestone,
                "quote": quote,
                "task": task
            }
            
        except Exception as e:
            print(f"❌ Fehler beim Erstellen der Testdaten: {e}")
            return None

async def main():
    """Hauptfunktion"""
    print("🚀 Erstelle Testdaten für BuildWise...")
    
    data = await create_test_data()
    
    if data:
        print("\n🎉 Testdaten erstellt! Das Frontend sollte jetzt Daten anzeigen.")
    else:
        print("\n❌ Fehler beim Erstellen der Testdaten!")

if __name__ == "__main__":
    asyncio.run(main()) 