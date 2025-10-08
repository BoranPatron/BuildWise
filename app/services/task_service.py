from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, or_, and_
from typing import List, Optional
from datetime import datetime, timedelta

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
        is_milestone=task_in.is_milestone,
        milestone_id=task_in.milestone_id
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def get_task_by_id(db: AsyncSession, task_id: int) -> Task | None:
    result = await db.execute(select(Task).where(Task.id == task_id))
    return result.scalars().first()


async def get_tasks_for_project(db: AsyncSession, project_id: int) -> List[Task]:
    from sqlalchemy.orm import selectinload
    
    result = await db.execute(
        select(Task)
        .options(
            selectinload(Task.assigned_user),
            selectinload(Task.milestone)
        )
        .where(Task.project_id == project_id)
    )
    return list(result.scalars().all())


async def get_tasks_for_user(db: AsyncSession, user_id: int) -> List[Task]:
    # Hole alle Aufgaben, die der Benutzer erstellt hat ODER denen er zugewiesen ist
    from sqlalchemy.orm import selectinload
    
    result = await db.execute(
        select(Task)
        .options(
            selectinload(Task.assigned_user),
            selectinload(Task.milestone)
        )
        .where(
            or_(Task.created_by == user_id, Task.assigned_to == user_id)
        )
    )
    return list(result.scalars().all())


async def get_tasks_assigned_to_user(db: AsyncSession, user_id: int) -> List[Task]:
    """Hole nur Tasks, die einem bestimmten Benutzer zugewiesen sind"""
    try:
        print(f"[DEBUG] [TASK-SERVICE] get_tasks_assigned_to_user called for user_id={user_id}")
        from sqlalchemy.orm import selectinload
        from ..models import User, Milestone
        
        # Zusätzliche Validierung: Prüfe auf korrupte Daten
        validation_result = await db.execute(
            select(Task.id, Task.assigned_to, Task.milestone_id)
            .where(Task.assigned_to == user_id)
        )
        validation_tasks = validation_result.fetchall()
        
        # Bereinige korrupte Tasks
        corrupted_ids = []
        for task_id, assigned_to, milestone_id in validation_tasks:
            if isinstance(assigned_to, str) or (milestone_id is not None and isinstance(milestone_id, str) and '-' in str(milestone_id)):
                print(f"[ERROR] [TASK-SERVICE] Korrupte Task gefunden: ID={task_id}, assigned_to={assigned_to}, milestone_id={milestone_id}")
                corrupted_ids.append(task_id)
        
        # Lösche korrupte Tasks
        if corrupted_ids:
            print(f"🧹 [TASK-SERVICE] Lösche {len(corrupted_ids)} korrupte Tasks")
            from sqlalchemy import delete
            for task_id in corrupted_ids:
                await db.execute(delete(Task).where(Task.id == task_id))
            await db.commit()
        
        result = await db.execute(
            select(Task)
            .options(
                selectinload(Task.assigned_user),
                selectinload(Task.milestone)
            )
            .where(Task.assigned_to == user_id)
        )
        tasks = list(result.scalars().all())
        print(f"[SUCCESS] [TASK-SERVICE] Found {len(tasks)} tasks assigned to user {user_id}")
        return tasks
        
    except Exception as e:
        print(f"[ERROR] [TASK-SERVICE] Error in get_tasks_assigned_to_user: {e}")
        import traceback
        traceback.print_exc()
        raise


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


async def get_tasks_by_milestone(db: AsyncSession, milestone_id: int) -> List[Task]:
    """Hole alle Tasks die einem Gewerk zugeordnet sind"""
    result = await db.execute(
        select(Task).where(Task.milestone_id == milestone_id)
    )
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


async def get_tasks_by_milestone(db: AsyncSession, milestone_id: int) -> List[Task]:
    """Hole alle Tasks die einem Gewerk zugeordnet sind"""
    result = await db.execute(
        select(Task).where(Task.milestone_id == milestone_id)
    )
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


async def get_tasks_by_milestone(db: AsyncSession, milestone_id: int) -> List[Task]:
    """Hole alle Tasks die einem Gewerk zugeordnet sind"""
    result = await db.execute(
        select(Task).where(Task.milestone_id == milestone_id)
    )
    return list(result.scalars().all()) 