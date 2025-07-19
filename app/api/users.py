from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from ..core.database import get_db
from ..schemas.user import UserRead, UserUpdate, UserProfile
from ..api.deps import get_current_user
from ..models import User, UserType, UserStatus
from ..services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def read_users_me(
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    return current_user


@router.put("/me", response_model=UserRead)
async def update_users_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    updated_user = await UserService.update_user(db, current_user.id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Benutzer nicht gefunden"
        )
    return updated_user


@router.get("/profile/{user_id}", response_model=UserProfile)
async def get_user_profile(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user = await UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Benutzer nicht gefunden"
        )
    return user


@router.get("/service-providers", response_model=List[UserProfile])
async def get_service_providers_list(
    region: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Holt alle verifizierten Dienstleister"""
    providers = await UserService.get_users_by_type(db, UserType.SERVICE_PROVIDER)
    # Filtere nach Region falls angegeben
    if region:
        providers = [p for p in providers if p.region and region.lower() in p.region.lower()]
    return providers


@router.get("/search", response_model=List[UserProfile])
async def search_users_endpoint(
    q: str,
    user_type: Optional[UserType] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Sucht nach Benutzern"""
    if len(q) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Suchbegriff muss mindestens 2 Zeichen lang sein"
        )
    
    # Einfache Suche - erweitere dies nach Bedarf
    all_users = await UserService.get_active_users(db)
    filtered_users = []
    
    for user in all_users:
        # Suche in Namen, E-Mail und Firmenname
        search_fields = [
            user.first_name, user.last_name, user.email,
            user.company_name, user.bio, user.region
        ]
        
        if any(q.lower() in str(field).lower() for field in search_fields if field):
            if user_type is None or user.user_type == user_type:
                filtered_users.append(user)
    
    return filtered_users


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_users_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Deaktiviert das eigene Benutzerkonto"""
    # Aktualisiere Benutzer-Status
    current_user.is_active = False
    current_user.status = UserStatus.INACTIVE
    current_user.updated_at = datetime.utcnow()
    await db.commit()
    
    return None
