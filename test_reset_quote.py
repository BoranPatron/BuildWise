#!/usr/bin/env python3
"""
Testskript für die neue reset_quote Funktionalität
"""

import asyncio
import sys
import os
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Füge das BuildWise-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import Quote, QuoteStatus, Milestone, Project, User
from app.services.quote_service import accept_quote, reset_quote


async def test_reset_quote_functionality():
    """Testet die neue reset_quote Funktionalität"""
    
    # Erstelle Engine für SQLite
    DATABASE_URL = "sqlite+aiosqlite:///./buildwise.db"
    engine = create_async_engine(DATABASE_URL, echo=False, future=True)
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        print("🧪 Teste reset_quote Funktionalität...")
        
        # Hole ein Projekt und ein Gewerk
        project_result = await db.execute(select(Project).limit(1))
        project = project_result.scalar_one_or_none()
        
        if not project:
            print("❌ Kein Projekt gefunden")
            return
        
        milestone_result = await db.execute(select(Milestone).where(Milestone.project_id == project.id).limit(1))
        milestone = milestone_result.scalar_one_or_none()
        
        if not milestone:
            print("❌ Kein Gewerk für das Projekt gefunden")
            return
        
        # Hole alle Angebote für das Gewerk
        quotes_result = await db.execute(
            select(Quote).where(Quote.milestone_id == milestone.id)
        )
        quotes = list(quotes_result.scalars().all())
        
        if len(quotes) < 2:
            print("❌ Nicht genügend Angebote für das Gewerk gefunden (mindestens 2 benötigt)")
            return
        
        print(f"📋 Gefunden: {len(quotes)} Angebote für Gewerk '{milestone.title}'")
        
        # Zeige Status vor dem Test
        print("\n📊 Status vor dem Test:")
        for quote in quotes:
            print(f"  - Angebot {quote.id}: {quote.status.value}")
        
        # Akzeptiere das erste Angebot
        first_quote = quotes[0]
        print(f"\n✅ Akzeptiere Angebot {first_quote.id}...")
        accepted_quote = await accept_quote(db, first_quote.id)
        
        if not accepted_quote:
            print("❌ Fehler beim Akzeptieren des Angebots")
            return
        
        # Zeige Status nach dem Akzeptieren
        print("\n📊 Status nach dem Akzeptieren:")
        for quote in quotes:
            quote_result = await db.execute(select(Quote).where(Quote.id == quote.id))
            updated_quote = quote_result.scalar_one_or_none()
            if updated_quote:
                print(f"  - Angebot {updated_quote.id}: {updated_quote.status.value}")
        
        # Setze das Angebot zurück
        print(f"\n🔄 Setze Angebot {first_quote.id} zurück...")
        reset_quote_result = await reset_quote(db, first_quote.id)
        
        if not reset_quote_result:
            print("❌ Fehler beim Zurücksetzen des Angebots")
            return
        
        # Zeige Status nach dem Zurücksetzen
        print("\n📊 Status nach dem Zurücksetzen:")
        for quote in quotes:
            quote_result = await db.execute(select(Quote).where(Quote.id == quote.id))
            updated_quote = quote_result.scalar_one_or_none()
            if updated_quote:
                print(f"  - Angebot {updated_quote.id}: {updated_quote.status.value}")
        
        # Prüfe, ob alle Angebote wieder auf "submitted" sind
        submitted_count = 0
        for quote in quotes:
            quote_result = await db.execute(select(Quote).where(Quote.id == quote.id))
            updated_quote = quote_result.scalar_one_or_none()
            if updated_quote and updated_quote.status == QuoteStatus.SUBMITTED:
                submitted_count += 1
        
        if submitted_count == len(quotes):
            print("\n✅ Test erfolgreich! Alle Angebote sind wieder auf 'submitted'")
        else:
            print(f"\n❌ Test fehlgeschlagen! Nur {submitted_count}/{len(quotes)} Angebote sind auf 'submitted'")
    
    await engine.dispose()


async def main():
    """Hauptfunktion"""
    try:
        await test_reset_quote_functionality()
        print("\n🎉 Test abgeschlossen!")
    except Exception as e:
        print(f"❌ Fehler beim Test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 