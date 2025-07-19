from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.security import create_access_token
from ..api.deps import get_current_user
from ..schemas.user import (
    UserCreate, UserRead, UserLogin, PasswordReset, PasswordChange, 
    EmailVerification, ConsentUpdate
)
from ..services.user_service import UserService
from ..services.security_service import SecurityService
from ..models.audit_log import AuditAction

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate, 
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Erweiterte Benutzerregistrierung mit DSGVO-Konformität"""
    try:
        user = await UserService.create_user(db, user_in)
        
        # Audit-Log für Registrierung
        ip_address = request.client.host if request else None
        await SecurityService.create_audit_log(
            db, user.id, AuditAction.USER_REGISTER,
            f"Neuer Benutzer registriert: {user.email} (Typ: {user.user_type}, Plan: {user.subscription_plan})",
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
    """Erweiterte Anmeldung mit Rollen- und Subscription-Informationen"""
    # IP-Adresse für Audit-Log
    ip_address = request.client.host if request else None
    
    user = await UserService.authenticate_user(db, form_data.username, form_data.password, ip_address)
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
    
    # Prüfe E-Mail-Verifizierung (Bypass für Admin)
    if not user.email_verified and user.email != "admin@buildwise.de":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="E-Mail-Adresse muss zuerst verifiziert werden"
        )
    
    # Prüfe DSGVO-Einwilligungen (Bypass für Admin)
    if not user.data_processing_consent and user.email != "admin@buildwise.de":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Einwilligung zur Datenverarbeitung erforderlich"
        )
    
    # Prüfe Subscription-Status (Bypass für Admin)
    if not user.subscription_active and user.email != "admin@buildwise.de":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Subscription ist nicht aktiv"
        )
    
    token = create_access_token({"sub": user.email})
    
    # Audit-Log für erfolgreiche Anmeldung
    await SecurityService.create_audit_log(
        db, user.id, AuditAction.USER_LOGIN,
        f"Erfolgreiche Anmeldung: {user.email}",
        resource_type="user", resource_id=user.id,
        ip_address=SecurityService.anonymize_ip_address(ip_address) if ip_address else None,
        risk_level="low"
    )
    
    return {
        "access_token": token, 
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "user_type": user.user_type,
            "subscription_plan": user.subscription_plan,
            "roles": user.roles,
            "permissions": user.permissions,
            "consents": {
                "data_processing": user.data_processing_consent,
                "marketing": user.marketing_consent,
                "privacy_policy": user.privacy_policy_accepted,
                "terms": user.terms_accepted
            }
        }
    }


@router.post("/verify-email/{token}")
async def verify_email(
    token: str, 
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Verifiziert die E-Mail-Adresse eines Benutzers"""
    success = await UserService.verify_email(db, token)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ungültiger oder abgelaufener Verifizierungs-Token"
        )
    
    # Audit-Log für E-Mail-Verifizierung
    ip_address = request.client.host if request else None
    await SecurityService.create_audit_log(
        db, None, AuditAction.USER_UPDATE,
        f"E-Mail-Verifizierung erfolgreich mit Token: {token[:10]}...",
        ip_address=SecurityService.anonymize_ip_address(ip_address) if ip_address else None,
        processing_purpose="E-Mail-Verifizierung",
        legal_basis="Vertragserfüllung"
    )
    
    return {"message": "E-Mail erfolgreich verifiziert"}


@router.post("/resend-verification")
async def resend_verification_email(
    email: str,
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Sendet Verifizierungs-E-Mail erneut"""
    success = await UserService.resend_verification_email(db, email)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="E-Mail-Adresse nicht gefunden oder bereits verifiziert"
        )
    
    # Audit-Log für E-Mail-Neuversand
    ip_address = request.client.host if request else None
    await SecurityService.create_audit_log(
        db, None, AuditAction.USER_UPDATE,
        f"Verifizierungs-E-Mail erneut gesendet an: {email}",
        ip_address=SecurityService.anonymize_ip_address(ip_address) if ip_address else None,
        processing_purpose="E-Mail-Verifizierung",
        legal_basis="Vertragserfüllung"
    )
    
    return {"message": "Verifizierungs-E-Mail wurde erneut gesendet"}


@router.post("/password-reset")
async def request_password_reset(
    password_reset: PasswordReset, 
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Anfrage für Passwort-Reset (sendet E-Mail)"""
    success = await UserService.request_password_reset(db, password_reset.email)
    
    # Audit-Log für Passwort-Reset-Anfrage
    ip_address = request.client.host if request else None
    await SecurityService.create_audit_log(
        db, None, AuditAction.PASSWORD_RESET,
        f"Passwort-Reset angefordert für: {password_reset.email}",
        resource_type="user", resource_id=None,
        ip_address=SecurityService.anonymize_ip_address(ip_address) if ip_address else None,
        risk_level="medium"
    )
    
    # Immer Erfolg zurückgeben (Sicherheit)
    return {"message": "Wenn die E-Mail-Adresse existiert, wurde eine Reset-E-Mail gesendet"}


@router.post("/password-reset/{token}")
async def reset_password_with_token(
    token: str,
    new_password: str,
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Setzt Passwort mit Token zurück"""
    try:
        success = await UserService.reset_password_with_token(db, token, new_password)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ungültiger oder abgelaufener Reset-Token"
            )
        
        # Audit-Log für Passwort-Reset
        ip_address = request.client.host if request else None
        await SecurityService.create_audit_log(
            db, None, AuditAction.PASSWORD_RESET,
            f"Passwort erfolgreich zurückgesetzt mit Token: {token[:10]}...",
            ip_address=SecurityService.anonymize_ip_address(ip_address) if ip_address else None,
            risk_level="high"
        )
        
        return {"message": "Passwort erfolgreich zurückgesetzt"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/password-change")
async def change_user_password(
    password_change: PasswordChange,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Ändert das Passwort des aktuellen Benutzers"""
    try:
        success = await UserService.change_password(
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


@router.post("/consents")
async def update_consents(
    consents: ConsentUpdate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Aktualisiert DSGVO-Einwilligungen"""
    user = await UserService.update_consents(db, current_user.id, consents)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Benutzer nicht gefunden"
        )
    
    # Audit-Log für Einwilligungsaktualisierung
    ip_address = request.client.host if request else None
    await SecurityService.create_audit_log(
        db, current_user.id, AuditAction.USER_UPDATE,
        f"DSGVO-Einwilligungen aktualisiert: {current_user.email}",
        resource_type="user", resource_id=current_user.id,
        ip_address=SecurityService.anonymize_ip_address(ip_address) if ip_address else None,
        processing_purpose="Einwilligungsverwaltung",
        legal_basis="Einwilligung"
    )
    
    return {"message": "Einwilligungen erfolgreich aktualisiert"}


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
