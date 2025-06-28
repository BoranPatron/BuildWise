from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from typing import List, Optional
from datetime import datetime

from ..models import Project, ProjectStatus, ProjectType
from ..schemas.project import ProjectCreate, ProjectUpdate


async def create_project(db: AsyncSession, owner_id: int, project_in: ProjectCreate) -> Project:
    project = Project(owner_id=owner_id, **project_in.dict())
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


async def get_projects_for_user(db: AsyncSession, owner_id: int) -> List[Project]:
    result = await db.execute(select(Project).where(Project.owner_id == owner_id))
    return list(result.scalars().all())


async def get_project_by_id(db: AsyncSession, project_id: int) -> Project | None:
    result = await db.execute(select(Project).where(Project.id == project_id))
    return result.scalars().first()


async def update_project(db: AsyncSession, project_id: int, project_update: ProjectUpdate) -> Project | None:
    project = await get_project_by_id(db, project_id)
    if not project:
        return None
    
    update_data = project_update.dict(exclude_unset=True)
    if update_data:
        await db.execute(
            update(Project)
            .where(Project.id == project_id)
            .values(**update_data, updated_at=datetime.utcnow())
        )
        await db.commit()
        await db.refresh(project)
    
    return project


async def delete_project(db: AsyncSession, project_id: int) -> bool:
    project = await get_project_by_id(db, project_id)
    if not project:
        return False
    
    await db.delete(project)
    await db.commit()
    return True


async def get_public_projects(db: AsyncSession, project_type: Optional[ProjectType] = None, region: Optional[str] = None) -> List[Project]:
    query = select(Project).where(
        Project.is_public == True,
        Project.allow_quotes == True,
        Project.status.in_([ProjectStatus.PLANNING, ProjectStatus.PREPARATION])
    )
    
    if project_type:
        query = query.where(Project.project_type == project_type)
    
    if region:
        query = query.where(Project.address.ilike(f"%{region}%"))
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_project_progress(db: AsyncSession, project_id: int) -> bool:
    """Aktualisiert den Projektfortschritt basierend auf abgeschlossenen Tasks und Milestones"""
    from ..models import Task, Milestone
    
    # Berechne Fortschritt basierend auf Tasks
    task_result = await db.execute(
        select(func.avg(Task.progress_percentage))
        .where(Task.project_id == project_id)
    )
    task_progress = task_result.scalar() or 0
    
    # Berechne Fortschritt basierend auf Milestones
    milestone_result = await db.execute(
        select(func.avg(Milestone.progress_percentage))
        .where(Milestone.project_id == project_id)
    )
    milestone_progress = milestone_result.scalar() or 0
    
    # Kombiniere beide Fortschritte (gewichtet)
    overall_progress = (task_progress * 0.6) + (milestone_progress * 0.4)
    
    await db.execute(
        update(Project)
        .where(Project.id == project_id)
        .values(progress_percentage=overall_progress, updated_at=datetime.utcnow())
    )
    await db.commit()
    return True


async def get_project_dashboard_data(db: AsyncSession, project_id: int) -> dict:
    """Holt alle Daten für das Projekt-Dashboard"""
    from ..models import Task, Milestone, Document, Quote
    
    project = await get_project_by_id(db, project_id)
    if not project:
        return {}
    
    # Task-Statistiken
    task_stats = await db.execute(
        select(
            func.count(Task.id).label('total'),
            func.count(Task.id).filter(Task.status == 'completed').label('completed')
        ).where(Task.project_id == project_id)
    )
    task_data = task_stats.first()
    
    # Milestone-Statistiken
    milestone_stats = await db.execute(
        select(
            func.count(Milestone.id).label('total'),
            func.count(Milestone.id).filter(Milestone.status == 'completed').label('completed')
        ).where(Milestone.project_id == project_id)
    )
    milestone_data = milestone_stats.first()
    
    # Dokumente und Angebote zählen
    document_count = await db.execute(
        select(func.count(Document.id)).where(Document.project_id == project_id)
    )
    quote_count = await db.execute(
        select(func.count(Quote.id)).where(Quote.project_id == project_id)
    )
    
    return {
        "project": project,
        "task_count": task_data.total if task_data else 0,
        "completed_tasks": task_data.completed if task_data else 0,
        "milestone_count": milestone_data.total if milestone_data else 0,
        "completed_milestones": milestone_data.completed if milestone_data else 0,
        "document_count": document_count.scalar() or 0,
        "quote_count": quote_count.scalar() or 0,
        "recent_activities": []  # TODO: Implementiere Aktivitätsverfolgung
    }


async def search_projects(db: AsyncSession, search_term: str, user_id: Optional[int] = None) -> List[Project]:
    query = select(Project)
    
    if user_id:
        query = query.where(Project.owner_id == user_id)
    
    # Suche in Name und Beschreibung
    search_filter = (
        Project.name.ilike(f"%{search_term}%") |
        Project.description.ilike(f"%{search_term}%") |
        Project.address.ilike(f"%{search_term}%")
    )
    
    query = query.where(search_filter)
    result = await db.execute(query)
    return list(result.scalars().all())
