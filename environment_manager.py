#!/usr/bin/env python3
"""
BuildWise Environment Manager

Elegante Lösung zum Umschalten zwischen Beta und Production-Modus
ohne die .env Datei zu überschreiben.

Verwendung:
    python environment_manager.py --mode beta        # Beta-Modus (0% Gebühr)
    python environment_manager.py --mode production  # Production-Modus (4.7% Gebühr)
    python environment_manager.py --status           # Aktueller Status
    python environment_manager.py --info             # Detaillierte Informationen
"""

import argparse
import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

class EnvironmentManager:
    """Manager für BuildWise Environment-Konfiguration."""
    
    def __init__(self):
        self.config_file = Path("environment_config.json")
        self.modes = {
            "beta": {
                "name": "Beta-Modus",
                "description": "Beta-Test-Phase (kostenlos für Beta-Tester)",
                "fee_percentage": 0.0,
                "fee_phase": "beta",
                "fee_enabled": True,
                "environment_mode": "beta",
                "features": {
                    "free_testing": True,
                    "limited_users": True,
                    "debug_mode": True
                }
            },
            "production": {
                "name": "Production-Modus",
                "description": "Live-Betrieb (4.7% Gebühr für alle Nutzer)",
                "fee_percentage": 4.7,
                "fee_phase": "production",
                "fee_enabled": True,
                "environment_mode": "production",
                "features": {
                    "free_testing": False,
                    "limited_users": False,
                    "debug_mode": False
                }
            }
        }
    
    def load_config(self) -> Dict[str, Any]:
        """Lädt die aktuelle Konfiguration."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  Warnung: Konnte {self.config_file} nicht laden: {e}")
        
        # Standard-Konfiguration
        return {
            "environment_mode": "beta",
            "buildwise_fee_percentage": 0.0,
            "buildwise_fee_phase": "beta",
            "buildwise_fee_enabled": True,
            "last_updated": datetime.now().isoformat()
        }
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """Speichert die Konfiguration."""
        try:
            config["last_updated"] = datetime.now().isoformat()
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ Fehler beim Speichern der Konfiguration: {e}")
            return False
    
    def get_current_mode(self) -> str:
        """Gibt den aktuellen Modus zurück."""
        config = self.load_config()
        return config.get("environment_mode", "beta")
    
    def show_status(self):
        """Zeigt den aktuellen Status an."""
        current_mode = self.get_current_mode()
        config = self.load_config()
        
        print("🔧 BuildWise Environment Manager")
        print("=" * 50)
        print(f"📊 Aktueller Modus: {current_mode.upper()}")
        print(f"💰 Gebühren-Prozentsatz: {config.get('buildwise_fee_percentage', 0.0)}%")
        print(f"🏷️  Gebühren-Phase: {config.get('buildwise_fee_phase', 'beta')}")
        print(f"✅ Gebühren aktiviert: {config.get('buildwise_fee_enabled', True)}")
        
        if current_mode in self.modes:
            mode_info = self.modes[current_mode]
            print(f"📝 Beschreibung: {mode_info['description']}")
        
        print(f"🕒 Letzte Aktualisierung: {config.get('last_updated', 'Unbekannt')}")
    
    def show_detailed_info(self):
        """Zeigt detaillierte Informationen an."""
        current_mode = self.get_current_mode()
        config = self.load_config()
        
        print("🔧 BuildWise Environment Manager - Detaillierte Informationen")
        print("=" * 70)
        
        # Aktuelle Konfiguration
        print("📋 AKTUELLE KONFIGURATION:")
        print(f"   Modus: {current_mode.upper()}")
        print(f"   Gebühren-Prozentsatz: {config.get('buildwise_fee_percentage', 0.0)}%")
        print(f"   Gebühren-Phase: {config.get('buildwise_fee_phase', 'beta')}")
        print(f"   Gebühren aktiviert: {config.get('buildwise_fee_enabled', True)}")
        print(f"   Letzte Aktualisierung: {config.get('last_updated', 'Unbekannt')}")
        
        # Verfügbare Modi
        print("\n🎛️  VERFÜGBARE MODI:")
        for mode, info in self.modes.items():
            status = "✓" if mode == current_mode else " "
            print(f"   {status} {mode.upper()}: {info['name']}")
            print(f"      Beschreibung: {info['description']}")
            print(f"      Gebühren: {info['fee_percentage']}%")
            print(f"      Features: {', '.join([k for k, v in info['features'].items() if v])}")
            print()
        
        # Konfigurationsdatei
        print("📁 KONFIGURATIONSDATEI:")
        print(f"   Datei: {self.config_file.absolute()}")
        print(f"   Existiert: {'Ja' if self.config_file.exists() else 'Nein'}")
        if self.config_file.exists():
            print(f"   Größe: {self.config_file.stat().st_size} Bytes")
    
    def switch_mode(self, mode: str) -> bool:
        """Schaltet zu einem bestimmten Modus um."""
        if mode not in self.modes:
            print(f"❌ Fehler: Unbekannter Modus '{mode}'")
            print(f"   Verfügbare Modi: {', '.join(self.modes.keys())}")
            return False
        
        mode_info = self.modes[mode]
        current_mode = self.get_current_mode()
        
        print(f"🔄 Wechsle von {current_mode.upper()} zu {mode.upper()}")
        print(f"   Name: {mode_info['name']}")
        print(f"   Beschreibung: {mode_info['description']}")
        print(f"   Gebühren: {mode_info['fee_percentage']}%")
        
        # Bestätigung anfordern
        confirm = input(f"\n⚠️  Sind Sie sicher, dass Sie zu {mode.upper()} wechseln möchten? (j/N): ").lower().strip()
        if confirm not in ['j', 'ja', 'y', 'yes']:
            print("❌ Umschaltung abgebrochen")
            return False
        
        # Konfiguration aktualisieren
        config = self.load_config()
        config.update({
            "environment_mode": mode,
            "buildwise_fee_percentage": mode_info["fee_percentage"],
            "buildwise_fee_phase": mode_info["fee_phase"],
            "buildwise_fee_enabled": mode_info["fee_enabled"]
        })
        
        # Speichern
        if self.save_config(config):
            print(f"✅ Erfolgreich zu {mode.upper()} gewechselt!")
            print(f"   Neuer Gebühren-Prozentsatz: {mode_info['fee_percentage']}%")
            print("💡 Starten Sie den Backend-Server neu, um die Änderungen zu übernehmen.")
            return True
        else:
            print("❌ Fehler beim Speichern der Konfiguration")
            return False
    
    def reset_to_default(self) -> bool:
        """Setzt die Konfiguration auf Standard zurück."""
        print("🔄 Setze Konfiguration auf Standard zurück...")
        
        confirm = input("⚠️  Sind Sie sicher? (j/N): ").lower().strip()
        if confirm not in ['j', 'ja', 'y', 'yes']:
            print("❌ Zurücksetzung abgebrochen")
            return False
        
        default_config = {
            "environment_mode": "beta",
            "buildwise_fee_percentage": 0.0,
            "buildwise_fee_phase": "beta",
            "buildwise_fee_enabled": True,
            "last_updated": datetime.now().isoformat()
        }
        
        if self.save_config(default_config):
            print("✅ Konfiguration erfolgreich zurückgesetzt!")
            return True
        else:
            print("❌ Fehler beim Zurücksetzen der Konfiguration")
            return False
    
    def validate_config(self) -> bool:
        """Validiert die aktuelle Konfiguration."""
        config = self.load_config()
        
        print("🔍 Validiere Konfiguration...")
        
        # Prüfe erforderliche Felder
        required_fields = ["environment_mode", "buildwise_fee_percentage", "buildwise_fee_phase", "buildwise_fee_enabled"]
        missing_fields = [field for field in required_fields if field not in config]
        
        if missing_fields:
            print(f"❌ Fehlende Felder: {', '.join(missing_fields)}")
            return False
        
        # Prüfe gültige Werte
        if config["environment_mode"] not in self.modes:
            print(f"❌ Ungültiger Modus: {config['environment_mode']}")
            return False
        
        if not isinstance(config["buildwise_fee_percentage"], (int, float)):
            print(f"❌ Ungültiger Gebühren-Prozentsatz: {config['buildwise_fee_percentage']}")
            return False
        
        if config["buildwise_fee_phase"] not in ["beta", "production"]:
            print(f"❌ Ungültige Gebühren-Phase: {config['buildwise_fee_phase']}")
            return False
        
        print("✅ Konfiguration ist gültig!")
        return True

def main():
    """Hauptfunktion des Environment Managers."""
    parser = argparse.ArgumentParser(
        description="BuildWise Environment Manager - Elegante Umschaltung zwischen Beta und Production",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python environment_manager.py --mode beta        # Beta-Modus (0% Gebühr)
  python environment_manager.py --mode production  # Production-Modus (4.7% Gebühr)
  python environment_manager.py --status           # Aktueller Status
  python environment_manager.py --info             # Detaillierte Informationen
  python environment_manager.py --validate         # Konfiguration validieren
  python environment_manager.py --reset            # Zurücksetzen auf Standard
        """
    )
    
    parser.add_argument(
        "--mode", 
        choices=["beta", "production"],
        help="Modus umschalten (beta=0%%, production=4.7%%)"
    )
    parser.add_argument(
        "--status", 
        action="store_true",
        help="Aktuellen Status anzeigen"
    )
    parser.add_argument(
        "--info", 
        action="store_true",
        help="Detaillierte Informationen anzeigen"
    )
    parser.add_argument(
        "--validate", 
        action="store_true",
        help="Konfiguration validieren"
    )
    parser.add_argument(
        "--reset", 
        action="store_true",
        help="Konfiguration auf Standard zurücksetzen"
    )
    
    args = parser.parse_args()
    
    # Erstelle Manager-Instanz
    manager = EnvironmentManager()
    
    try:
        if args.status:
            manager.show_status()
        
        elif args.info:
            manager.show_detailed_info()
        
        elif args.mode:
            manager.switch_mode(args.mode)
        
        elif args.validate:
            manager.validate_config()
        
        elif args.reset:
            manager.reset_to_default()
        
        else:
            # Standard: Status anzeigen
            manager.show_status()
            print("\n💡 Verwenden Sie --help für alle verfügbaren Optionen")
    
    except KeyboardInterrupt:
        print("\n❌ Abgebrochen durch Benutzer")
    except Exception as e:
        print(f"❌ Fehler: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 