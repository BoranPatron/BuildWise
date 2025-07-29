from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import BaseModel

from ..core.database import get_db
from ..core.security import create_access_token
from ..api.deps import get_current_user
from ..schemas.user import UserCreate, UserRead, UserLogin, PasswordReset, PasswordChange
from ..services.user_service import authenticate_user, create_user, get_user_by_email, change_password
from ..services.security_service import SecurityService
from ..services.oauth_service import OAuthService
from ..models.audit_log import AuditAction
from ..models.user import AuthProvider, UserRole, User

router = APIRouter(prefix="/auth", tags=["auth"])


class OAuthCallbackRequest(BaseModel):
    code: str
    state: str | None = None
    error: str | None = None


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
            "user_type": user.user_type.value,
            "auth_provider": user.auth_provider.value,
            # Rolleninformationen hinzufügen
            "user_role": user.user_role.value if user.user_role else None,
            "role_selected": user.role_selected,
            "role_selection_modal_shown": user.role_selection_modal_shown,
            # Subscription-Informationen hinzufügen
            "subscription_plan": user.subscription_plan.value if user.subscription_plan else "BASIS",
            "subscription_status": user.subscription_status.value if user.subscription_status else "INACTIVE",
            "max_gewerke": user.max_gewerke,
            # Onboarding-Informationen
            "first_login_completed": user.first_login_completed,
            "onboarding_completed": user.onboarding_completed,
            "onboarding_step": user.onboarding_step,
            "consents": {
                "data_processing": user.data_processing_consent,
                "marketing": user.marketing_consent,
                "privacy_policy": user.privacy_policy_accepted,
                "terms": user.terms_accepted
            }
        }
    }


# Social-Login Endpunkte

@router.get("/oauth/{provider}/url")
async def get_oauth_url(
    provider: str,
    state: Optional[str] = None
):
    """Generiert OAuth-URL für den angegebenen Provider"""
    try:
        url = await OAuthService.get_oauth_url(provider, state)
        return {"oauth_url": url, "provider": provider}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.options("/oauth/{provider}/callback")
async def oauth_callback_options(provider: str):
    """OPTIONS-Handler für OAuth-Callback (CORS Preflight)"""
    from fastapi.responses import Response
    
    response = Response()
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Max-Age"] = "86400"
    return response

@router.post("/oauth/{provider}/callback")
async def oauth_callback(
    provider: str,
    body: OAuthCallbackRequest,
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Verarbeitet OAuth-Callback von Social-Login-Providern"""
    
    # IP-Adresse für Audit-Log
    ip_address = request.client.host if request else None
    
    # Extrahiere Code aus Request
    code = body.code
    state = body.state
    
    print(f"🔍 OAuth-Callback für {provider}:")
    print(f"  - Code: {code[:10] if code else 'None'}...")
    print(f"  - State: {state}")
    print(f"  - IP: {ip_address}")
    
    if not code:
        print(f"❌ OAuth-Callback: Authorization Code fehlt")
        raise HTTPException(
            status_code=400,
            detail="Authorization Code fehlt"
        )
    
    try:
        # Tausche Code gegen Token
        print(f"🔄 Tausche {provider} Code gegen Token...")
        token_data = await OAuthService.exchange_code_for_token(provider, code)
        
        if not token_data:
            print(f"❌ Token-Austausch fehlgeschlagen - keine Daten erhalten")
            raise HTTPException(
                status_code=400,
                detail=f"OAuth-Code ist abgelaufen oder bereits verwendet"
            )
        
        access_token = token_data.get("access_token")
        if not access_token:
            print(f"❌ Kein Access Token in Response: {list(token_data.keys())}")
            raise HTTPException(
                status_code=400,
                detail="Kein Access Token erhalten"
            )
        
        print(f"✅ Access Token erhalten: {access_token[:20]}...")
        
        # Hole Benutzerinformationen
        print(f"🔄 Hole {provider} Benutzerinformationen...")
        if provider == "google":
            user_info = await OAuthService.get_google_user_info(access_token)
        elif provider == "microsoft":
            user_info = await OAuthService.get_microsoft_user_info(access_token)
        else:
            print(f"❌ Unbekannter Provider: {provider}")
            raise HTTPException(
                status_code=400,
                detail=f"Unbekannter OAuth-Provider: {provider}"
            )
        
        if not user_info:
            print(f"❌ Keine Benutzerinformationen erhalten")
            raise HTTPException(
                status_code=400,
                detail="Benutzerinformationen konnten nicht abgerufen werden"
            )
        
        print(f"✅ Benutzerinformationen erhalten: {list(user_info.keys())}")
        
        # Bestimme AuthProvider
        auth_provider = AuthProvider.GOOGLE if provider == "google" else AuthProvider.MICROSOFT
        
        # Finde oder erstelle Benutzer
        print(f"🔄 Finde oder erstelle Benutzer...")
        user = await OAuthService.find_or_create_user_by_social_login(
            db, auth_provider, user_info, ip_address
        )
        
        print(f"✅ Benutzer erfolgreich verarbeitet: {user.id} ({user.email})")
        
        # Erstelle JWT-Token
        print(f"🔄 Erstelle JWT-Token...")
        jwt_token = create_access_token(
            data={"sub": user.email, "user_id": user.id}  # ✅ sub = email, user_id = id
        )
        
        print(f"✅ JWT-Token erstellt: {jwt_token[:20]}...")
        
        # Erfolgreiche Antwort
        response_data = {
            "access_token": jwt_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "user_role": user.user_role.value if user.user_role else None,
                "subscription_plan": user.subscription_plan.value if user.subscription_plan else None,
                "subscription_status": user.subscription_status.value if user.subscription_status else None,
                "role_selected": user.role_selected,
                "onboarding_completed": user.onboarding_completed,
                "first_login_completed": user.first_login_completed
            }
        }
        
        print(f"✅ OAuth-Callback erfolgreich abgeschlossen für User {user.id}")
        return response_data
        
    except HTTPException:
        # Re-raise HTTP-Exceptions
        raise
    except ValueError as e:
        print(f"❌ OAuth ValueError: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        print(f"❌ OAuth-Callback Fehler: {e}")
        print(f"   Typ: {type(e).__name__}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        
        # Spezifische Fehlerbehandlung
        error_message = str(e)
        if "database is locked" in error_message:
            raise HTTPException(
                status_code=503,
                detail="Datenbank ist momentan nicht verfügbar. Bitte versuchen Sie es in wenigen Sekunden erneut."
            )
        elif "invalid_grant" in error_message:
            raise HTTPException(
                status_code=400,
                detail="OAuth-Code ist abgelaufen oder bereits verwendet"
            )
        elif "nicht konfiguriert" in error_message:
            raise HTTPException(
                status_code=500,
                detail="OAuth ist nicht korrekt konfiguriert"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Interner Server-Fehler beim OAuth-Login: {error_message}"
            )


@router.post("/link-social-account/{provider}")
async def link_social_account(
    provider: str,
    code: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Verknüpft Social-Login mit existierendem Benutzerkonto"""
    
    ip_address = request.client.host if request else None
    
    try:
        # Token tauschen und Benutzerinformationen abrufen
        token_data = await OAuthService.exchange_code_for_token(provider, code)
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token-Austausch fehlgeschlagen"
            )
        
        # Benutzerinformationen abrufen
        if provider == "google":
            user_info = await OAuthService.get_google_user_info(token_data.get("access_token"))
            auth_provider = AuthProvider.GOOGLE
        elif provider == "microsoft":
            user_info = await OAuthService.get_microsoft_user_info(token_data.get("access_token"))
            auth_provider = AuthProvider.MICROSOFT
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unbekannter Provider: {provider}"
            )
        
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Benutzerinformationen konnten nicht abgerufen werden"
            )
        
        # Prüfe ob E-Mail-Adresse übereinstimmt
        if user_info.get("email") != current_user.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="E-Mail-Adresse muss mit dem aktuellen Konto übereinstimmen"
            )
        
        # Social-Account verknüpfen
        await OAuthService._link_social_account(db, current_user, auth_provider, user_info)
        
        # Audit-Log
        await SecurityService.create_audit_log(
            db, current_user.id, AuditAction.USER_UPDATE,
            f"Social-Account {provider} verknüpft: {current_user.email}",
            resource_type="user", resource_id=current_user.id,
            ip_address=SecurityService.anonymize_ip_address(ip_address) if ip_address else None,
            processing_purpose="Verknüpfung Social-Login",
            legal_basis="Einwilligung"
        )
        
        return {"message": f"{provider.capitalize()}-Account erfolgreich verknüpft"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Verknüpfung fehlgeschlagen: {str(e)}"
        )


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


@router.get("/check-role")
async def check_role(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Prüft ob der Benutzer seine Rolle bereits ausgewählt hat"""
    
    return {
        "role_selected": current_user.role_selected,
        "user_role": current_user.user_role.value if current_user.user_role else None,
        "user_type": current_user.user_type.value,
        "email": current_user.email
    }


class RoleSelectionRequest(BaseModel):
    role: str  # "bautraeger" oder "dienstleister"


class OnboardingStepRequest(BaseModel):
    step: int  # Onboarding-Schritt


@router.post("/select-role")
async def select_role(
    request: RoleSelectionRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    req: Request = None
):
    """Speichert die gewählte Rolle des Benutzers"""
    
    from datetime import datetime, timedelta
    
    # Prüfe ob User "neu" ist (innerhalb der ersten 24 Stunden nach Registrierung)
    if current_user.created_at is None:
        # Fallback für User ohne created_at
        is_new_user = True
    else:
        user_age = datetime.utcnow() - current_user.created_at
        is_new_user = user_age.total_seconds() < 24 * 60 * 60  # 24 Stunden
    
    # Erlaube Rollenänderung nur für neue User oder wenn noch keine Rolle gesetzt
    if current_user.role_selected and current_user.user_role and not is_new_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rolle wurde bereits ausgewählt. Kontaktieren Sie einen Administrator für Änderungen."
        )
    
    # Validiere die Rolle
    if request.role not in ["bautraeger", "dienstleister"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ungültige Rolle. Wählen Sie 'bautraeger' oder 'dienstleister'."
        )
    
    try:
        # Setze die Rolle
        from datetime import datetime
        from sqlalchemy import update
        
        role_enum = UserRole.BAUTRAEGER if request.role == "bautraeger" else UserRole.DIENSTLEISTER
        
        await db.execute(
            update(User)
            .where(User.id == current_user.id)
            .values(
                user_role=role_enum,
                role_selected=True,
                role_selected_at=datetime.utcnow(),
                role_selection_modal_shown=True  # Markiere dass Modal angezeigt wurde
            )
        )
        await db.commit()
        
        # Credit-Initialisierung für Bauträger
        if request.role == "bautraeger":
            try:
                from ..services.credit_service import CreditService
                
                # Initialisiere Credits für neuen Bauträger
                ip_address = req.client.host if req else None
                credits_initialized = await CreditService.initialize_credits_for_new_user(
                    db=db,
                    user_id=current_user.id,
                    user_role=role_enum,
                    ip_address=ip_address
                )
                
                if credits_initialized:
                    print(f"✅ Credits für neuen Bauträger {current_user.id} initialisiert")
                else:
                    print(f"ℹ️  Credits für User {current_user.id} bereits initialisiert oder nicht erforderlich")
                    
            except Exception as e:
                print(f"❌ Fehler bei Credit-Initialisierung: {e}")
                # Fehler bei Credit-Initialisierung sollte nicht die Rollenauswahl blockieren
        
        # Audit-Log
        ip_address = req.client.host if req else None
        await SecurityService.create_audit_log(
            db, current_user.id, AuditAction.USER_UPDATE,
            f"Rolle ausgewählt: {request.role}",
            resource_type="user", resource_id=current_user.id,
            ip_address=SecurityService.anonymize_ip_address(ip_address) if ip_address else None
        )
        
        return {
            "message": "Rolle erfolgreich ausgewählt",
            "role": request.role,
            "role_selected": True
        }
        
    except Exception as e:
        print(f"❌ Fehler beim Speichern der Rolle: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Speichern der Rolle"
        )


@router.post("/debug/reset-role")
async def debug_reset_role(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    req: Request = None
):
    """DEBUG ONLY: Setzt die Rolle zurück und markiert User als 'neu' für Tests"""
    
    # Nur im Entwicklungsmodus verfügbar
    from ..core.config import settings
    if not getattr(settings, 'DEBUG', False):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endpoint nicht verfügbar"
        )
    
    try:
        from datetime import datetime, timezone
        from sqlalchemy import update
        
        # Setze User als "neu" und entferne Rolle
        await db.execute(
            update(User)
            .where(User.id == current_user.id)
            .values(
                user_role=None,
                role_selected=False,
                role_selected_at=None,
                role_selection_modal_shown=False,  # Setze Modal-Flag zurück
                created_at=datetime.now(timezone.utc),  # Markiere als "neu"
                first_login_completed=False,
                onboarding_completed=False,
                onboarding_step=0
            )
        )
        await db.commit()
        
        # Audit-Log
        ip_address = req.client.host if req else None
        await SecurityService.create_audit_log(
            db, current_user.id, AuditAction.USER_UPDATE,
            f"DEBUG: Rolle zurückgesetzt für Tests",
            resource_type="user", resource_id=current_user.id,
            ip_address=SecurityService.anonymize_ip_address(ip_address) if ip_address else None
        )
        
        return {
            "message": "Rolle erfolgreich zurückgesetzt (DEBUG)",
            "user_id": current_user.id,
            "reset_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        print(f"❌ Fehler beim Zurücksetzen der Rolle: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Zurücksetzen der Rolle"
        )


@router.post("/mark-modal-shown")
async def mark_modal_shown(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    req: Request = None
):
    """Markiert dass das Rollenauswahl-Modal angezeigt wurde"""
    
    try:
        from sqlalchemy import update
        
        # Setze Modal-Flag
        await db.execute(
            update(User)
            .where(User.id == current_user.id)
            .values(
                role_selection_modal_shown=True
            )
        )
        await db.commit()
        
        return {
            "message": "Modal-Flag erfolgreich gesetzt",
            "user_id": current_user.id
        }
        
    except Exception as e:
        print(f"❌ Fehler beim Setzen des Modal-Flags: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Setzen des Modal-Flags"
        )


@router.post("/complete-first-login")
async def complete_first_login(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    req: Request = None
):
    """Markiert den ersten Login als abgeschlossen"""
    
    if current_user.first_login_completed:
        return {
            "message": "Erster Login bereits abgeschlossen",
            "first_login_completed": True
        }
    
    try:
        from datetime import datetime
        from sqlalchemy import update
        
        await db.execute(
            update(User)
            .where(User.id == current_user.id)
            .values(
                first_login_completed=True,
                onboarding_started_at=datetime.utcnow()
            )
        )
        await db.commit()
        
        # Audit-Log
        ip_address = req.client.host if req else None
        await SecurityService.create_audit_log(
            db, current_user.id, AuditAction.USER_UPDATE,
            "Erster Login abgeschlossen",
            resource_type="user", resource_id=current_user.id,
            ip_address=SecurityService.anonymize_ip_address(ip_address) if ip_address else None
        )
        
        return {
            "message": "Erster Login erfolgreich abgeschlossen",
            "first_login_completed": True
        }
        
    except Exception as e:
        print(f"❌ Fehler beim Abschließen des ersten Logins: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Abschließen des ersten Logins"
        )


@router.post("/update-onboarding-step")
async def update_onboarding_step(
    request: OnboardingStepRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    req: Request = None
):
    """Aktualisiert den aktuellen Onboarding-Schritt"""
    
    try:
        from sqlalchemy import update
        
        await db.execute(
            update(User)
            .where(User.id == current_user.id)
            .values(onboarding_step=request.step)
        )
        await db.commit()
        
        # Audit-Log
        ip_address = req.client.host if req else None
        await SecurityService.create_audit_log(
            db, current_user.id, AuditAction.USER_UPDATE,
            f"Onboarding-Schritt aktualisiert: {request.step}",
            resource_type="user", resource_id=current_user.id,
            ip_address=SecurityService.anonymize_ip_address(ip_address) if ip_address else None
        )
        
        return {
            "message": "Onboarding-Schritt erfolgreich aktualisiert",
            "onboarding_step": request.step
        }
        
    except Exception as e:
        print(f"❌ Fehler beim Aktualisieren des Onboarding-Schritts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Aktualisieren des Onboarding-Schritts"
        )


@router.post("/complete-onboarding")
async def complete_onboarding(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    req: Request = None
):
    """Schließt das gesamte Onboarding ab"""
    
    if current_user.onboarding_completed:
        return {
            "message": "Onboarding bereits abgeschlossen",
            "onboarding_completed": True
        }
    
    try:
        from datetime import datetime
        from sqlalchemy import update
        
        await db.execute(
            update(User)
            .where(User.id == current_user.id)
            .values(
                onboarding_completed=True,
                onboarding_completed_at=datetime.utcnow(),
                onboarding_step=999  # Spezial-Wert für "abgeschlossen"
            )
        )
        await db.commit()
        
        # Audit-Log
        ip_address = req.client.host if req else None
        await SecurityService.create_audit_log(
            db, current_user.id, AuditAction.USER_UPDATE,
            "Onboarding abgeschlossen",
            resource_type="user", resource_id=current_user.id,
            ip_address=SecurityService.anonymize_ip_address(ip_address) if ip_address else None
        )
        
        return {
            "message": "Onboarding erfolgreich abgeschlossen",
            "onboarding_completed": True
        }
        
    except Exception as e:
        print(f"❌ Fehler beim Abschließen des Onboardings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Abschließen des Onboardings"
        )


# Microsoft OAuth Endpunkte
@router.get("/oauth/microsoft/url")
async def get_microsoft_oauth_url(
    state: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Generiert Microsoft OAuth URL"""
    try:
        oauth_url = await OAuthService.get_oauth_url("microsoft", state)
        return {"url": oauth_url}
    except Exception as e:
        print(f"❌ Fehler beim Generieren der Microsoft OAuth URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/oauth/microsoft/callback")
async def microsoft_oauth_callback(
    callback_data: OAuthCallbackRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Verarbeitet Microsoft OAuth Callback"""
    if callback_data.error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth Fehler: {callback_data.error}"
        )
    
    try:
        # Exchange code for tokens
        token_data = await OAuthService.exchange_code("microsoft", callback_data.code)
        user_info = await OAuthService.get_microsoft_user_info(token_data.get("access_token"))
        
        # Prüfe ob Benutzer bereits existiert
        existing_user = await get_user_by_email(db, user_info["email"])
        
        if existing_user:
            # Update OAuth-Daten
            existing_user.auth_provider = AuthProvider.MICROSOFT
            existing_user.oauth_id = user_info["id"]
            await db.commit()
            user = existing_user
        else:
            # Erstelle neuen Benutzer
            user_create = UserCreate(
                email=user_info["email"],
                first_name=user_info.get("given_name", ""),
                last_name=user_info.get("family_name", ""),
                password="oauth_user_no_password",  # OAuth-Benutzer haben kein Passwort
                user_type="bautraeger",
                auth_provider=AuthProvider.MICROSOFT,
                oauth_id=user_info["id"]
            )
            user = await create_user(db, user_create)
        
        # JWT Token erstellen
        access_token = create_access_token(data={"sub": str(user.id)})
        
        # Audit-Log
        ip_address = request.client.host if request else None
        await SecurityService.create_audit_log(
            db, user.id, AuditAction.USER_LOGIN,
            f"Microsoft OAuth Login: {user.email}",
            resource_type="user", resource_id=user.id,
            ip_address=SecurityService.anonymize_ip_address(ip_address) if ip_address else None
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "user_type": user.user_type,
                "user_role": user.user_role,
                "subscription_plan": user.subscription_plan,
                "subscription_status": user.subscription_status,
                "onboarding_completed": user.onboarding_completed,
                "role_selected": user.role_selected
            }
        }
        
    except Exception as e:
        print(f"❌ Fehler beim Microsoft OAuth Callback: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth Fehler: {str(e)}"
        )
