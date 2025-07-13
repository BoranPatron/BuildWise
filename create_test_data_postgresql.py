#!/usr/bin/env python3
"""
Skript zum Erstellen von Testdaten in der PostgreSQL-Datenbank auf Render.com
"""

import os
import sys
import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import random

# Füge das app-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.config import settings
from app.models.user import User, UserType, UserStatus
from app.models.project import Project, ProjectType, ProjectStatus
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.milestone import Milestone, MilestoneStatus, MilestonePriority
from app.models.quote import Quote, QuoteStatus
from app.models.cost_position import CostPosition
from app.core.database import get_db

async def create_test_data():
    """Erstelle Testdaten in der PostgreSQL-Datenbank"""
    
    print("🔧 Starte Testdaten-Erstellung für PostgreSQL...")
    
    # Datenbankverbindung herstellen
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    try:
        with SessionLocal() as db:
            print("🔍 Prüfe bestehende Daten...")
            
            # Prüfe ob bereits Daten vorhanden sind
            existing_users = db.query(User).count()
            existing_projects = db.query(Project).count()
            
            if existing_users > 0 or existing_projects > 0:
                print(f"⚠️ Bereits {existing_users} Benutzer und {existing_projects} Projekte vorhanden")
                response = input("Möchten Sie die Datenbank zurücksetzen? (j/N): ")
                if response.lower() != 'j':
                    print("❌ Abgebrochen")
                    return
                
                # Datenbank zurücksetzen
                print("🗑️ Setze Datenbank zurück...")
                db.query(CostPosition).delete()
                db.query(Quote).delete()
                db.query(Milestone).delete()
                db.query(Task).delete()
                db.query(Project).delete()
                db.query(User).delete()
                db.commit()
                print("✅ Datenbank zurückgesetzt")
            
            print("👤 Erstelle Test-Benutzer...")
            
            # Admin-Benutzer erstellen
            admin_user = User(
                email="admin@buildwise.de",
                first_name="Admin",
                last_name="BuildWise",
                user_type=UserType.admin,
                status=UserStatus.active,
                is_verified=True,
                has_consented_gdpr=True,
                consent_date=datetime.utcnow()
            )
            admin_user.set_password("admin123")
            db.add(admin_user)
            
            # Service Provider erstellen
            service_provider = User(
                email="dienstleister@example.com",
                first_name="Max",
                last_name="Mustermann",
                user_type=UserType.service_provider,
                status=UserStatus.active,
                is_verified=True,
                has_consented_gdpr=True,
                consent_date=datetime.utcnow(),
                company_name="Mustermann Bau GmbH",
                company_address="Musterstraße 123, 12345 Musterstadt",
                company_phone="+49 123 456789",
                company_website="https://mustermann-bau.de",
                region="Bayern"
            )
            service_provider.set_password("dienstleister123")
            db.add(service_provider)
            
            db.commit()
            print("✅ Test-Benutzer erstellt")
            
            print("🏗️ Erstelle Test-Projekte...")
            
            # Projekt 1: Einfamilienhaus
            project1 = Project(
                name="Einfamilienhaus Musterstraße",
                description="Modernes Einfamilienhaus mit 4 Zimmern und Garten",
                project_type=ProjectType.new_build,
                status=ProjectStatus.execution,
                progress_percentage=65,
                budget=450000,
                current_costs=292500,
                address="Musterstraße 123, 12345 Musterstadt",
                property_size=800,
                construction_area=180,
                estimated_duration=12,
                is_public=True,
                allow_quotes=True,
                owner_id=admin_user.id
            )
            db.add(project1)
            
            # Projekt 2: Renovierung
            project2 = Project(
                name="Wohnungssanierung Altbau",
                description="Komplette Renovierung einer 3-Zimmer-Wohnung",
                project_type=ProjectType.renovation,
                status=ProjectStatus.planning,
                progress_percentage=25,
                budget=120000,
                current_costs=30000,
                address="Altbauweg 45, 54321 Altstadt",
                property_size=120,
                construction_area=85,
                estimated_duration=6,
                is_public=True,
                allow_quotes=True,
                owner_id=admin_user.id
            )
            db.add(project2)
            
            # Projekt 3: Anbau
            project3 = Project(
                name="Wintergarten-Anbau",
                description="Glasveranda mit Heizung und Belüftung",
                project_type=ProjectType.extension,
                status=ProjectStatus.preparation,
                progress_percentage=40,
                budget=85000,
                current_costs=34000,
                address="Gartenstraße 78, 98765 Gartenstadt",
                property_size=200,
                construction_area=25,
                estimated_duration=3,
                is_public=True,
                allow_quotes=True,
                owner_id=admin_user.id
            )
            db.add(project3)
            
            # Projekt 4: Sanierung
            project4 = Project(
                name="Denkmalschutz-Sanierung",
                description="Sanierung eines denkmalgeschützten Gebäudes",
                project_type=ProjectType.refurbishment,
                status=ProjectStatus.completion,
                progress_percentage=85,
                budget=280000,
                current_costs=238000,
                address="Denkmalplatz 1, 11111 Denkmalstadt",
                property_size=300,
                construction_area=220,
                estimated_duration=18,
                is_public=True,
                allow_quotes=True,
                owner_id=admin_user.id
            )
            db.add(project4)
            
            db.commit()
            print("✅ Test-Projekte erstellt")
            
            print("📋 Erstelle Test-Aufgaben...")
            
            # Aufgaben für Projekt 1
            tasks_project1 = [
                Task(
                    title="Fundament gießen",
                    description="Betonfundament für das Einfamilienhaus erstellen",
                    status=TaskStatus.completed,
                    priority=TaskPriority.high,
                    project_id=project1.id,
                    created_by=admin_user.id,
                    due_date=datetime.utcnow() - timedelta(days=30),
                    estimated_hours=40,
                    actual_hours=42,
                    progress_percentage=100,
                    is_milestone=True
                ),
                Task(
                    title="Rohbau errichten",
                    description="Mauerwerk und Dachstuhl errichten",
                    status=TaskStatus.in_progress,
                    priority=TaskPriority.high,
                    project_id=project1.id,
                    created_by=admin_user.id,
                    due_date=datetime.utcnow() + timedelta(days=15),
                    estimated_hours=120,
                    actual_hours=80,
                    progress_percentage=65,
                    is_milestone=True
                ),
                Task(
                    title="Elektroinstallation",
                    description="Elektrische Anlagen installieren",
                    status=TaskStatus.todo,
                    priority=TaskPriority.medium,
                    project_id=project1.id,
                    created_by=admin_user.id,
                    due_date=datetime.utcnow() + timedelta(days=30),
                    estimated_hours=60,
                    progress_percentage=0,
                    is_milestone=False
                )
            ]
            
            for task in tasks_project1:
                db.add(task)
            
            db.commit()
            print("✅ Test-Aufgaben erstellt")
            
            print("🎯 Erstelle Test-Meilensteine...")
            
            # Meilensteine für Projekt 1
            milestones_project1 = [
                Milestone(
                    title="Baugenehmigung erhalten",
                    description="Offizielle Baugenehmigung vom Bauamt",
                    project_id=project1.id,
                    status=MilestoneStatus.completed,
                    priority=MilestonePriority.critical,
                    planned_date=datetime.utcnow() - timedelta(days=90),
                    start_date=datetime.utcnow() - timedelta(days=95),
                    end_date=datetime.utcnow() - timedelta(days=85),
                    category="Rechtlich",
                    budget=5000,
                    contractor="Bauamt Musterstadt",
                    is_critical=True,
                    notify_on_completion=True
                ),
                Milestone(
                    title="Fundament fertig",
                    description="Betonfundament ist ausgehärtet und bereit",
                    project_id=project1.id,
                    status=MilestoneStatus.completed,
                    priority=MilestonePriority.high,
                    planned_date=datetime.utcnow() - timedelta(days=30),
                    start_date=datetime.utcnow() - timedelta(days=35),
                    end_date=datetime.utcnow() - timedelta(days=25),
                    category="Bauausführung",
                    budget=25000,
                    contractor="Betonbau GmbH",
                    is_critical=True,
                    notify_on_completion=True
                ),
                Milestone(
                    title="Rohbau fertig",
                    description="Mauerwerk und Dachstuhl sind fertiggestellt",
                    project_id=project1.id,
                    status=MilestoneStatus.in_progress,
                    priority=MilestonePriority.high,
                    planned_date=datetime.utcnow() + timedelta(days=15),
                    start_date=datetime.utcnow() - timedelta(days=20),
                    category="Bauausführung",
                    budget=80000,
                    contractor="Hochbau AG",
                    is_critical=True,
                    notify_on_completion=True
                )
            ]
            
            for milestone in milestones_project1:
                db.add(milestone)
            
            db.commit()
            print("✅ Test-Meilensteine erstellt")
            
            print("💰 Erstelle Test-Angebote...")
            
            # Angebote für Projekt 1
            quotes_project1 = [
                Quote(
                    title="Elektroinstallation Komplett",
                    description="Vollständige Elektroinstallation für Einfamilienhaus",
                    project_id=project1.id,
                    service_provider_id=service_provider.id,
                    total_amount=45000,
                    currency="EUR",
                    valid_until=datetime.utcnow() + timedelta(days=30),
                    labor_cost=25000,
                    material_cost=15000,
                    overhead_cost=5000,
                    estimated_duration=8,
                    start_date=datetime.utcnow() + timedelta(days=20),
                    completion_date=datetime.utcnow() + timedelta(days=28),
                    payment_terms="30 Tage netto",
                    warranty_period=24,
                    risk_score=2,
                    price_deviation=5.2,
                    ai_recommendation="Gutes Angebot mit fairer Preisgestaltung",
                    contact_released=True,
                    status=QuoteStatus.accepted,
                    accepted_at=datetime.utcnow() - timedelta(days=5)
                ),
                Quote(
                    title="Sanitärinstallation",
                    description="Sanitäranlagen und Heizungssystem",
                    project_id=project1.id,
                    service_provider_id=service_provider.id,
                    total_amount=38000,
                    currency="EUR",
                    valid_until=datetime.utcnow() + timedelta(days=45),
                    labor_cost=20000,
                    material_cost=15000,
                    overhead_cost=3000,
                    estimated_duration=6,
                    start_date=datetime.utcnow() + timedelta(days=25),
                    completion_date=datetime.utcnow() + timedelta(days=31),
                    payment_terms="50% Anzahlung, Rest bei Fertigstellung",
                    warranty_period=36,
                    risk_score=3,
                    price_deviation=8.1,
                    ai_recommendation="Höherer Preis, aber gute Qualität",
                    contact_released=True,
                    status=QuoteStatus.submitted,
                    submitted_at=datetime.utcnow() - timedelta(days=2)
                )
            ]
            
            for quote in quotes_project1:
                db.add(quote)
            
            db.commit()
            print("✅ Test-Angebote erstellt")
            
            print("💼 Erstelle Test-Kostenpositionen...")
            
            # Kostenpositionen aus akzeptierten Angeboten
            cost_positions = [
                CostPosition(
                    title="Elektroinstallation Komplett",
                    description="Vollständige Elektroinstallation für Einfamilienhaus",
                    amount=45000,
                    currency="EUR",
                    category="Elektro",
                    cost_type="installation",
                    status="in_progress",
                    contractor_name="Mustermann Bau GmbH",
                    contractor_contact="Max Mustermann",
                    contractor_phone="+49 123 456789",
                    contractor_email="max@mustermann-bau.de",
                    contractor_website="https://mustermann-bau.de",
                    progress_percentage=65,
                    paid_amount=29250,
                    payment_terms="30 Tage netto",
                    warranty_period=24,
                    estimated_duration=8,
                    start_date=datetime.utcnow() - timedelta(days=10),
                    completion_date=datetime.utcnow() + timedelta(days=18),
                    labor_cost=25000,
                    material_cost=15000,
                    overhead_cost=5000,
                    risk_score=2,
                    price_deviation=5.2,
                    ai_recommendation="Gutes Angebot mit fairer Preisgestaltung",
                    quote_id=quotes_project1[0].id,
                    project_id=project1.id
                )
            ]
            
            for cost_position in cost_positions:
                db.add(cost_position)
            
            db.commit()
            print("✅ Test-Kostenpositionen erstellt")
            
            print("📊 Datenbank-Statistik:")
            print(f"   👤 Benutzer: {db.query(User).count()}")
            print(f"   🏗️ Projekte: {db.query(Project).count()}")
            print(f"   📋 Aufgaben: {db.query(Task).count()}")
            print(f"   🎯 Meilensteine: {db.query(Milestone).count()}")
            print(f"   💰 Angebote: {db.query(Quote).count()}")
            print(f"   💼 Kostenpositionen: {db.query(CostPosition).count()}")
            
            print("\n✅ Testdaten erfolgreich erstellt!")
            print("\n🔑 Login-Daten:")
            print("   Admin: admin@buildwise.de / admin123")
            print("   Dienstleister: dienstleister@example.com / dienstleister123")
            
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der Testdaten: {e}")
        raise
    finally:
        engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_test_data()) 