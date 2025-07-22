#!/usr/bin/env python3
"""
BuildWise Environment Mode Switcher
===================================

Elegante Umschaltung zwischen Beta- und Production-Modi ohne .env-Überschreibung.

Features:
- Beta-Modus: 0.0% Gebühren
- Production-Modus: 4.7% Gebühren
- Sichere Umschaltung ohne OAuth-Credentials zu überschreiben
- Persistente Konfiguration in separater Datei
"""

import os
import json
from datetime import datetime
from pathlib import Path
from app.core.config import settings, EnvironmentMode


class EnvironmentModeSwitcher:
    """Elegante Umschaltung zwischen Beta- und Production-Modi."""
    
    def __init__(self):
        self.config_file = Path("environment_config.json")
        self.load_config()
    
    def load_config(self):
        """Lädt die aktuelle Environment-Konfiguration."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except Exception as e:
                print(f"⚠️  Fehler beim Laden der Konfiguration: {e}")
                self.config = {"environment_mode": "beta"}
        else:
            self.config = {"environment_mode": "beta"}
    
    def save_config(self):
        """Speichert die aktuelle Environment-Konfiguration."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print(f"✅ Konfiguration gespeichert: {self.config_file}")
        except Exception as e:
            print(f"❌ Fehler beim Speichern der Konfiguration: {e}")
    
    def get_current_mode(self) -> EnvironmentMode:
        """Gibt den aktuellen Environment-Modus zurück."""
        mode_str = self.config.get("environment_mode", "beta")
        try:
            return EnvironmentMode(mode_str)
        except ValueError:
            print(f"⚠️  Ungültiger Modus '{mode_str}', verwende Beta")
            return EnvironmentMode.BETA
    
    def switch_to_beta(self):
        """Wechselt zu Beta-Modus (0.0% Gebühren)."""
        print("🔄 Wechsle zu Beta-Modus...")
        
        # Aktualisiere Konfiguration
        self.config["environment_mode"] = "beta"
        self.config["last_switch"] = datetime.now().isoformat()
        self.config["fee_percentage"] = 0.0
        
        # Speichere Konfiguration
        self.save_config()
        
        # Aktualisiere Settings
        settings.switch_environment(EnvironmentMode.BETA)
        
        print("✅ Beta-Modus aktiviert!")
        print(f"   📊 Gebühren-Prozentsatz: {settings.get_current_fee_percentage()}%")
        print(f"   🎯 Modus: {settings.environment_mode}")
        print(f"   📅 Wechsel-Zeitpunkt: {self.config['last_switch']}")
    
    def switch_to_production(self):
        """Wechselt zu Production-Modus (4.7% Gebühren)."""
        print("🔄 Wechsle zu Production-Modus...")
        
        # Bestätigung für Production-Wechsel
        print("⚠️  WARNUNG: Production-Modus aktiviert Gebühren von 4.7%!")
        confirm = input("   Sind Sie sicher? (y/N): ").strip().lower()
        
        if confirm != 'y':
            print("❌ Wechsel abgebrochen")
            return
        
        # Aktualisiere Konfiguration
        self.config["environment_mode"] = "production"
        self.config["last_switch"] = datetime.now().isoformat()
        self.config["fee_percentage"] = 4.7
        
        # Speichere Konfiguration
        self.save_config()
        
        # Aktualisiere Settings
        settings.switch_environment(EnvironmentMode.PRODUCTION)
        
        print("✅ Production-Modus aktiviert!")
        print(f"   📊 Gebühren-Prozentsatz: {settings.get_current_fee_percentage()}%")
        print(f"   🎯 Modus: {settings.environment_mode}")
        print(f"   📅 Wechsel-Zeitpunkt: {self.config['last_switch']}")
    
    def show_status(self):
        """Zeigt den aktuellen Status an."""
        current_mode = self.get_current_mode()
        settings.switch_environment(current_mode)
        
        print("📊 BuildWise Environment Status")
        print("=" * 40)
        print(f"🎯 Aktueller Modus: {current_mode.value.upper()}")
        print(f"💰 Gebühren-Prozentsatz: {settings.get_current_fee_percentage()}%")
        
        if "last_switch" in self.config:
            last_switch = datetime.fromisoformat(self.config["last_switch"])
            print(f"📅 Letzter Wechsel: {last_switch.strftime('%d.%m.%Y %H:%M:%S')}")
        
        print(f"📁 Konfigurationsdatei: {self.config_file}")
        print()
        
        if current_mode == EnvironmentMode.BETA:
            print("🔵 Beta-Modus aktiv:")
            print("   - Keine Gebühren (0.0%)")
            print("   - Für Test- und Entwicklungsphase")
        else:
            print("🟢 Production-Modus aktiv:")
            print("   - Gebühren von 4.7%")
            print("   - Für Live-Betrieb")
    
    def interactive_menu(self):
        """Interaktives Menü für Environment-Wechsel."""
        while True:
            print("\n" + "=" * 50)
            print("🏗️  BuildWise Environment Mode Switcher")
            print("=" * 50)
            
            current_mode = self.get_current_mode()
            settings.switch_environment(current_mode)
            
            print(f"🎯 Aktueller Modus: {current_mode.value.upper()}")
            print(f"💰 Gebühren: {settings.get_current_fee_percentage()}%")
            print()
            
            print("Optionen:")
            print("1. Status anzeigen")
            print("2. Zu Beta wechseln (0.0%)")
            print("3. Zu Production wechseln (4.7%)")
            print("4. Beenden")
            
            choice = input("\nWählen Sie eine Option (1-4): ").strip()
            
            if choice == "1":
                self.show_status()
            elif choice == "2":
                self.switch_to_beta()
            elif choice == "3":
                self.switch_to_production()
            elif choice == "4":
                print("👋 Auf Wiedersehen!")
                break
            else:
                print("❌ Ungültige Option")


def main():
    """Hauptfunktion für das Environment-Switching."""
    print("🏗️  BuildWise Environment Mode Switcher")
    print("=" * 50)
    
    switcher = EnvironmentModeSwitcher()
    
    # Prüfe Kommandozeilen-Argumente
    import sys
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "status":
            switcher.show_status()
        elif command == "beta":
            switcher.switch_to_beta()
        elif command == "production":
            switcher.switch_to_production()
        elif command == "interactive":
            switcher.interactive_menu()
        else:
            print(f"❌ Unbekannter Befehl: {command}")
            print("Verfügbare Befehle: status, beta, production, interactive")
    else:
        # Interaktives Menü als Standard
        switcher.interactive_menu()


if __name__ == "__main__":
    main() 