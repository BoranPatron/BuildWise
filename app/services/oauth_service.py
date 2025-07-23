import aiohttp
import jwt
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json
import base64
from datetime import datetime, timedelta

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
        
        print(f"🔍 Google OAuth Debug:")
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
                        print(f"❌ Google token exchange failed: {error_data}")
                        
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
                        print(f"❌ Failed to parse error response: {e}")
                        print(f"  - Raw response: {response_text}")
                        raise e
    
    @staticmethod
    async def _exchange_microsoft_code(code: str) -> Optional[Dict[str, Any]]:
        """Tauscht Microsoft Authorization Code gegen Token"""
        
        if not settings.microsoft_client_id or not settings.microsoft_client_secret:
            raise ValueError("Microsoft OAuth ist nicht konfiguriert")
            
        token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        data = {
            "client_id": settings.microsoft_client_id,
            "client_secret": settings.microsoft_client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.microsoft_redirect_uri
        }
        
        print(f"🔍 Microsoft OAuth Debug:")
        print(f"  - Client ID: {settings.microsoft_client_id}")
        print(f"  - Redirect URI: {settings.microsoft_redirect_uri}")
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
                        print(f"❌ Microsoft token exchange failed: {error_data}")
                        
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
                        print(f"❌ Failed to parse error response: {e}")
                        print(f"  - Raw response: {response_text}")
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
        
        print(f"🔍 Microsoft User Info Debug:")
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
                    print(f"❌ Microsoft userinfo failed: {response.status}")
                    print(f"  - Error response: {response_text}")
                    return None
    
    @staticmethod
    async def find_or_create_user_by_social_login(
        db: AsyncSession, 
        auth_provider: AuthProvider, 
        user_info: Dict[str, Any],
        ip_address: Optional[str] = None
    ) -> User:
        """Findet oder erstellt Benutzer basierend auf Social-Login"""
        
        # Extrahiere E-Mail aus User-Info (unterschiedlich für verschiedene Provider)
        email = None
        
        if auth_provider == AuthProvider.GOOGLE:
            # Google gibt E-Mail direkt zurück
            email = user_info.get("email")
        elif auth_provider == AuthProvider.MICROSOFT:
            # Microsoft Graph API gibt E-Mail in verschiedenen Feldern zurück
            email = (
                user_info.get("email") or  # Direktes email-Feld
                user_info.get("mail") or   # Microsoft Graph mail-Feld
                user_info.get("userPrincipalName") or  # UPN (enthält oft E-Mail)
                user_info.get("upn")       # Alternative UPN-Schreibweise
            )
            
            # Falls UPN eine E-Mail-Adresse ist, verwende sie
            if email and "@" in email and not email.endswith(".onmicrosoft.com"):
                pass  # E-Mail ist bereits korrekt
            elif email and email.endswith(".onmicrosoft.com"):
                # UPN ist eine Microsoft-Domain, versuche andere Felder
                email = user_info.get("email") or user_info.get("mail")
        
        print(f"🔍 E-Mail-Extraktion für {auth_provider.value}:")
        print(f"  - Verfügbare Felder: {list(user_info.keys())}")
        print(f"  - Gefundene E-Mail: {email}")
        
        if not email:
            print(f"❌ Keine E-Mail-Adresse gefunden in User-Info:")
            print(f"  - User-Info: {user_info}")
            raise ValueError("E-Mail-Adresse nicht in OAuth-Response gefunden")
        
        # Suche nach bestehendem Benutzer
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            # Aktualisiere Social-Login-Informationen
            if auth_provider == AuthProvider.GOOGLE:
                existing_user.google_sub = user_info.get("id")
            elif auth_provider == AuthProvider.MICROSOFT:
                existing_user.microsoft_sub = user_info.get("id")
            
            existing_user.auth_provider = auth_provider
            existing_user.last_login_at = datetime.utcnow()
            existing_user.last_activity_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(existing_user)
            
            # Audit-Log für Social-Login
            await SecurityService.create_audit_log(
                db, existing_user.id, AuditAction.USER_LOGIN,
                f"Social-Login über {auth_provider.value}: {email}",
                resource_type="user", resource_id=existing_user.id,
                ip_address=SecurityService.anonymize_ip_address(ip_address) if ip_address else None,
                processing_purpose="Authentifizierung über Social-Login",
                legal_basis="Einwilligung"
            )
            
            return existing_user
        
        # Erstelle neuen Benutzer
        new_user = User(
            email=email,
            first_name=user_info.get("given_name", ""),
            last_name=user_info.get("family_name", ""),
            auth_provider=auth_provider,
            user_type=UserType.PRIVATE,  # Standard-Typ
            status=UserStatus.ACTIVE,
            is_active=True,
            is_verified=True,
            email_verified=True,
            # Onboarding-Felder für neue OAuth-User
            user_role=None,  # Rolle muss noch ausgewählt werden
            role_selected=False,  # Rolle noch nicht ausgewählt
            role_selection_modal_shown=False,  # Modal noch nicht angezeigt
            first_login_completed=False,  # Erster Login noch nicht abgeschlossen
            onboarding_completed=False,  # Onboarding noch nicht abgeschlossen
            onboarding_step=0,  # Onboarding nicht gestartet
            # Subscription-Felder (Standard: BASIS)
            subscription_plan=SubscriptionPlan.BASIS,
            subscription_status=SubscriptionStatus.INACTIVE,
            max_gewerke=3,
            # DSGVO-Einwilligungen (Standard: True für Social-Login)
            data_processing_consent=True,
            marketing_consent=False,  # Opt-out für Marketing
            privacy_policy_accepted=True,
            terms_accepted=True,
            # Social-Login-Identifiers
            google_sub=user_info.get("id") if auth_provider == AuthProvider.GOOGLE else None,
            microsoft_sub=user_info.get("id") if auth_provider == AuthProvider.MICROSOFT else None,
            # Social-Profile-Daten (verschlüsselt)
            social_profile_data=json.dumps(user_info)
        )
        
        try:
            db.add(new_user)
            await db.flush()  # Flush vor commit um ID zu generieren
            await db.commit()
            await db.refresh(new_user)
            print(f"✅ Neuer OAuth-User erfolgreich erstellt: {new_user.id}")
        except Exception as e:
            await db.rollback()
            print(f"❌ Fehler beim Erstellen des OAuth-Users: {e}")
            raise ValueError(f"Social-Login fehlgeschlagen: {str(e)}")
        
        # Audit-Log für Benutzerregistrierung
        await SecurityService.create_audit_log(
            db, new_user.id, AuditAction.USER_REGISTER,
            f"Neuer Benutzer über Social-Login registriert: {email}",
            resource_type="user", resource_id=new_user.id,
            ip_address=SecurityService.anonymize_ip_address(ip_address) if ip_address else None,
            processing_purpose="Benutzerregistrierung über Social-Login",
            legal_basis="Einwilligung"
        )
        
        return new_user
    
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