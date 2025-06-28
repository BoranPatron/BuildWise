from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..api.deps import get_current_user
from ..models import User, TaskStatus, TaskPriority
from ..schemas.task import TaskCreate, TaskRead, TaskUpdate, TaskSummary
from ..services.task_service import (
    create_task, get_task_by_id, get_tasks_for_project, get_tasks_for_user,
    update_task, delete_task, get_task_statistics, search_tasks,
    get_overdue_tasks, get_upcoming_tasks
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_new_task(
    task_in: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await create_task(db, task_in, current_user.id)
    return task


@router.get("/", response_model=List[TaskSummary])
async def read_tasks(
    project_id: int = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if project_id:
        tasks = await get_tasks_for_project(db, project_id)
    else:
        tasks = await get_tasks_for_user(db, current_user.id)
    return tasks


@router.get("/{task_id}", response_model=TaskRead)
async def read_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aufgabe nicht gefunden"
        )
    return task


@router.put("/{task_id}", response_model=TaskRead)
async def update_task_endpoint(
    task_id: int,
    task_update: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aufgabe nicht gefunden"
        )
    
    updated_task = await update_task(db, task_id, task_update)
    return updated_task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_endpoint(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aufgabe nicht gefunden"
        )
    
    success = await delete_task(db, task_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aufgabe konnte nicht gelöscht werden"
        )
    
    return None


@router.get("/project/{project_id}/statistics")
async def get_project_task_statistics(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Holt Statistiken für Tasks eines Projekts"""
    stats = await get_task_statistics(db, project_id)
    return stats


@router.get("/search", response_model=List[TaskSummary])
async def search_tasks_endpoint(
    q: str = Query(..., min_length=2, description="Suchbegriff"),
    project_id: int = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Sucht nach Tasks"""
    tasks = await search_tasks(db, q, project_id)
    return tasks


@router.get("/overdue", response_model=List[TaskSummary])
async def get_overdue_tasks_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Holt überfällige Tasks"""
    tasks = await get_overdue_tasks(db, current_user.id)
    return tasks


@router.get("/upcoming", response_model=List[TaskSummary])
async def get_upcoming_tasks_endpoint(
    days: int = Query(7, ge=1, le=90, description="Anzahl Tage"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Holt anstehende Tasks in den nächsten X Tagen"""
    tasks = await get_upcoming_tasks(db, current_user.id, days)
    return tasks 