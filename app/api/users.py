from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..schemas.user import UserRead
from ..api.deps import get_current_user
from ..models import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def read_users_me(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return current_user
