from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional

from ..core.database import get_db
from ..api.deps import get_current_user
from ..models import User
from ..schemas.user import UserRead
from ..services.user_service import (
    request_data_deletion, anonymize_user_data, update_consent,
    get_user_by_id
)
from ..services.security_service import SecurityService
from ..models.audit_log import AuditAction

router = APIRouter(prefix="/gdpr", tags=["gdpr"])


@router.post("/consent")
async def update_user_consent(
    consent_type: str,
    granted: bool,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """DSGVO: Einwilligung aktualisieren"""
    valid_consent_types = ["data_processing", "marketing", "privacy_policy", "terms"]
    
    if consent_type not in valid_consent_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ungültiger Einwilligungstyp. Erlaubt: {', '.join(valid_consent_types)}"
        )
    
    # Konvertiere SQLAlchemy-Column zu int
    user_id = int(getattr(current_user, 'id', 0))
    
    success = await update_consent(db, user_id, consent_type, granted)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Benutzer nicht gefunden"
        )
    
    # Audit-Log für Einwilligung
    await SecurityService.create_audit_log(
        db, user_id, 
        AuditAction.CONSENT_GIVEN if granted else AuditAction.CONSENT_WITHDRAWN,
        f"Einwilligung {consent_type}: {'erteilt' if granted else 'zurückgezogen'}",
        resource_type="user", resource_id=user_id,
        processing_purpose="Einwilligungsverwaltung",
        legal_basis="Einwilligung"
    )
    
    return {
        "message": f"Einwilligung {consent_type} erfolgreich {'erteilt' if granted else 'zurückgezogen'}",
        "consent_type": consent_type,
        "granted": granted
    }


@router.post("/data-deletion-request")
async def request_user_data_deletion(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """DSGVO: Antrag auf Datenlöschung"""
    user_id = int(getattr(current_user, 'id', 0))
    success = await request_data_deletion(db, user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Benutzer nicht gefunden"
        )
    
    # Audit-Log für Datenlöschungsantrag
    await SecurityService.create_audit_log(
        db, user_id, AuditAction.DATA_DELETION_REQUEST,
        f"Datenlöschung beantragt: {getattr(current_user, 'email', 'unknown')}",
        resource_type="user", resource_id=user_id,
        processing_purpose="DSGVO-Datenlöschung",
        legal_basis="Recht auf Löschung",
        risk_level="high"
    )
    
    return {
        "message": "Antrag auf Datenlöschung erfolgreich eingereicht",
        "status": "pending",
        "estimated_completion": "30 Tage"
    }


@router.post("/data-anonymization")
async def anonymize_user_data_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """DSGVO: Benutzerdaten anonymisieren"""
    user_id = int(getattr(current_user, 'id', 0))
    success = await anonymize_user_data(db, user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Benutzer nicht gefunden"
        )
    
    # Audit-Log für Datenanonymisierung
    await SecurityService.create_audit_log(
        db, user_id, AuditAction.DATA_ANONYMIZATION,
        f"Benutzerdaten anonymisiert: ID {user_id}",
        resource_type="user", resource_id=user_id,
        processing_purpose="DSGVO-Datenanonymisierung",
        legal_basis="Recht auf Löschung",
        risk_level="medium"
    )
    
    return {
        "message": "Benutzerdaten erfolgreich anonymisiert",
        "status": "completed"
    }


@router.get("/data-export")
async def export_user_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """DSGVO: Datenexport für Benutzer"""
    user_id = int(getattr(current_user, 'id', 0))
    
    # Hole alle Benutzerdaten
    user = await get_user_by_id(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Benutzer nicht gefunden"
        )
    
    # Erstelle Export-Daten (ohne sensible Informationen)
    export_data = {
        "user_id": getattr(user, 'id', None),
        "email": getattr(user, 'email', None),
        "first_name": getattr(user, 'first_name', None),
        "last_name": getattr(user, 'last_name', None),
        "user_type": getattr(user, 'user_type', None),
        "created_at": getattr(user, 'created_at', None),
        "last_login_at": getattr(user, 'last_login_at', None),
        "consents": {
            "data_processing": getattr(user, 'data_processing_consent', False),
            "marketing": getattr(user, 'marketing_consent', False),
            "privacy_policy": getattr(user, 'privacy_policy_accepted', False),
            "terms": getattr(user, 'terms_accepted', False)
        },
        "data_retention": {
            "retention_until": getattr(user, 'data_retention_until', None),
            "deletion_requested": getattr(user, 'data_deletion_requested', False),
            "deletion_requested_at": getattr(user, 'data_deletion_requested_at', None),
            "anonymized": getattr(user, 'data_anonymized', False)
        }
    }
    
    # Audit-Log für Datenexport
    await SecurityService.create_audit_log(
        db, user_id, AuditAction.DATA_EXPORT_REQUEST,
        f"Datenexport angefordert: {getattr(user, 'email', 'unknown')}",
        resource_type="user", resource_id=user_id,
        processing_purpose="DSGVO-Datenexport",
        legal_basis="Recht auf Datenübertragbarkeit",
        risk_level="low"
    )
    
    return {
        "message": "Datenexport erfolgreich erstellt",
        "data": export_data,
        "export_date": getattr(user, 'updated_at', None)
    }


@router.get("/privacy-policy")
async def get_privacy_policy():
    """DSGVO: Datenschutzerklärung"""
    return {
        "title": "Datenschutzerklärung - BuildWise",
        "version": "1.0",
        "last_updated": "2024-01-01",
        "content": {
            "data_controller": "BuildWise GmbH",
            "contact": "datenschutz@buildwise.de",
            "purposes": [
                "Bereitstellung der BuildWise-Plattform",
                "Projektmanagement und -verwaltung",
                "Kommunikation zwischen Benutzern",
                "Dienstleister-Vermittlung"
            ],
            "legal_basis": [
                "Einwilligung (Art. 6 Abs. 1 lit. a DSGVO)",
                "Vertragserfüllung (Art. 6 Abs. 1 lit. b DSGVO)",
                "Berechtigte Interessen (Art. 6 Abs. 1 lit. f DSGVO)"
            ],
            "data_retention": "2 Jahre nach letzter Aktivität",
            "user_rights": [
                "Recht auf Auskunft",
                "Recht auf Berichtigung",
                "Recht auf Löschung",
                "Recht auf Einschränkung",
                "Recht auf Datenübertragbarkeit",
                "Widerspruchsrecht"
            ]
        }
    }


@router.get("/terms-of-service")
async def get_terms_of_service():
    """AGB und Nutzungsbedingungen"""
    return {
        "title": "Allgemeine Geschäftsbedingungen - BuildWise",
        "version": "1.0",
        "last_updated": "2024-01-01",
        "content": {
            "service_description": "BuildWise ist eine Plattform für Immobilienprojekte",
            "user_obligations": [
                "Wahrheitsgemäße Angaben",
                "Einhaltung der Nutzungsbedingungen",
                "Respektvoller Umgang mit anderen Benutzern"
            ],
            "liability": "Haftung nach gesetzlichen Bestimmungen",
            "data_protection": "DSGVO-konforme Datenverarbeitung",
            "termination": "Kündigung mit 30 Tagen Frist",
            "changes": "Änderungen werden 30 Tage vorher angekündigt",
            "contact": "support@buildwise.de"
        }
    } 