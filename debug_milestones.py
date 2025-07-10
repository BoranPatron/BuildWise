import asyncio
import sqlalchemy
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text
import os
import sys

# Füge das BuildWise-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.join(os.path.dirname(__file__), 'BuildWise'))

from app.models import Milestone, MilestoneStatus, Project, User

async def debug_milestones():
    """Debug-Funktion um alle Milestones in der Datenbank zu prüfen"""
    
    # Erstelle Datenbankverbindung
    DATABASE_URL = "sqlite+aiosqlite:///buildwise.db"
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        # Prüfe alle Milestones
        result = await conn.execute(select(Milestone))
        all_milestones = result.fetchall()
        
        print(f"🔍 Gefundene Milestones in der Datenbank: {len(all_milestones)}")
        print("=" * 60)
        
        for milestone in all_milestones:
            print(f"ID: {milestone[0]}")
            print(f"Projekt ID: {milestone[1]}")
            print(f"Created By: {milestone[2]}")
            print(f"Titel: {milestone[3]}")
            print(f"Beschreibung: {milestone[4]}")
            print(f"Status: {milestone[5]}")
            print(f"Priorität: {milestone[6]}")
            print(f"Kategorie: {milestone[7]}")
            print(f"Geplantes Datum: {milestone[8]}")
            print("-" * 40)
        
        # Prüfe aktive Milestones (PLANNED oder IN_PROGRESS)
        active_result = await conn.execute(
            select(Milestone).where(
                Milestone.status.in_([MilestoneStatus.PLANNED, MilestoneStatus.IN_PROGRESS])
            )
        )
        active_milestones = active_result.fetchall()
        
        print(f"\n✅ Aktive Milestones (PLANNED/IN_PROGRESS): {len(active_milestones)}")
        print("=" * 60)
        
        for milestone in active_milestones:
            print(f"ID: {milestone[0]}")
            print(f"Titel: {milestone[3]}")
            print(f"Status: {milestone[5]}")
            print(f"Projekt ID: {milestone[1]}")
            print("-" * 40)
        
        # Prüfe alle Projekte
        project_result = await conn.execute(select(Project))
        projects = project_result.fetchall()
        
        print(f"\n📋 Projekte in der Datenbank: {len(projects)}")
        print("=" * 60)
        
        for project in projects:
            print(f"ID: {project[0]}")
            print(f"Name: {project[1]}")
            print(f"Owner ID: {project[2]}")
            print(f"Status: {project[3]}")
            print("-" * 40)
        
        # Prüfe alle User
        user_result = await conn.execute(select(User))
        users = user_result.fetchall()
        
        print(f"\n👥 User in der Datenbank: {len(users)}")
        print("=" * 60)
        
        for user in users:
            print(f"ID: {user[0]}")
            print(f"Email: {user[1]}")
            print(f"User Type: {user[2]}")
            print(f"First Name: {user[3]}")
            print(f"Last Name: {user[4]}")
            print("-" * 40)

if __name__ == "__main__":
    asyncio.run(debug_milestones()) 