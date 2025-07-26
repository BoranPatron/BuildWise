#!/usr/bin/env python3
"""
Debug-Skript für BuildWise-Gebühr-Erstellung
Diagnostiziert warum BuildWise-Gebühren nicht erstellt werden
"""

import asyncio
import sys
import os
from datetime import datetime

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import select, text
from app.core.database import get_db
from app.models.quote import Quote, QuoteStatus
from app.models.buildwise_fee import BuildWiseFee
from app.models.cost_position import CostPosition
from app.services.buildwise_fee_service import BuildWiseFeeService
from app.core.config import settings

async def debug_buildwise_fee_creation():
    """Debug-Funktion für BuildWise-Gebühr-Erstellung"""
    
    print("🔍 Debug: BuildWise-Gebühr-Erstellung")
    print("=" * 50)
    
    # Erstelle Datenbankverbindung
    engine = create_async_engine(settings.DATABASE_URL)
    
    async with engine.begin() as conn:
        async with AsyncSession(conn) as db:
            
            # 1. Prüfe akzeptierte Quotes
            print("\n1. 📋 Akzeptierte Quotes:")
            accepted_quotes_query = select(Quote).where(Quote.status == QuoteStatus.ACCEPTED)
            accepted_quotes_result = await db.execute(accepted_quotes_query)
            accepted_quotes = accepted_quotes_result.scalars().all()
            
            print(f"   Gefunden: {len(accepted_quotes)} akzeptierte Quotes")
            for quote in accepted_quotes:
                print(f"   • Quote ID: {quote.id}, Betrag: {quote.total_amount} {quote.currency}")
            
            # 2. Prüfe existierende BuildWise-Gebühren
            print("\n2. 💰 Existierende BuildWise-Gebühren:")
            fees_query = select(BuildWiseFee)
            fees_result = await db.execute(fees_query)
            fees = fees_result.scalars().all()
            
            print(f"   Gefunden: {len(fees)} BuildWise-Gebühren")
            for fee in fees:
                print(f"   • Fee ID: {fee.id}, Quote ID: {fee.quote_id}, Betrag: {fee.fee_amount}")
            
            # 3. Prüfe Kostenpositionen
            print("\n3. 📊 Kostenpositionen:")
            cost_positions_query = select(CostPosition)
            cost_positions_result = await db.execute(cost_positions_query)
            cost_positions = cost_positions_result.scalars().all()
            
            print(f"   Gefunden: {len(cost_positions)} Kostenpositionen")
            for cp in cost_positions:
                print(f"   • CP ID: {cp.id}, Quote ID: {cp.quote_id}, Betrag: {cp.amount}")
            
            # 4. Finde Quotes ohne BuildWise-Gebühren
            print("\n4. 🔍 Quotes ohne BuildWise-Gebühren:")
            quotes_without_fees = []
            for quote in accepted_quotes:
                fee_query = select(BuildWiseFee).where(BuildWiseFee.quote_id == quote.id)
                fee_result = await db.execute(fee_query)
                fee = fee_result.scalar_one_or_none()
                
                if not fee:
                    quotes_without_fees.append(quote)
                    print(f"   • Quote ID: {quote.id} hat keine BuildWise-Gebühr")
            
            # 5. Versuche Gebühren für fehlende Quotes zu erstellen
            if quotes_without_fees:
                print(f"\n5. 🛠️ Erstelle fehlende BuildWise-Gebühren für {len(quotes_without_fees)} Quotes:")
                
                for quote in quotes_without_fees:
                    try:
                        # Finde oder erstelle Kostenposition
                        cost_position_query = select(CostPosition).where(CostPosition.quote_id == quote.id)
                        cost_position_result = await db.execute(cost_position_query)
                        cost_position = cost_position_result.scalar_one_or_none()
                        
                        if cost_position:
                            cost_position_id = cost_position.id
                            print(f"   ✅ Kostenposition {cost_position_id} für Quote {quote.id} gefunden")
                        else:
                            cost_position_id = quote.id  # Fallback
                            print(f"   ⚠️ Keine Kostenposition für Quote {quote.id}, verwende Quote-ID als Fallback")
                        
                        # Erstelle BuildWise-Gebühr
                        fee = await BuildWiseFeeService.create_fee_from_quote(
                            db=db,
                            quote_id=quote.id,
                            cost_position_id=cost_position_id,
                            fee_percentage=1.0
                        )
                        
                        print(f"   ✅ BuildWise-Gebühr {fee.id} für Quote {quote.id} erstellt")
                        
                    except Exception as e:
                        print(f"   ❌ Fehler beim Erstellen der Gebühr für Quote {quote.id}: {e}")
            else:
                print("   ✅ Alle akzeptierten Quotes haben bereits BuildWise-Gebühren")
            
            # 6. Finale Prüfung
            print("\n6. 📈 Finale Prüfung:")
            final_fees_query = select(BuildWiseFee)
            final_fees_result = await db.execute(final_fees_query)
            final_fees = final_fees_result.scalars().all()
            
            print(f"   BuildWise-Gebühren nach Reparatur: {len(final_fees)}")
            for fee in final_fees:
                print(f"   • Fee ID: {fee.id}, Quote ID: {fee.quote_id}, Status: {fee.status}, Betrag: {fee.fee_amount}")
    
    await engine.dispose()
    print("\n✅ Debug abgeschlossen")

if __name__ == "__main__":
    asyncio.run(debug_buildwise_fee_creation()) 