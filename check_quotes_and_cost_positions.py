#!/usr/bin/env python3
"""
Analyse der Angebote und Kostenpositionen für Projekt 4
"""

import asyncio
import sys
import os
from sqlalchemy import text

# Füge das app-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models import Quote, QuoteStatus, CostPosition

async def analyze_quotes_and_cost_positions():
    """Analysiert Angebote und Kostenpositionen für Projekt 4"""
    try:
        async for db in get_db():
            print("🔍 Analysiere Angebote und Kostenpositionen für Projekt 4...")
            
            # 1. Alle Angebote für Projekt 4
            quotes_result = await db.execute(
                text("SELECT id, title, status, project_id FROM quotes WHERE project_id = 4")
            )
            quotes = quotes_result.fetchall()
            print(f"\n📋 Angebote für Projekt 4: {len(quotes)}")
            for quote in quotes:
                print(f"  - ID: {quote[0]}, Titel: {quote[1]}, Status: {quote[2]}")
            
            # 2. Akzeptierte Angebote
            accepted_quotes_result = await db.execute(
                text("SELECT id, title, status FROM quotes WHERE project_id = 4 AND status = 'accepted'")
            )
            accepted_quotes = accepted_quotes_result.fetchall()
            print(f"\n✅ Akzeptierte Angebote: {len(accepted_quotes)}")
            for quote in accepted_quotes:
                print(f"  - ID: {quote[0]}, Titel: {quote[1]}")
            
            # 3. Kostenpositionen für Projekt 4
            cost_positions_result = await db.execute(
                text("SELECT id, title, amount, quote_id, project_id FROM cost_positions WHERE project_id = 4")
            )
            cost_positions = cost_positions_result.fetchall()
            print(f"\n💰 Kostenpositionen für Projekt 4: {len(cost_positions)}")
            for cp in cost_positions:
                print(f"  - ID: {cp[0]}, Titel: {cp[1]}, Betrag: {cp[2]} EUR, Quote-ID: {cp[3]}")
            
            # 4. Kostenpositionen aus akzeptierten Angeboten
            accepted_cost_positions_result = await db.execute(text("""
                SELECT cp.id, cp.title, cp.amount, cp.quote_id, q.title as quote_title
                FROM cost_positions cp
                JOIN quotes q ON cp.quote_id = q.id
                WHERE cp.project_id = 4 AND q.status = 'accepted'
            """))
            accepted_cost_positions = accepted_cost_positions_result.fetchall()
            print(f"\n🎯 Kostenpositionen aus akzeptierten Angeboten: {len(accepted_cost_positions)}")
            for cp in accepted_cost_positions:
                print(f"  - ID: {cp[0]}, Titel: {cp[1]}, Betrag: {cp[2]} EUR, Quote: {cp[4]}")
            
            break
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(analyze_quotes_and_cost_positions()) 