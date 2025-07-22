#!/usr/bin/env python3
"""
Test-Skript für automatische BuildWise Gebühren-Erstellung bei Quote-Akzeptierung

Testet, ob beim Akzeptieren einer Quote automatisch eine BuildWise Gebühr
mit dem korrekten Provisionssatz erstellt wird.
"""

import asyncio
import sys
import os
from datetime import datetime

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.core.config import settings
from app.models.quote import Quote, QuoteStatus
from app.models.buildwise_fee import BuildWiseFee
from app.services.quote_service import accept_quote, get_quote_by_id
from app.services.buildwise_fee_service import BuildWiseFeeService
from sqlalchemy import select

class QuoteAcceptanceTester:
    """Testet die automatische BuildWise Gebühren-Erstellung bei Quote-Akzeptierung."""
    
    def __init__(self):
        self.test_results = []
    
    async def find_accepted_quotes(self, db):
        """Findet akzeptierte Quotes ohne BuildWise Gebühren."""
        print("🔍 Suche nach akzeptierten Quotes...")
        
        # Hole alle akzeptierten Quotes
        result = await db.execute(
            select(Quote).where(Quote.status == QuoteStatus.ACCEPTED)
        )
        accepted_quotes = result.scalars().all()
        
        print(f"📊 Gefundene akzeptierte Angebote: {len(accepted_quotes)}")
        
        quotes_without_fees = []
        for quote in accepted_quotes:
            # Prüfe, ob bereits eine BuildWise Gebühr existiert
            fee_result = await db.execute(
                select(BuildWiseFee).where(BuildWiseFee.quote_id == quote.id)
            )
            existing_fee = fee_result.scalar_one_or_none()
            
            if not existing_fee:
                quotes_without_fees.append(quote)
                print(f"   - Quote {quote.id}: {quote.title} (keine Gebühr)")
            else:
                print(f"   - Quote {quote.id}: {quote.title} (Gebühr existiert: {existing_fee.id})")
        
        return quotes_without_fees
    
    async def test_quote_acceptance_flow(self):
        """Testet den kompletten Quote-Akzeptierungs-Flow."""
        print("\n🧪 Teste Quote-Akzeptierungs-Flow...")
        
        try:
            async for db in get_db():
                # Finde eine Quote zum Testen
                result = await db.execute(
                    select(Quote).where(Quote.status == QuoteStatus.SUBMITTED).limit(1)
                )
                test_quote = result.scalar_one_or_none()
                
                if not test_quote:
                    print("❌ Keine submitted Quote für Test gefunden")
                    return False
                
                print(f"📋 Teste Quote: {test_quote.id} - {test_quote.title}")
                print(f"   - Status: {test_quote.status}")
                print(f"   - Amount: {test_quote.total_amount} {test_quote.currency}")
                print(f"   - Environment Mode: {settings.environment_mode}")
                print(f"   - Fee Percentage: {settings.get_fee_percentage()}%")
                
                # Akzeptiere die Quote
                print("\n🔄 Akzeptiere Quote...")
                accepted_quote = await accept_quote(db, test_quote.id)
                
                if not accepted_quote:
                    print("❌ Quote konnte nicht akzeptiert werden")
                    return False
                
                print(f"✅ Quote erfolgreich akzeptiert")
                print(f"   - Neuer Status: {accepted_quote.status}")
                print(f"   - accepted_at: {accepted_quote.accepted_at}")
                
                # Prüfe, ob BuildWise Gebühr erstellt wurde
                print("\n🔍 Prüfe BuildWise Gebühr...")
                fee_result = await db.execute(
                    select(BuildWiseFee).where(BuildWiseFee.quote_id == test_quote.id)
                )
                buildwise_fee = fee_result.scalar_one_or_none()
                
                if buildwise_fee:
                    print(f"✅ BuildWise Gebühr gefunden (ID: {buildwise_fee.id})")
                    print(f"   - Fee Amount: {buildwise_fee.fee_amount} {buildwise_fee.currency}")
                    print(f"   - Fee Percentage: {buildwise_fee.fee_percentage}%")
                    print(f"   - Quote Amount: {buildwise_fee.quote_amount} {buildwise_fee.currency}")
                    print(f"   - Status: {buildwise_fee.status}")
                    
                    # Validiere Gebühren-Berechnung
                    expected_fee = float(buildwise_fee.quote_amount) * (settings.get_fee_percentage() / 100.0)
                    actual_fee = float(buildwise_fee.fee_amount)
                    
                    if abs(expected_fee - actual_fee) < 0.01:  # Toleranz für Rundungsfehler
                        print(f"✅ Gebühren-Berechnung korrekt")
                        print(f"   - Erwartet: {expected_fee:.2f}")
                        print(f"   - Tatsächlich: {actual_fee:.2f}")
                        return True
                    else:
                        print(f"❌ Gebühren-Berechnung fehlerhaft")
                        print(f"   - Erwartet: {expected_fee:.2f}")
                        print(f"   - Tatsächlich: {actual_fee:.2f}")
                        return False
                else:
                    print("❌ Keine BuildWise Gebühr gefunden")
                    return False
                
                break
                
        except Exception as e:
            print(f"❌ Fehler beim Testen: {e}")
            return False
    
    async def create_fees_for_existing_accepted_quotes(self):
        """Erstellt BuildWise Gebühren für bereits akzeptierte Quotes."""
        print("\n🔧 Erstelle BuildWise Gebühren für bestehende akzeptierte Quotes...")
        
        try:
            async for db in get_db():
                quotes_without_fees = await self.find_accepted_quotes(db)
                
                if not quotes_without_fees:
                    print("✅ Alle akzeptierten Quotes haben bereits BuildWise Gebühren")
                    return True
                
                print(f"\n📋 Erstelle Gebühren für {len(quotes_without_fees)} Quotes...")
                
                created_fees = 0
                for i, quote in enumerate(quotes_without_fees, 1):
                    try:
                        print(f"\n[{i}/{len(quotes_without_fees)}] Erstelle Gebühr für Quote {quote.id}")
                        
                        # Hole die zugehörige Kostenposition
                        from app.services.cost_position_service import get_cost_position_by_quote_id
                        cost_position = await get_cost_position_by_quote_id(db, quote.id)
                        
                        if not cost_position:
                            print(f"   ⚠️  Keine Kostenposition für Quote {quote.id} gefunden")
                            continue
                        
                        # Erstelle BuildWise Gebühr
                        buildwise_fee = await BuildWiseFeeService.create_fee_from_quote(
                            db=db,
                            quote_id=quote.id,
                            cost_position_id=cost_position.id,
                            fee_percentage=None  # Verwende aktuellen Modus
                        )
                        
                        print(f"   ✅ Gebühr erstellt (ID: {buildwise_fee.id})")
                        print(f"      - Fee Amount: {buildwise_fee.fee_amount} {buildwise_fee.currency}")
                        print(f"      - Fee Percentage: {buildwise_fee.fee_percentage}%")
                        
                        created_fees += 1
                        
                    except Exception as e:
                        print(f"   ❌ Fehler bei Quote {quote.id}: {e}")
                
                print(f"\n📊 Zusammenfassung:")
                print(f"   - Quotes verarbeitet: {len(quotes_without_fees)}")
                print(f"   - Gebühren erstellt: {created_fees}")
                
                return created_fees > 0
                
        except Exception as e:
            print(f"❌ Fehler beim Erstellen der Gebühren: {e}")
            return False

async def run_comprehensive_test():
    """Führt einen umfassenden Test der Quote-Akzeptierung durch."""
    
    print("🚀 Starte Quote-Akzeptierung Test...")
    print("=" * 60)
    
    tester = QuoteAcceptanceTester()
    
    # Test-Suite
    tests = [
        ("Quote-Akzeptierungs-Flow", tester.test_quote_acceptance_flow),
        ("Gebühren für bestehende Quotes", tester.create_fees_for_existing_accepted_quotes)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        
        try:
            result = await test_func()
            results.append((test_name, result))
            
        except Exception as e:
            print(f"❌ Fehler in {test_name}: {e}")
            results.append((test_name, False))
    
    # Zusammenfassung
    print("\n" + "="*60)
    print("📊 TEST-ZUSAMMENFASSUNG")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ BESTANDEN" if result else "❌ FEHLGESCHLAGEN"
        print(f"{test_name:<30} {status}")
        if result:
            passed += 1
    
    print(f"\nErgebnis: {passed}/{total} Tests bestanden")
    
    if passed == total:
        print("🎉 Alle Tests bestanden! Quote-Akzeptierung funktioniert korrekt.")
        print("\n💡 Nächste Schritte:")
        print("1. Akzeptieren Sie eine Quote im Frontend")
        print("2. Überprüfen Sie die BuildWise Gebühren in der Dienstleister-Ansicht")
        print("3. Validiere, dass der korrekte Provisionssatz verwendet wird")
    else:
        print("⚠️  Einige Tests fehlgeschlagen. Überprüfen Sie die Konfiguration.")

if __name__ == "__main__":
    asyncio.run(run_comprehensive_test()) 