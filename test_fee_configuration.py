#!/usr/bin/env python3
"""
Test-Skript für BuildWise Gebühren-Konfiguration

Dieses Skript testet die neue Gebühren-Konfiguration und
validiert die Umschaltung zwischen Beta-Phase und Go-Live.
"""

import asyncio
import sys
import os
from decimal import Decimal

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.core.database import get_db
from app.services.buildwise_fee_service import BuildWiseFeeService

class FeeConfigurationTester:
    """Testet die BuildWise-Gebühren-Konfiguration."""
    
    def __init__(self):
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Loggt ein Testergebnis."""
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
    
    def test_configuration_defaults(self):
        """Testet die Standard-Konfiguration."""
        print("\n🔧 Teste Standard-Konfiguration...")
        
        # Test 1: Standard-Prozentsatz
        expected_percentage = 0.0
        actual_percentage = settings.buildwise_fee_percentage
        self.log_test(
            "Standard-Prozentsatz",
            actual_percentage == expected_percentage,
            f"Erwartet: {expected_percentage}%, Tatsächlich: {actual_percentage}%"
        )
        
        # Test 2: Standard-Phase
        expected_phase = "beta"
        actual_phase = settings.buildwise_fee_phase
        self.log_test(
            "Standard-Phase",
            actual_phase == expected_phase,
            f"Erwartet: {expected_phase}, Tatsächlich: {actual_phase}"
        )
        
        # Test 3: Standard-Aktivierung
        expected_enabled = True
        actual_enabled = settings.buildwise_fee_enabled
        self.log_test(
            "Standard-Aktivierung",
            actual_enabled == expected_enabled,
            f"Erwartet: {expected_enabled}, Tatsächlich: {actual_enabled}"
        )
    
    def test_service_methods(self):
        """Testet die Service-Methoden."""
        print("\n🔧 Teste Service-Methoden...")
        
        # Test 1: get_current_fee_percentage
        expected_percentage = settings.buildwise_fee_percentage
        actual_percentage = BuildWiseFeeService.get_current_fee_percentage()
        self.log_test(
            "get_current_fee_percentage",
            actual_percentage == expected_percentage,
            f"Erwartet: {expected_percentage}%, Tatsächlich: {actual_percentage}%"
        )
        
        # Test 2: get_current_fee_phase
        expected_phase = settings.buildwise_fee_phase
        actual_phase = BuildWiseFeeService.get_current_fee_phase()
        self.log_test(
            "get_current_fee_phase",
            actual_phase == expected_phase,
            f"Erwartet: {expected_phase}, Tatsächlich: {actual_phase}"
        )
        
        # Test 3: is_fee_enabled
        expected_enabled = settings.buildwise_fee_enabled
        actual_enabled = BuildWiseFeeService.is_fee_enabled()
        self.log_test(
            "is_fee_enabled",
            actual_enabled == expected_enabled,
            f"Erwartet: {expected_enabled}, Tatsächlich: {actual_enabled}"
        )
    
    def test_fee_calculation(self):
        """Testet die Gebühren-Berechnung."""
        print("\n🔧 Teste Gebühren-Berechnung...")
        
        # Test-Daten
        quote_amount = 1000.0
        test_percentages = [0.0, 1.0, 4.0, 10.0]
        
        for percentage in test_percentages:
            # Temporär Prozentsatz setzen
            original_percentage = settings.buildwise_fee_percentage
            settings.buildwise_fee_percentage = percentage
            
            # Berechnung testen
            expected_fee = quote_amount * (percentage / 100.0)
            actual_fee = quote_amount * (settings.buildwise_fee_percentage / 100.0)
            
            self.log_test(
                f"Gebühren-Berechnung ({percentage}%)",
                abs(actual_fee - expected_fee) < 0.01,
                f"Angebot: {quote_amount}€, Gebühr: {actual_fee}€ ({percentage}%)"
            )
            
            # Original-Wert wiederherstellen
            settings.buildwise_fee_percentage = original_percentage
    
    def test_phase_switching(self):
        """Testet die Phasen-Umschaltung."""
        print("\n🔧 Teste Phasen-Umschaltung...")
        
        # Test 1: Beta-Phase
        settings.buildwise_fee_percentage = 0.0
        settings.buildwise_fee_phase = "beta"
        settings.buildwise_fee_enabled = True
        
        self.log_test(
            "Beta-Phase Konfiguration",
            (settings.buildwise_fee_percentage == 0.0 and 
             settings.buildwise_fee_phase == "beta" and 
             settings.buildwise_fee_enabled == True),
            f"Beta: {settings.buildwise_fee_percentage}%, Phase: {settings.buildwise_fee_phase}"
        )
        
        # Test 2: Production-Phase
        settings.buildwise_fee_percentage = 4.0
        settings.buildwise_fee_phase = "production"
        settings.buildwise_fee_enabled = True
        
        self.log_test(
            "Production-Phase Konfiguration",
            (settings.buildwise_fee_percentage == 4.0 and 
             settings.buildwise_fee_phase == "production" and 
             settings.buildwise_fee_enabled == True),
            f"Production: {settings.buildwise_fee_percentage}%, Phase: {settings.buildwise_fee_phase}"
        )
    
    async def test_database_integration(self):
        """Testet die Datenbank-Integration."""
        print("\n🔧 Teste Datenbank-Integration...")
        
        try:
            async for db in get_db():
                # Test 1: Statistiken abrufen
                stats = await BuildWiseFeeService.get_statistics(db)
                self.log_test(
                    "Statistiken abrufen",
                    stats is not None,
                    f"Statistiken erfolgreich geladen: {stats.total_fees} Gebühren"
                )
                
                # Test 2: Gebühren-Liste abrufen
                fees = await BuildWiseFeeService.get_fees(db, limit=5)
                self.log_test(
                    "Gebühren-Liste abrufen",
                    isinstance(fees, list),
                    f"{len(fees)} Gebühren geladen"
                )
                
                break
        except Exception as e:
            self.log_test(
                "Datenbank-Integration",
                False,
                f"Fehler: {str(e)}"
            )
    
    def test_validation(self):
        """Testet die Validierung."""
        print("\n🔧 Teste Validierung...")
        
        # Test 1: Gültige Prozentsätze
        valid_percentages = [0.0, 1.0, 4.0, 10.0, 100.0]
        for percentage in valid_percentages:
            settings.buildwise_fee_percentage = percentage
            self.log_test(
                f"Gültiger Prozentsatz ({percentage}%)",
                0 <= percentage <= 100,
                f"Prozentsatz: {percentage}%"
            )
        
        # Test 2: Gültige Phasen
        valid_phases = ["beta", "production"]
        for phase in valid_phases:
            settings.buildwise_fee_phase = phase
            self.log_test(
                f"Gültige Phase ({phase})",
                phase in ["beta", "production"],
                f"Phase: {phase}"
            )
        
        # Test 3: Ungültige Werte
        invalid_percentages = [-1.0, 101.0, 150.0]
        for percentage in invalid_percentages:
            self.log_test(
                f"Ungültiger Prozentsatz ({percentage}%)",
                not (0 <= percentage <= 100),
                f"Prozentsatz: {percentage}% (erwartet: außerhalb 0-100)"
            )
    
    def show_summary(self):
        """Zeigt eine Zusammenfassung der Testergebnisse."""
        print("\n📊 Test-Zusammenfassung")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"📈 Gesamte Tests: {total_tests}")
        print(f"✅ Bestanden: {passed_tests}")
        print(f"❌ Fehlgeschlagen: {failed_tests}")
        print(f"📊 Erfolgsrate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Fehlgeschlagene Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   - {result['test']}: {result['message']}")
        
        print(f"\n{'✅ Alle Tests bestanden!' if failed_tests == 0 else '❌ Einige Tests fehlgeschlagen'}")
    
    async def run_all_tests(self):
        """Führt alle Tests aus."""
        print("🧪 BuildWise Gebühren-Konfiguration Test")
        print("=" * 60)
        
        # Führe alle Tests aus
        self.test_configuration_defaults()
        self.test_service_methods()
        self.test_fee_calculation()
        self.test_phase_switching()
        await self.test_database_integration()
        self.test_validation()
        
        # Zeige Zusammenfassung
        self.show_summary()

async def main():
    """Hauptfunktion."""
    tester = FeeConfigurationTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 