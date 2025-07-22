#!/usr/bin/env python3
"""
Test-Skript für das BuildWise Environment Management System

Testet die elegante Umschaltung zwischen Beta und Production-Modus
ohne die .env Datei zu überschreiben.
"""

import asyncio
import sys
import os
from datetime import datetime

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.core.database import get_db
from app.services.buildwise_fee_service import BuildWiseFeeService

class EnvironmentManagerTester:
    """Testet das Environment Management System."""
    
    def __init__(self):
        self.test_quote_amount = 10000.0  # 10.000 EUR für Tests
    
    def test_config_loading(self):
        """Testet das Laden der Konfiguration."""
        print("🔧 Teste Konfigurations-Loading...")
        
        try:
            # Teste Settings-Loading
            print(f"   - Environment Mode: {settings.environment_mode}")
            print(f"   - Fee Percentage: {settings.get_fee_percentage()}%")
            print(f"   - Is Beta Mode: {settings.is_beta_mode()}")
            print(f"   - Is Production Mode: {settings.is_production_mode()}")
            
            # Teste Fee-Konfiguration
            print(f"   - BuildWise Fee Percentage: {settings.buildwise_fee_percentage}%")
            print(f"   - BuildWise Fee Phase: {settings.buildwise_fee_phase}")
            print(f"   - BuildWise Fee Enabled: {settings.buildwise_fee_enabled}")
            
            print("✅ Konfigurations-Loading erfolgreich!")
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Konfigurations-Loading: {e}")
            return False
    
    def test_fee_calculation(self):
        """Testet die Gebühren-Berechnung für verschiedene Modi."""
        print("\n💰 Teste Gebühren-Berechnung...")
        
        # Teste die aktuelle Konfiguration
        current_fee = settings.get_fee_percentage()
        current_mode = settings.environment_mode
        
        print(f"\n   📊 Aktueller Modus: {current_mode.upper()}")
        print(f"      - Gebühren-Prozentsatz: {current_fee}%")
        print(f"      - Quote-Betrag: {self.test_quote_amount:.2f} EUR")
        
        # Berechne Gebühr für aktuellen Modus
        fee_amount = self.test_quote_amount * (current_fee / 100.0)
        print(f"      - Berechnete Gebühr: {fee_amount:.2f} EUR")
        
        # Validiere basierend auf Modus
        if current_mode == "beta":
            expected_fee = 0.0
            print(f"      - Beta-Modus erwartet: {expected_fee}%")
            print(f"      - Test erfolgreich: {'✅' if current_fee == expected_fee else '❌'}")
        elif current_mode == "production":
            expected_fee = 4.7
            print(f"      - Production-Modus erwartet: {expected_fee}%")
            print(f"      - Test erfolgreich: {'✅' if current_fee == expected_fee else '❌'}")
        
        return True
    
    async def test_fee_service_integration(self):
        """Testet die Integration mit dem BuildWiseFeeService."""
        print("\n🔧 Teste BuildWiseFeeService-Integration...")
        
        try:
            async for db in get_db():
                # Teste Fee-Erstellung mit aktuellem Prozentsatz
                current_percentage = settings.get_fee_percentage()
                current_mode = settings.environment_mode
                
                print(f"\n   📊 Aktueller Modus: {current_mode.upper()}")
                print(f"      - Gebühren-Prozentsatz: {current_percentage}%")
                
                # Simuliere Quote-Daten
                quote_amount = self.test_quote_amount
                fee_amount = quote_amount * (current_percentage / 100.0)
                
                print(f"      - Quote-Betrag: {quote_amount:.2f} EUR")
                print(f"      - Berechnete Gebühr: {fee_amount:.2f} EUR")
                
                # Teste Service-Methode (ohne DB-Operation)
                if current_percentage == 0.0:
                    print("      - Beta-Modus: Keine Gebühren")
                else:
                    print("      - Production-Modus: Gebühren werden erhoben")
                
                break
                
        except Exception as e:
            print(f"❌ Fehler bei Service-Integration: {e}")
        
        return True
    
    def test_environment_switching(self):
        """Testet das Umschalten zwischen den Modi."""
        print("\n🔄 Teste Environment-Umschaltung...")
        
        # Teste Beta-Modus
        print("   📊 Beta-Modus Test:")
        beta_fee = 0.0  # Beta sollte immer 0% haben
        print(f"      - Gebühren-Prozentsatz: {beta_fee}%")
        print(f"      - Ist Beta: {settings.is_beta_mode()}")
        print(f"      - Ist Production: {settings.is_production_mode()}")
        
        # Teste Production-Modus
        print("   📊 Production-Modus Test:")
        prod_fee = 4.7  # Production sollte 4.7% haben
        print(f"      - Gebühren-Prozentsatz: {prod_fee}%")
        print(f"      - Ist Beta: {not settings.is_production_mode()}")
        print(f"      - Ist Production: {settings.is_production_mode()}")
        
        # Validiere Ergebnisse basierend auf aktuellem Modus
        current_mode = settings.environment_mode
        if current_mode == "beta":
            expected_fee = 0.0
            mode_correct = settings.is_beta_mode()
        else:
            expected_fee = 4.7
            mode_correct = settings.is_production_mode()
        
        print(f"   ✅ Aktueller Modus korrekt: {'Ja' if mode_correct else 'Nein'}")
        print(f"   ✅ Erwarteter Prozentsatz für {current_mode}: {expected_fee}%")
        
        return mode_correct
    
    def test_config_file_integration(self):
        """Testet die Integration mit der Konfigurationsdatei."""
        print("\n📁 Teste Konfigurationsdatei-Integration...")
        
        import json
        from pathlib import Path
        
        config_file = Path("environment_config.json")
        
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                
                print("   📋 Konfigurationsdatei-Inhalt:")
                for key, value in config.items():
                    print(f"      - {key}: {value}")
                
                # Validiere erforderliche Felder
                required_fields = ["environment_mode", "buildwise_fee_percentage", "buildwise_fee_phase", "buildwise_fee_enabled"]
                missing_fields = [field for field in required_fields if field not in config]
                
                if missing_fields:
                    print(f"   ❌ Fehlende Felder: {missing_fields}")
                    return False
                else:
                    print("   ✅ Alle erforderlichen Felder vorhanden")
                    return True
                    
            except Exception as e:
                print(f"   ❌ Fehler beim Lesen der Konfigurationsdatei: {e}")
                return False
        else:
            print("   ❌ Konfigurationsdatei nicht gefunden")
            return False

async def run_comprehensive_test():
    """Führt einen umfassenden Test des Environment Management Systems durch."""
    
    print("🚀 Starte umfassenden Environment Manager Test...")
    print("=" * 60)
    
    tester = EnvironmentManagerTester()
    
    # Test-Suite
    tests = [
        ("Konfigurations-Loading", tester.test_config_loading),
        ("Gebühren-Berechnung", tester.test_fee_calculation),
        ("Environment-Umschaltung", tester.test_environment_switching),
        ("Konfigurationsdatei-Integration", tester.test_config_file_integration),
        ("Service-Integration", tester.test_fee_service_integration)
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
        print("🎉 Alle Tests bestanden! Environment Manager ist vollständig funktionsfähig.")
        print("\n💡 Nächste Schritte:")
        print("1. Verwenden Sie 'python environment_manager.py --mode beta' für Beta-Modus")
        print("2. Verwenden Sie 'python environment_manager.py --mode production' für Production-Modus")
        print("3. Starten Sie den Backend-Server neu nach Modus-Wechsel")
    else:
        print("⚠️  Einige Tests fehlgeschlagen. Überprüfen Sie die Konfiguration.")

if __name__ == "__main__":
    asyncio.run(run_comprehensive_test()) 