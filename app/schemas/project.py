from datetime import date, datetime
from pydantic import BaseModel


class ProjectBase(BaseModel):
    name: str
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class ProjectCreate(ProjectBase):
    pass


class ProjectRead(ProjectBase):
    id: int
    owner_id: int
    created_at: datetime

    class Config:
        orm_mode = True
