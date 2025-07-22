#!/usr/bin/env python3
"""
Skript zur Korrektur bestehender BuildWise Gebühren im Beta-Modus

Setzt alle bestehenden BuildWise Gebühren auf 0% Gebühr, wenn das System im Beta-Modus läuft.
"""

import asyncio
import sys
import os
from datetime import datetime

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.core.database import get_db
from app.models.buildwise_fee import BuildWiseFee
from sqlalchemy import select, update
from decimal import Decimal

class BetaModeFeeFixer:
    """Korrigiert BuildWise Gebühren für den Beta-Modus."""
    
    def __init__(self):
        self.fixed_fees = 0
        self.total_fees = 0
    
    async def check_current_mode(self):
        """Überprüft den aktuellen Modus."""
        print("🔧 Überprüfe aktuellen Modus...")
        
        print(f"   - Environment Mode: {settings.environment_mode}")
        print(f"   - Fee Percentage: {settings.get_fee_percentage()}%")
        print(f"   - Is Beta Mode: {settings.is_beta_mode()}")
        
        if settings.environment_mode == "beta":
            print("✅ System läuft im Beta-Modus")
            return True
        else:
            print("⚠️  System läuft nicht im Beta-Modus")
            return False
    
    async def find_fees_to_fix(self, db):
        """Findet Gebühren, die korrigiert werden müssen."""
        print("\n🔍 Suche nach Gebühren, die korrigiert werden müssen...")
        
        # Hole alle BuildWise Gebühren
        result = await db.execute(select(BuildWiseFee))
        all_fees = result.scalars().all()
        
        self.total_fees = len(all_fees)
        print(f"📊 Gefundene BuildWise Gebühren: {self.total_fees}")
        
        fees_to_fix = []
        for fee in all_fees:
            if fee.fee_percentage != 0.0:
                fees_to_fix.append(fee)
                print(f"   - Fee ID {fee.id}: {fee.fee_percentage}% = {fee.fee_amount} EUR (muss korrigiert werden)")
            else:
                print(f"   - Fee ID {fee.id}: {fee.fee_percentage}% = {fee.fee_amount} EUR (bereits korrekt)")
        
        return fees_to_fix
    
    async def fix_fees(self, db, fees_to_fix):
        """Korrigiert die Gebühren auf 0%."""
        if not fees_to_fix:
            print("✅ Keine Gebühren zu korrigieren")
            return True
        
        print(f"\n🔧 Korrigiere {len(fees_to_fix)} Gebühren auf 0%...")
        
        try:
            for i, fee in enumerate(fees_to_fix, 1):
                print(f"\n[{i}/{len(fees_to_fix)}] Korrigiere Fee ID {fee.id}")
                print(f"   - Vorher: {fee.fee_percentage}% = {fee.fee_amount} EUR")
                
                # Berechne neue Werte für 0% Gebühr
                new_fee_amount = Decimal('0.00')
                new_tax_amount = Decimal('0.00')
                new_net_amount = Decimal('0.00')
                new_gross_amount = Decimal('0.00')
                
                # Update die Gebühr
                await db.execute(
                    update(BuildWiseFee)
                    .where(BuildWiseFee.id == fee.id)
                    .values(
                        fee_percentage=Decimal('0.0'),
                        fee_amount=new_fee_amount,
                        tax_amount=new_tax_amount,
                        net_amount=new_net_amount,
                        gross_amount=new_gross_amount,
                        updated_at=datetime.utcnow()
                    )
                )
                
                print(f"   - Nachher: 0.0% = {new_fee_amount} EUR")
                self.fixed_fees += 1
            
            await db.commit()
            print(f"\n✅ {self.fixed_fees} Gebühren erfolgreich korrigiert")
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Korrigieren der Gebühren: {e}")
            await db.rollback()
            return False
    
    async def verify_fixes(self, db):
        """Überprüft, ob alle Korrekturen erfolgreich waren."""
        print("\n🔍 Überprüfe Korrekturen...")
        
        result = await db.execute(select(BuildWiseFee))
        all_fees = result.scalars().all()
        
        incorrect_fees = []
        for fee in all_fees:
            if fee.fee_percentage != 0.0:
                incorrect_fees.append(fee)
        
        if incorrect_fees:
            print(f"❌ {len(incorrect_fees)} Gebühren sind noch nicht korrekt:")
            for fee in incorrect_fees:
                print(f"   - Fee ID {fee.id}: {fee.fee_percentage}% = {fee.fee_amount} EUR")
            return False
        else:
            print(f"✅ Alle {len(all_fees)} Gebühren sind korrekt (0%)")
            return True

async def main():
    """Hauptfunktion für die Beta-Modus Gebühren-Korrektur."""
    
    print("🚀 Starte Beta-Modus Gebühren-Korrektur...")
    print("=" * 60)
    
    fixer = BetaModeFeeFixer()
    
    try:
        async for db in get_db():
            # Überprüfe aktuellen Modus
            if not await fixer.check_current_mode():
                print("❌ System läuft nicht im Beta-Modus. Korrektur nicht nötig.")
                return
            
            # Finde Gebühren, die korrigiert werden müssen
            fees_to_fix = await fixer.find_fees_to_fix(db)
            
            if not fees_to_fix:
                print("✅ Keine Gebühren zu korrigieren")
                return
            
            # Bestätigung anfordern
            confirm = input(f"\n⚠️  {len(fees_to_fix)} Gebühren auf 0% korrigieren? (j/N): ").lower().strip()
            if confirm not in ['j', 'ja', 'y', 'yes']:
                print("❌ Korrektur abgebrochen")
                return
            
            # Korrigiere die Gebühren
            if await fixer.fix_fees(db, fees_to_fix):
                # Überprüfe die Korrekturen
                if await fixer.verify_fixes(db):
                    print("\n🎉 Beta-Modus Gebühren-Korrektur erfolgreich abgeschlossen!")
                    print(f"   - Korrigierte Gebühren: {fixer.fixed_fees}")
                    print(f"   - Gesamte Gebühren: {fixer.total_fees}")
                else:
                    print("\n❌ Einige Korrekturen fehlgeschlagen")
            else:
                print("\n❌ Fehler bei der Korrektur")
            
            break
            
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 