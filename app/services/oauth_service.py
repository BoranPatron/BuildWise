import aiohttp
import jwt
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json
import base64
from datetime import datetime, timedelta

from ..core.config import settings
from ..models.user import User, AuthProvider, UserType, UserStatus
from ..services.security_service import SecurityService
from ..models.audit_log import AuditAction

class OAuthService:
    """OAuth-Service für Social-Login Integration"""
    
    @staticmethod
    async def get_oauth_url(provider: str, state: Optional[str] = None) -> str:
        """Generiert OAuth-URL für den angegebenen Provider"""
        
        if provider == "google":
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
                
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            return f"https://accounts.google.com/o/oauth2/auth?{query_string}"
            
        elif provider == "microsoft":
            if not settings.microsoft_client_id:
                raise ValueError("Microsoft OAuth ist nicht konfiguriert")
                
            params = {
                "client_id": settings.microsoft_client_id,
                "redirect_uri": settings.microsoft_redirect_uri,
                "response_type": "code",
                "scope": "openid email profile",
                "response_mode": "query"
            }
            if state:
                params["state"] = state
                
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            return f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?{query_string}"
            
        else:
            raise ValueError(f"Unbekannter OAuth-Provider: {provider}")
    
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
        
        async with aiohttp.ClientSession() as session:
            async with session.post(token_url, data=data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_data = await response.json()
                    print(f"Microsoft token exchange failed: {error_data}")
                    return None
    
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
        
        async with aiohttp.ClientSession() as session:
            async with session.get(userinfo_url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"Microsoft userinfo failed: {response.status}")
                    return None
    
    @staticmethod
    async def find_or_create_user_by_social_login(
        db: AsyncSession, 
        auth_provider: AuthProvider, 
        user_info: Dict[str, Any],
        ip_address: Optional[str] = None
    ) -> User:
        """Findet oder erstellt Benutzer basierend auf Social-Login"""
        
        # Extrahiere E-Mail aus User-Info
        email = user_info.get("email")
        if not email:
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
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
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