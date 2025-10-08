"""
Notification Preferences API Endpoints
API für Benachrichtigungspräferenzen
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import json

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.notification_preference import NotificationPreference as NotificationPreferenceModel
from app.schemas.notification_preference import (
    NotificationPreference,
    NotificationPreferenceCreate,
    NotificationPreferenceUpdate,
    NotificationPreferenceToggle,
    NotificationPreferenceCategories
)
from app.services.notification_preference_service import NotificationPreferenceService


router = APIRouter(
    prefix="/notification-preferences",
    tags=["Notification Preferences"]
)


def _preference_to_dict(pref: NotificationPreferenceModel) -> dict:
    """Konvertiert Model zu Dict und parsed JSON-Felder"""
    return {
        "id": pref.id,
        "contact_id": pref.contact_id,
        "user_id": pref.user_id,
        "service_provider_id": pref.service_provider_id,
        "enabled": pref.enabled,
        "categories": json.loads(pref.categories) if isinstance(pref.categories, str) else pref.categories,
        "created_at": pref.created_at,
        "updated_at": pref.updated_at
    }


@router.post("", response_model=NotificationPreference, status_code=status.HTTP_201_CREATED)
async def upsert_notification_preference(
    preference_data: NotificationPreferenceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Erstellt oder aktualisiert eine Benachrichtigungspräferenz
    
    - **contact_id**: ID des Kontakts
    - **service_provider_id**: ID des Dienstleisters
    - **enabled**: Benachrichtigungen aktiviert
    - **categories**: Liste der Kategorien
    """
    try:
        service = NotificationPreferenceService(db)
        preference = await service.upsert_preference(preference_data, current_user.id)
        return _preference_to_dict(preference)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Speichern der Benachrichtigungspräferenz: {str(e)}"
        )


@router.get("/contact/{contact_id}", response_model=Optional[NotificationPreference])
async def get_notification_preference_by_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Holt die Benachrichtigungspräferenz für einen Kontakt
    
    - **contact_id**: ID des Kontakts
    
    Returns None wenn keine Präferenz existiert
    """
    service = NotificationPreferenceService(db)
    preference = await service.get_by_contact_id(contact_id, current_user.id)
    
    if not preference:
        return None
    
    return _preference_to_dict(preference)


@router.put("/{preference_id}/toggle", response_model=NotificationPreference)
async def toggle_notification_preference(
    preference_id: int,
    toggle_data: NotificationPreferenceToggle,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Schaltet Benachrichtigungen an/aus
    
    - **preference_id**: ID der Präferenz
    - **enabled**: Neuer Status
    """
    try:
        service = NotificationPreferenceService(db)
        preference = await service.toggle(preference_id, toggle_data.enabled, current_user.id)
        return _preference_to_dict(preference)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{preference_id}/categories", response_model=NotificationPreference)
async def update_notification_categories(
    preference_id: int,
    categories_data: NotificationPreferenceCategories,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Aktualisiert die Kategorien einer Präferenz
    
    - **preference_id**: ID der Präferenz
    - **categories**: Neue Liste der Kategorien
    """
    try:
        service = NotificationPreferenceService(db)
        preference = await service.update_categories(
            preference_id,
            categories_data.categories,
            current_user.id
        )
        return _preference_to_dict(preference)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{preference_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification_preference(
    preference_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Löscht eine Benachrichtigungspräferenz
    
    - **preference_id**: ID der Präferenz
    """
    try:
        service = NotificationPreferenceService(db)
        await service.delete(preference_id, current_user.id)
        return None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

