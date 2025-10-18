from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from ..core.database import get_db
from ..api.deps import get_current_user
from ..models.user import User
from ..models.notification import Notification
from ..schemas.notification import (
    NotificationCreate, NotificationUpdate, NotificationRead, 
    NotificationStats, NotificationBulkAction
)
from ..services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("/", response_model=List[NotificationRead])
async def get_notifications(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    unread_only: bool = Query(False),
    unacknowledged_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Holt Benachrichtigungen für den aktuellen Benutzer"""
    notifications = await NotificationService.get_user_notifications(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        unread_only=unread_only,
        unacknowledged_only=unacknowledged_only
    )
    return notifications

@router.get("/stats", response_model=NotificationStats)
async def get_notification_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Holt Statistiken über Benachrichtigungen des aktuellen Benutzers"""
    stats = await NotificationService.get_notification_stats(
        db=db,
        user_id=current_user.id
    )
    return stats

@router.patch("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Markiert eine Benachrichtigung als gelesen"""
    notification = await NotificationService.mark_notification_as_read(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id
    )
    
    if not notification:
        raise HTTPException(status_code=404, detail="Benachrichtigung nicht gefunden")
    
    return {"message": "Benachrichtigung als gelesen markiert", "notification_id": notification_id}

@router.patch("/{notification_id}/acknowledge")
async def acknowledge_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Quittiert eine Benachrichtigung"""
    notification = await NotificationService.acknowledge_notification(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id
    )
    
    if not notification:
        raise HTTPException(status_code=404, detail="Benachrichtigung nicht gefunden")
    
    return {"message": "Benachrichtigung quittiert", "notification_id": notification_id}

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Löscht eine spezifische Benachrichtigung"""
    success = await NotificationService.delete_notification(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Benachrichtigung nicht gefunden")
    
    return {"message": "Benachrichtigung gelöscht", "notification_id": notification_id}

@router.delete("/delete-all")
async def delete_all_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Löscht alle Benachrichtigungen des aktuellen Benutzers"""
    count = await NotificationService.delete_all_notifications(
        db=db,
        user_id=current_user.id
    )
    
    return {"message": f"{count} Benachrichtigungen gelöscht", "count": count}

@router.patch("/mark-all-read")
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Markiert alle Benachrichtigungen als gelesen"""
    count = await NotificationService.mark_all_as_read(
        db=db,
        user_id=current_user.id
    )
    
    return {"message": f"{count} Benachrichtigungen als gelesen markiert", "count": count}

@router.patch("/acknowledge-all")
async def acknowledge_all_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Quittiert alle Benachrichtigungen"""
    count = await NotificationService.acknowledge_all(
        db=db,
        user_id=current_user.id
    )
    
    return {"message": f"{count} Benachrichtigungen quittiert", "count": count}

@router.post("/bulk-action")
async def bulk_notification_action(
    action_data: NotificationBulkAction,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Führt Bulk-Aktionen auf Benachrichtigungen aus"""
    # Implementierung für Bulk-Aktionen
    # Hier könnte man verschiedene Aktionen wie mark_read, acknowledge, delete implementieren
    
    if action_data.action == "mark_read":
        # Implementiere Bulk Mark as Read
        pass
    elif action_data.action == "acknowledge":
        # Implementiere Bulk Acknowledge
        pass
    elif action_data.action == "delete":
        # Implementiere Bulk Delete
        pass
    
    return {"message": f"Bulk-Aktion '{action_data.action}' ausgeführt", "affected_count": len(action_data.notification_ids)}

# Admin-Endpunkte (nur für Administratoren)
@router.post("/", response_model=NotificationRead)
async def create_notification(
    notification_data: NotificationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Erstellt eine neue Benachrichtigung"""
    from ..models.notification import NotificationType
    
    # Erweiterte Berechtigung: 
    # - Admins können alle Benachrichtigungen erstellen
    # - Benutzer können Benachrichtigungen für sich selbst erstellen
    # - Bei quote_submitted, milestone_completed: Dienstleister können Benachrichtigungen für Bauträger erstellen
    allowed_types = [
        NotificationType.QUOTE_SUBMITTED,
        NotificationType.MILESTONE_COMPLETED,
        NotificationType.DEFECTS_RESOLVED
    ]
    
    if current_user.user_type not in ["admin", "superuser"]:
        if notification_data.recipient_id != current_user.id:
            # Erlaube bestimmte Benachrichtigungen zwischen Dienstleister und Bauträger
            if notification_data.type not in allowed_types:
                print(f"[ERROR] Notification type {notification_data.type} not allowed for user {current_user.id}")
                print(f"[ERROR] Allowed types: {[t.value for t in allowed_types]}")
                raise HTTPException(status_code=403, detail="Keine Berechtigung für diesen Benachrichtigungstyp")
        
    print(f"[NOTIFICATION] Creating notification: {notification_data.type} for user {notification_data.recipient_id} by {current_user.id}")
    
    notification = await NotificationService.create_notification(
        db=db,
        notification_data=notification_data
    )
    
    return notification

@router.delete("/cleanup")
async def cleanup_old_notifications(
    days_old: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Löscht alte Benachrichtigungen (nur für Administratoren)"""
    # Prüfe Admin-Berechtigung
    if current_user.user_type not in ["admin", "superuser"]:
        raise HTTPException(status_code=403, detail="Keine Berechtigung")
    
    count = await NotificationService.delete_old_notifications(
        db=db,
        days_old=days_old
    )
    
    return {"message": f"{count} alte Benachrichtigungen gelöscht", "count": count}
