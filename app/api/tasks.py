from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..api.deps import get_current_user
from ..models import User, TaskStatus, TaskPriority
from ..schemas.task import TaskCreate, TaskRead, TaskUpdate, TaskSummary
from ..services.task_service import (
    create_task, get_task_by_id, get_tasks_for_project, get_tasks_for_user,
    get_tasks_assigned_to_user, update_task, delete_task, get_task_statistics, 
    search_tasks, get_overdue_tasks, get_upcoming_tasks
)
from ..services.task_archiving_service import (
    archive_completed_tasks, get_archived_tasks, restore_task_from_archive
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/health")
async def tasks_health_check():
    """Health check für Tasks API"""
    return {
        "status": "healthy",
        "service": "Tasks API",
        "timestamp": "2025-10-19T08:32:00Z"
    }


@router.post("/", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_new_task(
    task_in: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    print(f"[DEBUG] Backend: Empfange Task-Daten: {task_in}")
    print(f"[DEBUG] Backend: Task-Priorität: {task_in.priority} (Type: {type(task_in.priority)})")
    print(f"[DEBUG] Backend: Task-Beschreibung: {task_in.description}")
    print(f"[DEBUG] Backend: Task-Fälligkeitsdatum: {task_in.due_date}")
    print(f"[DEBUG] Backend: Task-Geschätzte Stunden: {task_in.estimated_hours}")
    print(f"[DEBUG] Backend: Task-Milestone ID: {task_in.milestone_id}")
    
    task = await create_task(db, task_in, current_user.id)
    print(f"[SUCCESS] Backend: Task erstellt mit ID: {task.id}")
    return task


@router.get("/", response_model=List[TaskSummary])
async def read_tasks(
    project_id: int = None,
    assigned_to: int = None,
    db: AsyncSession = Depends(get_db),
):
    try:
        print(f"[DEBUG] [TASKS-API] read_tasks called with project_id={project_id}, assigned_to={assigned_to}")
        
        # TEMPORÄR: Komplett ohne Authentifizierung für Debugging
        if assigned_to == 3:
            print(f"[DEBUG] [TASKS-API] TEMPORÄR: Komplett ohne Authentifizierung für assigned_to=3")
            try:
                tasks = await get_tasks_assigned_to_user(db, assigned_to)
                print(f"[SUCCESS] [TASKS-API] Found {len(tasks)} tasks for user {assigned_to}")
                return tasks
            except Exception as db_error:
                print(f"[ERROR] [TASKS-API] Database error loading tasks for user {assigned_to}: {db_error}")
                raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")
        
        # Für andere Fälle: normale Authentifizierung
        from ..api.deps import get_current_user
        current_user = await get_current_user(db=db, token="dummy")
        
        print(f"[DEBUG] [TASKS-API] Current user details: id={current_user.id}, email={current_user.email}, type={getattr(current_user, 'user_type', 'unknown')}")
        
        # Zusätzliche Validierung des Users
        if not current_user or not current_user.id:
            print(f"[ERROR] [TASKS-API] Invalid current_user: {current_user}")
            raise HTTPException(status_code=401, detail="Invalid user authentication")
        
        if assigned_to:
            # Lade Tasks für einen bestimmten Benutzer
            print(f"[DEBUG] [TASKS-API] Loading tasks assigned to user {assigned_to}")
            try:
                tasks = await get_tasks_assigned_to_user(db, assigned_to)
            except Exception as db_error:
                print(f"[ERROR] [TASKS-API] Database error loading tasks for user {assigned_to}: {db_error}")
                raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")
        elif project_id:
            print(f"[DEBUG] [TASKS-API] Loading tasks for project {project_id}")
            try:
                tasks = await get_tasks_for_project(db, project_id)
            except Exception as db_error:
                print(f"[ERROR] [TASKS-API] Database error loading tasks for project {project_id}: {db_error}")
                raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")
        else:
            print(f"[DEBUG] [TASKS-API] Loading tasks for current user {current_user.id}")
            try:
                tasks = await get_tasks_for_user(db, current_user.id)
            except Exception as db_error:
                print(f"[ERROR] [TASKS-API] Database error loading tasks for user {current_user.id}: {db_error}")
                raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")
        
        print(f"[SUCCESS] [TASKS-API] Found {len(tasks)} tasks")
        return tasks
        
    except HTTPException as he:
        print(f"[ERROR] [TASKS-API] HTTPException in read_tasks: {he.status_code} - {he.detail}")
        raise he
    except Exception as e:
        print(f"[ERROR] [TASKS-API] Error in read_tasks: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error loading tasks: {str(e)}")


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


@router.post("/{task_id}/status")
async def update_task_status_endpoint(
    task_id: int,
    status_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Aktualisiere Task-Status (für Drag & Drop)"""
    task = await get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task nicht gefunden"
        )
    
    # Prüfe Berechtigung
    if task.created_by != current_user.id and task.assigned_to != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für diese Task"
        )
    
    # Extrahiere Status aus JSON
    new_status = status_data.get("status")
    if not new_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status ist erforderlich"
        )
    
    try:
        # Konvertiere String zu TaskStatus Enum
        task_status = TaskStatus(new_status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ungültiger Status: {new_status}"
        )
    
    # Aktualisiere Status
    task_update = TaskUpdate(status=task_status)
    updated_task = await update_task(db, task_id, task_update)
    return {"message": "Status aktualisiert", "task": updated_task}


@router.get("/archived", response_model=List[TaskSummary])
async def get_archived_tasks_endpoint(
    project_id: int = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Hole archivierte Tasks"""
    tasks = await get_archived_tasks(db, project_id)
    return tasks


@router.post("/archive-completed")
async def archive_completed_tasks_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Archiviere alle completed Tasks die älter als 14 Tage sind"""
    archived_count = await archive_completed_tasks(db)
    return {"message": f"{archived_count} Tasks archiviert", "count": archived_count}


@router.post("/{task_id}/restore")
async def restore_task_endpoint(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stelle archivierten Task wieder her"""
    task = await restore_task_from_archive(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivierter Task nicht gefunden"
        )
    
    return {"message": "Task wiederhergestellt", "task": task}


@router.get("/milestone/{milestone_id}", response_model=List[TaskSummary])
async def get_tasks_by_milestone_endpoint(
    milestone_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Hole alle Tasks die einem Gewerk zugeordnet sind"""
    from ..services.task_service import get_tasks_by_milestone
    tasks = await get_tasks_by_milestone(db, milestone_id)
    return tasks 