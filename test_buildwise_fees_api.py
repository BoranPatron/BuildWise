#!/usr/bin/env python3
"""
Test-Skript für BuildWise Fees API
"""

import asyncio
import sys
import os
from datetime import datetime

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.services.buildwise_fee_service import BuildWiseFeeService
from app.models.buildwise_fee import BuildWiseFee
from sqlalchemy import select

class BuildWiseFeesAPITester:
    """Testet die BuildWise Fees API direkt."""
    
    def __init__(self):
        self.test_results = []
    
    async def test_get_fees_service(self):
        """Testet den BuildWiseFeeService direkt."""
        print("🔧 Teste BuildWiseFeeService.get_fees()...")
        
        try:
            async for db in get_db():
                # Teste verschiedene Parameter-Kombinationen
                test_cases = [
                    {"skip": 0, "limit": 100, "project_id": None, "status": None, "month": None, "year": None},
                    {"skip": 0, "limit": 100, "project_id": None, "status": None, "month": 7, "year": 2025},
                    {"skip": 0, "limit": 10, "project_id": None, "status": "open", "month": None, "year": None}
                ]
                
                for i, params in enumerate(test_cases, 1):
                    print(f"\n   Test {i}: {params}")
                    
                    try:
                        fees = await BuildWiseFeeService.get_fees(
                            db=db,
                            skip=params["skip"],
                            limit=params["limit"],
                            project_id=params["project_id"],
                            status=params["status"],
                            month=params["month"],
                            year=params["year"]
                        )
                        
                        print(f"      ✅ Erfolgreich: {len(fees)} Gebühren geladen")
                        
                        if fees:
                            for fee in fees[:3]:  # Zeige nur die ersten 3
                                print(f"         - Fee ID {fee.id}: {fee.fee_percentage}% = {fee.fee_amount} EUR")
                        
                    except Exception as e:
                        print(f"      ❌ Fehler: {e}")
                        return False
                
                break
                
    except Exception as e:
            print(f"❌ Fehler beim Testen: {e}")
            return False
        
        return True
    
    async def test_get_statistics_service(self):
        """Testet den BuildWiseFeeService.get_statistics() direkt."""
        print("\n📊 Teste BuildWiseFeeService.get_statistics()...")
        
        try:
            async for db in get_db():
                try:
                    stats = await BuildWiseFeeService.get_statistics(db=db)
                    
                    print(f"   ✅ Statistiken erfolgreich geladen:")
                    print(f"      - Total Fees: {stats.total_fees}")
                    print(f"      - Total Amount: {stats.total_amount}")
                    print(f"      - Total Paid: {stats.total_paid}")
                    print(f"      - Total Open: {stats.total_open}")
                    
                    return True
                    
                except Exception as e:
                    print(f"   ❌ Fehler beim Laden der Statistiken: {e}")
                    return False
                
                break
                
        except Exception as e:
            print(f"❌ Fehler beim Testen: {e}")
            return False
    
    async def test_database_connection(self):
        """Testet die Datenbankverbindung und BuildWiseFee Tabelle."""
        print("\n🗄️ Teste Datenbankverbindung...")
        
        try:
            async for db in get_db():
                # Teste direkte Datenbankabfrage
                result = await db.execute(select(BuildWiseFee))
                fees = result.scalars().all()
                
                print(f"   ✅ Datenbankverbindung erfolgreich")
                print(f"      - BuildWiseFee Tabelle existiert")
                print(f"      - {len(fees)} Gebühren in der Datenbank")
                
                if fees:
                    print(f"      - Erste Gebühr: ID {fees[0].id}, {fees[0].fee_percentage}% = {fees[0].fee_amount} EUR")
                
                return True
                
        except Exception as e:
            print(f"   ❌ Datenbankfehler: {e}")
            return False

async def run_api_test():
    """Führt einen umfassenden Test der BuildWise Fees API durch."""
    
    print("🚀 Starte BuildWise Fees API Test...")
    print("=" * 60)
    
    tester = BuildWiseFeesAPITester()
    
    # Test-Suite
    tests = [
        ("Datenbankverbindung", tester.test_database_connection),
        ("Get Fees Service", tester.test_get_fees_service),
        ("Get Statistics Service", tester.test_get_statistics_service)
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
        print("🎉 Alle Tests bestanden! BuildWise Fees API funktioniert.")
        print("\n💡 Das Problem liegt wahrscheinlich im Frontend oder der Authentifizierung.")
    else:
        print("⚠️  Einige Tests fehlgeschlagen. Backend-Problem erkannt.")

if __name__ == "__main__":
    asyncio.run(run_api_test()) 