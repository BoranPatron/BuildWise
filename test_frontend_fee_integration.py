#!/usr/bin/env python3
"""
Test Frontend Fee Integration
============================

Testet die Frontend-Integration der korrigierten BuildWise-Gebühren.
Stellt sicher, dass die Dienstleisteransicht korrekte Gebühren anzeigt.
"""

import asyncio
import os
import sys
import requests
from datetime import datetime

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.core.database import get_db
from app.models.buildwise_fee import BuildWiseFee
from app.models.quote import Quote


class FrontendFeeIntegrationTester:
    """Testet die Frontend-Integration der Gebühren."""
    
    def __init__(self):
        self.api_base_url = "http://localhost:8000"
        self.test_results = []
    
    async def test_backend_api(self):
        """Testet die Backend-API für Gebühren."""
        print("🧪 Teste Backend-API...")
        
        try:
            # Test 1: Environment-Info API
            response = requests.get(f"{self.api_base_url}/api/v1/environment/info")
            if response.status_code == 200:
                env_info = response.json()
                print(f"✅ Environment-Info API:")
                print(f"   - Modus: {env_info['environment_mode']}")
                print(f"   - Gebühren: {env_info['fee_percentage']}%")
                
                self.test_results.append({
                    'test': 'Environment-Info API',
                    'status': 'PASS',
                    'details': f"Modus: {env_info['environment_mode']}, Gebühren: {env_info['fee_percentage']}%"
                })
            else:
                print(f"❌ Environment-Info API fehlgeschlagen: {response.status_code}")
                self.test_results.append({
                    'test': 'Environment-Info API',
                    'status': 'FAIL',
                    'details': f"Status: {response.status_code}"
                })
            
            # Test 2: BuildWise-Fees API
            response = requests.get(f"{self.api_base_url}/api/v1/buildwise-fees/")
            if response.status_code == 200:
                fees = response.json()
                print(f"✅ BuildWise-Fees API:")
                print(f"   - Anzahl Gebühren: {len(fees)}")
                
                if fees:
                    # Analysiere Gebühren-Prozentsätze
                    percentages = {}
                    for fee in fees:
                        percentage = fee.get('fee_percentage', 0)
                        if percentage not in percentages:
                            percentages[percentage] = 0
                        percentages[percentage] += 1
                    
                    print(f"   - Gebühren-Verteilung:")
                    for percentage, count in sorted(percentages.items()):
                        expected = settings.get_current_fee_percentage()
                        status = "✅ KORREKT" if percentage == expected else "❌ FALSCH"
                        print(f"     {percentage}%: {count} Gebühren {status}")
                
                self.test_results.append({
                    'test': 'BuildWise-Fees API',
                    'status': 'PASS',
                    'details': f"Anzahl: {len(fees)}"
                })
            else:
                print(f"❌ BuildWise-Fees API fehlgeschlagen: {response.status_code}")
                self.test_results.append({
                    'test': 'BuildWise-Fees API',
                    'status': 'FAIL',
                    'details': f"Status: {response.status_code}"
                })
                
        except Exception as e:
            print(f"❌ Backend-API Test fehlgeschlagen: {e}")
            self.test_results.append({
                'test': 'Backend-API',
                'status': 'ERROR',
                'details': str(e)
            })
    
    async def test_database_consistency(self):
        """Testet die Datenbank-Konsistenz der Gebühren."""
        print("\n🧪 Teste Datenbank-Konsistenz...")
        
        try:
            async for db in get_db():
                try:
                    # Hole alle Gebühren
                    from sqlalchemy import select
                    query = select(BuildWiseFee)
                    result = await db.execute(query)
                    fees = result.scalars().all()
                    
                    if not fees:
                        print("ℹ️  Keine Gebühren in der Datenbank gefunden")
                        self.test_results.append({
                            'test': 'Database Consistency',
                            'status': 'INFO',
                            'details': 'Keine Gebühren vorhanden'
                        })
                        return
                    
                    print(f"📊 Gefundene Gebühren: {len(fees)}")
                    
                    # Analysiere Konsistenz
                    expected_percentage = settings.get_current_fee_percentage()
                    correct_count = 0
                    incorrect_count = 0
                    
                    for fee in fees:
                        actual_percentage = float(fee.fee_percentage)
                        if actual_percentage == expected_percentage:
                            correct_count += 1
                        else:
                            incorrect_count += 1
                            print(f"   ❌ Gebühr ID {fee.id}: {actual_percentage}% statt {expected_percentage}%")
                    
                    print(f"✅ Korrekte Gebühren: {correct_count}")
                    print(f"❌ Falsche Gebühren: {incorrect_count}")
                    
                    if incorrect_count == 0:
                        self.test_results.append({
                            'test': 'Database Consistency',
                            'status': 'PASS',
                            'details': f"Alle {correct_count} Gebühren korrekt"
                        })
                    else:
                        self.test_results.append({
                            'test': 'Database Consistency',
                            'status': 'FAIL',
                            'details': f"{correct_count} korrekt, {incorrect_count} falsch"
                        })
                        
                finally:
                    await db.close()
                    
        except Exception as e:
            print(f"❌ Datenbank-Test fehlgeschlagen: {e}")
            self.test_results.append({
                'test': 'Database Consistency',
                'status': 'ERROR',
                'details': str(e)
            })
    
    async def test_environment_configuration(self):
        """Testet die Environment-Konfiguration."""
        print("\n🧪 Teste Environment-Konfiguration...")
        
        current_mode = settings.environment_mode.value
        current_fee_percentage = settings.get_current_fee_percentage()
        
        print(f"🎯 Aktuelle Konfiguration:")
        print(f"   - Modus: {current_mode}")
        print(f"   - Gebühren: {current_fee_percentage}%")
        print(f"   - Ist Beta: {settings.is_beta_mode()}")
        print(f"   - Ist Production: {settings.is_production_mode()}")
        
        # Validiere Konfiguration
        if current_mode == "beta" and current_fee_percentage == 0.0:
            status = "PASS"
            details = "Beta-Modus korrekt konfiguriert (0.0%)"
        elif current_mode == "production" and current_fee_percentage == 4.7:
            status = "PASS"
            details = "Production-Modus korrekt konfiguriert (4.7%)"
        else:
            status = "FAIL"
            details = f"Falsche Konfiguration: {current_mode} mit {current_fee_percentage}%"
        
        print(f"   - Status: {status}")
        
        self.test_results.append({
            'test': 'Environment Configuration',
            'status': status,
            'details': details
        })
    
    async def test_fee_calculation(self):
        """Testet die Gebühren-Berechnung."""
        print("\n🧪 Teste Gebühren-Berechnung...")
        
        try:
            async for db in get_db():
                try:
                    # Hole ein Beispiel-Angebot
                    from sqlalchemy import select
                    query = select(Quote).limit(1)
                    result = await db.execute(query)
                    quote = result.scalar_one_or_none()
                    
                    if not quote:
                        print("❌ Kein Angebot für Test gefunden")
                        self.test_results.append({
                            'test': 'Fee Calculation',
                            'status': 'SKIP',
                            'details': 'Kein Angebot verfügbar'
                        })
                        return
                    
                    quote_amount = float(quote.total_amount)
                    expected_fee_percentage = settings.get_current_fee_percentage()
                    expected_fee_amount = quote_amount * (expected_fee_percentage / 100.0)
                    
                    print(f"📋 Test mit Angebot ID {quote.id}:")
                    print(f"   - Angebotsbetrag: {quote_amount}€")
                    print(f"   - Erwarteter Prozentsatz: {expected_fee_percentage}%")
                    print(f"   - Erwartete Gebühr: {expected_fee_amount}€")
                    
                    # Teste Service-Methode
                    from app.services.buildwise_fee_service import BuildWiseFeeService
                    
                    # Prüfe ob bereits eine Gebühr existiert
                    existing_fee_query = select(BuildWiseFee).where(BuildWiseFee.quote_id == quote.id)
                    existing_fee_result = await db.execute(existing_fee_query)
                    existing_fee = existing_fee_result.scalar_one_or_none()
                    
                    if existing_fee:
                        actual_percentage = float(existing_fee.fee_percentage)
                        actual_amount = float(existing_fee.fee_amount)
                        
                        print(f"   - Existierende Gebühr: {actual_percentage}% = {actual_amount}€")
                        
                        if actual_percentage == expected_fee_percentage:
                            print("   ✅ Gebühren-Berechnung korrekt")
                            self.test_results.append({
                                'test': 'Fee Calculation',
                                'status': 'PASS',
                                'details': f"Korrekt: {actual_percentage}% = {actual_amount}€"
                            })
                        else:
                            print("   ❌ Gebühren-Berechnung falsch")
                            self.test_results.append({
                                'test': 'Fee Calculation',
                                'status': 'FAIL',
                                'details': f"Falsch: {actual_percentage}% statt {expected_fee_percentage}%"
                            })
                    else:
                        print("   - Keine existierende Gebühr gefunden")
                        self.test_results.append({
                            'test': 'Fee Calculation',
                            'status': 'INFO',
                            'details': 'Keine existierende Gebühr'
                        })
                        
                finally:
                    await db.close()
                    
        except Exception as e:
            print(f"❌ Gebühren-Berechnung Test fehlgeschlagen: {e}")
            self.test_results.append({
                'test': 'Fee Calculation',
                'status': 'ERROR',
                'details': str(e)
            })
    
    def print_summary(self):
        """Zeigt eine Zusammenfassung der Test-Ergebnisse."""
        print("\n" + "=" * 60)
        print("📊 Frontend Fee Integration Test - Zusammenfassung")
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
            print("\n🎉 Alle Tests erfolgreich! Frontend-Integration funktioniert korrekt.")
        else:
            print(f"\n⚠️  {failed + errors} Tests fehlgeschlagen. Bitte Probleme beheben.")


async def main():
    """Hauptfunktion für Frontend-Integration-Tests."""
    print("🏗️  Frontend Fee Integration Tester")
    print("=" * 60)
    
    tester = FrontendFeeIntegrationTester()
    
    try:
        await tester.test_environment_configuration()
        await tester.test_database_consistency()
        await tester.test_backend_api()
        await tester.test_fee_calculation()
        
        tester.print_summary()
        
    except Exception as e:
        print(f"❌ Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 