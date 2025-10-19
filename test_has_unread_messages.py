#!/usr/bin/env python3
"""Test-Skript für has_unread_messages"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models.milestone import Milestone

async def test_has_unread_messages():
    """Teste das Lesen von has_unread_messages"""
    
    # Datenbankverbindung
    engine = create_async_engine("sqlite+aiosqlite:///buildwise.db")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Lade Milestone mit ID 1
        result = await session.execute(select(Milestone).where(Milestone.id == 1))
        milestone = result.scalar_one_or_none()
        
        if milestone:
            print(f"Milestone gefunden: ID={milestone.id}, Title={milestone.title}")
            print(f"has_unread_messages: {milestone.has_unread_messages}")
            print(f"has_unread_messages type: {type(milestone.has_unread_messages)}")
            
            # Teste getattr
            has_unread = getattr(milestone, 'has_unread_messages', False)
            print(f"getattr result: {has_unread}")
            print(f"getattr type: {type(has_unread)}")
        else:
            print("Kein Milestone mit ID 1 gefunden")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_has_unread_messages())
