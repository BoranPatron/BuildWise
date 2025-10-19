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
    print(f"[DEBUG] get_current_user: Token erhalten: {token[:50]}..." if token else "[DEBUG] get_current_user: Kein Token")
    
    try:
        # Prüfe ob Token vorhanden ist
        if not token:
            print(f"[ERROR] get_current_user: Kein Token erhalten")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No authentication token provided",
            )
        
        payload = decode_access_token(token)
        print(f"[DEBUG] get_current_user: Token decoded: {payload}")
        
        if not payload or "sub" not in payload:
            print(f"[ERROR] get_current_user: Ungültiger Token oder fehlendes 'sub'")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        
        # Versuche zuerst E-Mail aus sub zu verwenden
        email: str = payload["sub"]
        print(f"[DEBUG] get_current_user: Suche User mit E-Mail: {email}")
        
        try:
            user = await get_user_by_email(db, email=email)
            print(f"[DEBUG] get_current_user: User gefunden via E-Mail: {user is not None}")
        except Exception as db_error:
            print(f"[ERROR] get_current_user: Datenbankfehler bei E-Mail-Suche: {db_error}")
            print(f"[ERROR] get_current_user: Database error type: {type(db_error).__name__}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error during user lookup"
            )
        
        # Falls E-Mail nicht funktioniert, versuche User-ID
        if not user and "user_id" in payload:
            print(f"[DEBUG] get_current_user: Versuche User-ID fallback")
            try:
                from ..services.user_service import get_user_by_id
                user_id = payload["user_id"]
                print(f"[DEBUG] get_current_user: Suche User mit ID: {user_id}")
                user = await get_user_by_id(db, user_id)
                print(f"[DEBUG] get_current_user: User gefunden via ID: {user is not None}")
            except Exception as db_error:
                print(f"[ERROR] get_current_user: Datenbankfehler bei ID-Suche: {db_error}")
                print(f"[ERROR] get_current_user: Database error type: {type(db_error).__name__}")
                import traceback
                traceback.print_exc()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database error during user lookup"
                )
        
        if not user:
            print(f"[ERROR] get_current_user: User not found")
            print(f"   - Token payload: {payload}")
            print(f"   - Versuchte E-Mail: {email}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        
        print(f"[SUCCESS] get_current_user: User erfolgreich geladen: {user.id}, {user.email}")
        
        # Zusätzliche Validierung für Tasks API
        if not hasattr(user, 'id') or not user.id:
            print(f"[ERROR] get_current_user: User hat keine gültige ID: {user}")
            raise HTTPException(status_code=401, detail="Invalid user data")
        
        return user
        
    except HTTPException as he:
        print(f"[ERROR] get_current_user: HTTPException: {he.status_code} - {he.detail}")
        raise he
    except Exception as e:
        print(f"[ERROR] get_current_user: Unerwarteter Fehler: {e}")
        print(f"[ERROR] get_current_user: Exception type: {type(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )
