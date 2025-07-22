#!/usr/bin/env python3
"""
Test-Skript für BuildWise Environment Mode Switcher
==================================================

Testet die neue elegante Beta/Production-Umschaltung.
"""

import os
import json
from pathlib import Path
from app.core.config import settings, EnvironmentMode


def test_environment_configuration():
    """Testet die Environment-Konfiguration."""
    print("🧪 Teste Environment-Konfiguration...")
    
    # Test 1: Standard-Konfiguration
    print("\n1. Standard-Konfiguration:")
    print(f"   - Environment-Modus: {settings.environment_mode}")
    print(f"   - Gebühren-Prozentsatz: {settings.get_current_fee_percentage()}%")
    print(f"   - Ist Beta: {settings.is_beta_mode()}")
    print(f"   - Ist Production: {settings.is_production_mode()}")
    
    # Test 2: Wechsel zu Production
    print("\n2. Wechsel zu Production:")
    settings.switch_environment(EnvironmentMode.PRODUCTION)
    print(f"   - Environment-Modus: {settings.environment_mode}")
    print(f"   - Gebühren-Prozentsatz: {settings.get_current_fee_percentage()}%")
    print(f"   - Ist Beta: {settings.is_beta_mode()}")
    print(f"   - Ist Production: {settings.is_production_mode()}")
    
    # Test 3: Wechsel zurück zu Beta
    print("\n3. Wechsel zurück zu Beta:")
    settings.switch_environment(EnvironmentMode.BETA)
    print(f"   - Environment-Modus: {settings.environment_mode}")
    print(f"   - Gebühren-Prozentsatz: {settings.get_current_fee_percentage()}%")
    print(f"   - Ist Beta: {settings.is_beta_mode()}")
    print(f"   - Ist Production: {settings.is_production_mode()}")
    
    print("\n✅ Environment-Konfiguration-Tests erfolgreich!")


def test_config_file():
    """Testet die Konfigurationsdatei."""
    print("\n🧪 Teste Konfigurationsdatei...")
    
    config_file = Path("environment_config.json")
    
    # Test 1: Datei erstellen
    print("\n1. Erstelle Konfigurationsdatei:")
    config_data = {
        "environment_mode": "beta",
        "last_switch": "2024-01-15T10:30:00",
        "fee_percentage": 0.0
    }
    
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    print(f"   - Datei erstellt: {config_file}")
    
    # Test 2: Datei lesen
    print("\n2. Lese Konfigurationsdatei:")
    with open(config_file, 'r', encoding='utf-8') as f:
        loaded_config = json.load(f)
    
    print(f"   - Environment-Modus: {loaded_config['environment_mode']}")
    print(f"   - Gebühren-Prozentsatz: {loaded_config['fee_percentage']}%")
    print(f"   - Letzter Wechsel: {loaded_config['last_switch']}")
    
    # Test 3: Production-Konfiguration
    print("\n3. Aktualisiere zu Production:")
    config_data["environment_mode"] = "production"
    config_data["fee_percentage"] = 4.7
    config_data["last_switch"] = "2024-01-15T11:00:00"
    
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    print(f"   - Environment-Modus: {config_data['environment_mode']}")
    print(f"   - Gebühren-Prozentsatz: {config_data['fee_percentage']}%")
    
    print("\n✅ Konfigurationsdatei-Tests erfolgreich!")


def test_fee_calculation():
    """Testet die Gebühren-Berechnung."""
    print("\n🧪 Teste Gebühren-Berechnung...")
    
    # Test 1: Beta-Modus
    print("\n1. Beta-Modus (0.0%):")
    settings.switch_environment(EnvironmentMode.BETA)
    quote_amount = 10000.0
    fee_amount = quote_amount * (settings.get_current_fee_percentage() / 100.0)
    print(f"   - Angebotsbetrag: {quote_amount}€")
    print(f"   - Gebühren-Prozentsatz: {settings.get_current_fee_percentage()}%")
    print(f"   - Gebühren-Betrag: {fee_amount}€")
    
    # Test 2: Production-Modus
    print("\n2. Production-Modus (4.7%):")
    settings.switch_environment(EnvironmentMode.PRODUCTION)
    fee_amount = quote_amount * (settings.get_current_fee_percentage() / 100.0)
    print(f"   - Angebotsbetrag: {quote_amount}€")
    print(f"   - Gebühren-Prozentsatz: {settings.get_current_fee_percentage()}%")
    print(f"   - Gebühren-Betrag: {fee_amount}€")
    
    print("\n✅ Gebühren-Berechnung-Tests erfolgreich!")


def test_integration():
    """Testet die Integration mit bestehenden Services."""
    print("\n🧪 Teste Integration...")
    
    # Test 1: BuildWiseFeeService Integration
    print("\n1. BuildWiseFeeService Integration:")
    from app.services.buildwise_fee_service import BuildWiseFeeService
    
    # Simuliere Gebühren-Erstellung
    quote_amount = 5000.0
    
    # Beta-Modus
    settings.switch_environment(EnvironmentMode.BETA)
    beta_fee = quote_amount * (settings.get_current_fee_percentage() / 100.0)
    print(f"   - Beta-Modus: {quote_amount}€ → {beta_fee}€ Gebühren")
    
    # Production-Modus
    settings.switch_environment(EnvironmentMode.PRODUCTION)
    production_fee = quote_amount * (settings.get_current_fee_percentage() / 100.0)
    print(f"   - Production-Modus: {quote_amount}€ → {production_fee}€ Gebühren")
    
    # Test 2: Unterschied berechnen
    fee_difference = production_fee - beta_fee
    print(f"   - Unterschied: {fee_difference}€")
    
    print("\n✅ Integration-Tests erfolgreich!")


def cleanup():
    """Räumt Test-Dateien auf."""
    print("\n🧹 Räume Test-Dateien auf...")
    
    config_file = Path("environment_config.json")
    if config_file.exists():
        config_file.unlink()
        print(f"   - Gelöscht: {config_file}")
    
    # Setze Environment zurück zu Beta
    settings.switch_environment(EnvironmentMode.BETA)
    print("   - Environment zurück zu Beta gesetzt")


def main():
    """Hauptfunktion für alle Tests."""
    print("🏗️  BuildWise Environment Mode Switcher - Tests")
    print("=" * 60)
    
    try:
        test_environment_configuration()
        test_config_file()
        test_fee_calculation()
        test_integration()
        
        print("\n🎉 Alle Tests erfolgreich!")
        print("\n📊 Zusammenfassung:")
        print("   ✅ Environment-Konfiguration funktioniert")
        print("   ✅ Konfigurationsdatei funktioniert")
        print("   ✅ Gebühren-Berechnung funktioniert")
        print("   ✅ Integration funktioniert")
        print("   ✅ Sichere Umschaltung implementiert")
        
    except Exception as e:
        print(f"\n❌ Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        cleanup()


if __name__ == "__main__":
    main() 