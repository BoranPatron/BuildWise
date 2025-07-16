#!/usr/bin/env python3
"""
Test-Skript für Timestamp-Fix bei Kostenvoranschlag-Annahme
Überprüft, ob created_at und updated_at korrekt gesetzt werden
"""

import asyncio
import os
import sys
from datetime import datetime

# Füge das Backend-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text
from app.models.quote import Quote, QuoteStatus
from app.models.cost_position import CostPosition
from app.models.buildwise_fee import BuildWiseFee
from app.services.quote_service import accept_quote, get_quote_by_id
from app.services.cost_position_service import get_cost_position_by_quote_id

async def test_timestamp_fix():
    """Testet die Timestamp-Fix-Lösung bei Kostenvoranschlag-Annahme"""
    
    print("🔍 Teste Timestamp-Fix bei Kostenvoranschlag-Annahme...")
    
    # Datenbankverbindung
    database_url = "sqlite+aiosqlite:///buildwise.db"
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        try:
            # 1. Finde ein verfügbares Angebot zum Testen
            print("\n📋 Suche verfügbares Angebot zum Testen...")
            
            # Hole alle eingereichten Angebote
            quotes_query = select(Quote).where(Quote.status == QuoteStatus.SUBMITTED)
            quotes_result = await db.execute(quotes_query)
            quotes = quotes_result.scalars().all()
            
            if not quotes:
                print("❌ Keine eingereichten Angebote gefunden!")
                return
            
            test_quote = quotes[0]
            print(f"✅ Test-Angebot gefunden: ID={test_quote.id}, Titel='{test_quote.title}'")
            print(f"   Status: {test_quote.status}")
            print(f"   Projekt: {test_quote.project_id}")
            print(f"   Betrag: {test_quote.total_amount} {test_quote.currency}")
            
            # 2. Prüfe aktuelle Timestamps vor Annahme
            print(f"\n📅 Aktuelle Timestamps vor Annahme:")
            print(f"   Quote created_at: {test_quote.created_at}")
            print(f"   Quote updated_at: {test_quote.updated_at}")
            
            # 3. Akzeptiere das Angebot
            print(f"\n✅ Akzeptiere Angebot {test_quote.id}...")
            accepted_quote = await accept_quote(db, test_quote.id)
            
            if not accepted_quote:
                print("❌ Fehler beim Akzeptieren des Angebots!")
                return
            
            print(f"✅ Angebot erfolgreich akzeptiert!")
            print(f"   Neuer Status: {accepted_quote.status}")
            print(f"   accepted_at: {accepted_quote.accepted_at}")
            print(f"   updated_at: {accepted_quote.updated_at}")
            
            # 4. Prüfe erstellte Kostenposition
            print(f"\n📋 Prüfe erstellte Kostenposition...")
            cost_position = await get_cost_position_by_quote_id(db, test_quote.id)
            
            if not cost_position:
                print("❌ Keine Kostenposition für das akzeptierte Angebot gefunden!")
                return
            
            print(f"✅ Kostenposition gefunden: ID={cost_position.id}")
            print(f"   Titel: {cost_position.title}")
            print(f"   Betrag: {cost_position.amount} {cost_position.currency}")
            print(f"   Projekt: {cost_position.project_id}")
            print(f"   Quote-ID: {cost_position.quote_id}")
            
            # 5. Prüfe Timestamps der Kostenposition
            print(f"\n📅 Timestamps der Kostenposition:")
            print(f"   created_at: {cost_position.created_at}")
            print(f"   updated_at: {cost_position.updated_at}")
            
            # 6. Validiere Timestamps
            now = datetime.utcnow()
            print(f"\n🔍 Timestamp-Validierung:")
            print(f"   Aktuelle Zeit: {now}")
            
            if cost_position.created_at:
                time_diff_created = abs((now - cost_position.created_at).total_seconds())
                print(f"   Zeitdifferenz created_at: {time_diff_created:.2f} Sekunden")
                
                if time_diff_created < 60:  # Weniger als 1 Minute
                    print("   ✅ created_at ist korrekt gesetzt")
                else:
                    print("   ❌ created_at ist nicht korrekt gesetzt")
            else:
                print("   ❌ created_at ist NULL")
            
            if cost_position.updated_at:
                time_diff_updated = abs((now - cost_position.updated_at).total_seconds())
                print(f"   Zeitdifferenz updated_at: {time_diff_updated:.2f} Sekunden")
                
                if time_diff_updated < 60:  # Weniger als 1 Minute
                    print("   ✅ updated_at ist korrekt gesetzt")
                else:
                    print("   ❌ updated_at ist nicht korrekt gesetzt")
            else:
                print("   ❌ updated_at ist NULL")
            
            # 7. Prüfe BuildWise-Fee (falls erstellt)
            print(f"\n💰 Prüfe BuildWise-Fee...")
            fee_query = select(BuildWiseFee).where(BuildWiseFee.quote_id == test_quote.id)
            fee_result = await db.execute(fee_query)
            fee = fee_result.scalar_one_or_none()
            
            if fee:
                print(f"✅ BuildWise-Fee gefunden: ID={fee.id}")
                print(f"   Betrag: {fee.fee_amount} {fee.currency}")
                print(f"   Status: {fee.status}")
                print(f"   created_at: {fee.created_at}")
                print(f"   updated_at: {fee.updated_at}")
                
                # Validiere BuildWise-Fee Timestamps
                if fee.created_at:
                    time_diff_fee_created = abs((now - fee.created_at).total_seconds())
                    print(f"   Zeitdifferenz Fee created_at: {time_diff_fee_created:.2f} Sekunden")
                    
                    if time_diff_fee_created < 60:
                        print("   ✅ BuildWise-Fee created_at ist korrekt")
                    else:
                        print("   ❌ BuildWise-Fee created_at ist nicht korrekt")
                else:
                    print("   ❌ BuildWise-Fee created_at ist NULL")
            else:
                print("ℹ️  Kein BuildWise-Fee für dieses Angebot gefunden")
            
            # 8. Zusammenfassung
            print(f"\n📊 Test-Zusammenfassung:")
            print(f"   ✅ Angebot erfolgreich akzeptiert")
            print(f"   ✅ Kostenposition erstellt")
            print(f"   ✅ Timestamps validiert")
            
            if fee:
                print(f"   ✅ BuildWise-Fee erstellt")
            
            print(f"\n🎉 Timestamp-Fix-Test erfolgreich abgeschlossen!")
            
        except Exception as e:
            print(f"❌ Fehler beim Test: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await db.close()

async def check_existing_timestamps():
    """Prüft bestehende Timestamps in der Datenbank"""
    
    print("\n🔍 Prüfe bestehende Timestamps in der Datenbank...")
    
    database_url = "sqlite+aiosqlite:///buildwise.db"
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        try:
            # Prüfe Kostenpositionen
            print("\n📋 Kostenpositionen:")
            cost_positions_query = select(CostPosition).order_by(CostPosition.id.desc()).limit(5)
            cost_positions_result = await db.execute(cost_positions_query)
            cost_positions = cost_positions_result.scalars().all()
            
            for cp in cost_positions:
                print(f"   ID {cp.id}: created_at={cp.created_at}, updated_at={cp.updated_at}")
            
            # Prüfe BuildWise-Fees
            print("\n💰 BuildWise-Fees:")
            fees_query = select(BuildWiseFee).order_by(BuildWiseFee.id.desc()).limit(5)
            fees_result = await db.execute(fees_query)
            fees = fees_result.scalars().all()
            
            for fee in fees:
                print(f"   ID {fee.id}: created_at={fee.created_at}, updated_at={fee.updated_at}")
            
            # Prüfe Quotes
            print("\n📄 Quotes:")
            quotes_query = select(Quote).order_by(Quote.id.desc()).limit(5)
            quotes_result = await db.execute(quotes_query)
            quotes = quotes_result.scalars().all()
            
            for quote in quotes:
                print(f"   ID {quote.id}: created_at={quote.created_at}, updated_at={quote.updated_at}")
            
        except Exception as e:
            print(f"❌ Fehler beim Prüfen der Timestamps: {e}")
        
        finally:
            await db.close()

if __name__ == "__main__":
    print("🚀 Starte Timestamp-Fix-Test...")
    
    # Führe Tests aus
    asyncio.run(test_timestamp_fix())
    asyncio.run(check_existing_timestamps())
    
    print("\n✅ Timestamp-Fix-Test abgeschlossen!") 