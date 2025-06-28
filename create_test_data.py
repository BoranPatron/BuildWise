#!/usr/bin/env python3
"""
Skript zum Erstellen von Testdaten für BuildWise
"""

import asyncio
from datetime import date
from app.core.database import AsyncSessionLocal
from app.models import User, Project, ProjectType, ProjectStatus, UserType
from app.core.security import get_password_hash

async def create_test_data():
    """Erstellt Testdaten für die Anwendung"""
    async with AsyncSessionLocal() as db:
        try:
            # Erstelle einen Test-Benutzer
            test_user = User(
                email="test@example.com",
                hashed_password=get_password_hash("test123"),
                first_name="Test",
                last_name="User",
                user_type=UserType.PRIVATE,
                is_active=True,
                is_verified=True
            )
            db.add(test_user)
            await db.commit()
            await db.refresh(test_user)
            
            # Erstelle öffentliche Projekte
            public_projects = [
                Project(
                    owner_id=test_user.id,
                    name="Neubau Einfamilienhaus",
                    description="Modernes Einfamilienhaus mit 150m² Wohnfläche",
                    project_type=ProjectType.NEW_BUILD,
                    status=ProjectStatus.PLANNING,
                    address="Musterstraße 1, 12345 Musterstadt",
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
                    address="Beispielweg 10, 54321 Beispielort",
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
                    address="Testallee 5, 98765 Teststadt",
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
            print(f"   Benutzer: {test_user.email}")
            print(f"   Öffentliche Projekte: {len(public_projects)}")
            
        except Exception as e:
            print(f"❌ Fehler beim Erstellen der Testdaten: {e}")

if __name__ == "__main__":
    asyncio.run(create_test_data()) 