#!/usr/bin/env python3
"""
Skript zum Korrigieren der Projekt-ID einer Kostenposition
"""

import asyncio
import sys
import os

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models import CostPosition, Quote
from sqlalchemy import select, update

async def fix_cost_position_project():
    """Korrigiert die Projekt-ID einer Kostenposition"""
    print("🔧 Korrigiere Projekt-ID der Kostenposition")
    print("=" * 50)
    
    async for db in get_db():
        try:
            # Finde die Kostenposition mit Quote-ID 1
            cost_position_result = await db.execute(
                select(CostPosition).where(CostPosition.quote_id == 1)
            )
            cost_position = cost_position_result.scalar_one_or_none()
            
            if not cost_position:
                print("❌ Kostenposition mit Quote-ID 1 nicht gefunden")
                return
            
            print(f"📋 Gefundene Kostenposition:")
            print(f"  - ID: {cost_position.id}")
            print(f"  - Titel: {cost_position.title}")
            print(f"  - Aktuelle Projekt-ID: {cost_position.project_id}")
            print(f"  - Quote-ID: {cost_position.quote_id}")
            
            # Hole das zugehörige Quote
            quote_result = await db.execute(
                select(Quote).where(Quote.id == 1)
            )
            quote = quote_result.scalar_one_or_none()
            
            if not quote:
                print("❌ Quote mit ID 1 nicht gefunden")
                return
            
            print(f"📋 Zugehöriges Quote:")
            print(f"  - ID: {quote.id}")
            print(f"  - Titel: {quote.title}")
            print(f"  - Projekt-ID: {quote.project_id}")
            print(f"  - Status: {quote.status}")
            
            # Korrigiere die Projekt-ID
            if cost_position.project_id != quote.project_id:
                print(f"🔄 Korrigiere Projekt-ID von {cost_position.project_id} auf {quote.project_id}")
                
                await db.execute(
                    update(CostPosition)
                    .where(CostPosition.id == cost_position.id)
                    .values(project_id=quote.project_id)
                )
                
                await db.commit()
                
                # Bestätige die Änderung
                await db.refresh(cost_position)
                print(f"✅ Projekt-ID erfolgreich korrigiert: {cost_position.project_id}")
            else:
                print("ℹ️ Projekt-ID ist bereits korrekt")
            
            break
            
        except Exception as e:
            print(f"❌ Fehler: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(fix_cost_position_project()) 