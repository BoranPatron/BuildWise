from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..api.deps import get_current_user
from ..models import User
from ..schemas.project import ProjectCreate, ProjectRead
from ..services.project_service import create_project, get_projects_for_user

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/", response_model=ProjectRead)
async def create_new_project(
    project_in: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await create_project(db, current_user.id, project_in)
    return project


@router.get("/", response_model=List[ProjectRead])
async def read_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    projects = await get_projects_for_user(db, current_user.id)
    return projects
