from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional, List
from datetime import datetime, date

from ..models import User, UserType
from ..models.user import UserStatus
from ..models.audit_log import AuditAction
from ..services.security_service import SecurityService
from ..schemas.user import UserCreate, UserUpdate


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()


async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    # Passwort-Stärke validieren
    password_validation = SecurityService.validate_password_strength(user_in.password)
    if not password_validation['is_valid']:
        raise ValueError(f"Passwort erfüllt nicht die Sicherheitsanforderungen: {', '.join(password_validation['errors'])}")
    
    # Passwort hashen
    hashed_password = SecurityService.hash_password(user_in.password)
    
    # DSGVO: Standard-Datenaufbewahrung (2 Jahre)
    data_retention_until = date.today().replace(year=date.today().year + 2)
    
    user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        phone=user_in.phone,
        user_type=user_in.user_type,
        # DSGVO: Standard-Einwilligungen
        data_processing_consent=False,  # Muss explizit gegeben werden
        marketing_consent=False,  # Muss explizit gegeben werden
        privacy_policy_accepted=False,  # Muss explizit akzeptiert werden
        terms_accepted=False,  # Muss explizit akzeptiert werden
        data_retention_until=data_retention_until,
        status=UserStatus.ACTIVE
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Audit-Log erstellen
    user_id = getattr(user, 'id', None)
    if user_id:
        await SecurityService.create_audit_log(
            db, user_id, AuditAction.USER_REGISTER,
            f"Neuer Benutzer registriert: {user.email}",
            resource_type="user", resource_id=user_id,
            processing_purpose="Benutzerregistrierung",
            legal_basis="Einwilligung"
        )
    
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str, ip_address: str = None) -> User | None:
    user = await get_user_by_email(db, email)
    if not user:
        return None
    
    # Prüfe ob Account gesperrt ist
    account_locked_until = getattr(user, 'account_locked_until', None)
    if account_locked_until and SecurityService.is_account_locked(account_locked_until):
        user_id = getattr(user, 'id', None)
        if user_id:
            await SecurityService.create_audit_log(
                db, user_id, AuditAction.UNAUTHORIZED_ACCESS,
                f"Anmeldeversuch bei gesperrtem Account: {email}",
                resource_type="user", resource_id=user_id,
                ip_address=SecurityService.anonymize_ip_address(ip_address) if ip_address else None,
                risk_level="high"
            )
        return None
    
    # Passwort überprüfen
    hashed_password = getattr(user, 'hashed_password', '')
    if not SecurityService.verify_password(password, str(hashed_password)):
        # Fehlgeschlagene Anmeldung behandeln
        user_id = getattr(user, 'id', None)
        failed_attempts = getattr(user, 'failed_login_attempts', 0)
        if user_id:
            await SecurityService.handle_failed_login(db, user, ip_address or "")
        return None
    
    # Erfolgreiche Anmeldung
    user_id = getattr(user, 'id', None)
    if user_id:
        await SecurityService.reset_failed_login_attempts(db, user_id)
    
    # Login-Zeit aktualisieren
    await db.execute(
        update(User)
        .where(User.id == user.id)
        .values(
            last_login_at=datetime.utcnow(),
            last_activity_at=datetime.utcnow()
        )
    )
    await db.commit()
    
    # Audit-Log für erfolgreiche Anmeldung
    if user_id:
        await SecurityService.create_audit_log(
            db, user_id, AuditAction.USER_LOGIN,
            f"Erfolgreiche Anmeldung: {email}",
            resource_type="user", resource_id=user_id,
            ip_address=SecurityService.anonymize_ip_address(ip_address) if ip_address else None,
            risk_level="low"
        )
    
    return user


async def update_user(db: AsyncSession, user_id: int, user_update: UserUpdate) -> User | None:
    user = await get_user_by_id(db, user_id)
    if not user:
        return None
    
    update_data = user_update.dict(exclude_unset=True)
    if update_data:
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(**update_data, updated_at=datetime.utcnow())
        )
        await db.commit()
        await db.refresh(user)
        
        # Audit-Log erstellen
        await SecurityService.create_audit_log(
            db, user_id, AuditAction.USER_UPDATE,
            f"Benutzerdaten aktualisiert: {user.email}",
            resource_type="user", resource_id=user_id,
            processing_purpose="Profilaktualisierung",
            legal_basis="Vertragserfüllung"
        )
    
    return user


async def verify_email(db: AsyncSession, user_id: int) -> bool:
    user = await get_user_by_id(db, user_id)
    if not user:
        return False
    
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(email_verified=True, updated_at=datetime.utcnow())
    )
    await db.commit()
    
    # Audit-Log erstellen
    await SecurityService.create_audit_log(
        db, user_id, AuditAction.USER_UPDATE,
        f"E-Mail verifiziert: {user.email}",
        resource_type="user", resource_id=user_id,
        processing_purpose="E-Mail-Verifizierung",
        legal_basis="Vertragserfüllung"
    )
    
    return True


async def change_password(db: AsyncSession, user_id: int, current_password: str, new_password: str) -> bool:
    user = await get_user_by_id(db, user_id)
    if not user:
        return False
    
    hashed_password = getattr(user, 'hashed_password', '')
    if not SecurityService.verify_password(current_password, str(hashed_password)):
        return False
    
    # Neue Passwort-Stärke validieren
    password_validation = SecurityService.validate_password_strength(new_password)
    if not password_validation['is_valid']:
        raise ValueError(f"Neues Passwort erfüllt nicht die Sicherheitsanforderungen: {', '.join(password_validation['errors'])}")
    
    # Neues Passwort hashen
    hashed_new_password = SecurityService.hash_password(new_password)
    
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(
            hashed_password=hashed_new_password,
            password_changed_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    )
    await db.commit()
    
    # Audit-Log erstellen
    await SecurityService.create_audit_log(
        db, user_id, AuditAction.PASSWORD_CHANGE,
        f"Passwort geändert: {user.email}",
        resource_type="user", resource_id=user_id,
        risk_level="medium"
    )
    
    return True


async def get_service_providers(db: AsyncSession, region: Optional[str] = None) -> List[User]:
    query = select(User).where(
        User.user_type == UserType.SERVICE_PROVIDER,
        User.status == UserStatus.ACTIVE,
        User.is_verified == True,
        User.data_processing_consent == True  # Nur bei Einwilligung
    )
    
    if region:
        query = query.where(User.region == region)
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def search_users(db: AsyncSession, search_term: str, user_type: Optional[UserType] = None) -> List[User]:
    query = select(User).where(
        User.status == UserStatus.ACTIVE,
        User.data_processing_consent == True  # Nur bei Einwilligung
    )
    
    if user_type:
        query = query.where(User.user_type == user_type)
    
    # Suche in Name, Email und Firmenname
    search_filter = (
        User.first_name.ilike(f"%{search_term}%") |
        User.last_name.ilike(f"%{search_term}%") |
        User.email.ilike(f"%{search_term}%") |
        User.company_name.ilike(f"%{search_term}%")
    )
    
    query = query.where(search_filter)
    result = await db.execute(query)
    return list(result.scalars().all())


async def deactivate_user(db: AsyncSession, user_id: int) -> bool:
    user = await get_user_by_id(db, user_id)
    if not user:
        return False
    
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(
            status=UserStatus.INACTIVE,
            updated_at=datetime.utcnow()
        )
    )
    await db.commit()
    
    # Audit-Log erstellen
    await SecurityService.create_audit_log(
        db, user_id, AuditAction.USER_DELETE,
        f"Benutzer deaktiviert: {user.email}",
        resource_type="user", resource_id=user_id,
        processing_purpose="Account-Deaktivierung",
        legal_basis="Einwilligung"
    )
    
    return True


async def request_data_deletion(db: AsyncSession, user_id: int) -> bool:
    """DSGVO: Antrag auf Datenlöschung"""
    user = await get_user_by_id(db, user_id)
    if not user:
        return False
    
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(
            data_deletion_requested=True,
            data_deletion_requested_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    )
    await db.commit()
    
    # Audit-Log erstellen
    await SecurityService.create_audit_log(
        db, user_id, AuditAction.DATA_DELETION_REQUEST,
        f"Datenlöschung beantragt: {user.email}",
        resource_type="user", resource_id=user_id,
        processing_purpose="DSGVO-Datenlöschung",
        legal_basis="Recht auf Löschung",
        risk_level="high"
    )
    
    return True


async def anonymize_user_data(db: AsyncSession, user_id: int) -> bool:
    """DSGVO: Benutzerdaten anonymisieren"""
    user = await get_user_by_id(db, user_id)
    if not user:
        return False
    
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(
            first_name="Anonym",
            last_name="Benutzer",
            email=f"anonym_{user_id}@deleted.local",
            phone=None,
            company_name=None,
            company_address=None,
            company_phone=None,
            company_website=None,
            bio=None,
            profile_image=None,
            data_anonymized=True,
            updated_at=datetime.utcnow()
        )
    )
    await db.commit()
    
    # Audit-Log erstellen
    await SecurityService.create_audit_log(
        db, user_id, AuditAction.DATA_ANONYMIZATION,
        f"Benutzerdaten anonymisiert: ID {user_id}",
        resource_type="user", resource_id=user_id,
        processing_purpose="DSGVO-Datenanonymisierung",
        legal_basis="Recht auf Löschung",
        risk_level="medium"
    )
    
    return True


async def update_consent(db: AsyncSession, user_id: int, consent_type: str, granted: bool) -> bool:
    """DSGVO: Einwilligung aktualisieren"""
    user = await get_user_by_id(db, user_id)
    if not user:
        return False
    
    update_data = {}
    if consent_type == "data_processing":
        update_data["data_processing_consent"] = granted
    elif consent_type == "marketing":
        update_data["marketing_consent"] = granted
    elif consent_type == "privacy_policy":
        update_data["privacy_policy_accepted"] = granted
    elif consent_type == "terms":
        update_data["terms_accepted"] = granted
    
    if update_data:
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(**update_data, updated_at=datetime.utcnow())
        )
        await db.commit()
        
        # Audit-Log erstellen
        action = AuditAction.CONSENT_GIVEN if granted else AuditAction.CONSENT_WITHDRAWN
        await SecurityService.create_audit_log(
            db, user_id, action,
            f"Einwilligung {consent_type}: {'erteilt' if granted else 'zurückgezogen'}",
            resource_type="user", resource_id=user_id,
            processing_purpose="Einwilligungsverwaltung",
            legal_basis="Einwilligung"
        )
    
    return True
