#!/usr/bin/env python3
"""
Skript um die Milestones und Quotes zu überprüfen
"""

import asyncio
import sys
import os

# Füge das aktuelle Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.milestone import Milestone
from sqlalchemy import select, text

async def check_milestone_quotes():
    """Überprüfe Milestones und Quotes"""
    try:
        async for db in get_db():
            print("🔍 Überprüfe Milestones...")
            
            # Alle Milestones anzeigen
            stmt = select(Milestone)
            result = await db.execute(stmt)
            milestones = result.scalars().all()
            
            print(f"📋 Gefundene Milestones: {len(milestones)}")
            for milestone in milestones:
                print(f"   ID: {milestone.id}, Titel: '{milestone.title}', Projekt: {milestone.project_id}, Status: {milestone.status}")
            
            # Spezifisch nach "Gas wasser scheisse" suchen
            stmt = select(Milestone).where(Milestone.title.ilike('%gas%wasser%scheisse%'))
            result = await db.execute(stmt)
            gas_milestone = result.scalar_one_or_none()
            
            if gas_milestone:
                print(f"\n✅ Gewerk 'Gas wasser scheisse' gefunden:")
                print(f"   ID: {gas_milestone.id}")
                print(f"   Titel: {gas_milestone.title}")
                print(f"   Projekt: {gas_milestone.project_id}")
                print(f"   Status: {gas_milestone.status}")
                
                # Quotes für dieses Gewerk suchen (mit raw SQL um Enum-Problem zu umgehen)
                stmt = text("SELECT id, title, status, total_amount, milestone_id FROM quotes WHERE milestone_id = :milestone_id")
                result = await db.execute(stmt, {"milestone_id": gas_milestone.id})
                quotes = result.fetchall()
                
                print(f"\n📋 Quotes für Milestone {gas_milestone.id}: {len(quotes)}")
                for quote in quotes:
                    print(f"   Quote ID: {quote.id}, Titel: '{quote.title}', Status: {quote.status}, Betrag: {quote.total_amount}€")
            else:
                print("\n❌ Gewerk 'Gas wasser scheisse' nicht gefunden")
                
                # Suche nach ähnlichen Titeln
                stmt = select(Milestone).where(Milestone.title.ilike('%gas%'))
                result = await db.execute(stmt)
                gas_milestones = result.scalars().all()
                
                if gas_milestones:
                    print("🔍 Ähnliche Milestones gefunden:")
                    for milestone in gas_milestones:
                        print(f"   ID: {milestone.id}, Titel: '{milestone.title}'")
                
                # Suche nach Milestones mit "wasser"
                stmt = select(Milestone).where(Milestone.title.ilike('%wasser%'))
                result = await db.execute(stmt)
                water_milestones = result.scalars().all()
                
                if water_milestones:
                    print("🔍 Milestones mit 'wasser' gefunden:")
                    for milestone in water_milestones:
                        print(f"   ID: {milestone.id}, Titel: '{milestone.title}'")
            
            # Alle Quotes anzeigen (mit raw SQL)
            print(f"\n📋 Alle Quotes:")
            stmt = text("SELECT id, title, status, total_amount, milestone_id FROM quotes")
            result = await db.execute(stmt)
            quotes = result.fetchall()
            
            print(f"Gefundene Quotes: {len(quotes)}")
            for quote in quotes:
                print(f"   ID: {quote.id}, Titel: '{quote.title}', Milestone: {quote.milestone_id}, Status: {quote.status}")
            
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_milestone_quotes()) 