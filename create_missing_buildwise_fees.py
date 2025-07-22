#!/usr/bin/env python3
"""
Create Missing BuildWise Fees
=============================

Erstellt fehlende BuildWise-Gebühren für bestehende akzeptierte Angebote.
Behebt das Problem, dass die buildwise_fees Tabelle nicht befüllt wird.
"""

import asyncio
import os
import sys
from datetime import datetime

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.core.config import settings
from app.models.quote import Quote, QuoteStatus
from app.models.buildwise_fee import BuildWiseFee
from app.models.cost_position import CostPosition
from app.services.buildwise_fee_service import BuildWiseFeeService


class MissingFeesCreator:
    """Erstellt fehlende BuildWise-Gebühren für akzeptierte Angebote."""
    
    def __init__(self):
        self.created_count = 0
        self.error_count = 0
        self.skipped_count = 0
    
    async def find_accepted_quotes_without_fees(self, db):
        """Findet akzeptierte Angebote ohne BuildWise-Gebühren."""
        print("🔍 Suche nach akzeptierten Angeboten ohne BuildWise-Gebühren...")
        
        from sqlalchemy import select, and_
        
        # Hole alle akzeptierten Angebote
        query = select(Quote).where(Quote.status == QuoteStatus.ACCEPTED)
        result = await db.execute(query)
        accepted_quotes = result.scalars().all()
        
        print(f"📊 Gefundene akzeptierte Angebote: {len(accepted_quotes)}")
        
        quotes_without_fees = []
        for quote in accepted_quotes:
            # Prüfe ob bereits eine BuildWise-Gebühr existiert
            fee_query = select(BuildWiseFee).where(BuildWiseFee.quote_id == quote.id)
            fee_result = await db.execute(fee_query)
            existing_fee = fee_result.scalar_one_or_none()
            
            if not existing_fee:
                quotes_without_fees.append(quote)
                print(f"   ❌ Quote ID {quote.id}: Keine BuildWise-Gebühr vorhanden")
            else:
                print(f"   ✅ Quote ID {quote.id}: BuildWise-Gebühr vorhanden (ID: {existing_fee.id})")
        
        return quotes_without_fees
    
    async def create_fee_for_quote(self, db, quote):
        """Erstellt eine BuildWise-Gebühr für ein akzeptiertes Angebot."""
        try:
            print(f"\n💰 Erstelle BuildWise-Gebühr für Quote {quote.id}...")
            print(f"   - Titel: {quote.title}")
            print(f"   - Betrag: {quote.total_amount}€")
            print(f"   - Projekt: {quote.project_id}")
            
            # Hole die zugehörige Kostenposition
            from sqlalchemy import select
            cost_position_query = select(CostPosition).where(CostPosition.quote_id == quote.id)
            cost_position_result = await db.execute(cost_position_query)
            cost_position = cost_position_result.scalar_one_or_none()
            
            if not cost_position:
                print(f"   ❌ Keine Kostenposition für Quote {quote.id} gefunden")
                self.error_count += 1
                return False
            
            print(f"   - Kostenposition ID: {cost_position.id}")
            
            # Erstelle BuildWise-Gebühr
            fee = await BuildWiseFeeService.create_fee_from_quote(
                db=db,
                quote_id=quote.id,
                cost_position_id=cost_position.id
            )
            
            print(f"   ✅ BuildWise-Gebühr erfolgreich erstellt:")
            print(f"      - ID: {fee.id}")
            print(f"      - Prozentsatz: {fee.fee_percentage}%")
            print(f"      - Betrag: {fee.fee_amount}€")
            print(f"      - Environment-Modus: {settings.environment_mode.value}")
            
            self.created_count += 1
            return True
            
        except Exception as e:
            print(f"   ❌ Fehler beim Erstellen der BuildWise-Gebühr: {e}")
            self.error_count += 1
            return False
    
    async def process_all_missing_fees(self, db, dry_run: bool = False):
        """Verarbeitet alle fehlenden BuildWise-Gebühren."""
        print("\n🔧 Verarbeite fehlende BuildWise-Gebühren...")
        
        if dry_run:
            print("🧪 DRY RUN MODUS - Keine Änderungen werden vorgenommen")
        
        # Finde akzeptierte Angebote ohne Gebühren
        quotes_without_fees = await self.find_accepted_quotes_without_fees(db)
        
        if not quotes_without_fees:
            print("✅ Alle akzeptierten Angebote haben bereits BuildWise-Gebühren!")
            return
        
        print(f"\n📝 {len(quotes_without_fees)} akzeptierte Angebote ohne BuildWise-Gebühren gefunden")
        
        # Zeige Environment-Status
        print(f"\n🎯 Environment-Konfiguration:")
        print(f"   - Modus: {settings.environment_mode.value}")
        print(f"   - Gebühren: {settings.get_current_fee_percentage()}%")
        
        if not dry_run:
            # Erstelle Gebühren für alle gefundenen Angebote
            for quote in quotes_without_fees:
                await self.create_fee_for_quote(db, quote)
            
            # Commit Änderungen
            await db.commit()
            
            print(f"\n✅ {self.created_count} BuildWise-Gebühren erfolgreich erstellt!")
            if self.error_count > 0:
                print(f"⚠️  {self.error_count} Fehler aufgetreten")
        else:
            print(f"\n🧪 DRY RUN: {len(quotes_without_fees)} BuildWise-Gebühren würden erstellt werden")
    
    def print_summary(self):
        """Zeigt eine Zusammenfassung der Ergebnisse."""
        print("\n" + "=" * 60)
        print("📊 Missing BuildWise Fees Creation - Zusammenfassung")
        print("=" * 60)
        
        print(f"✅ Erstellt: {self.created_count}")
        print(f"❌ Fehler: {self.error_count}")
        print(f"ℹ️  Übersprungen: {self.skipped_count}")
        
        if self.error_count == 0 and self.created_count > 0:
            print("\n🎉 Alle fehlenden BuildWise-Gebühren erfolgreich erstellt!")
        elif self.error_count > 0:
            print(f"\n⚠️  {self.error_count} Fehler aufgetreten. Bitte prüfen.")
        else:
            print("\nℹ️  Keine fehlenden Gebühren gefunden.")


async def main():
    """Hauptfunktion für die Erstellung fehlender BuildWise-Gebühren."""
    print("🏗️  Missing BuildWise Fees Creator")
    print("=" * 60)
    
    # Prüfe Kommandozeilen-Argumente
    import sys
    dry_run = "--dry-run" in sys.argv
    
    creator = MissingFeesCreator()
    
    try:
        async for db in get_db():
            try:
                await creator.process_all_missing_fees(db, dry_run=dry_run)
                creator.print_summary()
                
            finally:
                await db.close()
                
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 