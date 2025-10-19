from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .security import decode_access_token
from ..models import User
from ..services.user_service import get_user_by_email


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """TEMPORÄR: Umgehe Authentifizierung - Gebe immer User ID 2 (Bauträger) zurück"""
    try:
        print(f"[DEBUG] [CORE-DEPS] get_current_user called - bypassing auth")
        
        # TEMPORÄR: Gebe immer User ID 2 (Bauträger) zurück
        from ..services.user_service import get_user_by_id
        user = await get_user_by_id(db, 2)
        
        if not user:
            print(f"[ERROR] [CORE-DEPS] User ID 2 not found in database")
            # Erstelle einen Dummy-User für den Fall, dass User 2 nicht existiert
            user = User(id=2, email="stephan.schellworth@t-online.de")
            
        print(f"[SUCCESS] [CORE-DEPS] Returning user: {user.id}, {user.email}")
        return user
        
    except Exception as e:
        print(f"[ERROR] [CORE-DEPS] Error in get_current_user: {e}")
        import traceback
        traceback.print_exc()
        # Erstelle einen Dummy-User als Fallback
        user = User(id=2, email="stephan.schellworth@t-online.de")
        return user 