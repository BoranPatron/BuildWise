#!/usr/bin/env python3
"""
Test-Skript für Beta-Modus Gebühren-Erstellung

Testet, ob im Beta-Modus korrekt 0% Gebühren erstellt werden.
"""

import asyncio
import sys
import os
from datetime import datetime

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.core.database import get_db
from app.models.quote import Quote, QuoteStatus
from app.models.buildwise_fee import BuildWiseFee
from app.services.quote_service import accept_quote, get_quote_by_id
from app.services.buildwise_fee_service import BuildWiseFeeService
from sqlalchemy import select

class BetaModeTester:
    """Testet die Gebühren-Erstellung im Beta-Modus."""
    
    def __init__(self):
        self.test_results = []
    
    def test_environment_configuration(self):
        """Testet die aktuelle Environment-Konfiguration."""
        print("🔧 Teste Environment-Konfiguration...")
        
        print(f"   - Environment Mode: {settings.environment_mode}")
        print(f"   - Fee Percentage: {settings.get_fee_percentage()}%")
        print(f"   - Is Beta Mode: {settings.is_beta_mode()}")
        print(f"   - Is Production Mode: {settings.is_production_mode()}")
        
        # Validiere Beta-Modus
        if settings.environment_mode == "beta" and settings.get_fee_percentage() == 0.0:
            print("✅ Beta-Modus korrekt konfiguriert (0% Gebühr)")
            return True
        else:
            print("❌ Beta-Modus nicht korrekt konfiguriert")
            return False
    
    async def test_fee_creation_in_beta_mode(self):
        """Testet die Gebühren-Erstellung im Beta-Modus."""
        print("\n🧪 Teste Gebühren-Erstellung im Beta-Modus...")
        
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
                
                # Prüfe, ob bereits eine BuildWise Gebühr existiert
                fee_result = await db.execute(
                    select(BuildWiseFee).where(BuildWiseFee.quote_id == test_quote.id)
                )
                existing_fee = fee_result.scalar_one_or_none()
                
                if existing_fee:
                    print(f"⚠️  Bereits eine BuildWise Gebühr vorhanden (ID: {existing_fee.id})")
                    print(f"   - Fee Amount: {existing_fee.fee_amount} {existing_fee.currency}")
                    print(f"   - Fee Percentage: {existing_fee.fee_percentage}%")
                    
                    # Validiere, ob die bestehende Gebühr korrekt ist
                    if existing_fee.fee_percentage == 0.0:
                        print("✅ Bestehende Gebühr ist korrekt (0%)")
                        return True
                    else:
                        print(f"❌ Bestehende Gebühr hat falschen Prozentsatz: {existing_fee.fee_percentage}%")
                        return False
                
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
                    
                    # Validiere Gebühren-Berechnung für Beta-Modus
                    if buildwise_fee.fee_percentage == 0.0 and float(buildwise_fee.fee_amount) == 0.0:
                        print(f"✅ Gebühren-Berechnung korrekt für Beta-Modus (0%)")
                        return True
                    else:
                        print(f"❌ Gebühren-Berechnung fehlerhaft für Beta-Modus")
                        print(f"   - Erwartet: 0% = 0.00 EUR")
                        print(f"   - Tatsächlich: {buildwise_fee.fee_percentage}% = {buildwise_fee.fee_amount} EUR")
                        return False
                else:
                    print("❌ Keine BuildWise Gebühr gefunden")
                    return False
                
                break
                
        except Exception as e:
            print(f"❌ Fehler beim Testen: {e}")
            return False
    
    async def check_existing_fees_in_beta_mode(self):
        """Überprüft bestehende Gebühren im Beta-Modus."""
        print("\n🔍 Überprüfe bestehende Gebühren im Beta-Modus...")
        
        try:
            async for db in get_db():
                # Hole alle BuildWise Gebühren
                result = await db.execute(select(BuildWiseFee))
                all_fees = result.scalars().all()
                
                print(f"📊 Gefundene BuildWise Gebühren: {len(all_fees)}")
                
                beta_fees = []
                production_fees = []
                
                for fee in all_fees:
                    if fee.fee_percentage == 0.0:
                        beta_fees.append(fee)
                    else:
                        production_fees.append(fee)
                
                print(f"   - Beta-Modus Gebühren (0%): {len(beta_fees)}")
                print(f"   - Production-Modus Gebühren (4.7%): {len(production_fees)}")
                
                # Zeige Details der Production-Gebühren
                if production_fees:
                    print(f"\n⚠️  Production-Gebühren gefunden (sollten 0% haben):")
                    for fee in production_fees[:3]:  # Zeige nur die ersten 3
                        print(f"   - Fee ID {fee.id}: {fee.fee_percentage}% = {fee.fee_amount} EUR")
                
                return len(production_fees) == 0
                
        except Exception as e:
            print(f"❌ Fehler beim Überprüfen: {e}")
            return False

async def run_beta_mode_test():
    """Führt einen umfassenden Test des Beta-Modus durch."""
    
    print("🚀 Starte Beta-Modus Test...")
    print("=" * 60)
    
    tester = BetaModeTester()
    
    # Test-Suite
    tests = [
        ("Environment-Konfiguration", tester.test_environment_configuration),
        ("Gebühren-Erstellung im Beta-Modus", tester.test_fee_creation_in_beta_mode),
        ("Überprüfung bestehender Gebühren", tester.check_existing_fees_in_beta_mode)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
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
        print("🎉 Alle Tests bestanden! Beta-Modus funktioniert korrekt.")
        print("\n💡 Nächste Schritte:")
        print("1. Akzeptieren Sie eine neue Quote im Frontend")
        print("2. Überprüfen Sie, dass 0% Gebühr erstellt wird")
        print("3. Wechseln Sie zu Production für echte Gebühren")
    else:
        print("⚠️  Einige Tests fehlgeschlagen. Überprüfen Sie die Konfiguration.")

if __name__ == "__main__":
    asyncio.run(run_beta_mode_test()) 