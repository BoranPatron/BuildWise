#!/usr/bin/env python3
"""
Debug-Script um zu überprüfen, ob Dokumente für Milestones in der Datenbank vorhanden sind
"""

import asyncio
import json
import sys
import os

# Füge das app-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import select
from app.core.database import get_db
from app.models.milestone import Milestone
from app.models.project import Project

async def check_milestone_documents():
    """Überprüft die Dokumente für alle Milestones"""
    
    # Erstelle eine Datenbankverbindung
    engine = create_async_engine("sqlite+aiosqlite:///buildwise.db")
    
    async with engine.begin() as conn:
        async with AsyncSession(conn) as session:
            print("🔍 Überprüfe alle Milestones und ihre Dokumente...")
            
            # Hole alle Milestones
            result = await session.execute(select(Milestone))
            milestones = result.scalars().all()
            
            print(f"📊 Gefundene Milestones: {len(milestones)}")
            
            for milestone in milestones:
                print(f"\n📋 Milestone ID {milestone.id}: {milestone.title}")
                print(f"   Projekt ID: {milestone.project_id}")
                print(f"   Status: {milestone.status}")
                print(f"   Documents Feld Typ: {type(milestone.documents)}")
                print(f"   Documents Feld Wert: {milestone.documents}")
                
                if milestone.documents:
                    try:
                        if isinstance(milestone.documents, str):
                            parsed_docs = json.loads(milestone.documents)
                            print(f"   ✅ Parsed Documents: {parsed_docs}")
                            print(f"   📄 Anzahl Dokumente: {len(parsed_docs) if isinstance(parsed_docs, list) else 'N/A'}")
                        elif isinstance(milestone.documents, list):
                            print(f"   ✅ Documents ist bereits Liste: {milestone.documents}")
                            print(f"   📄 Anzahl Dokumente: {len(milestone.documents)}")
                        else:
                            print(f"   ⚠️ Unbekannter Documents Typ: {type(milestone.documents)}")
                    except json.JSONDecodeError as e:
                        print(f"   ❌ JSON Parse Error: {e}")
                else:
                    print(f"   ❌ Keine Dokumente vorhanden")
            
            # Spezifische Überprüfung für Milestone ID 2
            print(f"\n🎯 Spezielle Überprüfung für Milestone ID 2:")
            milestone_2_result = await session.execute(select(Milestone).where(Milestone.id == 2))
            milestone_2 = milestone_2_result.scalar_one_or_none()
            
            if milestone_2:
                print(f"   📋 Milestone 2 gefunden: {milestone_2.title}")
                print(f"   📄 Documents: {milestone_2.documents}")
                print(f"   📄 Documents Typ: {type(milestone_2.documents)}")
                
                if milestone_2.documents:
                    try:
                        if isinstance(milestone_2.documents, str):
                            parsed_docs = json.loads(milestone_2.documents)
                            print(f"   ✅ Parsed Documents: {parsed_docs}")
                        elif isinstance(milestone_2.documents, list):
                            print(f"   ✅ Documents ist Liste: {milestone_2.documents}")
                        else:
                            print(f"   ⚠️ Unbekannter Typ: {type(milestone_2.documents)}")
                    except json.JSONDecodeError as e:
                        print(f"   ❌ JSON Parse Error: {e}")
                else:
                    print(f"   ❌ Keine Dokumente für Milestone 2")
            else:
                print(f"   ❌ Milestone mit ID 2 nicht gefunden")
            
            # Überprüfe auch die Projekte
            print(f"\n🏗️ Überprüfe Projekte:")
            projects_result = await session.execute(select(Project))
            projects = projects_result.scalars().all()
            
            for project in projects:
                print(f"   📋 Projekt ID {project.id}: {project.name}")
                print(f"   👤 Owner ID: {project.owner_id}")

if __name__ == "__main__":
    asyncio.run(check_milestone_documents()) 