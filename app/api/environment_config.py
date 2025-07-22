"""
Environment Configuration API
============================

API-Endpoints für die Verwaltung der BuildWise Environment-Konfiguration.
Ermöglicht elegante Umschaltung zwischen Beta- und Production-Modi.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.core.config import settings, EnvironmentMode
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/v1/environment", tags=["environment"])


class EnvironmentStatus(BaseModel):
    """Response-Modell für Environment-Status."""
    current_mode: str
    fee_percentage: float
    is_beta: bool
    is_production: bool
    last_switch: Optional[str] = None


class EnvironmentSwitchRequest(BaseModel):
    """Request-Modell für Environment-Wechsel."""
    target_mode: str
    confirm: bool = False


@router.get("/status", response_model=EnvironmentStatus)
async def get_environment_status(current_user: User = Depends(get_current_user)):
    """
    Gibt den aktuellen Environment-Status zurück.
    
    Nur für Administratoren verfügbar.
    """
    # Prüfe Admin-Berechtigung
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403, 
            detail="Nur Administratoren können den Environment-Status abfragen"
        )
    
    return EnvironmentStatus(
        current_mode=settings.environment_mode.value,
        fee_percentage=settings.get_current_fee_percentage(),
        is_beta=settings.is_beta_mode(),
        is_production=settings.is_production_mode(),
        last_switch=getattr(settings, 'last_switch', None)
    )


@router.post("/switch")
async def switch_environment(
    request: EnvironmentSwitchRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Wechselt den Environment-Modus.
    
    Nur für Administratoren verfügbar.
    """
    # Prüfe Admin-Berechtigung
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403, 
            detail="Nur Administratoren können den Environment-Modus wechseln"
        )
    
    # Validiere Target-Modus
    try:
        target_mode = EnvironmentMode(request.target_mode.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Ungültiger Modus: {request.target_mode}. Verfügbar: beta, production"
        )
    
    # Prüfe ob Wechsel notwendig ist
    if settings.environment_mode == target_mode:
        return {
            "message": f"System ist bereits im {target_mode.value}-Modus",
            "current_mode": settings.environment_mode.value,
            "fee_percentage": settings.get_current_fee_percentage()
        }
    
    # Bestätigung für Production-Wechsel
    if target_mode == EnvironmentMode.PRODUCTION and not request.confirm:
        raise HTTPException(
            status_code=400,
            detail="Production-Wechsel erfordert explizite Bestätigung (confirm=true)"
        )
    
    # Führe Wechsel durch
    try:
        settings.switch_environment(target_mode)
        settings.last_switch = datetime.now().isoformat()
        
        return {
            "message": f"Erfolgreich zu {target_mode.value}-Modus gewechselt",
            "current_mode": settings.environment_mode.value,
            "fee_percentage": settings.get_current_fee_percentage(),
            "switch_timestamp": settings.last_switch
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Environment-Wechsel: {str(e)}"
        )


@router.get("/fee-config")
async def get_fee_configuration(current_user: User = Depends(get_current_user)):
    """
    Gibt die aktuelle Gebühren-Konfiguration zurück.
    
    Verfügbar für alle authentifizierten Benutzer.
    """
    return {
        "current_fee_percentage": settings.get_current_fee_percentage(),
        "environment_mode": settings.environment_mode.value,
        "is_beta_mode": settings.is_beta_mode(),
        "is_production_mode": settings.is_production_mode()
    }


@router.get("/info")
async def get_environment_info():
    """
    Gibt allgemeine Informationen über die Environment-Konfiguration zurück.
    
    Öffentlich verfügbar (keine Authentifizierung erforderlich).
    """
    return {
        "application": "BuildWise",
        "environment_mode": settings.environment_mode.value,
        "fee_percentage": settings.get_current_fee_percentage(),
        "features": {
            "beta_mode": {
                "description": "Test- und Entwicklungsphase",
                "fee_percentage": 0.0,
                "features": ["Keine Gebühren", "Vollständige Funktionalität", "Test-Daten"]
            },
            "production_mode": {
                "description": "Live-Betrieb",
                "fee_percentage": 4.7,
                "features": ["Gebühren von 4.7%", "Vollständige Funktionalität", "Live-Daten"]
            }
        }
    } 