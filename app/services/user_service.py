from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional, List
from datetime import datetime

from ..models import User, UserType
from ..core.security import get_password_hash, verify_password
from ..schemas.user import UserCreate, UserUpdate


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()


async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    hashed_password = get_password_hash(user_in.password)
    user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        phone=user_in.phone,
        user_type=user_in.user_type
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def update_user(db: AsyncSession, user_id: int, user_update: UserUpdate) -> User | None:
    user = await get_user_by_id(db, user_id)
    if not user:
        return None
    
    update_data = user_update.dict(exclude_unset=True)
    if update_data:
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(**update_data, updated_at=datetime.utcnow())
        )
        await db.commit()
        await db.refresh(user)
    
    return user


async def verify_email(db: AsyncSession, user_id: int) -> bool:
    user = await get_user_by_id(db, user_id)
    if not user:
        return False
    
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(email_verified=True, updated_at=datetime.utcnow())
    )
    await db.commit()
    return True


async def change_password(db: AsyncSession, user_id: int, current_password: str, new_password: str) -> bool:
    user = await get_user_by_id(db, user_id)
    if not user or not verify_password(current_password, user.hashed_password):
        return False
    
    hashed_new_password = get_password_hash(new_password)
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(hashed_password=hashed_new_password, updated_at=datetime.utcnow())
    )
    await db.commit()
    return True


async def get_service_providers(db: AsyncSession, region: Optional[str] = None) -> List[User]:
    query = select(User).where(
        User.user_type == UserType.SERVICE_PROVIDER,
        User.is_active == True,
        User.is_verified == True
    )
    
    if region:
        query = query.where(User.region == region)
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def search_users(db: AsyncSession, search_term: str, user_type: Optional[UserType] = None) -> List[User]:
    query = select(User).where(User.is_active == True)
    
    if user_type:
        query = query.where(User.user_type == user_type)
    
    # Suche in Name, Email und Firmenname
    search_filter = (
        User.first_name.ilike(f"%{search_term}%") |
        User.last_name.ilike(f"%{search_term}%") |
        User.email.ilike(f"%{search_term}%") |
        User.company_name.ilike(f"%{search_term}%")
    )
    
    query = query.where(search_filter)
    result = await db.execute(query)
    return list(result.scalars().all())


async def deactivate_user(db: AsyncSession, user_id: int) -> bool:
    user = await get_user_by_id(db, user_id)
    if not user:
        return False
    
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(is_active=False, updated_at=datetime.utcnow())
    )
    await db.commit()
    return True
