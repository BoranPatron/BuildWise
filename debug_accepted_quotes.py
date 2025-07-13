#!/usr/bin/env python3
"""
Debug-Skript für akzeptierte Angebote und Kostenpositionen
Prüft warum akzeptierte Angebote nicht als Kostenpositionen erscheinen
"""

import asyncio
import sys
import os
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import Quote, CostPosition, QuoteStatus, Project
from app.services.cost_position_service import get_cost_positions_from_accepted_quotes


async def debug_accepted_quotes():
    """Debug-Funktion für akzeptierte Angebote"""
    print("🔍 Debug: Akzeptierte Angebote und Kostenpositionen")
    
    engine = create_async_engine("sqlite+aiosqlite:///buildwise.db")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            # 1. Prüfe alle Angebote für Projekt 4
            print("\n📊 1. Alle Angebote für Projekt 4:")
            quotes_query = select(Quote).where(Quote.project_id == 4)
            quotes = await session.execute(quotes_query)
            quotes_list = quotes.scalars().all()
            
            if not quotes_list:
                print("❌ Keine Angebote für Projekt 4 gefunden")
                return
            
            print(f"✅ {len(quotes_list)} Angebote gefunden:")
            for quote in quotes_list:
                print(f"  - ID: {quote.id}, Status: {quote.status}, Betrag: {quote.total_amount}€")
            
            # 2. Prüfe akzeptierte Angebote
            print("\n📊 2. Akzeptierte Angebote:")
            accepted_quotes = [q for q in quotes_list if q.status == QuoteStatus.ACCEPTED]
            print(f"✅ {len(accepted_quotes)} akzeptierte Angebote gefunden:")
            for quote in accepted_quotes:
                print(f"  - ID: {quote.id}, Betrag: {quote.total_amount}€, Service Provider: {quote.service_provider_id}")
            
            # 3. Prüfe alle Kostenpositionen für Projekt 4
            print("\n📊 3. Alle Kostenpositionen für Projekt 4:")
            cost_positions_query = select(CostPosition).where(CostPosition.project_id == 4)
            cost_positions = await session.execute(cost_positions_query)
            cost_positions_list = cost_positions.scalars().all()
            
            print(f"✅ {len(cost_positions_list)} Kostenpositionen gefunden:")
            for cp in cost_positions_list:
                print(f"  - ID: {cp.id}, Titel: {cp.title}, Betrag: {cp.amount}€, Quote ID: {cp.quote_id}")
            
            # 4. Prüfe Kostenpositionen aus akzeptierten Angeboten
            print("\n📊 4. Kostenpositionen aus akzeptierten Angeboten:")
            accepted_quote_ids = [q.id for q in accepted_quotes]
            cost_positions_from_accepted = [cp for cp in cost_positions_list if cp.quote_id in accepted_quote_ids]
            
            print(f"✅ {len(cost_positions_from_accepted)} Kostenpositionen aus akzeptierten Angeboten:")
            for cp in cost_positions_from_accepted:
                print(f"  - ID: {cp.id}, Titel: {cp.title}, Betrag: {cp.amount}€, Quote ID: {cp.quote_id}")
            
            # 5. Prüfe Service-Funktion
            print("\n📊 5. Teste Service-Funktion:")
            try:
                service_result = await get_cost_positions_from_accepted_quotes(session, 4)
                print(f"✅ Service-Funktion gibt {len(service_result)} Kostenpositionen zurück")
                for cp in service_result:
                    print(f"  - ID: {cp.id}, Titel: {cp.title}, Betrag: {cp.amount}€")
            except Exception as e:
                print(f"❌ Service-Funktion Fehler: {e}")
            
            # 6. Analyse des Problems
            print("\n🔍 6. Problem-Analyse:")
            
            if len(accepted_quotes) == 0:
                print("❌ Problem: Keine akzeptierten Angebote vorhanden")
                print("💡 Lösung: Akzeptieren Sie ein Angebot über die Quotes-Seite")
            elif len(cost_positions_from_accepted) == 0:
                print("❌ Problem: Akzeptierte Angebote haben keine zugehörigen Kostenpositionen")
                print("💡 Lösung: Kostenpositionen werden nicht automatisch erstellt")
                print("💡 Lösung: Implementieren Sie die automatische Kostenpositions-Erstellung")
            else:
                print("✅ Alles korrekt: Kostenpositionen sind vorhanden")
            
            # 7. Empfehlungen
            print("\n💡 7. Empfehlungen:")
            if len(accepted_quotes) > 0 and len(cost_positions_from_accepted) == 0:
                print("- Implementieren Sie die automatische Kostenpositions-Erstellung bei Angebotsannahme")
                print("- Prüfen Sie die Quote-Accept-Logik")
                print("- Erstellen Sie manuell Kostenpositionen für akzeptierte Angebote")
            
        except Exception as e:
            print(f"❌ Fehler beim Debug: {e}")
            import traceback
            traceback.print_exc()


async def create_cost_position_for_accepted_quote():
    """Erstellt eine Kostenposition für ein akzeptiertes Angebot"""
    print("\n🔧 Erstelle Kostenposition für akzeptiertes Angebot...")
    
    engine = create_async_engine("sqlite+aiosqlite:///buildwise.db")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            # Finde akzeptiertes Angebot für Projekt 4
            accepted_quote_query = select(Quote).where(
                and_(
                    Quote.project_id == 4,
                    Quote.status == QuoteStatus.ACCEPTED
                )
            )
            accepted_quotes = await session.execute(accepted_quote_query)
            accepted_quote = accepted_quotes.scalar()
            
            if not accepted_quote:
                print("❌ Kein akzeptiertes Angebot für Projekt 4 gefunden")
                return
            
            print(f"✅ Akzeptiertes Angebot gefunden: ID {accepted_quote.id}")
            
            # Prüfe ob bereits eine Kostenposition existiert
            existing_cp_query = select(CostPosition).where(CostPosition.quote_id == accepted_quote.id)
            existing_cp = await session.execute(existing_cp_query)
            existing_cp = existing_cp.scalar()
            
            if existing_cp:
                print(f"✅ Kostenposition bereits vorhanden: ID {existing_cp.id}")
                return
            
            # Erstelle neue Kostenposition
            new_cost_position = CostPosition(
                title=f"Kostenposition für Angebot {accepted_quote.id}",
                description=accepted_quote.description or "Aus akzeptiertem Angebot erstellt",
                amount=accepted_quote.total_amount,
                currency=accepted_quote.currency,
                category="other",  # Standard-Kategorie
                cost_type="service",
                status="active",
                project_id=4,
                quote_id=accepted_quote.id,
                progress_percentage=0,
                paid_amount=0
            )
            
            session.add(new_cost_position)
            await session.commit()
            
            print(f"✅ Neue Kostenposition erstellt: ID {new_cost_position.id}")
            print(f"  - Titel: {new_cost_position.title}")
            print(f"  - Betrag: {new_cost_position.amount}€")
            print(f"  - Quote ID: {new_cost_position.quote_id}")
            
        except Exception as e:
            print(f"❌ Fehler beim Erstellen der Kostenposition: {e}")
            await session.rollback()


if __name__ == "__main__":
    print("🚀 Starte Debug für akzeptierte Angebote...")
    
    # Führe Debug aus
    asyncio.run(debug_accepted_quotes())
    
    # Frage nach automatischer Erstellung
    print("\n" + "="*50)
    response = input("Möchten Sie automatisch eine Kostenposition für das akzeptierte Angebot erstellen? (j/n): ")
    
    if response.lower() in ['j', 'ja', 'y', 'yes']:
        asyncio.run(create_cost_position_for_accepted_quote())
    else:
        print("⏭️ Überspringe automatische Erstellung")
    
    print("\n✅ Debug abgeschlossen") 