from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func
from sqlalchemy.orm import selectinload

from ..models import CostPosition, CostCategory, CostType, CostStatus, Quote, QuoteStatus
from ..schemas.cost_position import CostPositionCreate, CostPositionUpdate


async def create_cost_position(db: AsyncSession, cost_position_in: CostPositionCreate) -> CostPosition:
    """Erstellt eine neue Kostenposition mit automatischer Bauphasen-Zuordnung vom Gewerk"""
    from ..models import Project, Milestone
    
    # Erstelle die Kostenposition
    cost_position_data = cost_position_in.dict()
    
    # Priorität 1: Bauphase vom verknüpften Gewerk (Milestone) erben
    if cost_position_in.milestone_id:
        milestone_result = await db.execute(
            select(Milestone).where(Milestone.id == cost_position_in.milestone_id)
        )
        milestone = milestone_result.scalar_one_or_none()
        
        if milestone and milestone.construction_phase:
            cost_position_data['construction_phase'] = milestone.construction_phase
            print(f"🏗️ Kostenposition erstellt mit Bauphase vom Gewerk: {milestone.construction_phase}")
        else:
            print(f"⚠️ Verknüpftes Gewerk hat keine Bauphase gesetzt")
    
    # Priorität 2: Falls kein Gewerk verknüpft, Bauphase vom Projekt erben
    else:
        project_result = await db.execute(
            select(Project).where(Project.id == cost_position_in.project_id)
        )
        project = project_result.scalar_one_or_none()
        
        if project and project.construction_phase:
            cost_position_data['construction_phase'] = project.construction_phase
            print(f"🏗️ Kostenposition erstellt mit Bauphase vom Projekt: {project.construction_phase}")
        else:
            print(f"⚠️ Projekt hat keine Bauphase gesetzt")
    
    cost_position = CostPosition(**cost_position_data)
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
    from ..models import Quote, QuoteStatus
    
    # Hole alle akzeptierten Angebote für das Projekt
    accepted_quotes_result = await db.execute(
        select(Quote.id)
        .where(
            and_(
                Quote.project_id == project_id,
                Quote.status == QuoteStatus.ACCEPTED
            )
        )
    )
    accepted_quote_ids = [row[0] for row in accepted_quotes_result.fetchall()]
    
    if not accepted_quote_ids:
        print(f"ℹ️ Keine akzeptierten Angebote für Projekt {project_id} gefunden")
        return []
    
    print(f"✅ {len(accepted_quote_ids)} akzeptierte Angebote für Projekt {project_id} gefunden")
    
    # Hole die entsprechenden Kostenpositionen
    cost_positions_result = await db.execute(
        select(CostPosition)
        .options(selectinload(CostPosition.quote))
        .options(selectinload(CostPosition.milestone))
        .options(selectinload(CostPosition.service_provider))
        .where(CostPosition.quote_id.in_(accepted_quote_ids))
        .order_by(CostPosition.created_at.desc())
    )
    cost_positions = cost_positions_result.scalars().all()
    
    print(f"✅ {len(cost_positions)} Kostenpositionen aus akzeptierten Angeboten gefunden")
    return list(cost_positions)


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


async def get_cost_positions_by_construction_phase(db: AsyncSession, project_id: int, construction_phase: str) -> List[CostPosition]:
    """Holt Kostenpositionen nach Bauphase"""
    result = await db.execute(
        select(CostPosition)
        .options(selectinload(CostPosition.quote))
        .options(selectinload(CostPosition.milestone))
        .options(selectinload(CostPosition.service_provider))
        .where(
            and_(
                CostPosition.project_id == project_id,
                CostPosition.construction_phase == construction_phase
            )
        )
        .order_by(CostPosition.created_at.desc())
    )
    return list(result.scalars().all())


async def get_cost_position_statistics_by_phase(db: AsyncSession, project_id: int) -> dict:
    """Holt Statistiken für Kostenpositionen nach Bauphasen"""
    # Gesamtbetrag pro Bauphase
    phase_distribution_result = await db.execute(
        select(
            CostPosition.construction_phase,
            func.count(CostPosition.id).label('count'),
            func.sum(CostPosition.amount).label('total_amount'),
            func.sum(CostPosition.paid_amount).label('total_paid')
        )
        .where(CostPosition.project_id == project_id)
        .group_by(CostPosition.construction_phase)
    )
    
    phase_distribution = {}
    for row in phase_distribution_result.all():
        phase = row.construction_phase or 'Keine Phase'
        phase_distribution[phase] = {
            'count': row.count,
            'total_amount': float(row.total_amount or 0),
            'total_paid': float(row.total_paid or 0),
            'remaining': float((row.total_amount or 0) - (row.total_paid or 0))
        }
    
    # Gesamtstatistiken
    total_stats_result = await db.execute(
        select(
            func.count(CostPosition.id).label('total_count'),
            func.sum(CostPosition.amount).label('total_amount'),
            func.sum(CostPosition.paid_amount).label('total_paid')
        )
        .where(CostPosition.project_id == project_id)
    )
    
    total_stats = total_stats_result.scalar_one()
    
    return {
        "phase_distribution": phase_distribution,
        "total_count": total_stats.total_count,
        "total_amount": float(total_stats.total_amount or 0),
        "total_paid": float(total_stats.total_paid or 0),
        "total_remaining": float((total_stats.total_amount or 0) - (total_stats.total_paid or 0))
    } 