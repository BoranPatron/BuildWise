from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models import Project
from ..schemas.project import ProjectCreate


async def create_project(db: AsyncSession, owner_id: int, project_in: ProjectCreate) -> Project:
    project = Project(owner_id=owner_id, **project_in.dict())
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


async def get_projects_for_user(db: AsyncSession, owner_id: int) -> list[Project]:
    result = await db.execute(select(Project).where(Project.owner_id == owner_id))
    return list(result.scalars().all())
