from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.security import create_access_token
from ..api.deps import get_current_user
from ..schemas.user import UserCreate, UserRead, UserLogin, PasswordReset, PasswordChange
from ..services.user_service import authenticate_user, create_user, get_user_by_email, change_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    # Prüfe ob Benutzer bereits existiert
    existing_user = await get_user_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ein Benutzer mit dieser E-Mail-Adresse existiert bereits"
        )
    
    user = await create_user(db, user_in)
    return user


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Falsche E-Mail oder Passwort"
        )
    
    # Prüfe ob Benutzer aktiv ist
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Benutzerkonto ist deaktiviert"
        )
    
    token = create_access_token({"sub": user.email})
    return {
        "access_token": token, 
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "user_type": user.user_type
        }
    }


@router.post("/password-reset")
async def request_password_reset(
    password_reset: PasswordReset, db: AsyncSession = Depends(get_db)
):
    """Anfrage für Passwort-Reset (sendet E-Mail)"""
    user = await get_user_by_email(db, password_reset.email)
    if user:
        # TODO: Implementiere E-Mail-Versand für Passwort-Reset
        pass
    
    # Immer Erfolg zurückgeben (Sicherheit)
    return {"message": "Wenn die E-Mail-Adresse existiert, wurde eine Reset-E-Mail gesendet"}


@router.post("/password-change")
async def change_user_password(
    password_change: PasswordChange,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Ändert das Passwort des aktuellen Benutzers"""
    success = await change_password(
        db, current_user.id, password_change.current_password, password_change.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aktuelles Passwort ist falsch"
        )
    
    return {"message": "Passwort erfolgreich geändert"}


@router.post("/verify-email/{token}")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    """Verifiziert die E-Mail-Adresse eines Benutzers"""
    # TODO: Implementiere Token-Validierung und E-Mail-Verifizierung
    return {"message": "E-Mail erfolgreich verifiziert"}


@router.post("/refresh-token")
async def refresh_token(current_user = Depends(get_current_user)):
    """Erstellt einen neuen Access-Token"""
    token = create_access_token({"sub": current_user.email})
    return {"access_token": token, "token_type": "bearer"}
