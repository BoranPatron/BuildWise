from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from typing import List, Optional
from datetime import datetime
import logging
import uuid

from ..models import Milestone, MilestoneStatus, Project
from ..schemas.milestone import MilestoneCreate, MilestoneUpdate


async def create_milestone(db: AsyncSession, milestone_in: MilestoneCreate, created_by: int) -> Milestone:
    """Erstellt ein neues Gewerk mit automatischer Bauphasen-Zuordnung"""
    from ..models import Project
    
    # Hole das Projekt, um die aktuelle Bauphase zu ermitteln
    project_result = await db.execute(
        select(Project).where(Project.id == milestone_in.project_id)
    )
    project = project_result.scalar_one_or_none()
    
    # Erstelle das Gewerk
    milestone_data = {
        'project_id': milestone_in.project_id,
        'created_by': created_by,
        'title': milestone_in.title,
        'description': milestone_in.description,
        'status': milestone_in.status,
        'priority': milestone_in.priority,
        'category': milestone_in.category,
        'planned_date': milestone_in.planned_date,
        'start_date': milestone_in.start_date,
        'end_date': milestone_in.end_date,
        'budget': milestone_in.budget,
        'actual_costs': milestone_in.actual_costs,
        'contractor': milestone_in.contractor,
        'is_critical': milestone_in.is_critical,
        'notify_on_completion': milestone_in.notify_on_completion,
        'notes': milestone_in.notes
    }
    
    # Setze automatisch die aktuelle Bauphase des Projekts
    if project and project.construction_phase:
        milestone_data['construction_phase'] = project.construction_phase
        print(f"🏗️ Gewerk erstellt mit Bauphase: {project.construction_phase}")
    else:
        print(f"⚠️ Projekt hat keine Bauphase gesetzt")
    
    milestone = Milestone(**milestone_data)
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


async def get_all_active_milestones(db: AsyncSession) -> list:
    from ..models import Project, MilestoneStatus
    import logging
    session_id = str(uuid.uuid4())
    logging.warning(f"[SERVICE] get_all_active_milestones: Session {session_id} gestartet")
    # Debug: Prüfe alle Projekte
    projects_result = await db.execute(select(Project))
    all_projects = list(projects_result.scalars().all())
    logging.warning(f"[SERVICE] Session {session_id}: Alle Projekte: {len(all_projects)}")
    for p in all_projects:
        logging.warning(f"[SERVICE] Session {session_id}: Projekt: id={p.id}, name={p.name}, is_public={p.is_public}, allow_quotes={p.allow_quotes}")
    # Debug: Prüfe alle Milestones
    milestones_result = await db.execute(select(Milestone))
    all_milestones = list(milestones_result.scalars().all())
    logging.warning(f"[SERVICE] Session {session_id}: Alle Milestones: {len(all_milestones)}")
    for m in all_milestones:
        logging.warning(f"[SERVICE] Session {session_id}: Milestone: id={m.id}, status={m.status}, project_id={m.project_id}")
    # Alle aktiven Gewerke zurückgeben (unabhängig von Projekt-Öffentlichkeit)
    result = await db.execute(
        select(Milestone)
        .where(
            Milestone.status.in_([MilestoneStatus.PLANNED, MilestoneStatus.IN_PROGRESS])
        )
        .order_by(Milestone.planned_date)
    )
    milestones = list(result.scalars().all())
    logging.warning(f"[SERVICE] Session {session_id}: get_all_active_milestones: {len(milestones)} gefunden.")
    for m in milestones:
        logging.warning(f"[SERVICE] Session {session_id}: Milestone: id={m.id}, title={m.title}, status={m.status}, project_id={m.project_id}")
    return milestones


async def get_milestones_by_construction_phase(db: AsyncSession, project_id: int, construction_phase: str) -> List[Milestone]:
    """Holt Gewerke nach Bauphase"""
    result = await db.execute(
        select(Milestone)
        .where(
            Milestone.project_id == project_id,
            Milestone.construction_phase == construction_phase
        )
        .order_by(Milestone.planned_date)
    )
    return list(result.scalars().all())


async def get_milestone_statistics_by_phase(db: AsyncSession, project_id: int) -> dict:
    """Holt Statistiken für Gewerke nach Bauphasen"""
    # Gesamtanzahl pro Bauphase
    phase_distribution_result = await db.execute(
        select(
            Milestone.construction_phase,
            func.count(Milestone.id).label('count'),
            func.sum(Milestone.budget).label('total_budget'),
            func.sum(Milestone.actual_costs).label('total_costs'),
            func.avg(Milestone.progress_percentage).label('avg_progress')
        )
        .where(Milestone.project_id == project_id)
        .group_by(Milestone.construction_phase)
    )
    
    phase_distribution = {}
    for row in phase_distribution_result.all():
        phase = row.construction_phase or 'Keine Phase'
        phase_distribution[phase] = {
            'count': row.count,
            'total_budget': float(row.total_budget or 0),
            'total_costs': float(row.total_costs or 0),
            'avg_progress': round(float(row.avg_progress or 0), 1),
            'budget_variance': float((row.total_budget or 0) - (row.total_costs or 0))
        }
    
    # Gesamtstatistiken
    total_stats_result = await db.execute(
        select(
            func.count(Milestone.id).label('total_count'),
            func.sum(Milestone.budget).label('total_budget'),
            func.sum(Milestone.actual_costs).label('total_costs'),
            func.avg(Milestone.progress_percentage).label('avg_progress')
        )
        .where(Milestone.project_id == project_id)
    )
    
    total_stats = total_stats_result.scalar_one()
    
    return {
        "phase_distribution": phase_distribution,
        "total_count": total_stats.total_count,
        "total_budget": float(total_stats.total_budget or 0),
        "total_costs": float(total_stats.total_costs or 0),
        "avg_progress": round(float(total_stats.avg_progress or 0), 1),
        "total_budget_variance": float((total_stats.total_budget or 0) - (total_stats.total_costs or 0))
    } 