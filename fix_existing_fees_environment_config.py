#!/usr/bin/env python3
"""
Fix Existing Fees Environment Config
===================================

Korrigiert bestehende BuildWise-Gebühren, um die Environment-Konfiguration zu verwenden.
Behebt das Problem mit 1% Gebühren in der Dienstleisteransicht.
"""

import asyncio
import os
import sys
from decimal import Decimal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import sessionmaker

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.core.config import settings
from app.models.buildwise_fee import BuildWiseFee
from app.models.quote import Quote


class FeeEnvironmentFixer:
    """Korrigiert bestehende Gebühren für Environment-Konfiguration."""
    
    def __init__(self):
        self.updated_count = 0
        self.error_count = 0
        self.current_fee_percentage = settings.get_current_fee_percentage()
    
    async def analyze_existing_fees(self, db: AsyncSession):
        """Analysiert bestehende Gebühren und zeigt Probleme auf."""
        print("🔍 Analysiere bestehende BuildWise-Gebühren...")
        
        # Hole alle Gebühren
        query = select(BuildWiseFee)
        result = await db.execute(query)
        fees = result.scalars().all()
        
        if not fees:
            print("ℹ️  Keine Gebühren in der Datenbank gefunden.")
            return
        
        print(f"📊 Gefundene Gebühren: {len(fees)}")
        
        # Analysiere Gebühren-Prozentsätze
        percentages = {}
        for fee in fees:
            percentage = float(fee.fee_percentage)
            if percentage not in percentages:
                percentages[percentage] = 0
            percentages[percentage] += 1
        
        print("\n📈 Aktuelle Gebühren-Verteilung:")
        for percentage, count in sorted(percentages.items()):
            status = "✅ KORREKT" if percentage == self.current_fee_percentage else "❌ FALSCH"
            print(f"   {percentage}%: {count} Gebühren {status}")
        
        # Zeige Environment-Status
        print(f"\n🎯 Environment-Konfiguration:")
        print(f"   - Aktueller Modus: {settings.environment_mode.value}")
        print(f"   - Erwarteter Prozentsatz: {self.current_fee_percentage}%")
        print(f"   - Ist Beta: {settings.is_beta_mode()}")
        print(f"   - Ist Production: {settings.is_production_mode()}")
    
    async def fix_existing_fees(self, db: AsyncSession, dry_run: bool = True):
        """Korrigiert bestehende Gebühren auf die korrekte Environment-Konfiguration."""
        print(f"\n🔧 Korrigiere bestehende Gebühren...")
        if dry_run:
            print("🧪 DRY RUN MODUS - Keine Änderungen werden vorgenommen")
        
        # Hole alle Gebühren mit falschem Prozentsatz
        query = select(BuildWiseFee).where(BuildWiseFee.fee_percentage != self.current_fee_percentage)
        result = await db.execute(query)
        fees_to_fix = result.scalars().all()
        
        if not fees_to_fix:
            print("✅ Alle Gebühren haben bereits den korrekten Prozentsatz!")
            return
        
        print(f"📝 {len(fees_to_fix)} Gebühren müssen korrigiert werden")
        
        for fee in fees_to_fix:
            try:
                old_percentage = float(fee.fee_percentage)
                old_amount = float(fee.fee_amount)
                
                # Berechne neue Gebühren
                quote_amount = float(fee.quote_amount)
                new_amount = quote_amount * (self.current_fee_percentage / 100.0)
                
                print(f"\n   Gebühr ID {fee.id}:")
                print(f"     - Alt: {old_percentage}% = {old_amount}€")
                print(f"     - Neu: {self.current_fee_percentage}% = {new_amount}€")
                print(f"     - Unterschied: {new_amount - old_amount}€")
                
                if not dry_run:
                    # Aktualisiere Gebühr
                    fee.fee_percentage = Decimal(str(self.current_fee_percentage))
                    fee.fee_amount = Decimal(str(new_amount))
                    fee.tax_amount = Decimal(str(new_amount * 0.19))
                    fee.net_amount = Decimal(str(new_amount))
                    fee.gross_amount = Decimal(str(new_amount * 1.19))
                    fee.updated_at = datetime.now()
                    
                    self.updated_count += 1
                    print(f"     ✅ Aktualisiert")
                else:
                    print(f"     🧪 Würde aktualisiert werden (DRY RUN)")
                
            except Exception as e:
                print(f"     ❌ Fehler: {e}")
                self.error_count += 1
        
        if not dry_run:
            await db.commit()
            print(f"\n✅ {self.updated_count} Gebühren erfolgreich aktualisiert!")
        else:
            print(f"\n🧪 DRY RUN: {len(fees_to_fix)} Gebühren würden aktualisiert werden")
        
        if self.error_count > 0:
            print(f"⚠️  {self.error_count} Fehler aufgetreten")
    
    async def create_new_fee_with_correct_config(self, db: AsyncSession, quote_id: int, cost_position_id: int):
        """Erstellt eine neue Gebühr mit korrekter Environment-Konfiguration."""
        print(f"\n🆕 Erstelle neue Gebühr für Angebot {quote_id}...")
        
        try:
            from app.services.buildwise_fee_service import BuildWiseFeeService
            
            fee = await BuildWiseFeeService.create_fee_from_quote(
                db=db,
                quote_id=quote_id,
                cost_position_id=cost_position_id
            )
            
            print(f"✅ Neue Gebühr erstellt:")
            print(f"   - ID: {fee.id}")
            print(f"   - Prozentsatz: {fee.fee_percentage}%")
            print(f"   - Betrag: {fee.fee_amount}€")
            print(f"   - Environment-Modus: {settings.environment_mode.value}")
            
            return fee
            
        except Exception as e:
            print(f"❌ Fehler beim Erstellen der Gebühr: {e}")
            return None
    
    async def test_fee_creation(self, db: AsyncSession):
        """Testet die Gebühren-Erstellung mit korrekter Konfiguration."""
        print(f"\n🧪 Teste Gebühren-Erstellung...")
        
        # Hole ein Beispiel-Angebot
        query = select(Quote).limit(1)
        result = await db.execute(query)
        quote = result.scalar_one_or_none()
        
        if not quote:
            print("❌ Kein Angebot für Test gefunden")
            return
        
        print(f"📋 Teste mit Angebot ID {quote.id}:")
        print(f"   - Angebotsbetrag: {quote.total_amount}€")
        print(f"   - Environment-Prozentsatz: {self.current_fee_percentage}%")
        
        # Berechne erwartete Gebühr
        expected_fee = float(quote.total_amount) * (self.current_fee_percentage / 100.0)
        print(f"   - Erwartete Gebühr: {expected_fee}€")
        
        # Teste Service-Methode
        try:
            from app.services.buildwise_fee_service import BuildWiseFeeService
            
            # Prüfe ob bereits eine Gebühr existiert
            existing_fee_query = select(BuildWiseFee).where(BuildWiseFee.quote_id == quote.id)
            existing_fee_result = await db.execute(existing_fee_query)
            existing_fee = existing_fee_result.scalar_one_or_none()
            
            if existing_fee:
                print(f"   - Bereits existierende Gebühr: {existing_fee.fee_percentage}% = {existing_fee.fee_amount}€")
                if float(existing_fee.fee_percentage) == self.current_fee_percentage:
                    print("   ✅ Bereits korrekt konfiguriert")
                else:
                    print("   ❌ Falsche Konfiguration")
            else:
                print("   - Keine existierende Gebühr gefunden")
                
        except Exception as e:
            print(f"   ❌ Test fehlgeschlagen: {e}")


async def main():
    """Hauptfunktion für das Fee-Fixing."""
    print("🏗️  BuildWise Fee Environment Config Fixer")
    print("=" * 60)
    
    # Prüfe Kommandozeilen-Argumente
    import sys
    dry_run = "--dry-run" in sys.argv
    fix_mode = "--fix" in sys.argv
    test_mode = "--test" in sys.argv
    analyze_mode = "--analyze" in sys.argv
    
    if not any([fix_mode, test_mode, analyze_mode]):
        print("Verwendung:")
        print("  python fix_existing_fees_environment_config.py --analyze")
        print("  python fix_existing_fees_environment_config.py --fix [--dry-run]")
        print("  python fix_existing_fees_environment_config.py --test")
        return
    
    fixer = FeeEnvironmentFixer()
    
    try:
        # Erstelle Datenbankverbindung
        async for db in get_db():
            try:
                if test_mode:
                    await fixer.test_fee_creation(db)
                elif analyze_mode:
                    # Analysiere bestehende Gebühren
                    await fixer.analyze_existing_fees(db)
                elif fix_mode:
                    # Analysiere bestehende Gebühren
                    await fixer.analyze_existing_fees(db)
                    # Korrigiere bestehende Gebühren
                    await fixer.fix_existing_fees(db, dry_run=dry_run)
                
            finally:
                await db.close()
                
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 