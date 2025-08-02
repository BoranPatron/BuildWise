#!/usr/bin/env python3
"""
Testet das Backend direkt für Milestone-Dokumente
"""

import asyncio
import sys
import os

# Füge das app-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.milestone import Milestone
from app.services.milestone_service import get_milestone_by_id

async def test_backend_milestone():
    print("🔍 Teste Backend Milestone-Service...")
    
    # Erstelle Datenbankverbindung
    DATABASE_URL = "sqlite+aiosqlite:///buildwise.db"
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as db:
            # Teste Milestone 1
            print("\n📋 Teste Milestone 1 (TEST_Bodenlegen):")
            milestone = await get_milestone_by_id(db, 1)
            if milestone:
                print(f"✅ Milestone geladen: {milestone.title}")
                print(f"📄 Documents: {milestone.documents}")
                print(f"📄 Shared Documents: {milestone.shared_document_ids}")
            else:
                print("❌ Milestone 1 nicht gefunden")
            
            # Teste Milestone 2
            print("\n📋 Teste Milestone 2 (tet):")
            milestone = await get_milestone_by_id(db, 2)
            if milestone:
                print(f"✅ Milestone geladen: {milestone.title}")
                print(f"📄 Documents: {milestone.documents}")
                print(f"📄 Shared Documents: {milestone.shared_document_ids}")
            else:
                print("❌ Milestone 2 nicht gefunden")
    
    except Exception as e:
        print(f"❌ Fehler: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_backend_milestone()) 