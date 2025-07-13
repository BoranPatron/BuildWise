#!/usr/bin/env python3
"""
Erstellt ein Angebot für Projekt 4 und akzeptiert es automatisch
"""

import asyncio
import sys
import os
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import Quote, QuoteStatus, Project, CostPosition
from datetime import datetime, timedelta


async def create_quote_for_project_4():
    """Erstellt ein Angebot für Projekt 4 und akzeptiert es"""
    print("🔧 Erstelle Angebot für Projekt 4...")
    
    engine = create_async_engine("sqlite+aiosqlite:///buildwise.db")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            # Prüfe ob Projekt 4 existiert
            project_query = select(Project).where(Project.id == 4)
            project = await session.execute(project_query)
            project = project.scalar()
            
            if not project:
                print("❌ Projekt 4 nicht gefunden")
                return
            
            print(f"✅ Projekt 4 gefunden: {project.name}")
            
            # Prüfe ob bereits ein Angebot für Projekt 4 existiert
            existing_quote_query = select(Quote).where(Quote.project_id == 4)
            existing_quotes = await session.execute(existing_quote_query)
            existing_quotes = existing_quotes.scalars().all()
            
            if existing_quotes:
                print(f"⚠️ {len(existing_quotes)} Angebote für Projekt 4 bereits vorhanden")
                for quote in existing_quotes:
                    print(f"  - ID: {quote.id}, Status: {quote.status}, Betrag: {quote.total_amount}€")
                
                # Akzeptiere das erste Angebot
                first_quote = existing_quotes[0]
                if first_quote.status != QuoteStatus.ACCEPTED:
                    first_quote.status = QuoteStatus.ACCEPTED
                    first_quote.accepted_at = datetime.utcnow()
                    await session.commit()
                    print(f"✅ Angebot {first_quote.id} akzeptiert")
                else:
                    print(f"✅ Angebot {first_quote.id} bereits akzeptiert")
                
                # Erstelle Kostenposition für das akzeptierte Angebot
                await create_cost_position_for_quote(session, first_quote)
                return
            
            # Erstelle neues Angebot für Projekt 4
            new_quote = Quote(
                title="Elektroinstallation",
                description="Vollständige Elektroinstallation für das Gebäude",
                project_id=4,
                service_provider_id=1,  # Verwende den ersten Service Provider
                total_amount=15000.00,
                currency="EUR",
                valid_until=datetime.utcnow() + timedelta(days=30),
                labor_cost=8000.00,
                material_cost=6000.00,
                overhead_cost=1000.00,
                estimated_duration=14,
                start_date=datetime.utcnow() + timedelta(days=7),
                completion_date=datetime.utcnow() + timedelta(days=21),
                payment_terms="30 Tage nach Rechnung",
                warranty_period=24,
                status=QuoteStatus.ACCEPTED,  # Direkt akzeptiert
                accepted_at=datetime.utcnow(),
                company_name="Elektro Müller GmbH",
                contact_person="Hans Müller",
                phone="+49 123 456789",
                email="hans.mueller@elektro-mueller.de",
                website="https://elektro-mueller.de"
            )
            
            session.add(new_quote)
            await session.commit()
            
            print(f"✅ Neues Angebot erstellt: ID {new_quote.id}")
            print(f"  - Titel: {new_quote.title}")
            print(f"  - Betrag: {new_quote.total_amount}€")
            print(f"  - Status: {new_quote.status}")
            
            # Erstelle Kostenposition für das neue Angebot
            await create_cost_position_for_quote(session, new_quote)
            
        except Exception as e:
            print(f"❌ Fehler: {e}")
            await session.rollback()
            import traceback
            traceback.print_exc()


async def create_cost_position_for_quote(session, quote):
    """Erstellt eine Kostenposition für ein akzeptiertes Angebot"""
    try:
        # Prüfe ob bereits eine Kostenposition existiert
        existing_cp_query = select(CostPosition).where(CostPosition.quote_id == quote.id)
        existing_cp = await session.execute(existing_cp_query)
        existing_cp = existing_cp.scalar()
        
        if existing_cp:
            print(f"✅ Kostenposition bereits vorhanden: ID {existing_cp.id}")
            return
        
        # Erstelle neue Kostenposition
        new_cost_position = CostPosition(
            title=f"Kostenposition für {quote.title}",
            description=quote.description or "Aus akzeptiertem Angebot erstellt",
            amount=quote.total_amount,
            currency=quote.currency,
            category="ELECTRICAL",  # Enum-Wert (großgeschrieben)
            cost_type="service",
            status="active",
            project_id=quote.project_id,
            quote_id=quote.id,
            progress_percentage=0,
            paid_amount=0,
            contractor_name=quote.company_name,
            contractor_contact=quote.contact_person,
            contractor_phone=quote.phone,
            contractor_email=quote.email,
            contractor_website=quote.website,
            payment_terms=quote.payment_terms,
            warranty_period=quote.warranty_period,
            estimated_duration=quote.estimated_duration,
            start_date=quote.start_date,
            completion_date=quote.completion_date,
            labor_cost=quote.labor_cost,
            material_cost=quote.material_cost,
            overhead_cost=quote.overhead_cost
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
    print("🚀 Erstelle Angebot für Projekt 4...")
    asyncio.run(create_quote_for_project_4())
    print("\n✅ Angebot für Projekt 4 erstellt!") 