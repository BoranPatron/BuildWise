#!/usr/bin/env python3
"""
Debug-Skript für Backend-Kostenpositionen-Problem
Behebt das 500 Internal Server Error bei /cost-positions/
"""

import asyncio
import sys
import os
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models import Quote, CostPosition, QuoteStatus
from app.services.cost_position_service import get_cost_positions_from_accepted_quotes


async def debug_cost_positions_issue():
    """Debug-Funktion für das Kostenpositionen-Problem"""
    print("🔍 Debug: Kostenpositionen-Backend-Problem")
    
    # Erstelle eine Datenbankverbindung
    engine = create_async_engine("sqlite+aiosqlite:///buildwise.db")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        try:
            print("\n1️⃣ Prüfe Quote-Status in der Datenbank...")
            
            # Hole alle Quotes für Projekt 4
            quotes_result = await db.execute(
                select(Quote).where(Quote.project_id == 4)
            )
            quotes = quotes_result.scalars().all()
            
            print(f"📊 Gefundene Quotes für Projekt 4: {len(quotes)}")
            
            for quote in quotes:
                print(f"  - Quote {quote.id}: Status = '{quote.status}' (Typ: {type(quote.status)})")
                
                # Prüfe ob Status ein Enum oder String ist
                if isinstance(quote.status, QuoteStatus):
                    print(f"    ✅ Korrektes Enum: {quote.status.value}")
                else:
                    print(f"    ⚠️ String-Wert: {quote.status}")
            
            print("\n2️⃣ Prüfe akzeptierte Quotes...")
            
            # Teste beide Abfragen
            accepted_quotes_enum = await db.execute(
                select(Quote).where(
                    and_(
                        Quote.project_id == 4,
                        Quote.status == QuoteStatus.ACCEPTED
                    )
                )
            )
            enum_quotes = accepted_quotes_enum.scalars().all()
            
            accepted_quotes_string = await db.execute(
                select(Quote).where(
                    and_(
                        Quote.project_id == 4,
                        Quote.status == 'accepted'
                    )
                )
            )
            string_quotes = accepted_quotes_string.scalars().all()
            
            print(f"📊 Quotes mit Enum-Status ACCEPTED: {len(enum_quotes)}")
            print(f"📊 Quotes mit String-Status 'accepted': {len(string_quotes)}")
            
            print("\n3️⃣ Teste get_cost_positions_from_accepted_quotes...")
            
            try:
                cost_positions = await get_cost_positions_from_accepted_quotes(db, 4)
                print(f"✅ Kostenpositionen erfolgreich geladen: {len(cost_positions)}")
                
                for cp in cost_positions:
                    print(f"  - Kostenposition {cp.id}: {cp.title} - {cp.amount} EUR")
                    
            except Exception as e:
                print(f"❌ Fehler beim Laden der Kostenpositionen: {e}")
                import traceback
                traceback.print_exc()
            
            print("\n4️⃣ Prüfe CostPosition-Tabelle...")
            
            cost_positions_result = await db.execute(
                select(CostPosition).where(CostPosition.project_id == 4)
            )
            all_cost_positions = cost_positions_result.scalars().all()
            
            print(f"📊 Alle Kostenpositionen für Projekt 4: {len(all_cost_positions)}")
            
            for cp in all_cost_positions:
                print(f"  - CostPosition {cp.id}: {cp.title} - Quote ID: {cp.quote_id}")
            
        except Exception as e:
            print(f"❌ Allgemeiner Fehler: {e}")
            import traceback
            traceback.print_exc()
    
    await engine.dispose()


async def fix_quote_status_issue():
    """Behebt Quote-Status-Probleme in der Datenbank"""
    print("\n🔧 Behebe Quote-Status-Probleme...")
    
    engine = create_async_engine("sqlite+aiosqlite:///buildwise.db")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        try:
            # Hole alle Quotes mit String-Status
            quotes_result = await db.execute(
                select(Quote).where(
                    or_(
                        Quote.status == 'accepted',
                        Quote.status == 'ACCEPTED'
                    )
                )
            )
            string_quotes = quotes_result.scalars().all()
            
            print(f"📊 Quotes mit String-Status gefunden: {len(string_quotes)}")
            
            # Konvertiere String-Status zu Enum
            for quote in string_quotes:
                if quote.status == 'accepted' or quote.status == 'ACCEPTED':
                    quote.status = QuoteStatus.ACCEPTED
                    print(f"  ✅ Quote {quote.id}: Status zu ACCEPTED konvertiert")
            
            await db.commit()
            print("✅ Quote-Status erfolgreich konvertiert")
            
        except Exception as e:
            print(f"❌ Fehler beim Konvertieren: {e}")
            await db.rollback()
    
    await engine.dispose()


async def create_test_cost_position():
    """Erstellt eine Test-Kostenposition für Projekt 4"""
    print("\n🔧 Erstelle Test-Kostenposition...")
    
    engine = create_async_engine("sqlite+aiosqlite:///buildwise.db")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        try:
            # Prüfe ob Quote 1 existiert und akzeptiert ist
            quote_result = await db.execute(
                select(Quote).where(Quote.id == 1)
            )
            quote = quote_result.scalar_one_or_none()
            
            if quote:
                print(f"📊 Quote 1 gefunden: Status = {quote.status}")
                
                # Setze Quote auf ACCEPTED falls nötig
                if quote.status != QuoteStatus.ACCEPTED:
                    quote.status = QuoteStatus.ACCEPTED
                    await db.commit()
                    print("✅ Quote 1 auf ACCEPTED gesetzt")
                
                # Erstelle Test-Kostenposition
                from app.models import CostPosition, CostCategory, CostType, CostStatus
                
                test_cost_position = CostPosition(
                    title="Test Kostenposition",
                    description="Test-Kostenposition aus akzeptiertem Angebot",
                    amount=5000.00,
                    currency="EUR",
                    category=CostCategory.ELECTRICAL,
                    cost_type=CostType.LABOR,
                    status=CostStatus.ACTIVE,
                    project_id=4,
                    quote_id=1,
                    progress_percentage=0,
                    paid_amount=0
                )
                
                db.add(test_cost_position)
                await db.commit()
                print("✅ Test-Kostenposition erstellt")
                
            else:
                print("❌ Quote 1 nicht gefunden")
                
        except Exception as e:
            print(f"❌ Fehler beim Erstellen der Test-Kostenposition: {e}")
            await db.rollback()
    
    await engine.dispose()


async def main():
    """Hauptfunktion"""
    print("🚀 Starte Backend-Debug für Kostenpositionen")
    
    # 1. Debug-Problem analysieren
    await debug_cost_positions_issue()
    
    # 2. Quote-Status-Probleme beheben
    await fix_quote_status_issue()
    
    # 3. Test-Kostenposition erstellen
    await create_test_cost_position()
    
    print("\n✅ Backend-Debug abgeschlossen")


if __name__ == "__main__":
    asyncio.run(main()) 