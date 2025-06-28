#!/usr/bin/env python3
"""
Skript zum Erstellen der Datenbank-Tabellen für BuildWise
"""

import asyncio
from app.core.database import engine
from app.models import Base

async def create_tables():
    """Erstellt alle Datenbank-Tabellen"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Datenbank-Tabellen erfolgreich erstellt!")
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der Tabellen: {e}")

if __name__ == "__main__":
    asyncio.run(create_tables()) 