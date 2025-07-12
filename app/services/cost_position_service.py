from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func
from sqlalchemy.orm import selectinload

from ..models import CostPosition, CostCategory, CostType, CostStatus, Quote, QuoteStatus
from ..schemas.cost_position import CostPositionCreate, CostPositionUpdate


async def create_cost_position(db: AsyncSession, cost_position_in: CostPositionCreate) -> CostPosition:
    """Erstellt eine neue Kostenposition"""
    cost_position = CostPosition(**cost_position_in.dict())
    db.add(cost_position)
    await db.commit()
    await db.refresh(cost_position)
    return cost_position


async def get_cost_position_by_id(db: AsyncSession, cost_position_id: int) -> CostPosition | None:
    """Holt eine Kostenposition anhand der ID"""
    result = await db.execute(
        select(CostPosition)
        .options(selectinload(CostPosition.project))
        .options(selectinload(CostPosition.quote))
        .options(selectinload(CostPosition.milestone))
        .options(selectinload(CostPosition.service_provider))
        .where(CostPosition.id == cost_position_id)
    )
    return result.scalar_one_or_none()


async def get_cost_positions_for_project(db: AsyncSession, project_id: int) -> List[CostPosition]:
    """Holt alle Kostenpositionen für ein Projekt"""
    result = await db.execute(
        select(CostPosition)
        .options(selectinload(CostPosition.quote))
        .options(selectinload(CostPosition.milestone))
        .options(selectinload(CostPosition.service_provider))
        .where(CostPosition.project_id == project_id)
        .order_by(CostPosition.created_at.desc())
    )
    return list(result.scalars().all())


async def update_cost_position(db: AsyncSession, cost_position_id: int, cost_position_update: CostPositionUpdate) -> CostPosition | None:
    """Aktualisiert eine Kostenposition"""
    cost_position = await get_cost_position_by_id(db, cost_position_id)
    if not cost_position:
        return None
    
    update_data = cost_position_update.dict(exclude_unset=True)
    await db.execute(
        update(CostPosition)
        .where(CostPosition.id == cost_position_id)
        .values(**update_data)
    )
    
    await db.commit()
    await db.refresh(cost_position)
    return cost_position


async def delete_cost_position(db: AsyncSession, cost_position_id: int) -> bool:
    """Löscht eine Kostenposition"""
    cost_position = await get_cost_position_by_id(db, cost_position_id)
    if not cost_position:
        return False
    
    await db.delete(cost_position)
    await db.commit()
    return True


async def get_cost_position_statistics(db: AsyncSession, project_id: int) -> dict:
    """Holt Statistiken für Kostenpositionen eines Projekts"""
    # Gesamtzahl der Kostenpositionen
    total_count_result = await db.execute(
        select(func.count(CostPosition.id))
        .where(CostPosition.project_id == project_id)
    )
    total_count = total_count_result.scalar()
    
    # Gesamtbetrag
    total_amount_result = await db.execute(
        select(func.sum(CostPosition.amount))
        .where(CostPosition.project_id == project_id)
    )
    total_amount = total_amount_result.scalar() or 0
    
    # Gesamtbetrag bezahlt
    total_paid_result = await db.execute(
        select(func.sum(CostPosition.paid_amount))
        .where(CostPosition.project_id == project_id)
    )
    total_paid = total_paid_result.scalar() or 0
    
    # Gesamtbetrag verbleibend
    total_remaining = total_amount - total_paid
    
    # Verteilung nach Kategorien
    category_distribution_result = await db.execute(
        select(CostPosition.category, func.count(CostPosition.id))
        .where(CostPosition.project_id == project_id)
        .group_by(CostPosition.category)
    )
    category_distribution = {cat: count for cat, count in category_distribution_result.all()}
    
    # Verteilung nach Status
    status_distribution_result = await db.execute(
        select(CostPosition.status, func.count(CostPosition.id))
        .where(CostPosition.project_id == project_id)
        .group_by(CostPosition.status)
    )
    status_distribution = {status: count for status, count in status_distribution_result.all()}
    
    # Verteilung nach Typ
    type_distribution_result = await db.execute(
        select(CostPosition.cost_type, func.count(CostPosition.id))
        .where(CostPosition.project_id == project_id)
        .group_by(CostPosition.cost_type)
    )
    type_distribution = {cost_type: count for cost_type, count in type_distribution_result.all()}
    
    return {
        "total_cost_positions": total_count,
        "total_amount": float(total_amount),
        "total_paid": float(total_paid),
        "total_remaining": float(total_remaining),
        "category_distribution": category_distribution,
        "status_distribution": status_distribution,
        "cost_type_distribution": type_distribution
    }


async def get_cost_positions_by_category(db: AsyncSession, project_id: int, category: CostCategory) -> List[CostPosition]:
    """Holt Kostenpositionen nach Kategorie"""
    result = await db.execute(
        select(CostPosition)
        .options(selectinload(CostPosition.quote))
        .options(selectinload(CostPosition.milestone))
        .options(selectinload(CostPosition.service_provider))
        .where(
            and_(
                CostPosition.project_id == project_id,
                CostPosition.category == category
            )
        )
        .order_by(CostPosition.created_at.desc())
    )
    return list(result.scalars().all())


async def get_cost_positions_by_status(db: AsyncSession, project_id: int, status: CostStatus) -> List[CostPosition]:
    """Holt Kostenpositionen nach Status"""
    result = await db.execute(
        select(CostPosition)
        .options(selectinload(CostPosition.quote))
        .options(selectinload(CostPosition.milestone))
        .options(selectinload(CostPosition.service_provider))
        .where(
            and_(
                CostPosition.project_id == project_id,
                CostPosition.status == status
            )
        )
        .order_by(CostPosition.created_at.desc())
    )
    return list(result.scalars().all())


async def update_cost_position_progress(db: AsyncSession, cost_position_id: int, progress_percentage: float) -> CostPosition | None:
    """Aktualisiert den Fortschritt einer Kostenposition"""
    cost_position = await get_cost_position_by_id(db, cost_position_id)
    if not cost_position:
        return None
    
    await db.execute(
        update(CostPosition)
        .where(CostPosition.id == cost_position_id)
        .values(progress_percentage=progress_percentage)
    )
    
    # Wenn Fortschritt 100%, setze Status auf completed
    if progress_percentage >= 100:
        await db.execute(
            update(CostPosition)
            .where(CostPosition.id == cost_position_id)
            .values(status=CostStatus.COMPLETED)
        )
    
    await db.commit()
    await db.refresh(cost_position)
    return cost_position


async def record_payment(db: AsyncSession, cost_position_id: int, payment_amount: float) -> CostPosition | None:
    """Zeichnet eine Zahlung für eine Kostenposition auf"""
    cost_position = await get_cost_position_by_id(db, cost_position_id)
    if not cost_position:
        return None
    
    new_paid_amount = cost_position.paid_amount + payment_amount
    
    await db.execute(
        update(CostPosition)
        .where(CostPosition.id == cost_position_id)
        .values(
            paid_amount=new_paid_amount,
            last_payment_date=func.now()
        )
    )
    
    await db.commit()
    await db.refresh(cost_position)
    return cost_position


async def get_cost_positions_from_accepted_quotes(db: AsyncSession, project_id: int) -> List[CostPosition]:
    """Holt nur Kostenpositionen, die aus akzeptierten Angeboten erstellt wurden"""
    # Hole alle akzeptierten Angebote für das Projekt
    accepted_quotes_result = await db.execute(
        select(Quote)
        .where(
            and_(
                Quote.project_id == project_id,
                Quote.status == QuoteStatus.ACCEPTED
            )
        )
    )
    accepted_quotes = accepted_quotes_result.scalars().all()
    
    # Hole die entsprechenden Kostenpositionen
    cost_positions = []
    for quote in accepted_quotes:
        cost_position_result = await db.execute(
            select(CostPosition)
            .where(CostPosition.quote_id == quote.id)
        )
        # Verwende all() statt scalar_one_or_none() um mehrere CostPositions zu erlauben
        quote_cost_positions = cost_position_result.scalars().all()
        cost_positions.extend(quote_cost_positions)
    
    return cost_positions


async def get_cost_position_statistics_for_accepted_quotes(db: AsyncSession, project_id: int) -> dict:
    """Holt Statistiken nur für Kostenpositionen aus akzeptierten Angeboten"""
    cost_positions = await get_cost_positions_from_accepted_quotes(db, project_id)
    
    if not cost_positions:
        return {
            "total_cost_positions": 0,
            "total_amount": 0.0,
            "total_paid": 0.0,
            "total_remaining": 0.0,
            "category_distribution": {},
            "status_distribution": {},
            "cost_type_distribution": {}
        }
    
    total_amount = sum(cp.amount for cp in cost_positions)
    total_paid = sum(cp.paid_amount for cp in cost_positions)
    total_remaining = total_amount - total_paid
    
    # Kategorie-Verteilung
    category_distribution = {}
    for cp in cost_positions:
        category = cp.category.value if hasattr(cp.category, 'value') else str(cp.category)
        category_distribution[category] = category_distribution.get(category, 0) + 1
    
    # Status-Verteilung
    status_distribution = {}
    for cp in cost_positions:
        status = cp.status.value if hasattr(cp.status, 'value') else str(cp.status)
        status_distribution[status] = status_distribution.get(status, 0) + 1
    
    # Typ-Verteilung
    cost_type_distribution = {}
    for cp in cost_positions:
        cost_type = cp.cost_type.value if hasattr(cp.cost_type, 'value') else str(cp.cost_type)
        cost_type_distribution[cost_type] = cost_type_distribution.get(cost_type, 0) + 1
    
    return {
        "total_cost_positions": len(cost_positions),
        "total_amount": total_amount,
        "total_paid": total_paid,
        "total_remaining": total_remaining,
        "category_distribution": category_distribution,
        "status_distribution": status_distribution,
        "cost_type_distribution": cost_type_distribution
    } 


async def get_cost_position_by_quote_id(db: AsyncSession, quote_id: int):
    result = await db.execute(
        select(CostPosition).where(CostPosition.quote_id == quote_id)
    )
    return result.scalar_one_or_none() 