#!/usr/bin/env python3
"""
Test-Skript für den kompletten BuildWise-Gebühren-Flow
"""

import asyncio
import sys
import os

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import AsyncSessionLocal
from app.models.quote import Quote, QuoteStatus
from app.models.cost_position import CostPosition
from app.models.buildwise_fee import BuildWiseFee
from app.services.buildwise_fee_service import BuildWiseFeeService
from sqlalchemy import text, select

async def test_complete_flow():
    """Testet den kompletten Flow von Angebot zu Gebühr"""
    
    async with AsyncSessionLocal() as db:
        try:
            print("🔍 Prüfe aktuelle Daten...")
            
            # Prüfe Angebote
            quotes = await db.execute(text("SELECT id, title, status, project_id, total_amount FROM quotes"))
            quotes = quotes.fetchall()
            print(f"📋 Verfügbare Angebote: {len(quotes)}")
            for q in quotes:
                print(f"  - ID: {q[0]}, Titel: {q[1]}, Status: {q[2]}, Projekt: {q[3]}, Betrag: {q[4]}")
            
            # Prüfe Kostenpositionen
            cost_positions = await db.execute(text("SELECT id, project_id, title, amount, quote_id FROM cost_positions"))
            cost_positions = cost_positions.fetchall()
            print(f"📋 Verfügbare Kostenpositionen: {len(cost_positions)}")
            for cp in cost_positions:
                print(f"  - ID: {cp[0]}, Projekt: {cp[1]}, Titel: {cp[2]}, Betrag: {cp[3]}, Quote: {cp[4]}")
            
            # Prüfe BuildWise-Gebühren
            fees = await db.execute(text("SELECT id, quote_id, cost_position_id, fee_amount, status FROM buildwise_fees"))
            fees = fees.fetchall()
            print(f"📋 Verfügbare BuildWise-Gebühren: {len(fees)}")
            for fee in fees:
                print(f"  - ID: {fee[0]}, Quote: {fee[1]}, CostPosition: {fee[2]}, Betrag: {fee[3]}, Status: {fee[4]}")
            
            # Teste den Service-Aufruf
            print("\n🚀 Teste BuildWiseFeeService.create_fee_from_quote...")
            
            # Verwende das erste akzeptierte Angebot
            accepted_quotes = [q for q in quotes if q[2] == 'ACCEPTED']
            if not accepted_quotes:
                print("❌ Keine akzeptierten Angebote gefunden!")
                return
            
            quote_id = accepted_quotes[0][0]
            print(f"🎯 Verwende Quote ID: {quote_id}")
            
            # Teste den Service
            try:
                fee = await BuildWiseFeeService.create_fee_from_quote(
                    db=db,
                    quote_id=quote_id,
                    cost_position_id=1,  # Wird vom Service überschrieben
                    fee_percentage=4.0
                )
                print(f"✅ Gebühr erfolgreich erstellt: ID={fee.id}, Amount={fee.fee_amount}")
            except Exception as e:
                print(f"❌ Fehler beim Erstellen der Gebühr: {e}")
                import traceback
                traceback.print_exc()
            
            # Prüfe das Ergebnis
            print("\n📊 Ergebnis-Prüfung:")
            fees_after = await db.execute(text("SELECT id, quote_id, cost_position_id, fee_amount, status FROM buildwise_fees"))
            fees_after = fees_after.fetchall()
            print(f"📋 BuildWise-Gebühren nach Test: {len(fees_after)}")
            for fee in fees_after:
                print(f"  - ID: {fee[0]}, Quote: {fee[1]}, CostPosition: {fee[2]}, Betrag: {fee[3]}, Status: {fee[4]}")
            
        except Exception as e:
            print(f"❌ Fehler: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Teste kompletten BuildWise-Gebühren-Flow...")
    asyncio.run(test_complete_flow())
    print("✅ Fertig!") 