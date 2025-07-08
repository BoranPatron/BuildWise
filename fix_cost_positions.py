import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.quote import Quote, QuoteStatus
from app.models.cost_position import CostPosition, CostCategory, CostType, CostStatus
from app.models.milestone import Milestone
from sqlalchemy import select, update
from datetime import datetime

async def fix_cost_positions():
    """Behebt das Problem mit fehlenden Kostenpositionen"""
    async for db in get_db():
        print("🔧 Behebe Problem mit Kostenpositionen...")
        
        # 1. Finde alle akzeptierten Angebote
        result = await db.execute(
            select(Quote).where(Quote.status == QuoteStatus.ACCEPTED)
        )
        accepted_quotes = result.scalars().all()
        
        print(f"📋 Akzeptierte Angebote gefunden: {len(accepted_quotes)}")
        
        # 2. Prüfe für jedes akzeptierte Angebot, ob eine Kostenposition existiert
        for quote in accepted_quotes:
            print(f"🔍 Prüfe Angebot: {quote.title} (ID: {quote.id})")
            
            # Prüfe ob bereits eine Kostenposition existiert
            cp_result = await db.execute(
                select(CostPosition).where(CostPosition.quote_id == quote.id)
            )
            existing_cp = cp_result.scalar_one_or_none()
            
            if existing_cp:
                print(f"✅ Kostenposition bereits vorhanden: {existing_cp.title}")
                continue
            
            # Erstelle Kostenposition für dieses Angebot
            print(f"🛠️ Erstelle Kostenposition für Angebot {quote.id}...")
            
            # Bestimme Kategorie basierend auf Gewerk
            category = CostCategory.OTHER
            milestone_id = quote.milestone_id
            if milestone_id is not None:
                milestone_result = await db.execute(
                    select(Milestone).where(Milestone.id == milestone_id)
                )
                milestone = milestone_result.scalar_one_or_none()
                if milestone is not None and milestone.title is not None:
                    title_lower = milestone.title.lower()
                    if 'elektro' in title_lower:
                        category = CostCategory.ELECTRICAL
                    elif 'sanitär' in title_lower or 'wasser' in title_lower:
                        category = CostCategory.PLUMBING
                    elif 'heizung' in title_lower:
                        category = CostCategory.HEATING
                    elif 'dach' in title_lower:
                        category = CostCategory.ROOFING
                    elif 'mauerwerk' in title_lower:
                        category = CostCategory.MASONRY
                    elif 'trockenbau' in title_lower:
                        category = CostCategory.DRYWALL
                    elif 'maler' in title_lower or 'anstrich' in title_lower:
                        category = CostCategory.PAINTING
                    elif 'boden' in title_lower or 'fußboden' in title_lower:
                        category = CostCategory.FLOORING
                    elif 'garten' in title_lower or 'landschaft' in title_lower:
                        category = CostCategory.LANDSCAPING
                    elif 'küche' in title_lower:
                        category = CostCategory.KITCHEN
                    elif 'bad' in title_lower or 'badezimmer' in title_lower:
                        category = CostCategory.BATHROOM
            
            # Erstelle die Kostenposition
            cost_position = CostPosition(
                project_id=quote.project_id,
                title=f"Kostenposition: {quote.title}",
                description=quote.description or f"Kostenposition für {quote.title}",
                amount=quote.total_amount,
                currency=quote.currency,
                category=category,
                cost_type=CostType.QUOTE_ACCEPTED,
                status=CostStatus.ACTIVE,
                payment_terms=quote.payment_terms,
                warranty_period=quote.warranty_period,
                estimated_duration=quote.estimated_duration,
                start_date=quote.start_date,
                completion_date=quote.completion_date,
                contractor_name=quote.company_name,
                contractor_contact=quote.contact_person,
                contractor_phone=quote.phone,
                contractor_email=quote.email,
                contractor_website=quote.website,
                quote_id=quote.id,
                milestone_id=quote.milestone_id,
                service_provider_id=quote.service_provider_id,
                labor_cost=quote.labor_cost,
                material_cost=quote.material_cost,
                overhead_cost=quote.overhead_cost,
                risk_score=quote.risk_score,
                price_deviation=quote.price_deviation,
                ai_recommendation=quote.ai_recommendation,
                progress_percentage=0.0,
                paid_amount=0.0
            )
            
            db.add(cost_position)
            await db.commit()
            
            print(f"✅ Kostenposition erstellt: {cost_position.title} (ID: {cost_position.id})")
        
        # 3. Zeige Zusammenfassung
        result = await db.execute(select(CostPosition))
        all_cp = result.scalars().all()
        print(f"\n📊 Zusammenfassung:")
        print(f"💰 Gesamte Kostenpositionen: {len(all_cp)}")
        
        for cp in all_cp:
            print(f"  - {cp.title} (Projekt: {cp.project_id}, Quote: {cp.quote_id})")
        
        break

async def main():
    await fix_cost_positions()

if __name__ == "__main__":
    asyncio.run(main()) 