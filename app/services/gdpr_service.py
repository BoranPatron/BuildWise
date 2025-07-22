import json
import zipfile
import io
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import secrets

from ..core.config import settings
from ..models.user import User
from ..models.audit_log import AuditAction
from ..services.security_service import SecurityService


class GDPRService:
    """Service für DSGVO-Compliance und Datenverwaltung"""
    
    @staticmethod
    async def export_user_data(db: AsyncSession, user_id: int) -> Dict[str, Any]:
        """Exportiert alle Benutzerdaten für Datenportabilität"""
        
        # Benutzer abrufen
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise ValueError("Benutzer nicht gefunden")
        
        # Strukturierte Daten exportieren
        export_data = {
            "export_info": {
                "exported_at": datetime.utcnow().isoformat(),
                "user_id": user.id,
                "email": user.email,
                "data_retention_until": user.data_retention_until.isoformat() if user.data_retention_until else None
            },
            "user_profile": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone": user.phone,
                "user_type": user.user_type.value,
                "company_name": user.company_name,
                "company_address": user.company_address,
                "company_phone": user.company_phone,
                "company_website": user.company_website,
                "bio": user.bio,
                "region": user.region,
                "languages": user.languages,
                "language_preference": user.language_preference,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat(),
                "last_activity_at": user.last_activity_at.isoformat() if user.last_activity_at else None
            },
            "authentication": {
                "auth_provider": user.auth_provider.value,
                "google_sub": user.google_sub,
                "microsoft_sub": user.microsoft_sub,
                "apple_sub": user.apple_sub,
                "email_verified": user.email_verified,
                "is_verified": user.is_verified,
                "mfa_enabled": user.mfa_enabled,
                "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
                "last_login_provider": user.last_login_provider.value if user.last_login_provider else None
            },
            "consents": {
                "data_processing_consent": user.data_processing_consent,
                "marketing_consent": user.marketing_consent,
                "privacy_policy_accepted": user.privacy_policy_accepted,
                "terms_accepted": user.terms_accepted,
                "consent_fields": user.consent_fields,
                "consent_history": user.consent_history
            },
            "data_retention": {
                "data_retention_until": user.data_retention_until.isoformat() if user.data_retention_until else None,
                "data_deletion_requested": user.data_deletion_requested,
                "data_deletion_requested_at": user.data_deletion_requested_at.isoformat() if user.data_deletion_requested_at else None,
                "data_anonymized": user.data_anonymized,
                "data_export_requested": user.data_export_requested,
                "data_export_requested_at": user.data_export_requested_at.isoformat() if user.data_export_requested_at else None
            },
            "social_profile_data": user.social_profile_data
        }
        
        # Audit-Log für Datenexport
        await SecurityService.create_audit_log(
            db, user.id, AuditAction.DATA_EXPORT_REQUEST,
            f"Datenexport durchgeführt: {user.email}",
            resource_type="user", resource_id=user.id,
            processing_purpose="Datenportabilität",
            legal_basis="DSGVO Art. 20"
        )
        
        return export_data
    
    @staticmethod
    async def generate_data_export_token(db: AsyncSession, user_id: int) -> str:
        """Generiert einen sicheren Token für Datenexport"""
        
        token = secrets.token_urlsafe(32)
        expiry = datetime.utcnow() + timedelta(hours=settings.data_export_token_expiry_hours)
        
        # Token in Datenbank speichern
        stmt = update(User).where(User.id == user_id).values(
            data_export_token=token,
            data_export_expires_at=expiry,
            data_export_requested=True,
            data_export_requested_at=datetime.utcnow()
        )
        await db.execute(stmt)
        await db.commit()
        
        return token
    
    @staticmethod
    async def verify_data_export_token(db: AsyncSession, user_id: int, token: str) -> bool:
        """Verifiziert einen Datenexport-Token"""
        
        stmt = select(User).where(
            User.id == user_id,
            User.data_export_token == token,
            User.data_export_expires_at > datetime.utcnow()
        )
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        return user is not None
    
    @staticmethod
    async def request_data_deletion(db: AsyncSession, user_id: int) -> bool:
        """Beantragt die Löschung aller Benutzerdaten"""
        
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            return False
        
        # Löschung beantragen
        stmt = update(User).where(User.id == user_id).values(
            data_deletion_requested=True,
            data_deletion_requested_at=datetime.utcnow(),
            data_retention_until=datetime.utcnow().date() + timedelta(days=30)  # 30 Tage Aufbewahrung
        )
        await db.execute(stmt)
        await db.commit()
        
        # Audit-Log
        await SecurityService.create_audit_log(
            db, user.id, AuditAction.DATA_DELETION_REQUEST,
            f"Datenlöschung beantragt: {user.email}",
            resource_type="user", resource_id=user.id,
            processing_purpose="Recht auf Löschung",
            legal_basis="DSGVO Art. 17"
        )
        
        return True
    
    @staticmethod
    async def anonymize_user_data(db: AsyncSession, user_id: int) -> bool:
        """Anonymisiert Benutzerdaten"""
        
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            return False
        
        # Daten anonymisieren
        stmt = update(User).where(User.id == user_id).values(
            first_name="Anonym",
            last_name="Benutzer",
            email=f"anonym_{user_id}@deleted.buildwise.de",
            phone=None,
            company_name=None,
            company_address=None,
            company_phone=None,
            company_website=None,
            bio=None,
            profile_image=None,
            social_profile_data=None,
            data_anonymized=True,
            data_anonymized_at=datetime.utcnow()
        )
        await db.execute(stmt)
        await db.commit()
        
        # Audit-Log
        await SecurityService.create_audit_log(
            db, user_id, AuditAction.DATA_ANONYMIZATION,
            f"Benutzerdaten anonymisiert: ID {user_id}",
            resource_type="user", resource_id=user_id,
            processing_purpose="Datenanonymisierung",
            legal_basis="DSGVO Art. 17"
        )
        
        return True
    
    @staticmethod
    async def update_consent(
        db: AsyncSession, 
        user_id: int, 
        consent_type: str, 
        granted: bool,
        legal_basis: str = "Einwilligung"
    ) -> bool:
        """Aktualisiert Benutzereinwilligungen"""
        
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            return False
        
        # Consent-Felder aktualisieren
        consent_fields = user.consent_fields or {}
        consent_fields[consent_type] = {
            "granted": granted,
            "timestamp": datetime.utcnow().isoformat(),
            "legal_basis": legal_basis
        }
        
        # Consent-Historie aktualisieren
        consent_history = user.consent_history or []
        consent_history.append({
            "consent_type": consent_type,
            "granted": granted,
            "timestamp": datetime.utcnow().isoformat(),
            "legal_basis": legal_basis
        })
        
        # Legacy-Felder für Kompatibilität
        update_values = {
            "consent_fields": consent_fields,
            "consent_history": consent_history
        }
        
        if consent_type == "data_processing":
            update_values["data_processing_consent"] = granted
        elif consent_type == "marketing":
            update_values["marketing_consent"] = granted
        elif consent_type == "privacy_policy":
            update_values["privacy_policy_accepted"] = granted
        elif consent_type == "terms":
            update_values["terms_accepted"] = granted
        
        stmt = update(User).where(User.id == user_id).values(**update_values)
        await db.execute(stmt)
        await db.commit()
        
        # Audit-Log
        action = AuditAction.CONSENT_GIVEN if granted else AuditAction.CONSENT_WITHDRAWN
        await SecurityService.create_audit_log(
            db, user_id, action,
            f"Einwilligung {consent_type}: {'gewährt' if granted else 'widerrufen'}",
            resource_type="user", resource_id=user_id,
            processing_purpose="Einwilligungsverwaltung",
            legal_basis=legal_basis
        )
        
        return True
    
    @staticmethod
    async def get_consent_status(db: AsyncSession, user_id: int) -> Dict[str, Any]:
        """Gibt den aktuellen Einwilligungsstatus zurück"""
        
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            return {}
        
        return {
            "data_processing": user.data_processing_consent,
            "marketing": user.marketing_consent,
            "privacy_policy": user.privacy_policy_accepted,
            "terms": user.terms_accepted,
            "consent_fields": user.consent_fields,
            "consent_history": user.consent_history
        }
    
    @staticmethod
    async def cleanup_expired_data(db: AsyncSession) -> int:
        """Bereinigt abgelaufene Daten"""
        
        cleanup_date = datetime.utcnow().date() - timedelta(days=settings.data_retention_days)
        
        # Benutzer mit abgelaufener Aufbewahrungsfrist anonymisieren
        stmt = select(User).where(
            User.data_retention_until < cleanup_date,
            User.data_anonymized == False
        )
        result = await db.execute(stmt)
        users_to_anonymize = result.scalars().all()
        
        anonymized_count = 0
        for user in users_to_anonymize:
            if await GDPRService.anonymize_user_data(db, user.id):
                anonymized_count += 1
        
        return anonymized_count
    
    @staticmethod
    async def create_data_export_zip(export_data: Dict[str, Any]) -> bytes:
        """Erstellt eine ZIP-Datei mit den exportierten Daten"""
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # JSON-Datei mit allen Daten
            zip_file.writestr(
                'user_data.json',
                json.dumps(export_data, indent=2, ensure_ascii=False)
            )
            
            # README-Datei
            readme_content = f"""
# Datenexport für {export_data['user_profile']['email']}

Exportiert am: {export_data['export_info']['exported_at']}

## Enthaltene Daten:
- Benutzerprofil
- Authentifizierungsdaten
- Einwilligungen
- Social-Login-Daten
- Audit-Logs

## DSGVO-Rechte:
- Recht auf Datenportabilität (Art. 20)
- Recht auf Löschung (Art. 17)
- Recht auf Berichtigung (Art. 16)

Für Fragen wenden Sie sich an: datenschutz@buildwise.de
            """
            zip_file.writestr('README.txt', readme_content.strip())
        
        return zip_buffer.getvalue() 