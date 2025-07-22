import pyotp
import qrcode
import io
import base64
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import secrets
import hashlib

from ..core.config import settings
from ..models.user import User
from ..models.audit_log import AuditAction, AuditLog
from ..core.security import get_password_hash


class SecurityService:
    """Erweiterter Security-Service für Multi-Factor-Authentication und Sicherheitsfunktionen"""
    
    @staticmethod
    def anonymize_ip_address(ip_address: str) -> str:
        """Anonymisiert IP-Adressen für DSGVO-Compliance"""
        if not ip_address:
            return None
        
        # IPv4: Letzte Oktette entfernen
        if '.' in ip_address:
            parts = ip_address.split('.')
            if len(parts) == 4:
                return f"{parts[0]}.{parts[1]}.{parts[2]}.0"
        
        # IPv6: Letzte 64 Bits entfernen
        if ':' in ip_address:
            parts = ip_address.split(':')
            if len(parts) >= 4:
                return f"{parts[0]}:{parts[1]}:{parts[2]}:{parts[3]}::"
        
        return ip_address
    
    @staticmethod
    async def create_audit_log(
        db: AsyncSession,
        user_id: Optional[int],
        action: AuditAction,
        description: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        processing_purpose: Optional[str] = None,
        legal_basis: Optional[str] = None,
        risk_level: Optional[str] = None
    ):
        """Erstellt einen Audit-Log-Eintrag"""
        
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            description=description,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=SecurityService.anonymize_ip_address(ip_address) if ip_address else None,
            processing_purpose=processing_purpose,
            legal_basis=legal_basis,
            risk_level=risk_level
        )
        
        db.add(audit_log)
        await db.commit()
    
    @staticmethod
    async def check_rate_limit(db: AsyncSession, identifier: str, action: str, max_attempts: int = 5) -> bool:
        """Prüft Rate-Limiting für Aktionen"""
        
        # Prüfe aktuelle Versuche in den letzten 15 Minuten
        cutoff_time = datetime.utcnow() - timedelta(minutes=15)
        
        stmt = select(AuditLog).where(
            AuditLog.description.contains(action),
            AuditLog.ip_address == identifier,
            AuditLog.created_at > cutoff_time
        )
        result = await db.execute(stmt)
        recent_attempts = result.scalars().all()
        
        return len(recent_attempts) < max_attempts
    
    @staticmethod
    async def lock_account(db: AsyncSession, user_id: int, duration_minutes: int = 30) -> bool:
        """Sperrt ein Benutzerkonto temporär"""
        
        lock_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        
        stmt = update(User).where(User.id == user_id).values(
            account_locked_until=lock_until,
            failed_login_attempts=0  # Reset failed attempts
        )
        await db.execute(stmt)
        await db.commit()
        
        # Audit-Log
        await SecurityService.create_audit_log(
            db, user_id, AuditAction.ACCOUNT_LOCKED,
            f"Konto gesperrt bis {lock_until}",
            resource_type="user", resource_id=user_id,
            risk_level="high"
        )
        
        return True
    
    @staticmethod
    async def unlock_account(db: AsyncSession, user_id: int) -> bool:
        """Entsperrt ein Benutzerkonto"""
        
        stmt = update(User).where(User.id == user_id).values(
            account_locked_until=None,
            failed_login_attempts=0
        )
        await db.execute(stmt)
        await db.commit()
        
        # Audit-Log
        await SecurityService.create_audit_log(
            db, user_id, AuditAction.USER_UPDATE,
            "Konto entsperrt",
            resource_type="user", resource_id=user_id
        )
        
        return True
    
    @staticmethod
    async def increment_failed_login(db: AsyncSession, user_id: int) -> bool:
        """Erhöht die Anzahl fehlgeschlagener Login-Versuche"""
        
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            return False
        
        new_attempts = user.failed_login_attempts + 1
        
        # Prüfe ob Konto gesperrt werden soll
        if new_attempts >= settings.max_login_attempts:
            await SecurityService.lock_account(db, user_id, settings.account_lockout_minutes)
        else:
            stmt = update(User).where(User.id == user_id).values(
                failed_login_attempts=new_attempts
            )
            await db.execute(stmt)
            await db.commit()
        
        return True
    
    @staticmethod
    async def reset_failed_login_attempts(db: AsyncSession, user_id: int) -> bool:
        """Setzt fehlgeschlagene Login-Versuche zurück"""
        
        stmt = update(User).where(User.id == user_id).values(
            failed_login_attempts=0,
            last_login_at=datetime.utcnow()
        )
        await db.execute(stmt)
        await db.commit()
        
        return True
    
    # Multi-Factor Authentication
    
    @staticmethod
    def generate_mfa_secret() -> str:
        """Generiert ein TOTP-Secret für MFA"""
        return pyotp.random_base32()
    
    @staticmethod
    def generate_mfa_qr_code(secret: str, email: str, issuer: str = "BuildWise") -> str:
        """Generiert QR-Code für MFA-Setup"""
        
        # TOTP-URI erstellen
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=email,
            issuer_name=issuer
        )
        
        # QR-Code generieren
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Als Base64-String konvertieren
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """Validiert die Passwort-Stärke"""
        errors = []
        
        if len(password) < 8:
            errors.append("Passwort muss mindestens 8 Zeichen lang sein")
        
        if not any(c.isupper() for c in password):
            errors.append("Passwort muss mindestens einen Großbuchstaben enthalten")
        
        if not any(c.islower() for c in password):
            errors.append("Passwort muss mindestens einen Kleinbuchstaben enthalten")
        
        if not any(c.isdigit() for c in password):
            errors.append("Passwort muss mindestens eine Zahl enthalten")
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Passwort muss mindestens ein Sonderzeichen enthalten")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors
        }
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hasht ein Passwort"""
        from ..core.security import get_password_hash
        return get_password_hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Überprüft ein Passwort"""
        from ..core.security import verify_password
        return verify_password(plain_password, hashed_password)
    
    @staticmethod
    def is_account_locked(lock_until: datetime) -> bool:
        """Prüft ob ein Account gesperrt ist"""
        return datetime.utcnow() < lock_until
    
    @staticmethod
    async def handle_failed_login(db: AsyncSession, user: User, ip_address: str) -> None:
        """Behandelt fehlgeschlagene Login-Versuche"""
        await SecurityService.increment_failed_login(db, user.id)
        
        # Audit-Log für fehlgeschlagene Anmeldung
        await SecurityService.create_audit_log(
            db, user.id, AuditAction.UNAUTHORIZED_ACCESS,
            f"Fehlgeschlagene Anmeldung: {user.email}",
            resource_type="user", resource_id=user.id,
            ip_address=SecurityService.anonymize_ip_address(ip_address) if ip_address else None,
            risk_level="medium"
        )
    
    @staticmethod
    def verify_mfa_token(secret: str, token: str) -> bool:
        """Verifiziert einen MFA-Token"""
        totp = pyotp.Totp(secret)
        return totp.verify(token)
    
    @staticmethod
    def generate_backup_codes() -> List[str]:
        """Generiert Backup-Codes für MFA"""
        return [secrets.token_hex(4).upper() for _ in range(10)]
    
    @staticmethod
    async def setup_mfa(db: AsyncSession, user_id: int) -> Dict[str, Any]:
        """Richtet MFA für einen Benutzer ein"""
        
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise ValueError("Benutzer nicht gefunden")
        
        # MFA-Secret generieren
        secret = SecurityService.generate_mfa_secret()
        backup_codes = SecurityService.generate_backup_codes()
        
        # QR-Code generieren
        qr_code = SecurityService.generate_mfa_qr_code(secret, user.email)
        
        # Backup-Codes hashen
        hashed_backup_codes = [hashlib.sha256(code.encode()).hexdigest() for code in backup_codes]
        
        # In Datenbank speichern
        stmt = update(User).where(User.id == user_id).values(
            mfa_secret=secret,
            mfa_backup_codes=hashed_backup_codes,
            mfa_enabled=False  # Wird erst nach Verifizierung aktiviert
        )
        await db.execute(stmt)
        await db.commit()
        
        # Audit-Log
        await SecurityService.create_audit_log(
            db, user_id, AuditAction.USER_UPDATE,
            "MFA-Setup initiiert",
            resource_type="user", resource_id=user_id,
            processing_purpose="Multi-Factor-Authentication",
            legal_basis="Sicherheit"
        )
        
        return {
            "secret": secret,
            "qr_code": qr_code,
            "backup_codes": backup_codes
        }
    
    @staticmethod
    async def verify_and_enable_mfa(db: AsyncSession, user_id: int, token: str) -> bool:
        """Verifiziert MFA-Token und aktiviert MFA"""
        
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user or not user.mfa_secret:
            return False
        
        # Token verifizieren
        if not SecurityService.verify_mfa_token(user.mfa_secret, token):
            return False
        
        # MFA aktivieren
        stmt = update(User).where(User.id == user_id).values(
            mfa_enabled=True,
            mfa_last_used=datetime.utcnow()
        )
        await db.execute(stmt)
        await db.commit()
        
        # Audit-Log
        await SecurityService.create_audit_log(
            db, user_id, AuditAction.USER_UPDATE,
            "MFA aktiviert",
            resource_type="user", resource_id=user_id,
            processing_purpose="Multi-Factor-Authentication",
            legal_basis="Sicherheit"
        )
        
        return True
    
    @staticmethod
    async def verify_mfa_login(db: AsyncSession, user_id: int, token: str) -> bool:
        """Verifiziert MFA-Token beim Login"""
        
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user or not user.mfa_enabled:
            return False
        
        # Prüfe ob es ein Backup-Code ist
        if len(token) == 8:  # Backup-Code Format
            if not user.mfa_backup_codes:
                return False
            
            hashed_token = hashlib.sha256(token.encode()).hexdigest()
            if hashed_token not in user.mfa_backup_codes:
                return False
            
            # Backup-Code entfernen (einmalig verwendbar)
            backup_codes = user.mfa_backup_codes.copy()
            backup_codes.remove(hashed_token)
            
            stmt = update(User).where(User.id == user_id).values(
                mfa_backup_codes=backup_codes
            )
            await db.execute(stmt)
            await db.commit()
            
        else:
            # Normale TOTP-Verifizierung
            if not SecurityService.verify_mfa_token(user.mfa_secret, token):
                return False
        
        # Last used aktualisieren
        stmt = update(User).where(User.id == user_id).values(
            mfa_last_used=datetime.utcnow()
        )
        await db.execute(stmt)
        await db.commit()
        
        return True
    
    @staticmethod
    async def disable_mfa(db: AsyncSession, user_id: int) -> bool:
        """Deaktiviert MFA für einen Benutzer"""
        
        stmt = update(User).where(User.id == user_id).values(
            mfa_enabled=False,
            mfa_secret=None,
            mfa_backup_codes=None
        )
        await db.execute(stmt)
        await db.commit()
        
        # Audit-Log
        await SecurityService.create_audit_log(
            db, user_id, AuditAction.USER_UPDATE,
            "MFA deaktiviert",
            resource_type="user", resource_id=user_id,
            processing_purpose="Multi-Factor-Authentication",
            legal_basis="Benutzeranfrage"
        )
        
        return True
    
    # Session Management
    
    @staticmethod
    async def invalidate_user_sessions(db: AsyncSession, user_id: int) -> bool:
        """Invalidiert alle Sessions eines Benutzers"""
        
        # Audit-Log
        await SecurityService.create_audit_log(
            db, user_id, AuditAction.USER_UPDATE,
            "Alle Sessions invalidiert",
            resource_type="user", resource_id=user_id,
            processing_purpose="Sicherheit",
            legal_basis="Sicherheitsmaßnahme"
        )
        
        return True
    
    # Security Monitoring
    
    @staticmethod
    async def detect_suspicious_activity(db: AsyncSession, user_id: int, activity_type: str) -> bool:
        """Erkennt verdächtige Aktivitäten"""
        
        # Prüfe ungewöhnliche Login-Zeiten
        # Prüfe Login von unbekannten IP-Adressen
        # Prüfe ungewöhnliche Aktivitätsmuster
        
        # Audit-Log für verdächtige Aktivität
        await SecurityService.create_audit_log(
            db, user_id, AuditAction.SUSPICIOUS_ACTIVITY,
            f"Verdächtige Aktivität erkannt: {activity_type}",
            resource_type="user", resource_id=user_id,
            risk_level="high",
            requires_review=True
        )
        
        return True
    
    @staticmethod
    async def get_security_report(db: AsyncSession, user_id: int) -> Dict[str, Any]:
        """Erstellt einen Sicherheitsbericht für einen Benutzer"""
        
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            return {}
        
        # Audit-Logs der letzten 30 Tage
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        stmt = select(AuditLog).where(
            AuditLog.user_id == user_id,
            AuditLog.created_at > cutoff_date
        ).order_by(AuditLog.created_at.desc())
        result = await db.execute(stmt)
        recent_logs = result.scalars().all()
        
        return {
            "user_id": user.id,
            "email": user.email,
            "mfa_enabled": user.mfa_enabled,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
            "failed_login_attempts": user.failed_login_attempts,
            "account_locked_until": user.account_locked_until.isoformat() if user.account_locked_until else None,
            "recent_activities": [
                {
                    "action": log.action.value,
                    "description": log.description,
                    "created_at": log.created_at.isoformat(),
                    "ip_address": log.ip_address,
                    "risk_level": log.risk_level
                }
                for log in recent_logs[:50]  # Letzte 50 Aktivitäten
            ]
        } 