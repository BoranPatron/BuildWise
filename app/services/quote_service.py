from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from typing import List, Optional
from datetime import datetime

from ..models import Quote, QuoteStatus
from ..schemas.quote import QuoteCreate, QuoteUpdate


async def create_quote(db: AsyncSession, quote_in: QuoteCreate, service_provider_id: int) -> Quote:
    quote = Quote(
        project_id=quote_in.project_id,
        service_provider_id=service_provider_id,
        title=quote_in.title,
        description=quote_in.description,
        status=quote_in.status,
        total_amount=quote_in.total_amount,
        currency=quote_in.currency,
        valid_until=quote_in.valid_until,
        labor_cost=quote_in.labor_cost,
        material_cost=quote_in.material_cost,
        overhead_cost=quote_in.overhead_cost,
        estimated_duration=quote_in.estimated_duration,
        start_date=quote_in.start_date,
        completion_date=quote_in.completion_date,
        payment_terms=quote_in.payment_terms,
        warranty_period=quote_in.warranty_period
    )
    db.add(quote)
    await db.commit()
    await db.refresh(quote)
    return quote


async def get_quote_by_id(db: AsyncSession, quote_id: int) -> Quote | None:
    result = await db.execute(select(Quote).where(Quote.id == quote_id))
    return result.scalars().first()


async def get_quotes_for_project(db: AsyncSession, project_id: int) -> List[Quote]:
    result = await db.execute(
        select(Quote)
        .where(Quote.project_id == project_id)
        .order_by(Quote.created_at.desc())
    )
    return list(result.scalars().all())


async def get_quotes_for_service_provider(db: AsyncSession, service_provider_id: int) -> List[Quote]:
    result = await db.execute(
        select(Quote)
        .where(Quote.service_provider_id == service_provider_id)
        .order_by(Quote.created_at.desc())
    )
    return list(result.scalars().all())


async def update_quote(db: AsyncSession, quote_id: int, quote_update: QuoteUpdate) -> Quote | None:
    quote = await get_quote_by_id(db, quote_id)
    if not quote:
        return None
    
    update_data = quote_update.dict(exclude_unset=True)
    if update_data:
        await db.execute(
            update(Quote)
            .where(Quote.id == quote_id)
            .values(**update_data, updated_at=datetime.utcnow())
        )
        await db.commit()
        await db.refresh(quote)
    
    return quote


async def delete_quote(db: AsyncSession, quote_id: int) -> bool:
    quote = await get_quote_by_id(db, quote_id)
    if not quote:
        return False
    
    await db.delete(quote)
    await db.commit()
    return True


async def submit_quote(db: AsyncSession, quote_id: int) -> Quote | None:
    """Reicht ein Angebot ein"""
    quote = await get_quote_by_id(db, quote_id)
    if not quote:
        return None
    
    await db.execute(
        update(Quote)
        .where(Quote.id == quote_id)
        .values(
            status=QuoteStatus.SUBMITTED,
            submitted_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    )
    await db.commit()
    await db.refresh(quote)
    return quote


async def accept_quote(db: AsyncSession, quote_id: int) -> Quote | None:
    """Akzeptiert ein Angebot"""
    quote = await get_quote_by_id(db, quote_id)
    if not quote:
        return None
    
    await db.execute(
        update(Quote)
        .where(Quote.id == quote_id)
        .values(
            status=QuoteStatus.ACCEPTED,
            accepted_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    )
    await db.commit()
    await db.refresh(quote)
    return quote


async def get_quote_statistics(db: AsyncSession, project_id: int) -> dict:
    """Holt Statistiken für Angebote eines Projekts"""
    result = await db.execute(
        select(
            func.count(Quote.id).label('total'),
            func.count(Quote.id).filter(Quote.status == QuoteStatus.DRAFT).label('drafts'),
            func.count(Quote.id).filter(Quote.status == QuoteStatus.SUBMITTED).label('submitted'),
            func.count(Quote.id).filter(Quote.status == QuoteStatus.ACCEPTED).label('accepted'),
            func.count(Quote.id).filter(Quote.status == QuoteStatus.REJECTED).label('rejected'),
            func.avg(Quote.total_amount).label('avg_amount'),
            func.min(Quote.total_amount).label('min_amount'),
            func.max(Quote.total_amount).label('max_amount')
        ).where(Quote.project_id == project_id)
    )
    
    stats = result.first()
    if not stats:
        return {
            "total": 0,
            "drafts": 0,
            "submitted": 0,
            "accepted": 0,
            "rejected": 0,
            "avg_amount": 0.0,
            "min_amount": 0.0,
            "max_amount": 0.0
        }
    
    return {
        "total": stats.total or 0,
        "drafts": stats.drafts or 0,
        "submitted": stats.submitted or 0,
        "accepted": stats.accepted or 0,
        "rejected": stats.rejected or 0,
        "avg_amount": round(stats.avg_amount or 0, 2),
        "min_amount": stats.min_amount or 0.0,
        "max_amount": stats.max_amount or 0.0
    }


async def analyze_quote(db: AsyncSession, quote_id: int) -> dict:
    """Analysiert ein Angebot mit KI (Platzhalter-Implementierung)"""
    quote = await get_quote_by_id(db, quote_id)
    if not quote:
        return {}
    
    # TODO: Implementiere echte KI-Analyse
    # Hier nur Platzhalter-Logik
    
    # Berechne Risiko-Score basierend auf verschiedenen Faktoren
    risk_score = 50.0  # Platzhalter
    
    # Berechne Preisabweichung vom Durchschnitt
    avg_amount_result = await db.execute(
        select(func.avg(Quote.total_amount))
        .where(Quote.project_id == quote.project_id, Quote.status == QuoteStatus.SUBMITTED)
    )
    avg_amount = avg_amount_result.scalar() or quote.total_amount
    
    if avg_amount > 0:
        price_deviation = ((quote.total_amount - avg_amount) / avg_amount) * 100
    else:
        price_deviation = 0.0
    
    # Generiere KI-Empfehlung
    if price_deviation < -20:
        ai_recommendation = "Sehr günstiges Angebot - empfohlen"
    elif price_deviation < 0:
        ai_recommendation = "Günstiges Angebot - gut"
    elif price_deviation < 20:
        ai_recommendation = "Durchschnittlicher Preis - akzeptabel"
    else:
        ai_recommendation = "Teures Angebot - prüfen Sie Alternativen"
    
    # Aktualisiere Quote mit Analyse-Ergebnissen
    await db.execute(
        update(Quote)
        .where(Quote.id == quote_id)
        .values(
            risk_score=risk_score,
            price_deviation=price_deviation,
            ai_recommendation=ai_recommendation,
            updated_at=datetime.utcnow()
        )
    )
    await db.commit()
    
    return {
        "quote_id": quote_id,
        "risk_score": risk_score,
        "price_deviation": price_deviation,
        "ai_recommendation": ai_recommendation,
        "comparison_data": {
            "average_amount": avg_amount,
            "total_quotes": await db.execute(
                select(func.count(Quote.id))
                .where(Quote.project_id == quote.project_id, Quote.status == QuoteStatus.SUBMITTED)
            ).scalar() or 0
        }
    } 