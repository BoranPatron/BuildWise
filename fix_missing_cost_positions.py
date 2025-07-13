#!/usr/bin/env python3
"""
Skript zum Erstellen fehlender Kostenpositionen für akzeptierte Angebote
"""

import asyncio
import sys
import os

# Füge das Backend-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models import Quote, CostPosition
from app.services.quote_service import create_cost_position_from_quote


async def fix_missing_cost_positions():
    """Erstellt fehlende Kostenpositionen für akzeptierte Angebote"""
    async with AsyncSessionLocal() as db:
        print("🔍 Prüfe fehlende Kostenpositionen...")
        
        # Hole alle akzeptierten Angebote
        result = await db.execute(
            select(Quote).where(Quote.status == "ACCEPTED")
        )
        accepted_quotes = result.scalars().all()
        
        print(f"📊 Gefundene akzeptierte Angebote: {len(accepted_quotes)}")
        
        # Prüfe für jedes akzeptierte Angebot, ob eine Kostenposition existiert
        missing_quotes = []
        for quote in accepted_quotes:
            # Prüfe, ob bereits eine Kostenposition für dieses Quote existiert
            cost_position_result = await db.execute(
                select(CostPosition).where(CostPosition.quote_id == quote.id)
            )
            existing_cost_position = cost_position_result.scalar_one_or_none()
            
            if not existing_cost_position:
                missing_quotes.append(quote)
                print(f"❌ Fehlende Kostenposition für Quote ID {quote.id}: {quote.title}")
            else:
                print(f"✅ Kostenposition existiert für Quote ID {quote.id}: {quote.title}")
        
        if not missing_quotes:
            print("🎉 Alle Kostenpositionen sind bereits vorhanden!")
            return
        
        print(f"\n🔧 Erstelle {len(missing_quotes)} fehlende Kostenpositionen...")
        
        # Erstelle fehlende Kostenpositionen
        for quote in missing_quotes:
            try:
                print(f"📝 Erstelle Kostenposition für Quote ID {quote.id}: {quote.title}")
                success = await create_cost_position_from_quote(db, quote)
                
                if success:
                    print(f"✅ Kostenposition für Quote ID {quote.id} erfolgreich erstellt")
                else:
                    print(f"❌ Fehler beim Erstellen der Kostenposition für Quote ID {quote.id}")
                    
            except Exception as e:
                print(f"❌ Fehler beim Erstellen der Kostenposition für Quote ID {quote.id}: {e}")
        
        print("\n📊 Zusammenfassung:")
        print(f"- Akzeptierte Angebote: {len(accepted_quotes)}")
        print(f"- Fehlende Kostenpositionen: {len(missing_quotes)}")
        print(f"- Erstellte Kostenpositionen: {len([q for q in missing_quotes if True])}")


if __name__ == "__main__":
    print("🚀 Starte Fix für fehlende Kostenpositionen...")
    asyncio.run(fix_missing_cost_positions())
    print("✅ Fertig!") 