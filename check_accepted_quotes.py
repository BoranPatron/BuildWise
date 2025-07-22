#!/usr/bin/env python3
"""
Prüft akzeptierte Angebote, für die noch keine Gebühren erstellt wurden
"""

import sys
import os
import asyncio

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def check_accepted_quotes():
    """Prüft akzeptierte Angebote ohne Gebühren"""
    
    print("🔍 Prüfe akzeptierte Angebote ohne Gebühren")
    print("=" * 50)
    
    try:
        from app.core.database import get_db
        from app.models.quote import Quote, QuoteStatus
        from app.models.buildwise_fee import BuildWiseFee
        from sqlalchemy import select
        
        async for db in get_db():
            # Hole alle akzeptierten Angebote
            accepted_quotes_query = select(Quote).where(Quote.status == QuoteStatus.ACCEPTED)
            accepted_quotes_result = await db.execute(accepted_quotes_query)
            accepted_quotes = accepted_quotes_result.scalars().all()
            
            print(f"📊 Gefundene akzeptierte Angebote: {len(accepted_quotes)}")
            
            if len(accepted_quotes) == 0:
                print("⚠️ Keine akzeptierten Angebote gefunden!")
                print("💡 Tipp: Erstellen Sie zuerst Angebote und akzeptieren Sie sie")
                return
            
            # Zeige alle akzeptierten Angebote
            for i, quote in enumerate(accepted_quotes):
                print(f"\n📋 Angebot {i+1}:")
                print(f"  - ID: {quote.id}")
                print(f"  - Projekt: {quote.project_id}")
                print(f"  - Kostenposition: {quote.cost_position_id}")
                print(f"  - Betrag: {quote.total_amount}€")
                print(f"  - Status: {quote.status}")
                print(f"  - Erstellt: {quote.created_at}")
            
            # Prüfe für jedes Angebot, ob bereits eine Gebühr existiert
            print(f"\n🔍 Prüfe Gebühren für akzeptierte Angebote...")
            
            for quote in accepted_quotes:
                # Prüfe ob bereits eine Gebühr für dieses Angebot existiert
                existing_fee_query = select(BuildWiseFee).where(
                    BuildWiseFee.quote_id == quote.id,
                    BuildWiseFee.cost_position_id == quote.cost_position_id
                )
                existing_fee_result = await db.execute(existing_fee_query)
                existing_fee = existing_fee_result.scalar_one_or_none()
                
                if existing_fee:
                    print(f"  ✅ Angebot {quote.id}: Gebühr bereits erstellt (ID: {existing_fee.id}, Betrag: {existing_fee.fee_amount}€)")
                else:
                    print(f"  ❌ Angebot {quote.id}: Keine Gebühr erstellt!")
                    print(f"     - Projekt: {quote.project_id}")
                    print(f"     - Kostenposition: {quote.cost_position_id}")
                    print(f"     - Angebotsbetrag: {quote.total_amount}€")
            
            # Zähle Angebote ohne Gebühren
            quotes_without_fees = 0
            for quote in accepted_quotes:
                existing_fee_query = select(BuildWiseFee).where(
                    BuildWiseFee.quote_id == quote.id,
                    BuildWiseFee.cost_position_id == quote.cost_position_id
                )
                existing_fee_result = await db.execute(existing_fee_query)
                existing_fee = existing_fee_result.scalar_one_or_none()
                
                if not existing_fee:
                    quotes_without_fees += 1
            
            print(f"\n📊 Zusammenfassung:")
            print(f"  - Akzeptierte Angebote: {len(accepted_quotes)}")
            print(f"  - Angebote ohne Gebühren: {quotes_without_fees}")
            
            if quotes_without_fees > 0:
                print(f"\n💡 Lösung: Erstellen Sie Gebühren für {quotes_without_fees} Angebote")
                print("   Führen Sie aus: python create_fees_for_accepted_quotes.py")
            else:
                print(f"\n✅ Alle akzeptierten Angebote haben bereits Gebühren!")
            
            break
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Prüfen: {e}")
        import traceback
        traceback.print_exc()
        return False

async def create_fees_for_accepted_quotes():
    """Erstellt Gebühren für alle akzeptierten Angebote ohne Gebühren"""
    
    print("🔧 Erstelle Gebühren für akzeptierte Angebote")
    print("=" * 50)
    
    try:
        from app.core.database import get_db
        from app.models.quote import Quote, QuoteStatus
        from app.models.buildwise_fee import BuildWiseFee
        from app.services.buildwise_fee_service import BuildWiseFeeService
        from sqlalchemy import select
        
        async for db in get_db():
            # Hole alle akzeptierten Angebote
            accepted_quotes_query = select(Quote).where(Quote.status == QuoteStatus.ACCEPTED)
            accepted_quotes_result = await db.execute(accepted_quotes_query)
            accepted_quotes = accepted_quotes_result.scalars().all()
            
            print(f"📊 Gefundene akzeptierte Angebote: {len(accepted_quotes)}")
            
            if len(accepted_quotes) == 0:
                print("⚠️ Keine akzeptierten Angebote gefunden!")
                return
            
            created_fees = 0
            
            for quote in accepted_quotes:
                # Prüfe ob bereits eine Gebühr für dieses Angebot existiert
                existing_fee_query = select(BuildWiseFee).where(
                    BuildWiseFee.quote_id == quote.id,
                    BuildWiseFee.cost_position_id == quote.cost_position_id
                )
                existing_fee_result = await db.execute(existing_fee_query)
                existing_fee = existing_fee_result.scalar_one_or_none()
                
                if not existing_fee:
                    try:
                        # Erstelle Gebühr für dieses Angebot
                        fee = await BuildWiseFeeService.create_fee_from_quote(
                            db=db,
                            quote_id=quote.id,
                            cost_position_id=quote.cost_position_id
                        )
                        print(f"  ✅ Gebühr erstellt für Angebot {quote.id}: ID={fee.id}, Betrag={fee.fee_amount}€")
                        created_fees += 1
                    except Exception as e:
                        print(f"  ❌ Fehler beim Erstellen der Gebühr für Angebot {quote.id}: {e}")
                else:
                    print(f"  ⏭️ Angebot {quote.id}: Gebühr bereits vorhanden (ID: {existing_fee.id})")
            
            print(f"\n📊 Zusammenfassung:")
            print(f"  - Akzeptierte Angebote: {len(accepted_quotes)}")
            print(f"  - Neue Gebühren erstellt: {created_fees}")
            
            if created_fees > 0:
                print(f"\n✅ {created_fees} Gebühren erfolgreich erstellt!")
            else:
                print(f"\nℹ️ Keine neuen Gebühren erstellt (alle bereits vorhanden)")
            
            break
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der Gebühren: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Hauptfunktion"""
    print("🔧 Prüfe akzeptierte Angebote und Gebühren")
    print("=" * 60)
    
    # 1. Prüfe akzeptierte Angebote
    await check_accepted_quotes()
    
    # 2. Frage nach Erstellung von Gebühren
    print("\n💡 Möchten Sie Gebühren für akzeptierte Angebote erstellen?")
    choice = input("Erstellen? (j/n): ").strip().lower()
    
    if choice in ["j", "ja", "y", "yes"]:
        await create_fees_for_accepted_quotes()
    else:
        print("ℹ️ Keine Gebühren erstellt")

if __name__ == "__main__":
    asyncio.run(main()) 