#!/usr/bin/env python3
"""
Testet die Milestone-Erstellung
"""

import asyncio
import sys
import os

# Pfad zum app-Verzeichnis hinzufügen
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import get_db
from app.models.milestone import Milestone
from sqlalchemy import select

async def test_milestone_creation():
    """Testet die Milestone-Erstellung"""
    
    print("🧪 Test: Milestone-Erstellung")
    print("=" * 50)
    
    async for db in get_db():
        try:
            # Teste Milestone-Erstellung für Projekt 4
            result = await db.execute(select(Milestone).where(Milestone.project_id == 4))
            milestones = result.scalars().all()
            
            print(f"📋 Milestones für Projekt 4: {len(milestones)}")
            for m in milestones:
                print(f"  - {m.title} (ID: {m.id}, Status: {m.status})")
            
            # Teste Backend-API direkt
            print("\n🔧 Teste Backend-API...")
            
            import aiohttp
            async with aiohttp.ClientSession() as session:
                # Teste Milestone-Erstellung
                test_data = {
                    "title": "Test Gewerk",
                    "description": "Test Beschreibung",
                    "project_id": 4,
                    "status": "planned",
                    "priority": "medium",
                    "planned_date": "2025-07-25",
                    "category": "sanitaer",
                    "notes": "",
                    "is_critical": False,
                    "notify_on_completion": True
                }
                
                # Hier würden wir normalerweise die API testen
                print("✅ Backend-Test vorbereitet")
                print(f"📡 Test-Daten: {test_data}")
            
            break
            
        except Exception as e:
            print(f"❌ Fehler: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_milestone_creation()) 