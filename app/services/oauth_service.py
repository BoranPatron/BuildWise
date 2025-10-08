import aiohttp
import jwt
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json
import base64
from datetime import datetime, timedelta
import asyncio

from ..core.config import settings
from ..models.user import User, AuthProvider, UserType, UserStatus, SubscriptionPlan, SubscriptionStatus
from ..services.security_service import SecurityService
from ..models.audit_log import AuditAction

class OAuthService:
    """OAuth-Service für Social-Login Integration"""
    
    @staticmethod
    async def get_oauth_url(provider: str, state: Optional[str] = None) -> str:
        """Generiert OAuth-URL für den angegebenen Provider"""
        
        if provider == "google":
            if not settings.google_client_id:
                raise ValueError("Google OAuth ist nicht konfiguriert")
            
            params = {
                "client_id": settings.google_client_id,
                "redirect_uri": settings.google_redirect_uri,
                "response_type": "code",
                "scope": "openid email profile",
                "access_type": "offline",
                "prompt": "consent"
            }
            
            if state:
                params["state"] = state
                
            url = "https://accounts.google.com/o/oauth2/v2/auth"
            
        elif provider == "microsoft":
            if not settings.microsoft_client_id:
                raise ValueError("Microsoft OAuth ist nicht konfiguriert")
            
            params = {
                "client_id": settings.microsoft_client_id,
                "redirect_uri": settings.microsoft_redirect_uri,
                "response_type": "code",
                "scope": "openid email profile User.Read",  # User.Read für Graph API
                "response_mode": "query",
                "prompt": "select_account",  # Erzwingt Account-Auswahl
                "login_hint": "",  # Leerer Login-Hint verhindert automatische Anmeldung
                "domain_hint": ""  # Leerer Domain-Hint verhindert automatische Anmeldung
            }
            
            if state:
                params["state"] = state
                
            url = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
            
        else:
            raise ValueError(f"Unbekannter OAuth-Provider: {provider}")
        
        # URL mit Parametern erstellen
        from urllib.parse import urlencode
        return f"{url}?{urlencode(params)}"
    
    @staticmethod
    async def exchange_code_for_token(provider: str, code: str) -> Optional[Dict[str, Any]]:
        """Tauscht Authorization Code gegen Access Token"""
        
        if provider == "google":
            return await OAuthService._exchange_google_code(code)
        elif provider == "microsoft":
            return await OAuthService._exchange_microsoft_code(code)
        else:
            raise ValueError(f"Unbekannter OAuth-Provider: {provider}")
    
    @staticmethod
    async def _exchange_google_code(code: str) -> Optional[Dict[str, Any]]:
        """Tauscht Google Authorization Code gegen Token"""
        
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.google_redirect_uri
        }
        
        print(f"[DEBUG] Google OAuth Debug:")
        print(f"  - Client ID: {settings.google_client_id}")
        print(f"  - Redirect URI: {settings.google_redirect_uri}")
        print(f"  - Code length: {len(code)}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(token_url, data=data) as response:
                response_text = await response.text()
                print(f"  - Response status: {response.status}")
                print(f"  - Response body: {response_text}")
                
                if response.status == 200:
                    token_data = await response.json()
                    print(f"  - Token exchange successful")
                    return token_data
                else:
                    try:
                        error_data = await response.json()
                        print(f"[ERROR] Google token exchange failed: {error_data}")
                        
                        # Spezifische Fehlerbehandlung
                        error_type = error_data.get('error')
                        if error_type == 'invalid_grant':
                            print(f"  - Code wurde bereits verwendet oder ist abgelaufen (normal)")
                            # Bei invalid_grant: Code wurde bereits verwendet, aber das ist normal
                            # wenn der User bereits erfolgreich eingeloggt ist
                            # Wir behandeln das als normalen Fall, nicht als Fehler
                            return None
                        elif error_type == 'invalid_client':
                            print(f"  - Client ID oder Secret falsch")
                            raise ValueError("Google OAuth Client-Konfiguration fehlerhaft")
                        elif error_type == 'redirect_uri_mismatch':
                            print(f"  - Redirect URI stimmt nicht überein")
                            raise ValueError("Google OAuth Redirect-URI stimmt nicht überein")
                        else:
                            print(f"  - Unbekannter Fehler: {error_type}")
                            raise ValueError(f"Google OAuth Fehler: {error_data.get('error_description', 'Unbekannter Fehler')}")
                        
                    except Exception as e:
                        print(f"[ERROR] Failed to parse error response: {e}")
                        print(f"  - Raw response: {response_text}")
                        raise e
    
    @staticmethod
    async def _exchange_microsoft_code(code: str) -> Optional[Dict[str, Any]]:
        """Tauscht Microsoft Authorization Code gegen Token"""
        
        if not settings.microsoft_client_id or not settings.microsoft_client_secret:
            print(f"[ERROR] Microsoft OAuth nicht konfiguriert:")
            print(f"  - Client ID: {settings.microsoft_client_id}")
            print(f"  - Client Secret: {'gesetzt' if settings.microsoft_client_secret else 'nicht gesetzt'}")
            raise ValueError("Microsoft OAuth ist nicht konfiguriert. Bitte setzen Sie microsoft_client_id und microsoft_client_secret in der Konfiguration.")
            
        token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        data = {
            "client_id": settings.microsoft_client_id,
            "client_secret": settings.microsoft_client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.microsoft_redirect_uri
        }
        
        print(f"[DEBUG] Microsoft OAuth Debug:")
        print(f"  - Client ID: {settings.microsoft_client_id}")
        print(f"  - Redirect URI: {settings.microsoft_redirect_uri}")
        print(f"  - Code length: {len(code)}")
        print(f"  - Token URL: {token_url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(token_url, data=data) as response:
                    response_text = await response.text()
                    print(f"  - Response status: {response.status}")
                    print(f"  - Response body: {response_text}")
                    
                    if response.status == 200:
                        token_data = await response.json()
                        print(f"  - Token exchange successful")
                        return token_data
                    else:
                        try:
                            error_data = await response.json()
                            print(f"[ERROR] Microsoft token exchange failed: {error_data}")
                            
                            # Spezifische Fehlerbehandlung
                            error_type = error_data.get('error')
                            if error_type == 'invalid_grant':
                                print(f"  - Code wurde bereits verwendet oder ist abgelaufen (normal)")
                                # Bei invalid_grant: Code wurde bereits verwendet, aber das ist normal
                                # wenn der User bereits erfolgreich eingeloggt ist
                                # Wir behandeln das als normalen Fall, nicht als Fehler
                                return None
                            elif error_type == 'invalid_client':
                                print(f"  - Client ID oder Secret falsch")
                                raise ValueError("Microsoft OAuth Client-Konfiguration fehlerhaft")
                            elif error_type == 'redirect_uri_mismatch':
                                print(f"  - Redirect URI stimmt nicht überein")
                                raise ValueError("Microsoft OAuth Redirect-URI stimmt nicht überein")
                            else:
                                print(f"  - Unbekannter Fehler: {error_type}")
                                raise ValueError(f"Microsoft OAuth Fehler: {error_data.get('error_description', 'Unbekannter Fehler')}")
                            
                        except Exception as e:
                            print(f"[ERROR] Failed to parse error response: {e}")
                            print(f"  - Raw response: {response_text}")
                            raise e
        except aiohttp.ClientError as e:
            print(f"[ERROR] Network error during Microsoft token exchange: {e}")
            raise ValueError(f"Netzwerkfehler beim Microsoft OAuth: {e}")
        except Exception as e:
            print(f"[ERROR] Unexpected error during Microsoft token exchange: {e}")
            raise e
    
    @staticmethod
    async def get_google_user_info(access_token: str) -> Optional[Dict[str, Any]]:
        """Ruft Google Benutzerinformationen ab"""
        
        userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(userinfo_url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"Google userinfo failed: {response.status}")
                    return None
    
    @staticmethod
    async def get_microsoft_user_info(access_token: str) -> Optional[Dict[str, Any]]:
        """Ruft Microsoft Benutzerinformationen ab"""
        
        userinfo_url = "https://graph.microsoft.com/v1.0/me"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        print(f"[DEBUG] Microsoft User Info Debug:")
        print(f"  - URL: {userinfo_url}")
        print(f"  - Access Token: {access_token[:20]}...")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(userinfo_url, headers=headers) as response:
                response_text = await response.text()
                print(f"  - Response status: {response.status}")
                print(f"  - Response body: {response_text[:200]}...")
                
                if response.status == 200:
                    user_data = await response.json()
                    print(f"  - User info erfolgreich abgerufen")
                    return user_data
                else:
                    print(f"[ERROR] Microsoft userinfo failed: {response.status}")
                    print(f"  - Error response: {response_text}")
                    return None
    
    @staticmethod
    def _extract_email_from_user_info(auth_provider: AuthProvider, user_info: Dict[str, Any]) -> Optional[str]:
        """Extrahiert die E-Mail-Adresse aus den Social-Login-Daten."""
        email = None
        
        if auth_provider == AuthProvider.GOOGLE:
            # Google: E-Mail ist direkt im "email" Feld
            email = user_info.get("email")
        elif auth_provider == AuthProvider.MICROSOFT:
            # Microsoft: E-Mail kann in verschiedenen Feldern sein
            email = user_info.get("mail") or user_info.get("email") or user_info.get("userPrincipalName")
        else:
            # Fallback: Versuche verschiedene Standard-Felder
            email = user_info.get("email") or user_info.get("mail")
        
        print(f"[DEBUG] E-Mail-Extraktion für {auth_provider.value}:")
        print(f"  - Verfügbare Felder: {list(user_info.keys())}")
        print(f"  - Gefundene E-Mail: {email}")
        
        return email
    
    @staticmethod
    async def find_or_create_user_by_social_login(
        db: AsyncSession,
        auth_provider: AuthProvider,
        user_info: Dict[str, Any],
        ip_address: Optional[str] = None
    ) -> User:
        """Findet oder erstellt Benutzer basierend auf Social-Login-Daten"""
        
        # E-Mail aus user_info extrahieren
        email = OAuthService._extract_email_from_user_info(auth_provider, user_info)
        if not email:
            raise ValueError("E-Mail-Adresse konnte nicht aus Social-Login-Daten extrahiert werden")
        
        print(f"[DEBUG] Suche nach existierendem User mit E-Mail: {email}")
        
        # Retry-Mechanismus für Database Lock Issues
        max_retries = 3
        retry_delay = 0.5  # 500ms
        
        for attempt in range(max_retries):
            try:
                # Suche nach existierendem Benutzer
                result = await db.execute(
                    select(User).where(User.email == email)
                )
                existing_user = result.scalar_one_or_none()
                
                if existing_user:
                    print(f"[SUCCESS] Existierender User gefunden: {existing_user.id}")
                    
                    # Aktualisiere Last-Login und Social-Login-Informationen
                    try:
                        existing_user.last_login_at = datetime.utcnow()
                        existing_user.last_activity_at = datetime.utcnow()
                        
                        # Social-Login-Identifiers aktualisieren falls nötig
                        if auth_provider == AuthProvider.GOOGLE and not existing_user.google_sub:
                            existing_user.google_sub = user_info.get("id")
                        elif auth_provider == AuthProvider.MICROSOFT and not existing_user.microsoft_sub:
                            existing_user.microsoft_sub = user_info.get("id")
                        
                        # Auth-Provider aktualisieren
                        existing_user.auth_provider = auth_provider
                        
                        await db.commit()
                        await db.refresh(existing_user)
                        print(f"[SUCCESS] User {existing_user.id} erfolgreich aktualisiert")
                        
                        # Audit-Log für Social-Login (separater Try-Block)
                        try:
                            await SecurityService.create_audit_log(
                                db, existing_user.id, AuditAction.USER_LOGIN,
                                f"Social-Login über {auth_provider.value}: {email}",
                                resource_type="user", resource_id=existing_user.id,
                                ip_address=SecurityService.anonymize_ip_address(ip_address) if ip_address else None,
                                processing_purpose="Authentifizierung über Social-Login",
                                legal_basis="Einwilligung"
                            )
                        except Exception as e:
                            print(f"[WARNING] Warnung: Audit-Log konnte nicht erstellt werden: {e}")
                        
                        return existing_user
                        
                    except Exception as e:
                        await db.rollback()
                        if "database is locked" in str(e) and attempt < max_retries - 1:
                            print(f"[WARNING] Database Lock bei User-Update (Versuch {attempt + 1}/{max_retries}): {e}")
                            await asyncio.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                            continue
                        else:
                            print(f"[ERROR] Fehler beim Aktualisieren des existierenden Users: {e}")
                            # Fallback: Gib den User ohne Update zurück
                            return existing_user
                
                # Erstelle neuen Benutzer
                print(f"[UPDATE] Erstelle neuen User für E-Mail: {email}")
                new_user = User(
                    email=email,
                    first_name=user_info.get("given_name", user_info.get("givenName", "")),
                    last_name=user_info.get("family_name", user_info.get("surname", "")),
                    auth_provider=auth_provider,
                    user_type=UserType.PRIVATE,
                    status=UserStatus.ACTIVE,
                    is_active=True,
                    is_verified=True,
                    email_verified=True,
                    # Onboarding-Felder für neue OAuth-User
                    user_role=None,
                    role_selected=False,
                    role_selection_modal_shown=False,
                    first_login_completed=False,
                    onboarding_completed=False,
                    onboarding_step=0,
                    # Subscription-Felder (Standard: BASIS)
                    subscription_plan=SubscriptionPlan.BASIS,
                    subscription_status=SubscriptionStatus.INACTIVE,
                    max_gewerke=3,
                    # DSGVO-Einwilligungen (Standard: True für Social-Login)
                    data_processing_consent=True,
                    marketing_consent=False,
                    privacy_policy_accepted=True,
                    terms_accepted=True,
                    # Social-Login-Identifiers
                    google_sub=user_info.get("id") if auth_provider == AuthProvider.GOOGLE else None,
                    microsoft_sub=user_info.get("id") if auth_provider == AuthProvider.MICROSOFT else None,
                    # Social-Profile-Daten
                    social_profile_data=json.dumps(user_info),
                    # Timestamps
                    last_login_at=datetime.utcnow(),
                    last_activity_at=datetime.utcnow()
                )
                
                try:
                    db.add(new_user)
                    await db.flush()  # Flush vor commit um ID zu generieren
                    await db.commit()
                    await db.refresh(new_user)
                    print(f"[SUCCESS] Neuer OAuth-User erfolgreich erstellt: {new_user.id}")
                    
                    # Audit-Log für Benutzerregistrierung (separater Try-Block)
                    try:
                        await SecurityService.create_audit_log(
                            db, new_user.id, AuditAction.USER_REGISTER,
                            f"Neuer Benutzer über Social-Login registriert: {email}",
                            resource_type="user", resource_id=new_user.id,
                            ip_address=SecurityService.anonymize_ip_address(ip_address) if ip_address else None,
                            processing_purpose="Benutzerregistrierung über Social-Login",
                            legal_basis="Einwilligung"
                        )
                    except Exception as e:
                        print(f"[WARNING] Warnung: Audit-Log konnte nicht erstellt werden: {e}")
                    
                    return new_user
                    
                except Exception as e:
                    await db.rollback()
                    if "database is locked" in str(e) and attempt < max_retries - 1:
                        print(f"[WARNING] Database Lock bei User-Erstellung (Versuch {attempt + 1}/{max_retries}): {e}")
                        await asyncio.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                        continue
                    else:
                        print(f"[ERROR] Fehler beim Erstellen des neuen OAuth-Users: {e}")
                        raise ValueError(f"Social-Login fehlgeschlagen: Benutzer konnte nicht erstellt werden")
                        
            except Exception as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    print(f"[WARNING] Database Lock bei User-Suche (Versuch {attempt + 1}/{max_retries}): {e}")
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue
                else:
                    print(f"[ERROR] Unerwarteter Fehler bei Social-Login: {e}")
                    raise ValueError(f"Social-Login fehlgeschlagen: {str(e)}")
        
        # Wenn alle Retries fehlgeschlagen sind
        raise ValueError("Social-Login fehlgeschlagen: Datenbank ist gesperrt. Bitte versuchen Sie es erneut.")
    
    @staticmethod
    async def link_social_account(
        db: AsyncSession,
        user: User,
        auth_provider: AuthProvider,
        user_info: Dict[str, Any],
        ip_address: Optional[str] = None
    ) -> bool:
        """Verknüpft Social-Account mit bestehendem Benutzer"""
        
        try:
            # Aktualisiere Social-Login-Informationen
            if auth_provider == AuthProvider.GOOGLE:
                user.google_sub = user_info.get("id")
            elif auth_provider == AuthProvider.MICROSOFT:
                user.microsoft_sub = user_info.get("id")
            
            user.auth_provider = auth_provider
            user.updated_at = datetime.utcnow()
            
            await db.commit()
            
            # Audit-Log für Account-Verknüpfung
            await SecurityService.create_audit_log(
                db, user.id, AuditAction.USER_UPDATE,
                f"Social-Account verknüpft: {auth_provider.value}",
                resource_type="user", resource_id=user.id,
                ip_address=SecurityService.anonymize_ip_address(ip_address) if ip_address else None,
                processing_purpose="Social-Account-Verknüpfung",
                legal_basis="Einwilligung"
            )
            
            return True
            
        except Exception as e:
            print(f"Fehler beim Verknüpfen des Social-Accounts: {e}")
            return False 