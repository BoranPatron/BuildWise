from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
from datetime import datetime

from ..core.database import get_db
from ..api.deps import get_current_user
from ..models import User
from ..schemas.user import UserRead, ConsentUpdate
from ..services.user_service import UserService
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
    
    # Erstelle ConsentUpdate-Objekt
    consent_update = ConsentUpdate(**{consent_type: granted})
    
    # Aktualisiere Benutzer-Einwilligungen
    updated_user = await UserService.update_consents(db, current_user.id, consent_update)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Benutzer nicht gefunden"
        )
    
    # Audit-Log für Einwilligung
    await SecurityService.create_audit_log(
        db, current_user.id, 
        AuditAction.CONSENT_GIVEN if granted else AuditAction.CONSENT_WITHDRAWN,
        f"Einwilligung {consent_type}: {'erteilt' if granted else 'zurückgezogen'}",
        resource_type="user", resource_id=current_user.id,
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
    # Markiere Benutzer für Löschung
    current_user.data_deletion_requested = True
    current_user.data_deletion_requested_at = datetime.utcnow()
    await db.commit()
    
    # Audit-Log für Datenlöschungsantrag
    await SecurityService.create_audit_log(
        db, current_user.id, AuditAction.DATA_DELETION_REQUEST,
        f"Datenlöschung beantragt: {current_user.email}",
        resource_type="user", resource_id=current_user.id,
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
    # Anonymisiere Benutzerdaten
    current_user.first_name = "Anonym"
    current_user.last_name = "Benutzer"
    current_user.email = f"anonym_{current_user.id}@deleted.buildwise.de"
    current_user.phone = None
    current_user.company_name = None
    current_user.company_address = None
    current_user.company_phone = None
    current_user.company_website = None
    current_user.business_license = None
    current_user.tax_id = None
    current_user.vat_id = None
    current_user.bio = None
    current_user.profile_image = None
    current_user.region = None
    current_user.languages = None
    current_user.data_anonymized = True
    current_user.updated_at = datetime.utcnow()
    
    await db.commit()
    
    # Audit-Log für Datenanonymisierung
    await SecurityService.create_audit_log(
        db, current_user.id, AuditAction.DATA_ANONYMIZATION,
        f"Benutzerdaten anonymisiert: ID {current_user.id}",
        resource_type="user", resource_id=current_user.id,
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
    # Erstelle Export-Daten (ohne sensible Informationen)
    export_data = {
        "user_id": current_user.id,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "user_type": current_user.user_type,
        "created_at": current_user.created_at,
        "last_login_at": current_user.last_login_at,
        "consents": {
            "data_processing": current_user.data_processing_consent,
            "marketing": current_user.marketing_consent,
            "privacy_policy": current_user.privacy_policy_accepted,
            "terms": current_user.terms_accepted
        },
        "data_retention": {
            "retention_until": current_user.data_retention_until,
            "deletion_requested": current_user.data_deletion_requested,
            "deletion_requested_at": current_user.data_deletion_requested_at,
            "anonymized": current_user.data_anonymized
        }
    }
    
    # Audit-Log für Datenexport
    await SecurityService.create_audit_log(
        db, current_user.id, AuditAction.DATA_EXPORT_REQUEST,
        f"Datenexport angefordert: {current_user.email}",
        resource_type="user", resource_id=current_user.id,
        processing_purpose="DSGVO-Datenexport",
        legal_basis="Recht auf Datenübertragbarkeit",
        risk_level="low"
    )
    
    return {
        "message": "Datenexport erfolgreich erstellt",
        "data": export_data,
        "export_date": current_user.updated_at
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