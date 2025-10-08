"""
Task Archivierung Service
Behandelt automatische Archivierung von completed Tasks nach 14 Tagen
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List
from datetime import datetime, timedelta

from ..models import Task, TaskStatus


async def archive_completed_tasks(db: AsyncSession) -> int:
    """Archiviere alle Tasks die seit 14 Tagen completed sind"""
    cutoff_date = datetime.now() - timedelta(days=14)
    
    # Finde alle completed Tasks die älter als 14 Tage sind
    tasks_to_archive = await db.execute(
        select(Task).where(
            and_(
                Task.status == TaskStatus.COMPLETED,
                Task.completed_at <= cutoff_date,
                Task.archived_at.is_(None)
            )
        )
    )
    
    tasks = list(tasks_to_archive.scalars().all())
    archived_count = 0
    
    for task in tasks:
        task.status = TaskStatus.ARCHIVED
        task.archived_at = datetime.now()
        archived_count += 1
    
    if archived_count > 0:
        await db.commit()
        print(f"[SUCCESS] {archived_count} Tasks archiviert")
    
    return archived_count


async def get_archived_tasks(db: AsyncSession, project_id: int = None) -> List[Task]:
    """Hole alle archivierten Tasks"""
    query = select(Task).where(Task.status == TaskStatus.ARCHIVED)
    
    if project_id:
        query = query.where(Task.project_id == project_id)
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def restore_task_from_archive(db: AsyncSession, task_id: int) -> Task | None:
    """Stelle einen archivierten Task wieder her"""
    task = await db.execute(select(Task).where(Task.id == task_id))
    task = task.scalars().first()
    
    if not task or task.status != TaskStatus.ARCHIVED:
        return None
    
    # Setze Status zurück auf completed
    task.status = TaskStatus.COMPLETED
    task.archived_at = None
    task.updated_at = datetime.now()
    
    await db.commit()
    await db.refresh(task)
    return task


async def permanently_delete_archived_tasks(db: AsyncSession, older_than_days: int = 365) -> int:
    """Lösche archivierte Tasks permanent nach X Tagen"""
    cutoff_date = datetime.now() - timedelta(days=older_than_days)
    
    tasks_to_delete = await db.execute(
        select(Task).where(
            and_(
                Task.status == TaskStatus.ARCHIVED,
                Task.archived_at <= cutoff_date
            )
        )
    )
    
    tasks = list(tasks_to_delete.scalars().all())
    deleted_count = len(tasks)
    
    for task in tasks:
        await db.delete(task)
    
    if deleted_count > 0:
        await db.commit()
        print(f"🗑️ {deleted_count} archivierte Tasks permanent gelöscht")
    
    return deleted_count