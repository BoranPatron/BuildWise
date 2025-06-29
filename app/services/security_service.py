import bcrypt
import hashlib
import secrets
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from ..models.user import User, UserStatus
from ..models.audit_log import AuditLog, AuditAction


class SecurityService:
    """DSGVO-konformer Security-Service für BuildWise"""
    
    # Passwort-Richtlinien
    MIN_PASSWORD_LENGTH = 12
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_NUMBERS = True
    REQUIRE_SPECIAL_CHARS = True
    
    # Account-Sperrung
    MAX_FAILED_LOGIN_ATTEMPTS = 5
    ACCOUNT_LOCKOUT_DURATION = timedelta(minutes=30)
    
    # Session-Management
    SESSION_TIMEOUT = timedelta(hours=2)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash-Passwort mit bcrypt und individuellem Salt"""
        salt = bcrypt.gensalt(rounds=12)  # 12 Runden für hohe Sicherheit
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Überprüfe Passwort gegen Hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """Überprüfe Passwort-Stärke nach DSGVO-Richtlinien"""
        errors = []
        warnings = []
        
        # Mindestlänge
        if len(password) < SecurityService.MIN_PASSWORD_LENGTH:
            errors.append(f"Passwort muss mindestens {SecurityService.MIN_PASSWORD_LENGTH} Zeichen lang sein")
        
        # Großbuchstaben
        if SecurityService.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            errors.append("Passwort muss mindestens einen Großbuchstaben enthalten")
        
        # Kleinbuchstaben
        if SecurityService.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            errors.append("Passwort muss mindestens einen Kleinbuchstaben enthalten")
        
        # Zahlen
        if SecurityService.REQUIRE_NUMBERS and not re.search(r'\d', password):
            errors.append("Passwort muss mindestens eine Zahl enthalten")
        
        # Sonderzeichen
        if SecurityService.REQUIRE_SPECIAL_CHARS and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Passwort muss mindestens ein Sonderzeichen enthalten")
        
        # Häufige Passwörter vermeiden
        common_passwords = ['password', '123456', 'qwerty', 'admin', 'letmein']
        if password.lower() in common_passwords:
            errors.append("Passwort ist zu einfach - verwenden Sie ein komplexeres Passwort")
        
        # Warnungen für schwache Passwörter
        if len(password) < 16:
            warnings.append("Für höhere Sicherheit verwenden Sie ein längeres Passwort")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            warnings.append("Sonderzeichen erhöhen die Passwort-Sicherheit")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'strength_score': SecurityService._calculate_strength_score(password)
        }
    
    @staticmethod
    def _calculate_strength_score(password: str) -> int:
        """Berechne Passwort-Stärke-Score (0-100)"""
        score = 0
        
        # Länge
        score += min(len(password) * 4, 40)
        
        # Zeichentypen
        if re.search(r'[a-z]', password): score += 10
        if re.search(r'[A-Z]', password): score += 10
        if re.search(r'\d', password): score += 10
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password): score += 20
        
        # Komplexität
        if len(set(password)) > len(password) * 0.7: score += 10
        
        return min(score, 100)
    
    @staticmethod
    def anonymize_ip_address(ip_address: str) -> str:
        """Anonymisiere IP-Adresse für DSGVO-Konformität"""
        if not ip_address:
            return ""
        
        # IPv4: Letztes Oktett entfernen
        if '.' in ip_address:
            parts = ip_address.split('.')
            if len(parts) == 4:
                return '.'.join(parts[:3]) + '.0'
        
        # IPv6: Letzte 64 Bits entfernen
        if ':' in ip_address:
            parts = ip_address.split(':')
            if len(parts) >= 4:
                return ':'.join(parts[:4]) + '::'
        
        return ip_address
    
    @staticmethod
    def anonymize_user_agent(user_agent: str) -> str:
        """Anonymisiere User-Agent für DSGVO-Konformität"""
        if not user_agent:
            return ""
        
        # Nur Browser und Version behalten, persönliche Daten entfernen
        if 'Mozilla' in user_agent:
            # Vereinfachte Browser-Erkennung
            if 'Chrome' in user_agent:
                return 'Chrome Browser'
            elif 'Firefox' in user_agent:
                return 'Firefox Browser'
            elif 'Safari' in user_agent:
                return 'Safari Browser'
            elif 'Edge' in user_agent:
                return 'Edge Browser'
        
        return 'Unknown Browser'
    
    @staticmethod
    async def handle_failed_login(db: AsyncSession, user: User, ip_address: str) -> bool:
        """Behandle fehlgeschlagene Anmeldung und sperre Account bei Bedarf"""
        # Erhöhe fehlgeschlagene Anmeldeversuche
        new_attempts = user.failed_login_attempts + 1
        
        # Prüfe ob Account gesperrt werden soll
        is_locked = new_attempts >= SecurityService.MAX_FAILED_LOGIN_ATTEMPTS
        
        if is_locked:
            # Account sperren
            await db.execute(
                update(User)
                .where(User.id == user.id)
                .values(
                    failed_login_attempts=new_attempts,
                    account_locked_until=datetime.utcnow() + SecurityService.ACCOUNT_LOCKOUT_DURATION,
                    status=UserStatus.SUSPENDED
                )
            )
            
            # Audit-Log erstellen
            await SecurityService.create_audit_log(
                db, int(user.id), AuditAction.ACCOUNT_LOCKED,
                f"Account nach {new_attempts} fehlgeschlagenen Anmeldeversuchen gesperrt",
                resource_type="user", resource_id=int(user.id),
                ip_address=SecurityService.anonymize_ip_address(ip_address),
                risk_level="high"
            )
        else:
            # Nur fehlgeschlagene Versuche erhöhen
            await db.execute(
                update(User)
                .where(User.id == user.id)
                .values(failed_login_attempts=new_attempts)
            )
        
        # Audit-Log für fehlgeschlagene Anmeldung
        await SecurityService.create_audit_log(
            db, int(user.id), AuditAction.FAILED_LOGIN,
            f"Fehlgeschlagener Anmeldeversuch (Versuch {new_attempts})",
            resource_type="user", resource_id=int(user.id),
            ip_address=SecurityService.anonymize_ip_address(ip_address),
            risk_level="medium"
        )
        
        await db.commit()
        return is_locked
    
    @staticmethod
    async def reset_failed_login_attempts(db: AsyncSession, user_id: int):
        """Setze fehlgeschlagene Anmeldeversuche zurück"""
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                failed_login_attempts=0,
                account_locked_until=None,
                status=UserStatus.ACTIVE
            )
        )
        await db.commit()
    
    @staticmethod
    async def create_audit_log(
        db: AsyncSession,
        user_id: Optional[int],
        action: AuditAction,
        description: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        details: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        risk_level: str = "low",
        processing_purpose: Optional[str] = None,
        legal_basis: Optional[str] = None
    ):
        """Erstelle DSGVO-konformen Audit-Log"""
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            details=details,
            ip_address=SecurityService.anonymize_ip_address(ip_address) if ip_address else None,
            user_agent=SecurityService.anonymize_user_agent(user_agent) if user_agent else None,
            risk_level=risk_level,
            processing_purpose=processing_purpose,
            legal_basis=legal_basis,
            requires_review=risk_level in ["high", "critical"]
        )
        
        db.add(audit_log)
        await db.commit()
    
    @staticmethod
    def generate_secure_token() -> str:
        """Generiere sicheren Token für Passwort-Reset etc."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def is_account_locked(user: User) -> bool:
        """Prüfe ob Account gesperrt ist"""
        if user.account_locked_until and user.account_locked_until > datetime.utcnow():
            return True
        return False 