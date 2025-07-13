#!/usr/bin/env python3
"""
Skript zum Erstellen von Test-Milestones für BuildWise auf Render.com
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Füge das Projektverzeichnis zum Python-Pfad hinzu
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import create_async_engine
from app.core.database import get_database_url
from app.models.base import Base
from app.models.milestone import Milestone
from app.models.project import Project
from app.models.user import User
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

async def create_test_milestones():
    """Erstellt Test-Milestones für Render.com"""
    print("🚀 Starte Test-Milestones-Erstellung für Render.com...")
    
    # Datenbank-URL für Render.com
    database_url = "sqlite+aiosqlite:////var/data/buildwise.db"
    print(f"📊 Datenbank-URL: {database_url}")
    
    # Erstelle Engine
    engine = create_async_engine(database_url, echo=True)
    
    try:
        # Verbinde zur Datenbank
        async with engine.begin() as conn:
            print("✅ Datenbankverbindung erfolgreich")
            
            # Erstelle Tabellen falls nicht vorhanden
            await conn.run_sync(Base.metadata.create_all)
            print("✅ Tabellen erstellt/überprüft")
        
        # Erstelle Session
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        async with async_session() as session:
            # Finde Admin-User und Test-Projekt
            admin_user = await session.get(User, 1)  # Admin-User
            test_project = await session.get(Project, 1)  # Test-Projekt
            
            if not admin_user:
                print("❌ Admin-User nicht gefunden")
                return
            if not test_project:
                print("❌ Test-Projekt nicht gefunden")
                return
            
            print(f"✅ Admin-User gefunden: {admin_user.email}")
            print(f"✅ Test-Projekt gefunden: {test_project.name}")
            
            # Erstelle Test-Milestones
            test_milestones = [
                {
                    "title": "Fundament",
                    "description": "Betonfundament für das Wohnhaus",
                    "project_id": test_project.id,
                    "status": "in_progress",
                    "priority": "critical",
                    "planned_date": datetime.utcnow() - timedelta(days=7),
                    "start_date": datetime.utcnow() - timedelta(days=10),
                    "category": "Bau",
                    "budget": 45000,
                    "is_critical": True,
                    "notify_on_completion": True,
                    "notes": "Fundament ist bereits zu 75% fertiggestellt"
                },
                {
                    "title": "Mauerwerk",
                    "description": "Hochziehen der Außenwände",
                    "project_id": test_project.id,
                    "status": "planned",
                    "priority": "high",
                    "planned_date": datetime.utcnow() + timedelta(days=3),
                    "category": "Bau",
                    "budget": 80000,
                    "is_critical": True,
                    "notify_on_completion": True,
                    "notes": "Mauerwerk beginnt in 3 Tagen"
                },
                {
                    "title": "Dachstuhl",
                    "description": "Holzdachstuhl mit Dacheindeckung",
                    "project_id": test_project.id,
                    "status": "planned",
                    "priority": "medium",
                    "planned_date": datetime.utcnow() + timedelta(days=10),
                    "category": "Dach",
                    "budget": 65000,
                    "is_critical": False,
                    "notify_on_completion": True,
                    "notes": "Dachstuhl wird nach Mauerwerk erstellt"
                },
                {
                    "title": "Elektroinstallation",
                    "description": "Vollständige Elektroinstallation für das Wohnhaus",
                    "project_id": test_project.id,
                    "status": "planned",
                    "priority": "high",
                    "planned_date": datetime.utcnow() + timedelta(days=14),
                    "category": "Elektro",
                    "budget": 25000,
                    "is_critical": True,
                    "notify_on_completion": True,
                    "notes": "Elektroinstallation nach Dachstuhl"
                },
                {
                    "title": "Sanitärinstallation",
                    "description": "Sanitär- und Heizungsinstallation",
                    "project_id": test_project.id,
                    "status": "planned",
                    "priority": "medium",
                    "planned_date": datetime.utcnow() + timedelta(days=21),
                    "category": "Sanitär",
                    "budget": 35000,
                    "is_critical": False,
                    "notify_on_completion": True,
                    "notes": "Sanitär parallel zur Elektroinstallation"
                }
            ]
            
            # Erstelle Milestones
            created_milestones = []
            for milestone_data in test_milestones:
                # Prüfe ob Milestone bereits existiert
                existing = await session.execute(
                    "SELECT id FROM milestones WHERE title = :title AND project_id = :project_id",
                    {"title": milestone_data["title"], "project_id": milestone_data["project_id"]}
                )
                
                if existing.fetchone():
                    print(f"ℹ️ Milestone '{milestone_data['title']}' bereits vorhanden")
                    continue
                
                # Erstelle neuen Milestone
                milestone = Milestone(**milestone_data)
                session.add(milestone)
                created_milestones.append(milestone_data["title"])
                print(f"✅ Milestone erstellt: {milestone_data['title']}")
            
            # Commit Änderungen
            await session.commit()
            
            print(f"🎉 {len(created_milestones)} neue Milestones erstellt:")
            for title in created_milestones:
                print(f"  - {title}")
            
            # Zeige alle Milestones an
            result = await session.execute("SELECT title, status, priority FROM milestones")
            all_milestones = result.fetchall()
            print(f"\n📊 Alle Milestones in der Datenbank ({len(all_milestones)}):")
            for milestone in all_milestones:
                print(f"  - {milestone[0]} ({milestone[1]}, {milestone[2]})")
    
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der Test-Milestones: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_test_milestones()) 