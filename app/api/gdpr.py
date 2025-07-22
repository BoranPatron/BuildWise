from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import io

from ..core.database import get_db
from ..api.deps import get_current_user
from ..models.user import User
from ..models.audit_log import AuditAction
from ..services.gdpr_service import GDPRService
from ..services.security_service import SecurityService
from ..schemas.user import UserRead

router = APIRouter(prefix="/gdpr", tags=["gdpr"])


@router.post("/consent")
async def update_user_consent(
    consent_type: str,
    granted: bool,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Aktualisiert Benutzereinwilligungen"""
    
    valid_consent_types = [
        "data_processing", "marketing", "privacy_policy", 
        "terms", "analytics", "cookies", "third_party"
    ]
    
    if consent_type not in valid_consent_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ungültiger Consent-Typ. Erlaubte Typen: {valid_consent_types}"
        )
    
    try:
        success = await GDPRService.update_consent(
            db, current_user.id, consent_type, granted
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Einwilligung konnte nicht aktualisiert werden"
            )
        
        # Audit-Log
        ip_address = request.client.host if request else None
        await SecurityService.create_audit_log(
            db, current_user.id, 
            AuditAction.CONSENT_GIVEN if granted else AuditAction.CONSENT_WITHDRAWN,
            f"Einwilligung {consent_type}: {'gewährt' if granted else 'widerrufen'}",
            resource_type="user", resource_id=current_user.id,
            ip_address=SecurityService.anonymize_ip_address(ip_address) if ip_address else None,
            processing_purpose="Einwilligungsverwaltung",
            legal_basis="DSGVO Art. 7"
        )
        
        return {
            "message": f"Einwilligung {consent_type} erfolgreich {'gewährt' if granted else 'widerrufen'}",
            "consent_type": consent_type,
            "granted": granted
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Aktualisieren der Einwilligung: {str(e)}"
        )


@router.get("/consent-status")
async def get_consent_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Gibt den aktuellen Einwilligungsstatus zurück"""
    
    try:
        consent_status = await GDPRService.get_consent_status(db, current_user.id)
        return consent_status
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Abrufen des Einwilligungsstatus: {str(e)}"
        )


@router.post("/data-deletion-request")
async def request_user_data_deletion(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Beantragt die Löschung aller Benutzerdaten (Recht auf Löschung)"""
    
    try:
        success = await GDPRService.request_data_deletion(db, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Datenlöschung konnte nicht beantragt werden"
            )
        
        # Audit-Log
        ip_address = request.client.host if request else None
        await SecurityService.create_audit_log(
            db, current_user.id, AuditAction.DATA_DELETION_REQUEST,
            f"Datenlöschung beantragt: {current_user.email}",
            resource_type="user", resource_id=current_user.id,
            ip_address=SecurityService.anonymize_ip_address(ip_address) if ip_address else None,
            processing_purpose="Recht auf Löschung",
            legal_basis="DSGVO Art. 17"
        )
        
        return {
            "message": "Datenlöschung wurde beantragt. Ihre Daten werden innerhalb von 30 Tagen gelöscht.",
            "deletion_requested_at": "now",
            "estimated_deletion_date": "30 days from now"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Beantragen der Datenlöschung: {str(e)}"
        )


@router.post("/data-anonymization")
async def anonymize_user_data_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Anonymisiert Benutzerdaten sofort"""
    
    try:
        success = await GDPRService.anonymize_user_data(db, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Datenanonymisierung konnte nicht durchgeführt werden"
            )
        
        # Audit-Log
        ip_address = request.client.host if request else None
        await SecurityService.create_audit_log(
            db, current_user.id, AuditAction.DATA_ANONYMIZATION,
            f"Benutzerdaten anonymisiert: {current_user.email}",
            resource_type="user", resource_id=current_user.id,
            ip_address=SecurityService.anonymize_ip_address(ip_address) if ip_address else None,
            processing_purpose="Datenanonymisierung",
            legal_basis="DSGVO Art. 17"
        )
        
        return {
            "message": "Ihre Daten wurden erfolgreich anonymisiert.",
            "anonymized_at": "now"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler bei der Datenanonymisierung: {str(e)}"
        )


@router.get("/data-export")
async def export_user_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Exportiert alle Benutzerdaten (Recht auf Datenportabilität)"""
    
    try:
        # Daten exportieren
        export_data = await GDPRService.export_user_data(db, current_user.id)
        
        # ZIP-Datei erstellen
        zip_data = await GDPRService.create_data_export_zip(export_data)
        
        # Audit-Log
        ip_address = request.client.host if request else None
        await SecurityService.create_audit_log(
            db, current_user.id, AuditAction.DATA_EXPORT_REQUEST,
            f"Datenexport durchgeführt: {current_user.email}",
            resource_type="user", resource_id=current_user.id,
            ip_address=SecurityService.anonymize_ip_address(ip_address) if ip_address else None,
            processing_purpose="Datenportabilität",
            legal_basis="DSGVO Art. 20"
        )
        
        # Streaming-Response für ZIP-Datei
        return StreamingResponse(
            io.BytesIO(zip_data),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=buildwise_user_data_{current_user.id}.zip"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Datenexport: {str(e)}"
        )


@router.post("/data-export-token")
async def generate_data_export_token(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Generiert einen sicheren Token für Datenexport"""
    
    try:
        token = await GDPRService.generate_data_export_token(db, current_user.id)
        
        # Audit-Log
        ip_address = request.client.host if request else None
        await SecurityService.create_audit_log(
            db, current_user.id, AuditAction.DATA_EXPORT_REQUEST,
            f"Export-Token generiert: {current_user.email}",
            resource_type="user", resource_id=current_user.id,
            ip_address=SecurityService.anonymize_ip_address(ip_address) if ip_address else None,
            processing_purpose="Datenportabilität",
            legal_basis="DSGVO Art. 20"
        )
        
        return {
            "message": "Export-Token wurde generiert und per E-Mail gesendet",
            "token_expires_in_hours": 24
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Generieren des Export-Tokens: {str(e)}"
        )


@router.get("/data-export/{token}")
async def download_data_export_with_token(
    token: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Lädt Datenexport mit Token herunter"""
    
    try:
        # Token verifizieren
        is_valid = await GDPRService.verify_data_export_token(db, current_user.id, token)
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ungültiger oder abgelaufener Export-Token"
            )
        
        # Daten exportieren
        export_data = await GDPRService.export_user_data(db, current_user.id)
        zip_data = await GDPRService.create_data_export_zip(export_data)
        
        # Audit-Log
        ip_address = request.client.host if request else None
        await SecurityService.create_audit_log(
            db, current_user.id, AuditAction.DATA_EXPORT_REQUEST,
            f"Datenexport mit Token durchgeführt: {current_user.email}",
            resource_type="user", resource_id=current_user.id,
            ip_address=SecurityService.anonymize_ip_address(ip_address) if ip_address else None,
            processing_purpose="Datenportabilität",
            legal_basis="DSGVO Art. 20"
        )
        
        return StreamingResponse(
            io.BytesIO(zip_data),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=buildwise_user_data_{current_user.id}.zip"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Datenexport: {str(e)}"
        )


@router.get("/privacy-policy")
async def get_privacy_policy():
    """Gibt die aktuelle Datenschutzerklärung zurück"""
    
    privacy_policy = {
        "version": "2.0",
        "last_updated": "2024-01-15",
        "title": "Datenschutzerklärung für BuildWise",
        "content": {
            "data_controller": {
                "name": "BuildWise GmbH",
                "address": "Musterstraße 123, 12345 Musterstadt",
                "email": "datenschutz@buildwise.de",
                "phone": "+49 123 456789"
            },
            "data_processing": {
                "purpose": "Bereitstellung der BuildWise-Plattform für Bauprojekte",
                "legal_basis": "Art. 6 Abs. 1 lit. b) DSGVO (Vertragserfüllung)",
                "retention_period": "7 Jahre nach Projektabschluss"
            },
            "user_rights": {
                "access": "Recht auf Auskunft (Art. 15 DSGVO)",
                "rectification": "Recht auf Berichtigung (Art. 16 DSGVO)",
                "erasure": "Recht auf Löschung (Art. 17 DSGVO)",
                "portability": "Recht auf Datenportabilität (Art. 20 DSGVO)",
                "objection": "Widerspruchsrecht (Art. 21 DSGVO)"
            },
            "cookies": {
                "necessary": "Session-Cookies für Login-Funktionalität",
                "analytics": "Google Analytics (nur mit Einwilligung)",
                "marketing": "Marketing-Cookies (nur mit Einwilligung)"
            },
            "third_party_services": {
                "google": "Google OAuth für Login (nur mit Einwilligung)",
                "microsoft": "Microsoft OAuth für Login (nur mit Einwilligung)",
                "email": "E-Mail-Versand über SMTP-Server"
            }
        }
    }
    
    return privacy_policy


@router.get("/terms-of-service")
async def get_terms_of_service():
    """Gibt die aktuellen AGB zurück"""
    
    terms = {
        "version": "2.0",
        "last_updated": "2024-01-15",
        "title": "Allgemeine Geschäftsbedingungen für BuildWise",
        "content": {
            "service_description": "BuildWise ist eine Plattform für Bauprojektmanagement",
            "user_obligations": [
                "Wahrung der Vertraulichkeit von Zugangsdaten",
                "Sofortige Meldung von Sicherheitsvorfällen",
                "Einhaltung der Nutzungsbedingungen"
            ],
            "liability": {
                "limitation": "Haftung beschränkt auf Vorsatz und grobe Fahrlässigkeit",
                "data_loss": "Keine Haftung für Datenverlust bei höherer Gewalt"
            },
            "termination": {
                "user": "Jederzeit kündbar mit 30 Tagen Kündigungsfrist",
                "provider": "Bei Verstoß gegen AGB sofortige Kündigung möglich"
            }
        }
    }
    
    return terms


@router.get("/data-processing-register")
async def get_data_processing_register():
    """Gibt das Verarbeitungsverzeichnis zurück (Art. 30 DSGVO)"""
    
    register = {
        "version": "1.0",
        "last_updated": "2024-01-15",
        "data_processing_activities": [
            {
                "activity": "Benutzerregistrierung und -verwaltung",
                "purpose": "Bereitstellung der Plattform",
                "legal_basis": "Art. 6 Abs. 1 lit. b) DSGVO",
                "data_categories": ["Name", "E-Mail", "Passwort-Hash", "Einwilligungen"],
                "recipients": ["Intern", "E-Mail-Provider"],
                "retention_period": "7 Jahre",
                "security_measures": ["Verschlüsselung", "Access Control", "Audit-Logging"]
            },
            {
                "activity": "Social-Login Integration",
                "purpose": "Vereinfachte Anmeldung",
                "legal_basis": "Art. 6 Abs. 1 lit. a) DSGVO",
                "data_categories": ["OAuth-Tokens", "Social-Profile-Daten"],
                "recipients": ["Google", "Microsoft"],
                "retention_period": "7 Jahre",
                "security_measures": ["Token-Verschlüsselung", "Secure OAuth-Flow"]
            },
            {
                "activity": "Projektmanagement",
                "purpose": "Bauprojekt-Verwaltung",
                "legal_basis": "Art. 6 Abs. 1 lit. b) DSGVO",
                "data_categories": ["Projektdaten", "Dokumente", "Nachrichten"],
                "recipients": ["Projektbeteiligte"],
                "retention_period": "10 Jahre",
                "security_measures": ["Projekt-spezifische Berechtigungen", "Verschlüsselung"]
            }
        ]
    }
    
    return register 