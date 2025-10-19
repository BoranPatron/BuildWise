from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.security import decode_access_token, oauth2_scheme_name
from ..models import User
from ..services.user_service import get_user_by_email


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """
    Authentifiziert den aktuellen User über JWT Token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Token dekodieren
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise credentials_exception
    
    # User-Email aus Token holen
    email: str = payload["sub"]
    
    # User aus Datenbank laden
    user = await get_user_by_email(db, email=email)
    if not user:
        raise credentials_exception
    
    return user
