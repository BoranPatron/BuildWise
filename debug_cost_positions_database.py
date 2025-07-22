#!/usr/bin/env python3
"""
Debug-Skript für Kostenpositionen in der Finance-Kachel
Analysiert die Datenbank und prüft, warum keine Kostenpositionen angezeigt werden
"""

import asyncio
import sqlite3
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, and_
import os
import sys

# Füge das app-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.models import Quote, QuoteStatus, CostPosition, Project
from app.core.database import get_db
from app.services.cost_position_service import get_cost_positions_from_accepted_quotes


async def analyze_database():
    """Analysiert die Datenbank für Kostenpositionen"""
    print("🔍 Starte Datenbank-Analyse für Kostenpositionen...")
    
    # SQLite-Verbindung für direkte Abfragen
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()
    
    try:
        # 1. Prüfe alle Tabellen
        print("\n📊 Verfügbare Tabellen:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        for table in tables:
            print(f"  - {table[0]}")
        
        # 2. Prüfe Quotes-Tabelle
        print("\n📋 Quotes-Analyse:")
        cursor.execute("SELECT COUNT(*) FROM quotes")
        total_quotes = cursor.fetchone()[0]
        print(f"  Gesamte Quotes: {total_quotes}")
        
        cursor.execute("SELECT status, COUNT(*) FROM quotes GROUP BY status")
        quote_status = cursor.fetchall()
        for status, count in quote_status:
            print(f"  Status '{status}': {count}")
        
        # 3. Prüfe akzeptierte Quotes
        print("\n✅ Akzeptierte Quotes:")
        cursor.execute("""
            SELECT id, title, project_id, status, accepted_at 
            FROM quotes 
            WHERE status = 'accepted'
        """)
        accepted_quotes = cursor.fetchall()
        for quote in accepted_quotes:
            print(f"  Quote ID {quote[0]}: '{quote[1]}' (Projekt {quote[2]}) - Akzeptiert: {quote[4]}")
        
        # 4. Prüfe CostPositions-Tabelle
        print("\n💰 CostPositions-Analyse:")
        cursor.execute("SELECT COUNT(*) FROM cost_positions")
        total_cost_positions = cursor.fetchone()[0]
        print(f"  Gesamte CostPositions: {total_cost_positions}")
        
        if total_cost_positions > 0:
            cursor.execute("""
                SELECT id, title, project_id, quote_id, amount, status 
                FROM cost_positions
            """)
            cost_positions = cursor.fetchall()
            for cp in cost_positions:
                print(f"  CostPosition ID {cp[0]}: '{cp[1]}' (Projekt {cp[2]}, Quote {cp[3]}) - {cp[4]}€ - Status: {cp[5]}")
        
        # 5. Prüfe Projekte
        print("\n🏗️ Projekte:")
        cursor.execute("SELECT id, name FROM projects")
        projects = cursor.fetchall()
        for project in projects:
            print(f"  Projekt {project[0]}: {project[1]}")
        
        # 6. Prüfe Verbindung zwischen Quotes und CostPositions
        print("\n🔗 Quote-CostPosition-Verbindung:")
        cursor.execute("""
            SELECT q.id, q.title, q.status, cp.id, cp.title
            FROM quotes q
            LEFT JOIN cost_positions cp ON q.id = cp.quote_id
            WHERE q.status = 'accepted'
        """)
        connections = cursor.fetchall()
        for conn in connections:
            quote_id, quote_title, quote_status, cp_id, cp_title = conn
            if cp_id:
                print(f"  Quote {quote_id} ('{quote_title}') -> CostPosition {cp_id} ('{cp_title}')")
            else:
                print(f"  Quote {quote_id} ('{quote_title}') -> KEINE CostPosition")
        
        # 7. Prüfe spezifisch für Projekt 4 (falls vorhanden)
        print("\n🎯 Spezielle Analyse für Projekt 4:")
        cursor.execute("""
            SELECT q.id, q.title, q.status, cp.id, cp.title
            FROM quotes q
            LEFT JOIN cost_positions cp ON q.id = cp.quote_id
            WHERE q.project_id = 4 AND q.status = 'accepted'
        """)
        project4_connections = cursor.fetchall()
        if project4_connections:
            for conn in project4_connections:
                quote_id, quote_title, quote_status, cp_id, cp_title = conn
                if cp_id:
                    print(f"  Projekt 4 - Quote {quote_id} ('{quote_title}') -> CostPosition {cp_id} ('{cp_title}')")
                else:
                    print(f"  Projekt 4 - Quote {quote_id} ('{quote_title}') -> KEINE CostPosition")
        else:
            print("  Keine akzeptierten Quotes für Projekt 4 gefunden")
        
    except Exception as e:
        print(f"❌ Fehler bei der Datenbank-Analyse: {e}")
    finally:
        conn.close()


async def test_cost_position_service():
    """Testet den CostPosition-Service"""
    print("\n🧪 Teste CostPosition-Service...")
    
    try:
        # Erstelle async engine
        engine = create_async_engine("sqlite+aiosqlite:///./buildwise.db")
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Teste für Projekt 4
            print("🔍 Teste get_cost_positions_from_accepted_quotes für Projekt 4...")
            cost_positions = await get_cost_positions_from_accepted_quotes(session, 4)
            print(f"✅ Gefundene CostPositions: {len(cost_positions)}")
            
            for cp in cost_positions:
                print(f"  - {cp.title}: {cp.amount}€ (Quote ID: {cp.quote_id})")
            
            # Teste für alle Projekte
            cursor = session.execute(select(Project.id, Project.name))
            projects = cursor.scalars().all()
            
            for project in projects:
                print(f"\n🔍 Teste Projekt {project.id} ('{project.name}')...")
                cost_positions = await get_cost_positions_from_accepted_quotes(session, project.id)
                print(f"  Gefundene CostPositions: {len(cost_positions)}")
                
                for cp in cost_positions:
                    print(f"    - {cp.title}: {cp.amount}€ (Quote ID: {cp.quote_id})")
        
    except Exception as e:
        print(f"❌ Fehler beim Testen des CostPosition-Service: {e}")
        import traceback
        traceback.print_exc()


async def create_missing_cost_positions():
    """Erstellt fehlende CostPositions für akzeptierte Quotes"""
    print("\n🔧 Erstelle fehlende CostPositions...")
    
    try:
        engine = create_async_engine("sqlite+aiosqlite:///./buildwise.db")
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Finde akzeptierte Quotes ohne CostPosition
            cursor = session.execute(
                select(Quote).where(
                    and_(
                        Quote.status == QuoteStatus.ACCEPTED,
                        ~Quote.id.in_(
                            select(CostPosition.quote_id).where(CostPosition.quote_id.isnot(None))
                        )
                    )
                )
            )
            quotes_without_cost_positions = cursor.scalars().all()
            
            print(f"📋 Gefundene akzeptierte Quotes ohne CostPosition: {len(quotes_without_cost_positions)}")
            
            for quote in quotes_without_cost_positions:
                print(f"  Erstelle CostPosition für Quote {quote.id} ('{quote.title}')...")
                
                # Erstelle CostPosition
                cost_position = CostPosition(
                    project_id=quote.project_id,
                    title=f"Kostenposition: {quote.title}",
                    description=quote.description or f"Kostenposition basierend auf Angebot: {quote.title}",
                    amount=quote.total_amount,
                    currency=quote.currency or "EUR",
                    category="other",  # Standard-Kategorie
                    cost_type="quote_accepted",
                    status="active",
                    contractor_name=quote.company_name,
                    contractor_contact=quote.contact_person,
                    contractor_phone=quote.phone,
                    contractor_email=quote.email,
                    contractor_website=quote.website,
                    progress_percentage=0.0,
                    paid_amount=0.0,
                    payment_terms=quote.payment_terms,
                    warranty_period=quote.warranty_period,
                    estimated_duration=quote.estimated_duration,
                    start_date=quote.start_date,
                    completion_date=quote.completion_date,
                    labor_cost=quote.labor_cost,
                    material_cost=quote.material_cost,
                    overhead_cost=quote.overhead_cost,
                    risk_score=quote.risk_score,
                    price_deviation=quote.price_deviation,
                    ai_recommendation=quote.ai_recommendation,
                    quote_id=quote.id,
                    milestone_id=quote.milestone_id
                )
                
                session.add(cost_position)
                print(f"    ✅ CostPosition erstellt: {cost_position.title}")
            
            await session.commit()
            print(f"✅ {len(quotes_without_cost_positions)} CostPositions erfolgreich erstellt")
            
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der CostPositions: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Hauptfunktion"""
    print("🚀 Starte Debug-Analyse für CostPositions...")
    
    # 1. Datenbank-Analyse
    await analyze_database()
    
    # 2. Service-Test
    await test_cost_position_service()
    
    # 3. Erstelle fehlende CostPositions
    await create_missing_cost_positions()
    
    # 4. Erneute Analyse
    print("\n🔄 Erneute Analyse nach Erstellung...")
    await analyze_database()
    await test_cost_position_service()
    
    print("\n✅ Debug-Analyse abgeschlossen!")


if __name__ == "__main__":
    asyncio.run(main()) 