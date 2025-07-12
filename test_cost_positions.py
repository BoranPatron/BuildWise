#!/usr/bin/env python3
"""
Test-Skript für CostPositions-Funktionalität
"""

import asyncio
import sys
import os

# Füge das app-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.services.cost_position_service import get_cost_positions_from_accepted_quotes

async def test_cost_positions():
    """Testet die CostPositions-Funktionalität"""
    try:
        async for db in get_db():
            print("🔍 Teste CostPositions für Projekt 4...")
            result = await get_cost_positions_from_accepted_quotes(db, 4)
            print(f"✅ Ergebnis: {len(result)} CostPositions gefunden")
            for cp in result:
                print(f"  - {cp.title}: {cp.amount} EUR")
            break
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_cost_positions()) 