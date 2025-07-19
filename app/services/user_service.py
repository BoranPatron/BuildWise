import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from ..models.user import User, UserType, SubscriptionPlan, UserStatus
from ..schemas.user import UserCreate, UserUpdate, ConsentUpdate, SubscriptionUpdate
from ..core.security import get_password_hash, verify_password
from ..services.security_service import SecurityService
from ..models.audit_log import AuditAction
from .email_service import email_service


class UserService:
    """Erweiterter User-Service mit Rollen-Management und E-Mail-Verifizierung"""
    
    # Standard-Rollen und Berechtigungen
    ROLES = {
        "admin": {
            "permissions": ["*"],  # Alle Berechtigungen
            "description": "System-Administrator"
        },
        "service_provider": {
            "permissions": [
                "view_trades",
                "create_quotes", 
                "view_projects",
                "view_milestones",
                "view_documents",
                "send_messages",
                "view_buildwise_fees"
            ],
            "description": "Dienstleister"
        },
        "builder_basic": {
            "permissions": [
                "view_trades",
                "view_documents", 
                "visualize"
            ],
            "description": "Bauträger (Basis)"
        },
        "builder_pro": {
            "permissions": [
                "view_trades",
                "create_projects",
                "manage_milestones",
                "view_documents",
                "visualize",
                "manage_quotes",
                "view_analytics",
                "manage_tasks",
                "view_finance"
            ],
            "description": "Bauträger (Pro)"
        }
    }
    
    @staticmethod
    def generate_verification_token() -> str:
        """Generiert einen sicheren Verifizierungs-Token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def get_default_roles(user_type: UserType, subscription_plan: SubscriptionPlan) -> List[str]:
        """Ermittelt Standard-Rollen basierend auf User-Type und Subscription"""
        if user_type == UserType.SERVICE_PROVIDER:
            return ["service_provider"]
        elif user_type in [UserType.PRIVATE, UserType.PROFESSIONAL]:
            if subscription_plan == SubscriptionPlan.BASIS:
                return ["builder_basic"]
            else:
                return ["builder_pro"]
        return []
    
    @staticmethod
    def get_default_permissions(roles: List[str]) -> Dict[str, Any]:
        """Ermittelt Standard-Berechtigungen basierend auf Rollen"""
        permissions = {}
        for role in roles:
            if role in UserService.ROLES:
                role_permissions = UserService.ROLES[role]["permissions"]
                for permission in role_permissions:
                    if permission == "*":
                        permissions["*"] = True
                    else:
                        permissions[permission] = True
        return permissions
    
    @staticmethod
    async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
        """Erstellt einen neuen Benutzer mit vollständiger Validierung"""
        # Prüfe ob Benutzer bereits existiert
        existing_user = await UserService.get_user_by_email(db, user_in.email)
        if existing_user:
            raise ValueError("Ein Benutzer mit dieser E-Mail-Adresse existiert bereits")
        
        # Validiere User-Type und Subscription-Kombination
        if user_in.user_type == UserType.SERVICE_PROVIDER and user_in.subscription_plan == SubscriptionPlan.PRO:
            raise ValueError("Dienstleister können nur das Basis-Modell wählen")
        
        # Erstelle Verifizierungs-Token
        verification_token = UserService.generate_verification_token()
        
        # Ermittle Standard-Rollen und Berechtigungen
        default_roles = UserService.get_default_roles(user_in.user_type, user_in.subscription_plan)
        default_permissions = UserService.get_default_permissions(default_roles)
        
        # Erstelle User-Objekt
        user_data = user_in.dict()
        user_data["hashed_password"] = get_password_hash(user_in.password)
        user_data["email_verification_token"] = verification_token
        user_data["email_verification_sent_at"] = datetime.utcnow()
        user_data["roles"] = default_roles
        user_data["permissions"] = default_permissions
        user_data["status"] = UserStatus.PENDING_VERIFICATION
        
        # Entferne Passwort aus user_data
        user_data.pop("password", None)
        
        user = User(**user_data)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # Sende E-Mail-Verifizierung
        try:
            user_name = f"{user.first_name} {user.last_name}"
            email_sent = email_service.send_verification_email(
                user.email, verification_token, user_name
            )
            if email_sent:
                print(f"✅ Verifizierungs-E-Mail gesendet an: {user.email}")
            else:
                print(f"❌ Fehler beim Senden der Verifizierungs-E-Mail an: {user.email}")
        except Exception as e:
            print(f"❌ E-Mail-Service-Fehler: {e}")
        
        return user
    
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Ermittelt Benutzer anhand E-Mail-Adresse"""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """Ermittelt Benutzer anhand ID"""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def authenticate_user(db: AsyncSession, email: str, password: str, ip_address: str = None) -> Optional[User]:
        """Authentifiziert einen Benutzer"""
        user = await UserService.get_user_by_email(db, email)
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            # Erhöhe fehlgeschlagene Login-Versuche
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.account_locked_until = datetime.utcnow() + timedelta(minutes=30)
            await db.commit()
            return None
        
        # Prüfe Account-Sperre
        if user.account_locked_until and user.account_locked_until > datetime.utcnow():
            return None
        
        # Reset fehlgeschlagene Login-Versuche
        user.failed_login_attempts = 0
        user.last_login_at = datetime.utcnow()
        user.last_activity_at = datetime.utcnow()
        await db.commit()
        
        return user
    
    @staticmethod
    async def verify_email(db: AsyncSession, token: str) -> bool:
        """Verifiziert E-Mail-Adresse mit Token"""
        result = await db.execute(
            select(User).where(
                User.email_verification_token == token,
                User.email_verified == False
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return False
        
        # Prüfe Token-Gültigkeit (24 Stunden)
        if user.email_verification_sent_at:
            token_age = datetime.utcnow() - user.email_verification_sent_at
            if token_age > timedelta(hours=24):
                return False
        
        # Verifiziere E-Mail
        user.email_verified = True
        user.email_verified_at = datetime.utcnow()
        user.email_verification_token = None
        user.status = UserStatus.ACTIVE
        await db.commit()
        
        return True
    
    @staticmethod
    async def resend_verification_email(db: AsyncSession, email: str) -> bool:
        """Sendet Verifizierungs-E-Mail erneut"""
        user = await UserService.get_user_by_email(db, email)
        if not user or user.email_verified:
            return False
        
        # Generiere neuen Token
        new_token = UserService.generate_verification_token()
        user.email_verification_token = new_token
        user.email_verification_sent_at = datetime.utcnow()
        await db.commit()
        
        # Sende E-Mail
        try:
            user_name = f"{user.first_name} {user.last_name}"
            email_sent = email_service.send_verification_email(
                user.email, new_token, user_name
            )
            return email_sent
        except Exception as e:
            print(f"❌ E-Mail-Service-Fehler: {e}")
            return False
    
    @staticmethod
    async def request_password_reset(db: AsyncSession, email: str) -> bool:
        """Erstellt Passwort-Reset-Token und sendet E-Mail"""
        user = await UserService.get_user_by_email(db, email)
        if not user:
            return False
        
        # Generiere Reset-Token
        reset_token = UserService.generate_verification_token()
        user.password_reset_token = reset_token
        user.password_reset_sent_at = datetime.utcnow()
        user.password_reset_expires_at = datetime.utcnow() + timedelta(hours=1)
        await db.commit()
        
        # Sende Passwort-Reset-E-Mail
        try:
            user_name = f"{user.first_name} {user.last_name}"
            email_sent = email_service.send_password_reset_email(
                user.email, reset_token, user_name
            )
            return email_sent
        except Exception as e:
            print(f"❌ E-Mail-Service-Fehler: {e}")
            return False
    
    @staticmethod
    async def reset_password_with_token(db: AsyncSession, token: str, new_password: str) -> bool:
        """Setzt Passwort mit Token zurück"""
        result = await db.execute(
            select(User).where(
                User.password_reset_token == token,
                User.password_reset_expires_at > datetime.utcnow()
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return False
        
        # Validiere neues Passwort
        if len(new_password) < 8:
            raise ValueError("Passwort muss mindestens 8 Zeichen lang sein")
        
        # Setze neues Passwort
        user.hashed_password = get_password_hash(new_password)
        user.password_reset_token = None
        user.password_reset_sent_at = None
        user.password_reset_expires_at = None
        user.password_changed_at = datetime.utcnow()
        user.updated_at = datetime.utcnow()
        await db.commit()
        
        return True
    
    @staticmethod
    async def update_user(db: AsyncSession, user_id: int, user_update: UserUpdate) -> Optional[User]:
        """Aktualisiert Benutzer-Daten"""
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            return None
        
        update_data = user_update.dict(exclude_unset=True)
        
        # Aktualisiere Subscription-spezifische Felder
        if "subscription_plan" in update_data:
            user.subscription_plan = update_data["subscription_plan"]
            # Aktualisiere Rollen basierend auf neuer Subscription
            new_roles = UserService.get_default_roles(user.user_type, user.subscription_plan)
            user.roles = new_roles
            user.permissions = UserService.get_default_permissions(new_roles)
        
        # Aktualisiere andere Felder
        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(user)
        
        return user
    
    @staticmethod
    async def update_consents(db: AsyncSession, user_id: int, consents: ConsentUpdate) -> Optional[User]:
        """Aktualisiert DSGVO-Einwilligungen"""
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            return None
        
        update_data = consents.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(user)
        
        return user
    
    @staticmethod
    async def change_password(db: AsyncSession, user_id: int, current_password: str, new_password: str) -> bool:
        """Ändert das Passwort eines Benutzers"""
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            return False
        
        if not verify_password(current_password, user.hashed_password):
            return False
        
        user.hashed_password = get_password_hash(new_password)
        user.password_changed_at = datetime.utcnow()
        user.updated_at = datetime.utcnow()
        await db.commit()
        
        return True
    
    @staticmethod
    async def has_permission(user: User, permission: str) -> bool:
        """Prüft ob Benutzer eine bestimmte Berechtigung hat"""
        if not user.permissions:
            return False
        
        # Admin hat alle Berechtigungen
        if user.permissions.get("*"):
            return True
        
        return user.permissions.get(permission, False)
    
    @staticmethod
    async def get_users_by_type(db: AsyncSession, user_type: UserType) -> List[User]:
        """Ermittelt alle Benutzer eines bestimmten Typs"""
        result = await db.execute(
            select(User).where(User.user_type == user_type)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_active_users(db: AsyncSession) -> List[User]:
        """Ermittelt alle aktiven Benutzer"""
        result = await db.execute(
            select(User).where(
                User.is_active == True,
                User.status == UserStatus.ACTIVE
            )
        )
        return result.scalars().all()


# Legacy-Funktionen für Kompatibilität
async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    return await UserService.create_user(db, user_in)

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    return await UserService.get_user_by_email(db, email)

async def authenticate_user(db: AsyncSession, email: str, password: str, ip_address: str = None) -> Optional[User]:
    return await UserService.authenticate_user(db, email, password, ip_address)

async def change_password(db: AsyncSession, user_id: int, current_password: str, new_password: str) -> bool:
    return await UserService.change_password(db, user_id, current_password, new_password)
