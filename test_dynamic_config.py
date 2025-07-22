#!/usr/bin/env python3
"""
Test-Skript für dynamische Konfigurations-Ladung

Testet, ob die Konfiguration dynamisch geladen wird, ohne Backend-Neustart.
"""

import asyncio
import sys
import os
from datetime import datetime

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings, get_fee_percentage, is_beta_mode, is_production_mode

class DynamicConfigTester:
    """Testet die dynamische Konfigurations-Ladung."""
    
    def __init__(self):
        self.test_results = []
    
    def test_dynamic_config_loading(self):
        """Testet die dynamische Konfigurations-Ladung."""
        print("🔧 Teste dynamische Konfigurations-Ladung...")
        
        # Teste aktuelle Konfiguration
        current_fee = get_fee_percentage()
        current_beta = is_beta_mode()
        current_production = is_production_mode()
        
        print(f"   - Aktueller Fee Percentage: {current_fee}%")
        print(f"   - Is Beta Mode: {current_beta}")
        print(f"   - Is Production Mode: {current_production}")
        
        # Validiere Konsistenz
        if current_beta and current_fee == 0.0:
            print("✅ Beta-Modus korrekt erkannt (0% Gebühr)")
            return True
        elif current_production and current_fee == 4.7:
            print("✅ Production-Modus korrekt erkannt (4.7% Gebühr)")
            return True
        else:
            print("❌ Inkonsistente Konfiguration erkannt")
            return False
    
    def test_multiple_calls(self):
        """Testet mehrere Aufrufe der dynamischen Funktionen."""
        print("\n🧪 Teste mehrere Aufrufe...")
        
        results = []
        for i in range(5):
            fee = get_fee_percentage()
            beta = is_beta_mode()
            production = is_production_mode()
            
            print(f"   Aufruf {i+1}: {fee}% (Beta: {beta}, Production: {production})")
            results.append((fee, beta, production))
        
        # Prüfe Konsistenz
        first_result = results[0]
        all_consistent = all(result == first_result for result in results)
        
        if all_consistent:
            print("✅ Alle Aufrufe konsistent")
            return True
        else:
            print("❌ Inkonsistente Ergebnisse zwischen Aufrufen")
            return False
    
    def test_config_file_changes(self):
        """Simuliert Änderungen in der Konfigurationsdatei."""
        print("\n🔄 Teste Konfigurationsdatei-Änderungen...")
        
        # Lade aktuelle Konfiguration
        current_config = self._load_current_config()
        print(f"   Aktuelle Konfiguration: {current_config}")
        
        # Teste beide Modi
        test_modes = [
            ("beta", 0.0),
            ("production", 4.7)
        ]
        
        for mode, expected_fee in test_modes:
            print(f"\n   Teste {mode.upper()}-Modus:")
            
            # Simuliere Modus-Wechsel
            self._simulate_mode_change(mode)
            
            # Prüfe dynamische Funktionen
            fee = get_fee_percentage()
            beta = is_beta_mode()
            production = is_production_mode()
            
            print(f"      - Fee Percentage: {fee}%")
            print(f"      - Is Beta: {beta}")
            print(f"      - Is Production: {production}")
            
            # Validiere Ergebnis
            if mode == "beta" and fee == expected_fee and beta:
                print(f"      ✅ {mode.upper()}-Modus korrekt")
            elif mode == "production" and fee == expected_fee and production:
                print(f"      ✅ {mode.upper()}-Modus korrekt")
            else:
                print(f"      ❌ {mode.upper()}-Modus fehlerhaft")
                return False
        
        # Stelle ursprüngliche Konfiguration wieder her
        self._restore_original_config(current_config)
        return True
    
    def _load_current_config(self):
        """Lädt die aktuelle Konfiguration."""
        try:
            with open("environment_config.json", "r", encoding="utf-8") as f:
                import json
                return json.load(f)
        except Exception as e:
            print(f"   ⚠️  Konnte Konfiguration nicht laden: {e}")
            return {}
    
    def _simulate_mode_change(self, mode):
        """Simuliert einen Modus-Wechsel."""
        try:
            config = self._load_current_config()
            config["environment_mode"] = mode
            config["buildwise_fee_percentage"] = 0.0 if mode == "beta" else 4.7
            config["buildwise_fee_phase"] = mode
            config["last_updated"] = datetime.utcnow().isoformat()
            
            with open("environment_config.json", "w", encoding="utf-8") as f:
                import json
                json.dump(config, f, indent=2)
            
            print(f"      - Konfiguration auf {mode.upper()}-Modus geändert")
            
        except Exception as e:
            print(f"      ❌ Fehler beim Ändern der Konfiguration: {e}")
    
    def _restore_original_config(self, original_config):
        """Stellt die ursprüngliche Konfiguration wieder her."""
        try:
            with open("environment_config.json", "w", encoding="utf-8") as f:
                import json
                json.dump(original_config, f, indent=2)
            
            print("      - Ursprüngliche Konfiguration wiederhergestellt")
            
        except Exception as e:
            print(f"      ❌ Fehler beim Wiederherstellen: {e}")

async def run_dynamic_config_test():
    """Führt einen umfassenden Test der dynamischen Konfiguration durch."""
    
    print("🚀 Starte dynamische Konfigurations-Test...")
    print("=" * 60)
    
    tester = DynamicConfigTester()
    
    # Test-Suite
    tests = [
        ("Dynamische Konfigurations-Ladung", tester.test_dynamic_config_loading),
        ("Mehrere Aufrufe", tester.test_multiple_calls),
        ("Konfigurationsdatei-Änderungen", tester.test_config_file_changes)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        
        try:
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
        print("🎉 Alle Tests bestanden! Dynamische Konfiguration funktioniert.")
        print("\n💡 Nächste Schritte:")
        print("1. Wechseln Sie den Environment-Modus: python environment_manager.py --mode production")
        print("2. Akzeptieren Sie eine Quote ohne Backend-Neustart")
        print("3. Überprüfen Sie, dass der neue Provisionssatz verwendet wird")
    else:
        print("⚠️  Einige Tests fehlgeschlagen. Backend-Neustart erforderlich.")

if __name__ == "__main__":
    asyncio.run(run_dynamic_config_test()) 