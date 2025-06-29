from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from typing import List, Optional
from datetime import datetime

from ..models import Milestone, MilestoneStatus, Project
from ..schemas.milestone import MilestoneCreate, MilestoneUpdate


async def create_milestone(db: AsyncSession, milestone_in: MilestoneCreate, created_by: int) -> Milestone:
    milestone = Milestone(
        project_id=milestone_in.project_id,
        created_by=created_by,
        title=milestone_in.title,
        description=milestone_in.description,
        status=milestone_in.status,
        priority=milestone_in.priority,
        category=milestone_in.category,
        planned_date=milestone_in.planned_date,
        start_date=milestone_in.start_date,
        end_date=milestone_in.end_date,
        budget=milestone_in.budget,
        actual_costs=milestone_in.actual_costs,
        contractor=milestone_in.contractor,
        is_critical=milestone_in.is_critical,
        notify_on_completion=milestone_in.notify_on_completion,
        notes=milestone_in.notes
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


async def get_all_milestones_for_user(db: AsyncSession, user_id: int) -> List[Milestone]:
    """Holt alle Gewerke für alle Projekte des Benutzers"""
    # Hole alle Projekte des Benutzers
    projects_result = await db.execute(
        select(Project.id).where(Project.owner_id == user_id)
    )
    project_ids = [row[0] for row in projects_result.fetchall()]
    
    if not project_ids:
        return []
    
    # Hole alle Gewerke für diese Projekte
    result = await db.execute(
        select(Milestone)
        .where(Milestone.project_id.in_(project_ids))
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
        new_status = update_data.get('status')
        if new_status == MilestoneStatus.COMPLETED and milestone.status.value != MilestoneStatus.COMPLETED.value:
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
    
    return {
        "total": int(stats.total) if stats and stats.total is not None else 0,
        "planned": int(stats.planned) if stats and stats.planned is not None else 0,
        "in_progress": int(stats.in_progress) if stats and stats.in_progress is not None else 0,
        "completed": int(stats.completed) if stats and stats.completed is not None else 0,
        "delayed": int(stats.delayed) if stats and stats.delayed is not None else 0,
        "avg_progress": round(float(stats.avg_progress), 1) if stats and stats.avg_progress is not None else 0.0
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