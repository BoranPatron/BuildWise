import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.quote import Quote, QuoteStatus
from app.models.cost_position import CostPosition
from sqlalchemy import select

async def simple_test():
    """Einfacher Test der Datenbank"""
    async for db in get_db():
        print("🔍 Einfacher Datenbank-Test...")
        
        # 1. Zähle Angebote
        result = await db.execute(select(Quote))
        quotes = result.scalars().all()
        print(f"📋 Gesamte Angebote: {len(quotes)}")
        
        # 2. Zähle akzeptierte Angebote
        result = await db.execute(select(Quote).where(Quote.status == QuoteStatus.ACCEPTED))
        accepted_quotes = result.scalars().all()
        print(f"✅ Akzeptierte Angebote: {len(accepted_quotes)}")
        
        for quote in accepted_quotes:
            print(f"  - {quote.title} (Projekt: {quote.project_id})")
        
        # 3. Zähle Kostenpositionen
        result = await db.execute(select(CostPosition))
        cost_positions = result.scalars().all()
        print(f"💰 Kostenpositionen: {len(cost_positions)}")
        
        for cp in cost_positions:
            print(f"  - {cp.title} (Projekt: {cp.project_id}, Quote: {cp.quote_id})")
        
        # 4. Prüfe Projekt 4 spezifisch
        result = await db.execute(select(Quote).where(Quote.project_id == 4))
        project4_quotes = result.scalars().all()
        print(f"🏗️ Angebote für Projekt 4: {len(project4_quotes)}")
        
        result = await db.execute(select(CostPosition).where(CostPosition.project_id == 4))
        project4_cp = result.scalars().all()
        print(f"💰 Kostenpositionen für Projekt 4: {len(project4_cp)}")
        
        break

if __name__ == "__main__":
    asyncio.run(simple_test()) 