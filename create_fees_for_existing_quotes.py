#!/usr/bin/env python3
"""
Erstellt Gebühren für bestehende akzeptierte Angebote

Dieses Skript erstellt BuildWise-Gebühren für alle bereits akzeptierten Angebote,
die noch keine Gebühr haben.
"""

import sys
import os
import asyncio
from datetime import datetime

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def create_fees_for_existing_quotes():
    """Erstellt Gebühren für alle bestehenden akzeptierten Angebote."""
    print("🔧 Erstelle Gebühren für bestehende akzeptierte Angebote")
    print("=" * 60)
    
    try:
        from app.core.database import get_db
        from app.models.quote import Quote, QuoteStatus
        from app.models.buildwise_fee import BuildWiseFee
        from app.services.buildwise_fee_service import BuildWiseFeeService
        from sqlalchemy import select
        
        async for db in get_db():
            # Finde alle akzeptierten Angebote
            query = select(Quote).where(Quote.status == QuoteStatus.ACCEPTED)
            result = await db.execute(query)
            accepted_quotes = result.scalars().all()
            
            if not accepted_quotes:
                print("❌ Keine akzeptierten Angebote gefunden")
                return False
            
            print(f"📋 Gefundene akzeptierte Angebote: {len(accepted_quotes)}")
            
            # Zeige alle akzeptierten Angebote
            for i, quote in enumerate(accepted_quotes):
                print(f"   {i+1}. ID: {quote.id}, Betrag: {quote.total_amount}, Service Provider: {quote.service_provider_id}")
            
            created_fees = 0
            skipped_fees = 0
            
            # Prüfe für jedes Angebot, ob bereits eine Gebühr existiert
            for quote in accepted_quotes:
                print(f"\n🔍 Prüfe Angebot ID: {quote.id}...")
                
                # Prüfe ob bereits eine Gebühr existiert
                fee_query = select(BuildWiseFee).where(BuildWiseFee.quote_id == quote.id)
                fee_result = await db.execute(fee_query)
                existing_fee = fee_result.scalar_one_or_none()
                
                if existing_fee:
                    print(f"   ⚠️ Für Angebot {quote.id} existiert bereits eine Gebühr (ID: {existing_fee.id})")
                    skipped_fees += 1
                    continue
                
                # Erstelle neue Gebühr
                try:
                    print(f"   💰 Erstelle Gebühr für Angebot {quote.id}...")
                    
                    fee = await BuildWiseFeeService.create_fee_from_quote(
                        db=db,
                        quote_id=quote.id,
                        cost_position_id=quote.id  # Verwende Quote-ID als Cost Position ID
                    )
                    
                    print(f"   ✅ Gebühr erfolgreich erstellt:")
                    print(f"      - Gebühren-ID: {fee.id}")
                    print(f"      - Gebühren-Betrag: {fee.fee_amount}")
                    print(f"      - Gebühren-Prozentsatz: {fee.fee_percentage}%")
                    print(f"      - Status: {fee.status}")
                    print(f"      - Rechnungsnummer: {fee.invoice_number}")
                    
                    # Zeige Berechnung
                    quote_amount = float(quote.total_amount)
                    fee_amount = float(fee.fee_amount)
                    percentage = float(fee.fee_percentage)
                    
                    print(f"      - Berechnung: {quote_amount} EUR × {percentage}% = {fee_amount} EUR")
                    
                    created_fees += 1
                    
                except Exception as fee_error:
                    print(f"   ❌ Fehler beim Erstellen der Gebühr für Angebot {quote.id}: {fee_error}")
                    continue
            
            # Zusammenfassung
            print(f"\n📊 Zusammenfassung:")
            print(f"   - Akzeptierte Angebote: {len(accepted_quotes)}")
            print(f"   - Neue Gebühren erstellt: {created_fees}")
            print(f"   - Gebühren übersprungen (bereits vorhanden): {skipped_fees}")
            
            if created_fees > 0:
                print(f"\n🎉 {created_fees} Gebühren erfolgreich erstellt!")
                print("💡 Die Gebühren sollten jetzt in der Dienstleister-Ansicht sichtbar sein.")
            else:
                print(f"\nℹ️ Keine neuen Gebühren erstellt.")
                if skipped_fees > 0:
                    print("💡 Alle akzeptierten Angebote haben bereits Gebühren.")
            
            break
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der Gebühren: {e}")
        import traceback
        traceback.print_exc()
        return False

async def check_fee_configuration():
    """Prüft die aktuelle Gebühren-Konfiguration."""
    print("🔧 Prüfe Gebühren-Konfiguration...")
    
    try:
        from app.core.config import settings
        from app.services.buildwise_fee_service import BuildWiseFeeService
        
        print(f"✅ Aktuelle Konfiguration:")
        print(f"   - Gebühren-Prozentsatz: {settings.buildwise_fee_percentage}%")
        print(f"   - Gebühren-Phase: {settings.buildwise_fee_phase}")
        print(f"   - Gebühren aktiviert: {settings.buildwise_fee_enabled}")
        
        # Prüfe Service-Methoden
        percentage = BuildWiseFeeService.get_current_fee_percentage()
        phase = BuildWiseFeeService.get_current_fee_phase()
        enabled = BuildWiseFeeService.is_fee_enabled()
        
        print(f"\n✅ Service-Methoden:")
        print(f"   - get_current_fee_percentage(): {percentage}%")
        print(f"   - get_current_fee_phase(): {phase}")
        print(f"   - is_fee_enabled(): {enabled}")
        
        if not enabled:
            print("⚠️ WARNUNG: Gebühren sind deaktiviert!")
            return False
        
        if percentage == 0:
            print("⚠️ WARNUNG: Gebühren-Prozentsatz ist 0%!")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Prüfen der Konfiguration: {e}")
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
    print("🧪 Erstelle Gebühren für bestehende akzeptierte Angebote")
    print("=" * 70)
    
    # Prüfe Konfiguration
    config_ok = await check_fee_configuration()
    
    if not config_ok:
        print("\n❌ Konfiguration ist nicht korrekt!")
        print("💡 Führen Sie folgende Schritte aus:")
        print("   1. python switch_buildwise_fees.py --phase production")
        print("   2. Starten Sie den Backend-Server neu")
        print("   3. Führen Sie dieses Skript erneut aus")
        return
    
    # Liste bestehende Gebühren
    await list_all_fees()
    
    # Erstelle Gebühren für bestehende Angebote
    success = await create_fees_for_existing_quotes()
    
    if success:
        print("\n🎉 Gebühren-Erstellung abgeschlossen!")
        
        # Liste Gebühren erneut
        await list_all_fees()
    else:
        print("\n❌ Gebühren-Erstellung fehlgeschlagen!")
        print("💡 Überprüfen Sie:")
        print("   - Sind akzeptierte Angebote vorhanden?")
        print("   - Ist die Datenbank korrekt konfiguriert?")
        print("   - Läuft der Backend-Server?")

if __name__ == "__main__":
    asyncio.run(main()) 