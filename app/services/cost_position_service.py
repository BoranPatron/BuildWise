from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func
from sqlalchemy.orm import selectinload

from ..models import CostPosition, Quote, QuoteStatus, Invoice, Milestone, User
from ..schemas.cost_position import CostPositionListItem
from ..schemas.cost_position import CostPositionCreate, CostPositionUpdate


async def create_cost_position(db: AsyncSession, cost_position_in: CostPositionCreate) -> CostPosition:
    """Erstellt eine neue Kostenposition für eine Rechnung"""
    
    # Erstelle die Kostenposition
    cost_position = CostPosition(**cost_position_in.dict())
    db.add(cost_position)
    await db.commit()
    await db.refresh(cost_position)
    return cost_position


async def get_cost_position_by_id(db: AsyncSession, cost_position_id: int) -> CostPosition | None:
    """Holt eine Kostenposition anhand der ID"""
    result = await db.execute(
        select(CostPosition)
        .options(selectinload(CostPosition.invoice))
        .where(CostPosition.id == cost_position_id)
    )
    return result.scalar_one_or_none()


async def get_cost_positions_for_invoice(db: AsyncSession, invoice_id: int) -> List[CostPosition]:
    """Holt alle Kostenpositionen für eine Rechnung"""
    result = await db.execute(
        select(CostPosition)
        .options(selectinload(CostPosition.invoice))
        .where(CostPosition.invoice_id == invoice_id)
        .order_by(CostPosition.position_order)
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


async def get_cost_position_statistics(db: AsyncSession, invoice_id: int) -> dict:
    """Holt Statistiken für Kostenpositionen einer Rechnung"""
    result = await db.execute(
        select(
            func.count(CostPosition.id).label('total_positions'),
            func.sum(CostPosition.amount).label('total_amount'),
            func.avg(CostPosition.amount).label('average_amount')
        )
        .where(CostPosition.invoice_id == invoice_id)
    )
    
    stats = result.first()
    return {
        'total_positions': stats.total_positions or 0,
        'total_amount': float(stats.total_amount or 0),
        'average_amount': float(stats.average_amount or 0)
    }


async def get_cost_position_by_quote_id(db: AsyncSession, quote_id: int):
    """Holt Kostenposition für ein Angebot über die verknüpfte Rechnung"""
    from sqlalchemy import select
    from ..models.cost_position import CostPosition
    from ..models.invoice import Invoice
    from ..models.quote import Quote
    
    # Finde die Rechnung, die zu diesem Angebot gehört
    result = await db.execute(
        select(Invoice)
        .join(Quote, Quote.milestone_id == Invoice.milestone_id)
        .where(Quote.id == quote_id)
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        return None
    
    # Finde die Kostenposition für diese Rechnung
    cp_result = await db.execute(
        select(CostPosition).where(CostPosition.invoice_id == invoice.id)
    )
    cost_position = cp_result.scalar_one_or_none()
    
    return cost_position 


async def get_cost_positions_for_project(db: AsyncSession, project_id: int) -> List[CostPositionListItem]:
    """Holt alle Kostenpositionen für ein Projekt über die verknüpften Rechnungen"""
    result = await db.execute(
        select(
            CostPosition.id,
            CostPosition.title,
            CostPosition.amount,
            CostPosition.created_at,
            Milestone.id.label("milestone_id"),
            Milestone.title.label("milestone_title"),
            Invoice.service_provider_id,
            User.company_name.label("service_provider_name"),
            CostPosition.contractor_name
        )
        .join(Invoice, CostPosition.invoice_id == Invoice.id)
        .join(Milestone, Invoice.milestone_id == Milestone.id)
        .join(User, User.id == Invoice.service_provider_id)
        .where((Invoice.project_id == project_id) | (CostPosition.project_id == project_id))
        .order_by(CostPosition.created_at.desc())
    )
    rows = result.all()
    items: List[CostPositionListItem] = []
    for row in rows:
        items.append(CostPositionListItem(
            id=row.id,
            title=row.title,
            amount=float(row.amount or 0),
            created_at=row.created_at,
            milestone_id=row.milestone_id,
            milestone_title=row.milestone_title,
            service_provider_id=row.service_provider_id,
            service_provider_name=row.service_provider_name,
            contractor_name=row.contractor_name
        ))
    return items