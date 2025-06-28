from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from typing import List, Optional
from datetime import datetime

from ..models import Milestone, MilestoneStatus
from ..schemas.milestone import MilestoneCreate, MilestoneUpdate


async def create_milestone(db: AsyncSession, milestone_in: MilestoneCreate, created_by: int) -> Milestone:
    milestone = Milestone(
        project_id=milestone_in.project_id,
        created_by=created_by,
        title=milestone_in.title,
        description=milestone_in.description,
        status=milestone_in.status,
        planned_date=milestone_in.planned_date,
        is_critical=milestone_in.is_critical,
        notify_on_completion=milestone_in.notify_on_completion
    )
    db.add(milestone)
    await db.commit()
    await db.refresh(milestone)
    return milestone


async def get_milestone_by_id(db: AsyncSession, milestone_id: int) -> Milestone | None:
    result = await db.execute(select(Milestone).where(Milestone.id == milestone_id))
    return result.scalars().first()


async def get_milestones_for_project(db: AsyncSession, project_id: int) -> List[Milestone]:
    result = await db.execute(
        select(Milestone)
        .where(Milestone.project_id == project_id)
        .order_by(Milestone.planned_date)
    )
    return list(result.scalars().all())


async def update_milestone(db: AsyncSession, milestone_id: int, milestone_update: MilestoneUpdate) -> Milestone | None:
    milestone = await get_milestone_by_id(db, milestone_id)
    if not milestone:
        return None
    
    update_data = milestone_update.dict(exclude_unset=True)
    if update_data:
        # Wenn Meilenstein abgeschlossen wird, setze completed_at
        if update_data.get('status') == MilestoneStatus.COMPLETED and milestone.status != MilestoneStatus.COMPLETED:
            update_data['completed_at'] = datetime.utcnow()
            update_data['progress_percentage'] = 100
            update_data['actual_date'] = datetime.utcnow().date()
        
        await db.execute(
            update(Milestone)
            .where(Milestone.id == milestone_id)
            .values(**update_data, updated_at=datetime.utcnow())
        )
        await db.commit()
        await db.refresh(milestone)
    
    return milestone


async def delete_milestone(db: AsyncSession, milestone_id: int) -> bool:
    milestone = await get_milestone_by_id(db, milestone_id)
    if not milestone:
        return False
    
    await db.delete(milestone)
    await db.commit()
    return True


async def get_milestone_statistics(db: AsyncSession, project_id: int) -> dict:
    """Holt Statistiken für Meilensteine eines Projekts"""
    result = await db.execute(
        select(
            func.count(Milestone.id).label('total'),
            func.count(Milestone.id).filter(Milestone.status == MilestoneStatus.PLANNED).label('planned'),
            func.count(Milestone.id).filter(Milestone.status == MilestoneStatus.IN_PROGRESS).label('in_progress'),
            func.count(Milestone.id).filter(Milestone.status == MilestoneStatus.COMPLETED).label('completed'),
            func.count(Milestone.id).filter(Milestone.status == MilestoneStatus.DELAYED).label('delayed'),
            func.avg(Milestone.progress_percentage).label('avg_progress')
        ).where(Milestone.project_id == project_id)
    )
    
    stats = result.first()
    if not stats:
        return {
            "total": 0,
            "planned": 0,
            "in_progress": 0,
            "completed": 0,
            "delayed": 0,
            "avg_progress": 0.0
        }
    
    return {
        "total": stats.total or 0,
        "planned": stats.planned or 0,
        "in_progress": stats.in_progress or 0,
        "completed": stats.completed or 0,
        "delayed": stats.delayed or 0,
        "avg_progress": round(stats.avg_progress or 0, 1)
    }


async def get_upcoming_milestones(db: AsyncSession, project_id: Optional[int] = None, days: int = 30) -> List[Milestone]:
    """Holt anstehende Meilensteine in den nächsten X Tagen"""
    from datetime import date, timedelta
    
    start_date = date.today()
    end_date = start_date + timedelta(days=days)
    
    query = select(Milestone).where(
        Milestone.planned_date >= start_date,
        Milestone.planned_date <= end_date,
        Milestone.status.in_([MilestoneStatus.PLANNED, MilestoneStatus.IN_PROGRESS])
    )
    
    if project_id:
        query = query.where(Milestone.project_id == project_id)
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_overdue_milestones(db: AsyncSession, project_id: Optional[int] = None) -> List[Milestone]:
    """Holt überfällige Meilensteine"""
    from datetime import date
    
    query = select(Milestone).where(
        Milestone.planned_date < date.today(),
        Milestone.status.in_([MilestoneStatus.PLANNED, MilestoneStatus.IN_PROGRESS])
    )
    
    if project_id:
        query = query.where(Milestone.project_id == project_id)
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def search_milestones(db: AsyncSession, search_term: str, project_id: Optional[int] = None) -> List[Milestone]:
    query = select(Milestone)
    
    if project_id:
        query = query.where(Milestone.project_id == project_id)
    
    # Suche in Titel und Beschreibung
    search_filter = (
        Milestone.title.ilike(f"%{search_term}%") |
        Milestone.description.ilike(f"%{search_term}%")
    )
    
    query = query.where(search_filter)
    result = await db.execute(query)
    return list(result.scalars().all()) 