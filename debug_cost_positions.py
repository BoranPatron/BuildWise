import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func
from app.core.config import get_settings
from app.models.quote import Quote, QuoteStatus
from app.models.cost_position import CostPosition
from app.models.project import Project

async def debug_cost_positions():
    """Debug-Skript um Kostenpositionen und Angebote zu prüfen"""
    settings = get_settings()
    
    # Datenbankverbindung
    database_url = f"sqlite+aiosqlite:///{settings.db_name}"
    engine = create_async_engine(database_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        print("🔍 Debug: Prüfe Datenbank-Inhalt...")
        
        # 1. Prüfe alle Projekte
        projects_result = await db.execute(select(Project))
        projects = projects_result.scalars().all()
        print(f"📊 Projekte gefunden: {len(projects)}")
        for project in projects:
            print(f"  - Projekt {project.id}: {project.name}")
        
        # 2. Prüfe alle Angebote
        quotes_result = await db.execute(select(Quote))
        quotes = quotes_result.scalars().all()
        print(f"📋 Angebote gefunden: {len(quotes)}")
        for quote in quotes:
            print(f"  - Angebot {quote.id}: {quote.title} (Status: {quote.status}, Projekt: {quote.project_id})")
        
        # 3. Prüfe akzeptierte Angebote
        accepted_quotes_result = await db.execute(
            select(Quote).where(Quote.status == QuoteStatus.ACCEPTED)
        )
        accepted_quotes = accepted_quotes_result.scalars().all()
        print(f"✅ Akzeptierte Angebote: {len(accepted_quotes)}")
        for quote in accepted_quotes:
            print(f"  - Akzeptiert: {quote.title} (Projekt: {quote.project_id})")
        
        # 4. Prüfe alle Kostenpositionen
        cost_positions_result = await db.execute(select(CostPosition))
        cost_positions = cost_positions_result.scalars().all()
        print(f"💰 Kostenpositionen gefunden: {len(cost_positions)}")
        for cp in cost_positions:
            print(f"  - Kostenposition {cp.id}: {cp.title} (Projekt: {cp.project_id}, Quote: {cp.quote_id})")
        
        # 5. Prüfe Kostenpositionen für Projekt 4
        project4_cp_result = await db.execute(
            select(CostPosition).where(CostPosition.project_id == 4)
        )
        project4_cp = project4_cp_result.scalars().all()
        print(f"🏗️ Kostenpositionen für Projekt 4: {len(project4_cp)}")
        for cp in project4_cp:
            print(f"  - {cp.title} (Quote-ID: {cp.quote_id}, Status: {cp.status})")
        
        # 6. Prüfe akzeptierte Angebote für Projekt 4
        project4_quotes_result = await db.execute(
            select(Quote).where(
                Quote.project_id == 4,
                Quote.status == QuoteStatus.ACCEPTED
            )
        )
        project4_quotes = project4_quotes_result.scalars().all()
        print(f"📋 Akzeptierte Angebote für Projekt 4: {len(project4_quotes)}")
        for quote in project4_quotes:
            print(f"  - {quote.title} (ID: {quote.id})")
        
        # 7. Prüfe ob Kostenpositionen für akzeptierte Angebote existieren
        for quote in project4_quotes:
            cp_result = await db.execute(
                select(CostPosition).where(CostPosition.quote_id == quote.id)
            )
            cp = cp_result.scalar_one_or_none()
            if cp:
                print(f"✅ Kostenposition für Angebot {quote.id} gefunden: {cp.title}")
            else:
                print(f"❌ KEINE Kostenposition für Angebot {quote.id} gefunden!")

async def main():
    await debug_cost_positions()

if __name__ == "__main__":
    asyncio.run(main()) 