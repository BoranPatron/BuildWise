#!/usr/bin/env python3
"""
Erstellt die verbleibende Gebühr für das zweite Angebot

Dieses Skript erstellt die Gebühr für das zweite akzeptierte Angebot,
das aufgrund des Decimal-Präzisionsfehlers nicht erstellt werden konnte.
"""

import sys
import os
import asyncio
from datetime import datetime

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def create_remaining_fee():
    """Erstellt die Gebühr für das zweite Angebot."""
    print("🔧 Erstelle verbleibende Gebühr")
    print("=" * 40)
    
    try:
        from app.core.database import get_db
        from app.models.quote import Quote, QuoteStatus
        from app.models.buildwise_fee import BuildWiseFee
        from app.services.buildwise_fee_service import BuildWiseFeeService
        from sqlalchemy import select
        
        async for db in get_db():
            # Finde das zweite akzeptierte Angebot (ID: 2)
            query = select(Quote).where(Quote.id == 2)
            result = await db.execute(query)
            quote = result.scalar_one_or_none()
            
            if not quote:
                print("❌ Angebot mit ID 2 nicht gefunden")
                return False
            
            print(f"📋 Verwende Angebot ID: {quote.id}")
            print(f"   - Betrag: {quote.total_amount}")
            print(f"   - Service Provider: {quote.service_provider_id}")
            
            # Prüfe ob bereits eine Gebühr existiert
            fee_query = select(BuildWiseFee).where(BuildWiseFee.quote_id == quote.id)
            fee_result = await db.execute(fee_query)
            existing_fee = fee_result.scalar_one_or_none()
            
            if existing_fee:
                print(f"⚠️ Für Angebot {quote.id} existiert bereits eine Gebühr (ID: {existing_fee.id})")
                return True
            
            # Erstelle neue Gebühr
            try:
                print(f"💰 Erstelle Gebühr für Angebot {quote.id}...")
                
                fee = await BuildWiseFeeService.create_fee_from_quote(
                    db=db,
                    quote_id=quote.id,
                    cost_position_id=quote.id  # Verwende Quote-ID als Cost Position ID
                )
                
                print(f"✅ Gebühr erfolgreich erstellt:")
                print(f"   - Gebühren-ID: {fee.id}")
                print(f"   - Gebühren-Betrag: {fee.fee_amount}")
                print(f"   - Gebühren-Prozentsatz: {fee.fee_percentage}%")
                print(f"   - Status: {fee.status}")
                print(f"   - Rechnungsnummer: {fee.invoice_number}")
                
                # Zeige Berechnung
                quote_amount = float(quote.total_amount)
                fee_amount = float(fee.fee_amount)
                percentage = float(fee.fee_percentage)
                
                print(f"\n📊 Berechnung:")
                print(f"   - Angebotsbetrag: {quote_amount} EUR")
                print(f"   - Gebühren-Prozentsatz: {percentage}%")
                print(f"   - Gebühren-Betrag: {fee_amount} EUR")
                print(f"   - Berechnung: {quote_amount} × {percentage}% = {fee_amount}")
                
                return True
                
            except Exception as fee_error:
                print(f"❌ Fehler beim Erstellen der Gebühr: {fee_error}")
                import traceback
                traceback.print_exc()
                return False
            
            break
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der Gebühr: {e}")
        import traceback
        traceback.print_exc()
        return False

async def list_all_fees():
    """Listet alle Gebühren in der Datenbank auf."""
    print("\n🔧 Liste alle Gebühren...")
    
    try:
        from app.core.database import get_db
        from app.models.buildwise_fee import BuildWiseFee
        from sqlalchemy import select
        
        async for db in get_db():
            query = select(BuildWiseFee)
            result = await db.execute(query)
            fees = result.scalars().all()
            
            print(f"📋 Gebühren in der Datenbank: {len(fees)}")
            
            if len(fees) > 0:
                for i, fee in enumerate(fees):
                    print(f"   {i+1}. ID: {fee.id}, Quote: {fee.quote_id}, Betrag: {fee.fee_amount}, Status: {fee.status}")
            else:
                print("   Keine Gebühren gefunden")
            
            break
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Auflisten der Gebühren: {e}")
        return False

async def main():
    """Hauptfunktion."""
    print("🧪 Erstelle verbleibende Gebühr")
    print("=" * 50)
    
    # Liste bestehende Gebühren
    await list_all_fees()
    
    # Erstelle verbleibende Gebühr
    success = await create_remaining_fee()
    
    if success:
        print("\n🎉 Gebühren-Erstellung erfolgreich!")
        
        # Liste Gebühren erneut
        await list_all_fees()
    else:
        print("\n❌ Gebühren-Erstellung fehlgeschlagen!")
        print("💡 Überprüfen Sie:")
        print("   - Ist das Angebot mit ID 2 vorhanden?")
        print("   - Ist die Datenbank korrekt konfiguriert?")
        print("   - Läuft der Backend-Server?")

if __name__ == "__main__":
    asyncio.run(main()) 