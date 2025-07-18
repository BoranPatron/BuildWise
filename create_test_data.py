#!/usr/bin/env python3
"""
Skript zum Erstellen von Testdaten für BuildWise
"""

import asyncio
from datetime import date
from sqlalchemy import delete
from app.core.database import AsyncSessionLocal
from app.models import User, Project, ProjectType, ProjectStatus, UserType
from app.core.security import get_password_hash

async def delete_existing_test_data():
    """Löscht bestehende Testdaten"""
    async with AsyncSessionLocal() as db:
        try:
            # Lösche bestehende Test-Benutzer
            test_emails = ['test@example.com', 'test-dienstleister@buildwise.de']
            for email in test_emails:
                await db.execute(
                    delete(User).where(User.email == email)
                )
                print(f"🗑️ Bestehender Benutzer gelöscht: {email}")
            
            await db.commit()
            print("✅ Bestehende Testdaten gelöscht")
        except Exception as e:
            print(f"⚠️ Fehler beim Löschen bestehender Daten: {e}")

async def create_test_data():
    """Erstellt Testdaten für die Anwendung"""
    async with AsyncSessionLocal() as db:
        try:
            # Lösche zuerst bestehende Testdaten
            await delete_existing_test_data()
            
            # Erstelle einen Test-Benutzer (Bauträger)
            test_user = User(
                email="test@example.com",
                hashed_password=get_password_hash("test123"),
                first_name="Test",
                last_name="User",
                user_type=UserType.PRIVATE,
                is_active=True,
                is_verified=True,
                data_processing_consent=True,
                privacy_policy_accepted=True,
                terms_accepted=True
            )
            db.add(test_user)
            await db.commit()
            await db.refresh(test_user)
            
            # Erstelle einen Test-Dienstleister
            test_service_provider = User(
                email="test-dienstleister@buildwise.de",
                hashed_password=get_password_hash("test1234"),
                first_name="Max",
                last_name="Mustermann",
                user_type=UserType.SERVICE_PROVIDER,
                is_active=True,
                is_verified=True,
                data_processing_consent=True,
                privacy_policy_accepted=True,
                terms_accepted=True,
                company_name="Mustermann Bau GmbH",
                company_address="Dienstleisterstraße 1, 12345 Musterstadt",
                company_phone="+49 123 456789",
                company_website="https://www.mustermann-bau.de"
            )
            db.add(test_service_provider)
            await db.commit()
            await db.refresh(test_service_provider)
            
            # Erstelle öffentliche Projekte
            public_projects = [
                Project(
                    owner_id=test_user.id,
                    name="Neubau Einfamilienhaus",
                    description="Modernes Einfamilienhaus mit 150m² Wohnfläche",
                    project_type=ProjectType.NEW_BUILD,
                    status=ProjectStatus.PLANNING,
                    address="Forchstrasse 6C, 8610 Uster, Schweiz",
                    property_size=500.0,
                    construction_area=150.0,
                    budget=350000.0,
                    is_public=True,
                    allow_quotes=True
                ),
                Project(
                    owner_id=test_user.id,
                    name="Dachgeschossausbau",
                    description="Ausbau des Dachgeschosses zu Wohnraum",
                    project_type=ProjectType.RENOVATION,
                    status=ProjectStatus.PREPARATION,
                    address="Forchstrasse 8A, 8610 Uster, Schweiz",
                    property_size=200.0,
                    construction_area=80.0,
                    budget=120000.0,
                    is_public=True,
                    allow_quotes=True
                ),
                Project(
                    owner_id=test_user.id,
                    name="Küchenrenovierung",
                    description="Komplette Renovierung der Küche",
                    project_type=ProjectType.REFURBISHMENT,
                    status=ProjectStatus.PLANNING,
                    address="Forchstrasse 12, 8610 Uster, Schweiz",
                    property_size=120.0,
                    construction_area=25.0,
                    budget=45000.0,
                    is_public=True,
                    allow_quotes=True
                )
            ]
            
            for project in public_projects:
                db.add(project)
            
            await db.commit()
            print("✅ Testdaten erfolgreich erstellt!")
            print(f"   Bauträger: {test_user.email} (Passwort: test123)")
            print(f"   Dienstleister: {test_service_provider.email} (Passwort: test1234)")
            print(f"   Öffentliche Projekte: {len(public_projects)}")
            
        except Exception as e:
            print(f"❌ Fehler beim Erstellen der Testdaten: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(create_test_data()) 