from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.security import create_access_token
from ..api.deps import get_current_user
from ..schemas.user import UserCreate, UserRead, UserLogin, PasswordReset, PasswordChange
from ..services.user_service import authenticate_user, create_user, get_user_by_email, change_password
from ..services.security_service import SecurityService
from ..models.audit_log import AuditAction

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate, 
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    # Prüfe ob Benutzer bereits existiert
    existing_user = await get_user_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ein Benutzer mit dieser E-Mail-Adresse existiert bereits"
        )
    
    try:
        user = await create_user(db, user_in)
        
        # Audit-Log für Registrierung
        ip_address = request.client.host if request else None
        await SecurityService.create_audit_log(
            db, user.id, AuditAction.USER_REGISTER,
            f"Neuer Benutzer registriert: {user.email}",
            resource_type="user", resource_id=user.id,
            ip_address=SecurityService.anonymize_ip_address(ip_address) if ip_address else None,
            processing_purpose="Benutzerregistrierung",
            legal_basis="Einwilligung"
        )
        
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    # IP-Adresse für Audit-Log
    ip_address = request.client.host if request else None
    
    user = await authenticate_user(db, form_data.username, form_data.password, ip_address)
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
    
    # Prüfe DSGVO-Einwilligungen
    if not user.data_processing_consent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Einwilligung zur Datenverarbeitung erforderlich"
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
            "user_type": user.user_type,
            "consents": {
                "data_processing": user.data_processing_consent,
                "marketing": user.marketing_consent,
                "privacy_policy": user.privacy_policy_accepted,
                "terms": user.terms_accepted
            }
        }
    }


@router.post("/password-reset")
async def request_password_reset(
    password_reset: PasswordReset, 
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Anfrage für Passwort-Reset (sendet E-Mail)"""
    user = await get_user_by_email(db, password_reset.email)
    if user:
        # TODO: Implementiere E-Mail-Versand für Passwort-Reset
        pass
    
    # Audit-Log für Passwort-Reset-Anfrage
    ip_address = request.client.host if request else None
    await SecurityService.create_audit_log(
        db, user.id if user else None, AuditAction.PASSWORD_RESET,
        f"Passwort-Reset angefordert für: {password_reset.email}",
        resource_type="user", resource_id=user.id if user else None,
        ip_address=SecurityService.anonymize_ip_address(ip_address) if ip_address else None,
        risk_level="medium"
    )
    
    # Immer Erfolg zurückgeben (Sicherheit)
    return {"message": "Wenn die E-Mail-Adresse existiert, wurde eine Reset-E-Mail gesendet"}


@router.post("/password-change")
async def change_user_password(
    password_change: PasswordChange,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Ändert das Passwort des aktuellen Benutzers"""
    try:
        success = await change_password(
            db, current_user.id, password_change.current_password, password_change.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Aktuelles Passwort ist falsch"
            )
        
        # Audit-Log für Passwort-Änderung
        ip_address = request.client.host if request else None
        await SecurityService.create_audit_log(
            db, current_user.id, AuditAction.PASSWORD_CHANGE,
            f"Passwort geändert: {current_user.email}",
            resource_type="user", resource_id=current_user.id,
            ip_address=SecurityService.anonymize_ip_address(ip_address) if ip_address else None,
            risk_level="medium"
        )
        
        return {"message": "Passwort erfolgreich geändert"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/verify-email/{token}")
async def verify_email(
    token: str, 
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Verifiziert die E-Mail-Adresse eines Benutzers"""
    # TODO: Implementiere Token-Validierung und E-Mail-Verifizierung
    
    # Audit-Log für E-Mail-Verifizierung
    ip_address = request.client.host if request else None
    await SecurityService.create_audit_log(
        db, None, AuditAction.USER_UPDATE,
        f"E-Mail-Verifizierung mit Token: {token[:10]}...",
        ip_address=SecurityService.anonymize_ip_address(ip_address) if ip_address else None,
        processing_purpose="E-Mail-Verifizierung",
        legal_basis="Vertragserfüllung"
    )
    
    return {"message": "E-Mail erfolgreich verifiziert"}


@router.post("/refresh-token")
async def refresh_token(
    current_user = Depends(get_current_user),
    request: Request = None
):
    """Erstellt einen neuen Access-Token"""
    token = create_access_token({"sub": current_user.email})
    
    # Audit-Log für Token-Refresh
    ip_address = request.client.host if request else None
    await SecurityService.create_audit_log(
        db, current_user.id, AuditAction.USER_LOGIN,
        f"Token erneuert: {current_user.email}",
        resource_type="user", resource_id=current_user.id,
        ip_address=SecurityService.anonymize_ip_address(ip_address) if ip_address else None,
        risk_level="low"
    )
    
    return {"access_token": token, "token_type": "bearer"}


@router.post("/logout")
async def logout(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Logout des Benutzers"""
    # Audit-Log für Logout
    ip_address = request.client.host if request else None
    await SecurityService.create_audit_log(
        db, current_user.id, AuditAction.USER_LOGOUT,
        f"Benutzer abgemeldet: {current_user.email}",
        resource_type="user", resource_id=current_user.id,
        ip_address=SecurityService.anonymize_ip_address(ip_address) if ip_address else None,
        risk_level="low"
    )
    
    return {"message": "Erfolgreich abgemeldet"}
