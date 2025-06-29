from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, or_
from typing import List, Optional
from datetime import datetime

from ..models import Task, TaskStatus, TaskPriority
from ..schemas.task import TaskCreate, TaskUpdate


async def create_task(db: AsyncSession, task_in: TaskCreate, created_by: int) -> Task:
    task = Task(
        project_id=task_in.project_id,
        assigned_to=task_in.assigned_to,
        created_by=created_by,
        title=task_in.title,
        description=task_in.description,
        status=task_in.status,
        priority=task_in.priority,
        due_date=task_in.due_date,
        estimated_hours=task_in.estimated_hours,
        is_milestone=task_in.is_milestone
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def get_task_by_id(db: AsyncSession, task_id: int) -> Task | None:
    result = await db.execute(select(Task).where(Task.id == task_id))
    return result.scalars().first()


async def get_tasks_for_project(db: AsyncSession, project_id: int) -> List[Task]:
    result = await db.execute(select(Task).where(Task.project_id == project_id))
    return list(result.scalars().all())


async def get_tasks_for_user(db: AsyncSession, user_id: int) -> List[Task]:
    # Hole alle Aufgaben, die der Benutzer erstellt hat ODER denen er zugewiesen ist
    result = await db.execute(
        select(Task).where(
            or_(Task.created_by == user_id, Task.assigned_to == user_id)
        )
    )
    return list(result.scalars().all())


async def update_task(db: AsyncSession, task_id: int, task_update: TaskUpdate) -> Task | None:
    task = await get_task_by_id(db, task_id)
    if not task:
        return None
    
    update_data = task_update.dict(exclude_unset=True)
    if update_data:
        # Wenn Task abgeschlossen wird, setze completed_at
        if update_data.get('status') == TaskStatus.COMPLETED and task.status != TaskStatus.COMPLETED:
            update_data['completed_at'] = datetime.utcnow()
            update_data['progress_percentage'] = 100
        
        await db.execute(
            update(Task)
            .where(Task.id == task_id)
            .values(**update_data, updated_at=datetime.utcnow())
        )
        await db.commit()
        await db.refresh(task)
    
    return task


async def delete_task(db: AsyncSession, task_id: int) -> bool:
    task = await get_task_by_id(db, task_id)
    if not task:
        return False
    
    await db.delete(task)
    await db.commit()
    return True


async def get_task_statistics(db: AsyncSession, project_id: int) -> dict:
    """Holt Statistiken für Tasks eines Projekts"""
    result = await db.execute(
        select(
            func.count(Task.id).label('total'),
            func.count(Task.id).filter(Task.status == TaskStatus.TODO).label('todo'),
            func.count(Task.id).filter(Task.status == TaskStatus.IN_PROGRESS).label('in_progress'),
            func.count(Task.id).filter(Task.status == TaskStatus.REVIEW).label('review'),
            func.count(Task.id).filter(Task.status == TaskStatus.COMPLETED).label('completed'),
            func.avg(Task.progress_percentage).label('avg_progress')
        ).where(Task.project_id == project_id)
    )
    
    stats = result.first()
    if not stats:
        return {
            "total": 0,
            "todo": 0,
            "in_progress": 0,
            "review": 0,
            "completed": 0,
            "avg_progress": 0.0
        }
    
    return {
        "total": stats.total or 0,
        "todo": stats.todo or 0,
        "in_progress": stats.in_progress or 0,
        "review": stats.review or 0,
        "completed": stats.completed or 0,
        "avg_progress": round(stats.avg_progress or 0, 1)
    }


async def search_tasks(db: AsyncSession, search_term: str, project_id: Optional[int] = None) -> List[Task]:
    query = select(Task)
    
    if project_id:
        query = query.where(Task.project_id == project_id)
    
    # Suche in Titel und Beschreibung
    search_filter = (
        Task.title.ilike(f"%{search_term}%") |
        Task.description.ilike(f"%{search_term}%")
    )
    
    query = query.where(search_filter)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_overdue_tasks(db: AsyncSession, user_id: Optional[int] = None) -> List[Task]:
    """Holt überfällige Tasks"""
    from datetime import date
    
    query = select(Task).where(
        Task.due_date < date.today(),
        Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS])
    )
    
    if user_id:
        query = query.where(Task.assigned_to == user_id)
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_upcoming_tasks(db: AsyncSession, user_id: Optional[int] = None, days: int = 7) -> List[Task]:
    """Holt anstehende Tasks in den nächsten X Tagen"""
    from datetime import date, timedelta
    
    start_date = date.today()
    end_date = start_date + timedelta(days=days)
    
    query = select(Task).where(
        Task.due_date >= start_date,
        Task.due_date <= end_date,
        Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS])
    )
    
    if user_id:
        query = query.where(Task.assigned_to == user_id)
    
    result = await db.execute(query)
    return list(result.scalars().all()) 