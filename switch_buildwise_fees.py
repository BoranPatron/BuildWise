#!/usr/bin/env python3
"""
BuildWise Gebühren-Umschaltung Tool

Dieses Tool ermöglicht es Administratoren, die BuildWise-Gebühren
zwischen Beta-Phase und Go-Live umzuschalten.

Verwendung:
    python switch_buildwise_fees.py --phase beta      # Setzt auf 0% (Beta-Phase)
    python switch_buildwise_fees.py --phase production # Setzt auf 4% (Go-Live)
    python switch_buildwise_fees.py --status          # Zeigt aktuellen Status
    python switch_buildwise_fees.py --disable         # Deaktiviert Gebühren
    python switch_buildwise_fees.py --enable          # Aktiviert Gebühren
"""

import argparse
import asyncio
import sys
import os
from datetime import datetime
from decimal import Decimal

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.core.database import get_db
from app.services.buildwise_fee_service import BuildWiseFeeService

class BuildWiseFeeSwitcher:
    """Tool für die Umschaltung der BuildWise-Gebühren."""
    
    def __init__(self):
        self.phases = {
            "beta": {
                "percentage": 0.0,
                "description": "Beta-Phase (kostenlos für Beta-Tester)"
            },
            "production": {
                "percentage": 4.0,
                "description": "Go-Live (4% Gebühr für alle Nutzer)"
            }
        }
    
    def show_current_status(self):
        """Zeigt den aktuellen Status der Gebühren-Konfiguration."""
        print("🔧 BuildWise Gebühren-Konfiguration")
        print("=" * 50)
        print(f"📊 Aktueller Prozentsatz: {settings.buildwise_fee_percentage}%")
        print(f"🏷️  Aktuelle Phase: {settings.buildwise_fee_phase}")
        print(f"✅ Aktiviert: {'Ja' if settings.buildwise_fee_enabled else 'Nein'}")
        
        if settings.buildwise_fee_phase in self.phases:
            phase_info = self.phases[settings.buildwise_fee_phase]
            print(f"📝 Beschreibung: {phase_info['description']}")
        
        print("\n💡 Verfügbare Phasen:")
        for phase, info in self.phases.items():
            status = "✓" if phase == settings.buildwise_fee_phase else " "
            print(f"  {status} {phase}: {info['percentage']}% - {info['description']}")
    
    def save_config_to_env(self):
        """Speichert die aktuelle Konfiguration in die .env-Datei."""
        try:
            # Lese bestehende .env-Datei
            env_lines = []
            if os.path.exists(".env"):
                with open(".env", "r", encoding="utf-8") as f:
                    env_lines = f.readlines()
            
            # Erstelle neue .env-Inhalte
            new_env_content = f"""# BuildWise Gebühren-Konfiguration
# Generiert am {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# Umgebung
ENVIRONMENT=development
DEBUG_MODE=true

# BuildWise Gebühren-Konfiguration
BUILDWISE_FEE_PERCENTAGE={settings.buildwise_fee_percentage}
BUILDWISE_FEE_PHASE={settings.buildwise_fee_phase}
BUILDWISE_FEE_ENABLED={str(settings.buildwise_fee_enabled).lower()}

# Datenbank
DATABASE_URL=sqlite:///./buildwise.db

# JWT
SECRET_KEY=your-secret-key-here-change-in-production
JWT_SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]

# Google OAuth
GOOGLE_CLIENT_ID=1039127200110-vav094cta93qmtleivdj63un5dne17eb.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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
GOOGLE_REDIRECT_URI=http://localhost:5173/auth/google/callback

# Microsoft OAuth (optional)
MICROSOFT_CLIENT_ID=
MICROSOFT_CLIENT_SECRET=
MICROSOFT_REDIRECT_URI=http://localhost:5173/auth/microsoft/callback

# Sicherheit
BCRYPT_ROUNDS=12
MAX_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_DURATION_MINUTES=30

# DSGVO
DATA_RETENTION_DAYS=730
CONSENT_REQUIRED=true
"""
            
            # Schreibe neue .env-Datei
            with open(".env", "w", encoding="utf-8") as f:
                f.write(new_env_content)
            
            print("✅ Konfiguration in .env-Datei gespeichert!")
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Speichern der .env-Datei: {e}")
            return False
    
    def switch_to_phase(self, phase: str):
        """Schaltet zu einer bestimmten Phase um."""
        if phase not in self.phases:
            print(f"❌ Fehler: Unbekannte Phase '{phase}'")
            print(f"   Verfügbare Phasen: {', '.join(self.phases.keys())}")
            return False
        
        phase_info = self.phases[phase]
        
        print(f"🔄 Wechsle zu Phase: {phase}")
        print(f"   Prozentsatz: {phase_info['percentage']}%")
        print(f"   Beschreibung: {phase_info['description']}")
        
        # Bestätigung anfordern
        confirm = input("\n⚠️  Sind Sie sicher? (j/N): ").lower().strip()
        if confirm not in ['j', 'ja', 'y', 'yes']:
            print("❌ Umschaltung abgebrochen")
            return False
        
        # Konfiguration aktualisieren
        settings.buildwise_fee_percentage = phase_info['percentage']
        settings.buildwise_fee_phase = phase
        settings.buildwise_fee_enabled = True
        
        # Speichere Änderungen in .env-Datei
        if self.save_config_to_env():
            print(f"✅ Erfolgreich zu Phase '{phase}' gewechselt!")
            print(f"   Neuer Prozentsatz: {settings.buildwise_fee_percentage}%")
            print("💡 Starten Sie den Backend-Server neu, um die Änderungen zu übernehmen.")
            return True
        else:
            print("❌ Fehler beim Speichern der Konfiguration")
            return False
    
    def toggle_fees(self, enable: bool):
        """Aktiviert oder deaktiviert BuildWise-Gebühren."""
        action = "aktiviert" if enable else "deaktiviert"
        print(f"🔄 {action.title()} BuildWise-Gebühren...")
        
        # Bestätigung anfordern
        confirm = input(f"⚠️  Sind Sie sicher, dass Sie Gebühren {action} möchten? (j/N): ").lower().strip()
        if confirm not in ['j', 'ja', 'y', 'yes']:
            print("❌ Änderung abgebrochen")
            return False
        
        settings.buildwise_fee_enabled = enable
        
        # Speichere Änderungen in .env-Datei
        if self.save_config_to_env():
            status = "aktiviert" if settings.buildwise_fee_enabled else "deaktiviert"
            print(f"✅ BuildWise-Gebühren erfolgreich {status}!")
            print("💡 Starten Sie den Backend-Server neu, um die Änderungen zu übernehmen.")
            return True
        else:
            print("❌ Fehler beim Speichern der Konfiguration")
            return False
    
    async def show_fee_statistics(self):
        """Zeigt Statistiken der aktuellen Gebühren."""
        try:
            async for db in get_db():
                stats = await BuildWiseFeeService.get_statistics(db)
                
                print("\n📊 BuildWise-Gebühren Statistiken")
                print("=" * 40)
                print(f"📈 Gesamtanzahl Gebühren: {stats.total_fees}")
                print(f"💰 Gesamtbetrag: {stats.total_amount} EUR")
                print(f"✅ Bezahlte Gebühren: {stats.total_paid} EUR")
                print(f"⏳ Offene Gebühren: {stats.total_open} EUR")
                print(f"🚨 Überfällige Gebühren: {stats.total_overdue} EUR")
                
                if stats.status_breakdown:
                    print("\n📋 Status-Aufschlüsselung:")
                    for status, data in stats.status_breakdown.items():
                        print(f"   {status}: {data['count']} Gebühren, {data['amount']} EUR")
                
                break
        except Exception as e:
            print(f"❌ Fehler beim Laden der Statistiken: {e}")
    
    def create_env_file(self):
        """Erstellt eine .env-Datei mit den aktuellen Einstellungen."""
        env_content = f"""# BuildWise Gebühren-Konfiguration
# Generiert am {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# Gebühren-Konfiguration
BUILDWISE_FEE_PERCENTAGE={settings.buildwise_fee_percentage}
BUILDWISE_FEE_PHASE={settings.buildwise_fee_phase}
BUILDWISE_FEE_ENABLED={str(settings.buildwise_fee_enabled).lower()}

# Andere Konfigurationen (falls benötigt)
# BUILDWISE_FEE_CURRENCY=EUR
# BUILDWISE_FEE_TAX_RATE=19.0
"""
        
        with open(".env", "w", encoding="utf-8") as f:
            f.write(env_content)
        
        print("✅ .env-Datei mit aktueller Konfiguration erstellt!")

def main():
    """Hauptfunktion des Tools."""
    parser = argparse.ArgumentParser(
        description="BuildWise Gebühren-Umschaltung Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python switch_buildwise_fees.py --phase beta        # Beta-Phase (0%)
  python switch_buildwise_fees.py --phase production  # Go-Live (4%)
  python switch_buildwise_fees.py --status            # Aktueller Status
  python switch_buildwise_fees.py --disable           # Gebühren deaktivieren
  python switch_buildwise_fees.py --enable            # Gebühren aktivieren
  python switch_buildwise_fees.py --stats             # Statistiken anzeigen
        """
    )
    
    parser.add_argument(
        "--phase", 
        choices=["beta", "production"],
        help="Phase umschalten (beta=0%%, production=4%%)"
    )
    parser.add_argument(
        "--status", 
        action="store_true",
        help="Aktuellen Status anzeigen"
    )
    parser.add_argument(
        "--enable", 
        action="store_true",
        help="BuildWise-Gebühren aktivieren"
    )
    parser.add_argument(
        "--disable", 
        action="store_true",
        help="BuildWise-Gebühren deaktivieren"
    )
    parser.add_argument(
        "--stats", 
        action="store_true",
        help="Gebühren-Statistiken anzeigen"
    )
    parser.add_argument(
        "--create-env", 
        action="store_true",
        help="Erstellt .env-Datei mit aktueller Konfiguration"
    )
    
    args = parser.parse_args()
    
    # Erstelle Switcher-Instanz
    switcher = BuildWiseFeeSwitcher()
    
    try:
        if args.status:
            switcher.show_current_status()
        
        elif args.phase:
            switcher.switch_to_phase(args.phase)
        
        elif args.enable:
            switcher.toggle_fees(True)
        
        elif args.disable:
            switcher.toggle_fees(False)
        
        elif args.stats:
            asyncio.run(switcher.show_fee_statistics())
        
        elif args.create_env:
            switcher.create_env_file()
        
        else:
            # Standard: Status anzeigen
            switcher.show_current_status()
            print("\n💡 Verwenden Sie --help für alle verfügbaren Optionen")
    
    except KeyboardInterrupt:
        print("\n❌ Abgebrochen durch Benutzer")
    except Exception as e:
        print(f"❌ Fehler: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 