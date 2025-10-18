from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..schemas.user import UserRead, UserUpdate, UserProfile
from ..api.deps import get_current_user
from ..models import User, UserType
from ..services.user_service import (
    get_user_by_id, update_user, get_service_providers, 
    search_users, deactivate_user
)

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
    updated_user = await update_user(db, current_user.id, user_update)
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
    user = await get_user_by_id(db, user_id)
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
    providers = await get_service_providers(db, region)
    return providers


@router.get("/{user_id}/company-logo")
async def get_user_company_logo(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Holt das Firmenlogo eines Benutzers"""
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Benutzer nicht gefunden"
        )
    
    return {
        "user_id": user.id,
        "company_name": user.company_name,
        "company_logo": user.company_logo,
        "company_logo_advertising_consent": user.company_logo_advertising_consent
    }


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
    
    users = await search_users(db, q, user_type)
    return users


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_users_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Deaktiviert das eigene Benutzerkonto"""
    success = await deactivate_user(db, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Benutzer nicht gefunden"
        )
    return None
