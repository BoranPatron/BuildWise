#!/usr/bin/env python3
"""
Test Quote Acceptance BuildWise Fee Creation
===========================================

Testet die automatische Erstellung von BuildWise-Gebühren bei Quote-Akzeptierung.
"""

import asyncio
import os
import sys
from datetime import datetime

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.core.config import settings
from app.models.quote import Quote, QuoteStatus
from app.models.buildwise_fee import BuildWiseFee
from app.models.cost_position import CostPosition
from app.services.quote_service import accept_quote, get_quote_by_id
from app.services.buildwise_fee_service import BuildWiseFeeService


class QuoteAcceptanceTester:
    """Testet die Quote-Akzeptierung und BuildWise-Gebühren-Erstellung."""
    
    def __init__(self):
        self.test_results = []
    
    async def test_environment_configuration(self):
        """Testet die Environment-Konfiguration."""
        print("🧪 Teste Environment-Konfiguration...")
        
        current_mode = settings.environment_mode.value
        current_fee_percentage = settings.get_current_fee_percentage()
        
        print(f"🎯 Aktuelle Konfiguration:")
        print(f"   - Modus: {current_mode}")
        print(f"   - Gebühren: {current_fee_percentage}%")
        print(f"   - Ist Beta: {settings.is_beta_mode()}")
        print(f"   - Ist Production: {settings.is_production_mode()}")
        
        self.test_results.append({
            'test': 'Environment Configuration',
            'status': 'PASS',
            'details': f"Modus: {current_mode}, Gebühren: {current_fee_percentage}%"
        })
    
    async def find_accepted_quotes(self, db):
        """Findet akzeptierte Angebote ohne BuildWise-Gebühren."""
        print("\n🔍 Suche nach akzeptierten Angeboten...")
        
        from sqlalchemy import select, and_
        
        # Hole alle akzeptierten Angebote
        query = select(Quote).where(Quote.status == QuoteStatus.ACCEPTED)
        result = await db.execute(query)
        accepted_quotes = result.scalars().all()
        
        print(f"📊 Gefundene akzeptierte Angebote: {len(accepted_quotes)}")
        
        quotes_without_fees = []
        for quote in accepted_quotes:
            # Prüfe ob bereits eine BuildWise-Gebühr existiert
            fee_query = select(BuildWiseFee).where(BuildWiseFee.quote_id == quote.id)
            fee_result = await db.execute(fee_query)
            existing_fee = fee_result.scalar_one_or_none()
            
            if not existing_fee:
                quotes_without_fees.append(quote)
                print(f"   ❌ Quote ID {quote.id}: Keine BuildWise-Gebühr vorhanden")
            else:
                print(f"   ✅ Quote ID {quote.id}: BuildWise-Gebühr vorhanden (ID: {existing_fee.id})")
        
        return quotes_without_fees
    
    async def test_manual_fee_creation(self, db, quote_id):
        """Testet die manuelle Erstellung einer BuildWise-Gebühr."""
        print(f"\n🧪 Teste manuelle Gebühren-Erstellung für Quote {quote_id}...")
        
        try:
            # Hole das Quote
            quote = await get_quote_by_id(db, quote_id)
            if not quote:
                print(f"❌ Quote {quote_id} nicht gefunden")
                return False
            
            print(f"📋 Quote Details:")
            print(f"   - ID: {quote.id}")
            print(f"   - Status: {quote.status}")
            print(f"   - Betrag: {quote.total_amount}€")
            print(f"   - Projekt: {quote.project_id}")
            
            # Hole die zugehörige Kostenposition
            from sqlalchemy import select
            cost_position_query = select(CostPosition).where(CostPosition.quote_id == quote.id)
            cost_position_result = await db.execute(cost_position_query)
            cost_position = cost_position_result.scalar_one_or_none()
            
            if not cost_position:
                print(f"❌ Keine Kostenposition für Quote {quote_id} gefunden")
                return False
            
            print(f"📋 Kostenposition Details:")
            print(f"   - ID: {cost_position.id}")
            print(f"   - Titel: {cost_position.title}")
            print(f"   - Betrag: {cost_position.amount}€")
            
            # Erstelle BuildWise-Gebühr
            print(f"💰 Erstelle BuildWise-Gebühr...")
            fee = await BuildWiseFeeService.create_fee_from_quote(
                db=db,
                quote_id=quote.id,
                cost_position_id=cost_position.id
            )
            
            print(f"✅ BuildWise-Gebühr erfolgreich erstellt:")
            print(f"   - ID: {fee.id}")
            print(f"   - Prozentsatz: {fee.fee_percentage}%")
            print(f"   - Betrag: {fee.fee_amount}€")
            print(f"   - Environment-Modus: {settings.environment_mode.value}")
            
            self.test_results.append({
                'test': f'Manual Fee Creation (Quote {quote_id})',
                'status': 'PASS',
                'details': f"Gebühr erstellt: {fee.fee_percentage}% = {fee.fee_amount}€"
            })
            
            return True
            
        except Exception as e:
            print(f"❌ Fehler bei manueller Gebühren-Erstellung: {e}")
            self.test_results.append({
                'test': f'Manual Fee Creation (Quote {quote_id})',
                'status': 'FAIL',
                'details': str(e)
            })
            return False
    
    async def test_quote_acceptance_flow(self, db):
        """Testet den kompletten Quote-Akzeptierungs-Flow."""
        print(f"\n🧪 Teste Quote-Akzeptierungs-Flow...")
        
        try:
            # Finde ein Quote zum Testen (erstes verfügbares)
            from sqlalchemy import select
            query = select(Quote).where(Quote.status == QuoteStatus.SUBMITTED).limit(1)
            result = await db.execute(query)
            test_quote = result.scalar_one_or_none()
            
            if not test_quote:
                print("❌ Kein Quote zum Testen gefunden")
                self.test_results.append({
                    'test': 'Quote Acceptance Flow',
                    'status': 'SKIP',
                    'details': 'Kein Quote zum Testen verfügbar'
                })
                return
            
            print(f"📋 Teste mit Quote ID {test_quote.id}:")
            print(f"   - Titel: {test_quote.title}")
            print(f"   - Status: {test_quote.status}")
            print(f"   - Betrag: {test_quote.total_amount}€")
            
            # Prüfe ob bereits eine BuildWise-Gebühr existiert
            fee_query = select(BuildWiseFee).where(BuildWiseFee.quote_id == test_quote.id)
            fee_result = await db.execute(fee_query)
            existing_fee = fee_result.scalar_one_or_none()
            
            if existing_fee:
                print(f"   ⚠️  Bereits eine BuildWise-Gebühr vorhanden (ID: {existing_fee.id})")
                self.test_results.append({
                    'test': 'Quote Acceptance Flow',
                    'status': 'INFO',
                    'details': f"Bereits Gebühr vorhanden für Quote {test_quote.id}"
                })
                return
            
            # Simuliere Quote-Akzeptierung
            print(f"🔄 Simuliere Quote-Akzeptierung...")
            accepted_quote = await accept_quote(db, test_quote.id)
            
            if not accepted_quote:
                print(f"❌ Quote-Akzeptierung fehlgeschlagen")
                self.test_results.append({
                    'test': 'Quote Acceptance Flow',
                    'status': 'FAIL',
                    'details': 'Quote-Akzeptierung fehlgeschlagen'
                })
                return
            
            print(f"✅ Quote erfolgreich akzeptiert")
            
            # Prüfe ob BuildWise-Gebühr erstellt wurde
            fee_query = select(BuildWiseFee).where(BuildWiseFee.quote_id == test_quote.id)
            fee_result = await db.execute(fee_query)
            new_fee = fee_result.scalar_one_or_none()
            
            if new_fee:
                print(f"✅ BuildWise-Gebühr automatisch erstellt:")
                print(f"   - ID: {new_fee.id}")
                print(f"   - Prozentsatz: {new_fee.fee_percentage}%")
                print(f"   - Betrag: {new_fee.fee_amount}€")
                
                self.test_results.append({
                    'test': 'Quote Acceptance Flow',
                    'status': 'PASS',
                    'details': f"Gebühr automatisch erstellt: {new_fee.fee_percentage}% = {new_fee.fee_amount}€"
                })
            else:
                print(f"❌ BuildWise-Gebühr wurde nicht automatisch erstellt")
                self.test_results.append({
                    'test': 'Quote Acceptance Flow',
                    'status': 'FAIL',
                    'details': 'BuildWise-Gebühr nicht automatisch erstellt'
                })
                
        except Exception as e:
            print(f"❌ Fehler im Quote-Akzeptierungs-Flow: {e}")
            self.test_results.append({
                'test': 'Quote Acceptance Flow',
                'status': 'ERROR',
                'details': str(e)
            })
    
    def print_summary(self):
        """Zeigt eine Zusammenfassung der Test-Ergebnisse."""
        print("\n" + "=" * 60)
        print("📊 Quote Acceptance BuildWise Fee Test - Zusammenfassung")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['status'] == 'PASS')
        failed = sum(1 for result in self.test_results if result['status'] == 'FAIL')
        errors = sum(1 for result in self.test_results if result['status'] == 'ERROR')
        skipped = sum(1 for result in self.test_results if result['status'] in ['SKIP', 'INFO'])
        
        print(f"✅ Bestanden: {passed}")
        print(f"❌ Fehlgeschlagen: {failed}")
        print(f"⚠️  Fehler: {errors}")
        print(f"ℹ️  Übersprungen: {skipped}")
        
        print("\n📋 Detaillierte Ergebnisse:")
        for result in self.test_results:
            status_icon = "✅" if result['status'] == 'PASS' else "❌" if result['status'] == 'FAIL' else "⚠️" if result['status'] == 'ERROR' else "ℹ️"
            print(f"   {status_icon} {result['test']}: {result['details']}")
        
        if failed == 0 and errors == 0:
            print("\n🎉 Alle Tests erfolgreich! BuildWise-Gebühren werden korrekt erstellt.")
        else:
            print(f"\n⚠️  {failed + errors} Tests fehlgeschlagen. Bitte Probleme beheben.")


async def main():
    """Hauptfunktion für Quote-Akzeptierungs-Tests."""
    print("🏗️  Quote Acceptance BuildWise Fee Tester")
    print("=" * 60)
    
    tester = QuoteAcceptanceTester()
    
    try:
        async for db in get_db():
            try:
                await tester.test_environment_configuration()
                
                # Teste bestehende akzeptierte Angebote
                quotes_without_fees = await tester.find_accepted_quotes(db)
                
                if quotes_without_fees:
                    print(f"\n🔧 {len(quotes_without_fees)} akzeptierte Angebote ohne BuildWise-Gebühren gefunden")
                    
                    # Teste manuelle Gebühren-Erstellung für das erste Quote
                    first_quote = quotes_without_fees[0]
                    await tester.test_manual_fee_creation(db, first_quote.id)
                else:
                    print("\n✅ Alle akzeptierten Angebote haben bereits BuildWise-Gebühren")
                
                # Teste Quote-Akzeptierungs-Flow
                await tester.test_quote_acceptance_flow(db)
                
                tester.print_summary()
                
            finally:
                await db.close()
                
    except Exception as e:
        print(f"❌ Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 