#!/usr/bin/env python3
"""
Update bestehende BuildWise-Gebühren auf aktuelle Konfiguration

Dieses Skript aktualisiert alle bestehenden Gebühren, die noch den alten
festen Prozentsatz von 1% haben, auf die aktuelle konfigurierte Gebühren-Einstellung.
"""

import asyncio
import sys
import os
from decimal import Decimal
from datetime import datetime

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.core.database import get_db
from app.services.buildwise_fee_service import BuildWiseFeeService
from sqlalchemy import select, update
from app.models.buildwise_fee import BuildWiseFee

class FeeUpdater:
    """Aktualisiert bestehende Gebühren auf die aktuelle Konfiguration."""
    
    def __init__(self):
        self.updated_count = 0
        self.skipped_count = 0
        self.error_count = 0
    
    async def update_existing_fees(self):
        """Aktualisiert alle bestehenden Gebühren auf die aktuelle Konfiguration."""
        
        print("🔄 Update bestehende BuildWise-Gebühren...")
        print(f"📊 Aktuelle Konfiguration:")
        print(f"   - Prozentsatz: {settings.buildwise_fee_percentage}%")
        print(f"   - Phase: {settings.buildwise_fee_phase}")
        print(f"   - Aktiviert: {settings.buildwise_fee_enabled}")
        
        try:
            async for db in get_db():
                # Hole alle Gebühren
                query = select(BuildWiseFee)
                result = await db.execute(query)
                fees = result.scalars().all()
                
                print(f"📋 Gefundene Gebühren: {len(fees)}")
                
                for fee in fees:
                    try:
                        # Prüfe ob Gebühr aktualisiert werden muss
                        current_percentage = float(fee.fee_percentage)
                        config_percentage = settings.buildwise_fee_percentage
                        
                        if abs(current_percentage - config_percentage) > 0.01:
                            # Berechne neue Gebühren-Beträge
                            old_fee_amount = float(fee.fee_amount)
                            new_fee_amount = float(fee.quote_amount) * (config_percentage / 100.0)
                            
                            # Aktualisiere Gebühr
                            fee.fee_percentage = Decimal(str(config_percentage))
                            fee.fee_amount = Decimal(str(new_fee_amount))
                            fee.fee_details = f"BuildWise-Gebühr für akzeptiertes Angebot {fee.quote_id} (Phase: {settings.buildwise_fee_phase})"
                            fee.notes = f"Automatisch aktualisiert am {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Phase: {settings.buildwise_fee_phase}"
                            
                            # Aktualisiere Steuer-Beträge
                            tax_rate = float(fee.tax_rate)
                            fee.tax_amount = Decimal(str(new_fee_amount * (tax_rate / 100.0)))
                            fee.net_amount = Decimal(str(new_fee_amount))
                            fee.gross_amount = Decimal(str(new_fee_amount * (1 + tax_rate / 100.0)))
                            
                            print(f"✅ Gebühr {fee.id} aktualisiert: {current_percentage}% → {config_percentage}% (€{old_fee_amount:.2f} → €{new_fee_amount:.2f})")
                            self.updated_count += 1
                        else:
                            print(f"⏭️  Gebühr {fee.id} bereits aktuell: {current_percentage}%")
                            self.skipped_count += 1
                            
                    except Exception as e:
                        print(f"❌ Fehler bei Gebühr {fee.id}: {e}")
                        self.error_count += 1
                
                # Commit Änderungen
                await db.commit()
                break
                
        except Exception as e:
            print(f"❌ Fehler beim Update: {e}")
            return False
        
        return True
    
    def show_summary(self):
        """Zeigt eine Zusammenfassung der Updates."""
        print("\n📊 Update-Zusammenfassung")
        print("=" * 40)
        print(f"✅ Aktualisiert: {self.updated_count}")
        print(f"⏭️  Übersprungen: {self.skipped_count}")
        print(f"❌ Fehler: {self.error_count}")
        print(f"📈 Gesamt: {self.updated_count + self.skipped_count + self.error_count}")
        
        if self.updated_count > 0:
            print(f"\n🎉 {self.updated_count} Gebühren erfolgreich auf {settings.buildwise_fee_percentage}% aktualisiert!")
        else:
            print(f"\nℹ️  Alle Gebühren sind bereits auf {settings.buildwise_fee_percentage}% konfiguriert.")

async def main():
    """Hauptfunktion."""
    print("🔄 BuildWise Gebühren-Update Tool")
    print("=" * 50)
    
    updater = FeeUpdater()
    
    # Bestätigung anfordern
    print(f"\n⚠️  WARNUNG: Dieses Tool wird alle bestehenden Gebühren auf {settings.buildwise_fee_percentage}% aktualisieren!")
    print("   Bestehende Gebühren-Beträge werden neu berechnet.")
    
    confirm = input("\nSind Sie sicher? (j/N): ").lower().strip()
    if confirm not in ['j', 'ja', 'y', 'yes']:
        print("❌ Update abgebrochen")
        return
    
    # Update durchführen
    success = await updater.update_existing_fees()
    
    if success:
        updater.show_summary()
    else:
        print("❌ Update fehlgeschlagen")

if __name__ == "__main__":
    asyncio.run(main()) 