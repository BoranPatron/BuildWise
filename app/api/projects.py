from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..api.deps import get_current_user
from ..models import User, ProjectType, ProjectStatus
from ..schemas.project import (
    ProjectCreate, ProjectRead, ProjectUpdate, ProjectSummary, ProjectDashboard
)
from ..services.project_service import (
    create_project, get_projects_for_user, get_project_by_id, update_project,
    delete_project, get_public_projects, get_project_dashboard_data, search_projects
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_new_project(
    project_in: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await create_project(db, current_user.id, project_in)
    return project


@router.get("/", response_model=List[ProjectSummary])
async def read_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    projects = await get_projects_for_user(db, current_user.id)
    return projects


@router.get("/public", response_model=List[ProjectSummary])
async def read_public_projects(
    project_type: Optional[ProjectType] = None,
    region: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Holt öffentliche Projekte für Dienstleister"""
    projects = await get_public_projects(db, project_type, region)
    return projects


@router.get("/{project_id}", response_model=ProjectRead)
async def read_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projekt nicht gefunden"
        )
    
    # Prüfe Zugriffsberechtigung
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für dieses Projekt"
        )
    
    return project


@router.put("/{project_id}", response_model=ProjectRead)
async def update_project_endpoint(
    project_id: int,
    project_update: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Prüfe Zugriffsberechtigung
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projekt nicht gefunden"
        )
    
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für dieses Projekt"
        )
    
    updated_project = await update_project(db, project_id, project_update)
    return updated_project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project_endpoint(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Prüfe Zugriffsberechtigung
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projekt nicht gefunden"
        )
    
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für dieses Projekt"
        )
    
    success = await delete_project(db, project_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projekt konnte nicht gelöscht werden"
        )
    
    return None


@router.get("/{project_id}/dashboard", response_model=ProjectDashboard)
async def get_project_dashboard(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Prüfe Zugriffsberechtigung
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projekt nicht gefunden"
        )
    
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für dieses Projekt"
        )
    
    dashboard_data = await get_project_dashboard_data(db, project_id)
    return dashboard_data


@router.get("/search", response_model=List[ProjectSummary])
async def search_projects_endpoint(
    q: str = Query(..., min_length=2, description="Suchbegriff"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Sucht nach Projekten des aktuellen Benutzers"""
    projects = await search_projects(db, q, current_user.id)
    return projects
