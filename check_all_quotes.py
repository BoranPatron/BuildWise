#!/usr/bin/env python3
"""
Prüft alle Angebote in der Datenbank
"""

import asyncio
import sys
import os
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import Quote, QuoteStatus, Project


async def check_all_quotes():
    """Prüft alle Angebote in der Datenbank"""
    print("🔍 Prüfe alle Angebote in der Datenbank...")
    
    engine = create_async_engine("sqlite+aiosqlite:///buildwise.db")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            # Prüfe alle Projekte
            print("\n📊 1. Alle Projekte:")
            projects_query = select(Project)
            projects = await session.execute(projects_query)
            projects_list = projects.scalars().all()
            
            print(f"✅ {len(projects_list)} Projekte gefunden:")
            for project in projects_list:
                print(f"  - ID: {project.id}, Name: {project.name}")
            
            # Prüfe alle Angebote
            print("\n📊 2. Alle Angebote:")
            quotes_query = select(Quote)
            quotes = await session.execute(quotes_query)
            quotes_list = quotes.scalars().all()
            
            if not quotes_list:
                print("❌ Keine Angebote in der Datenbank gefunden")
                return
            
            print(f"✅ {len(quotes_list)} Angebote gefunden:")
            for quote in quotes_list:
                print(f"  - ID: {quote.id}, Projekt: {quote.project_id}, Status: {quote.status}, Betrag: {quote.total_amount}€")
            
            # Gruppiere nach Projekten
            print("\n📊 3. Angebote nach Projekten:")
            quotes_by_project = {}
            for quote in quotes_list:
                if quote.project_id not in quotes_by_project:
                    quotes_by_project[quote.project_id] = []
                quotes_by_project[quote.project_id].append(quote)
            
            for project_id, quotes in quotes_by_project.items():
                print(f"\n  Projekt {project_id}:")
                for quote in quotes:
                    print(f"    - Quote ID: {quote.id}, Status: {quote.status}, Betrag: {quote.total_amount}€")
            
            # Prüfe akzeptierte Angebote
            print("\n📊 4. Akzeptierte Angebote:")
            accepted_quotes = [q for q in quotes_list if q.status == QuoteStatus.ACCEPTED]
            print(f"✅ {len(accepted_quotes)} akzeptierte Angebote gefunden:")
            for quote in accepted_quotes:
                print(f"  - ID: {quote.id}, Projekt: {quote.project_id}, Betrag: {quote.total_amount}€")
            
            # Empfehlungen
            print("\n💡 5. Empfehlungen:")
            if len(accepted_quotes) == 0:
                print("- Keine akzeptierten Angebote vorhanden")
                print("- Akzeptieren Sie ein Angebot über die Quotes-Seite")
            elif len([q for q in accepted_quotes if q.project_id == 4]) == 0:
                print("- Keine akzeptierten Angebote für Projekt 4")
                print("- Akzeptierte Angebote sind für andere Projekte")
                print("- Wechseln Sie zu einem anderen Projekt oder akzeptieren Sie ein Angebot für Projekt 4")
            else:
                print("- Akzeptierte Angebote für Projekt 4 vorhanden")
                print("- Prüfen Sie die Kostenpositions-Erstellung")
            
        except Exception as e:
            print(f"❌ Fehler: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(check_all_quotes())
    print("\n✅ Prüfung abgeschlossen") 