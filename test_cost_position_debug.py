#!/usr/bin/env python3
"""
Debug-Skript für Kostenpositionen aus akzeptierten Angeboten
"""

import asyncio
import sys
import os

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.cost_position_service import get_cost_positions_from_accepted_quotes
from app.services.quote_service import get_quotes_for_project
from app.models import Quote, QuoteStatus, CostPosition

async def debug_cost_positions():
    """Debug-Funktion für Kostenpositionen"""
    print("🔍 Debug: Kostenpositionen aus akzeptierten Angeboten")
    print("=" * 60)
    
    async for db in get_db():
        try:
            # Teste für Projekt 5
            project_id = 5
            print(f"\n📊 Analysiere Projekt {project_id}:")
            
            # 1. Hole alle Angebote für das Projekt
            quotes = await get_quotes_for_project(db, project_id)
            print(f"📋 Gesamte Angebote für Projekt {project_id}: {len(quotes)}")
            
            for quote in quotes:
                print(f"  - Quote {quote.id}: {quote.title} (Status: {quote.status})")
            
            # 2. Hole akzeptierte Angebote
            accepted_quotes = [q for q in quotes if q.status == QuoteStatus.ACCEPTED]
            print(f"✅ Akzeptierte Angebote: {len(accepted_quotes)}")
            
            for quote in accepted_quotes:
                print(f"  - Quote {quote.id}: {quote.title} (Projekt: {quote.project_id})")
            
            # 3. Hole Kostenpositionen aus akzeptierten Angeboten
            cost_positions = await get_cost_positions_from_accepted_quotes(db, project_id)
            print(f"💰 Kostenpositionen aus akzeptierten Angeboten: {len(cost_positions)}")
            
            for cp in cost_positions:
                print(f"  - Kostenposition {cp.id}: {cp.title} (Quote: {cp.quote_id}, Projekt: {cp.project_id})")
            
            # 4. Prüfe alle Kostenpositionen für das Projekt
            from sqlalchemy import select
            all_cost_positions = await db.execute(
                select(CostPosition).where(CostPosition.project_id == project_id)
            )
            all_cps = all_cost_positions.scalars().all()
            print(f"📊 Alle Kostenpositionen für Projekt {project_id}: {len(all_cps)}")
            
            for cp in all_cps:
                print(f"  - Kostenposition {cp.id}: {cp.title} (Quote: {cp.quote_id}, Projekt: {cp.project_id})")
            
            # 5. Prüfe Quote-Status in der Datenbank
            from sqlalchemy import text
            status_check = await db.execute(
                text("SELECT id, title, status, project_id FROM quotes WHERE project_id = :project_id"),
                {"project_id": project_id}
            )
            print(f"\n🔍 Quote-Status in der Datenbank:")
            for row in status_check.fetchall():
                print(f"  - Quote {row[0]}: {row[1]} (Status: '{row[2]}', Projekt: {row[3]})")
            
            break
            
        except Exception as e:
            print(f"❌ Fehler: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_cost_positions()) 