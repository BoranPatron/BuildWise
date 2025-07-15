from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..api.deps import get_current_user
from ..models import User, MessageType
from ..schemas.message import MessageCreate, MessageRead, MessageSummary, ChatRoom
from ..services.message_service import (
    create_message, get_message_by_id, get_messages_for_project,
    update_message, delete_message, mark_message_as_read,
    get_unread_message_count, get_total_unread_count
)

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("/", response_model=MessageRead, status_code=status.HTTP_201_CREATED)
async def create_new_message(
    message_in: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    message = await create_message(db, message_in, current_user.id)
    return message


@router.get("/project/{project_id}", response_model=ChatRoom)
async def read_project_messages(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Holt alle Nachrichten für ein Projekt"""
    messages = await get_messages_for_project(db, project_id)
    unread_count = await get_unread_message_count(db, project_id, current_user.id)
    
    return ChatRoom(
        project_id=project_id,
        messages=messages,
        unread_count=unread_count
    )


@router.get("/{message_id}", response_model=MessageRead)
async def read_message(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    message = await get_message_by_id(db, message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nachricht nicht gefunden"
        )
    
    # Markiere als gelesen
    await mark_message_as_read(db, message_id, current_user.id)
    
    return message


@router.put("/{message_id}", response_model=MessageRead)
async def update_message_endpoint(
    message_id: int,
    message_update: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    message = await get_message_by_id(db, message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nachricht nicht gefunden"
        )
    
    # Nur der Absender kann seine Nachricht bearbeiten
    if message.sender_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für diese Nachricht"
        )
    
    updated_message = await update_message(db, message_id, message_update)
    return updated_message


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message_endpoint(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    message = await get_message_by_id(db, message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nachricht nicht gefunden"
        )
    
    # Nur der Absender kann seine Nachricht löschen
    if message.sender_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für diese Nachricht"
        )
    
    success = await delete_message(db, message_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nachricht konnte nicht gelöscht werden"
        )
    
    return None


@router.post("/{message_id}/read", status_code=status.HTTP_200_OK)
async def mark_message_read_endpoint(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Markiert eine Nachricht als gelesen"""
    message = await get_message_by_id(db, message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nachricht nicht gefunden"
        )
    
    await mark_message_as_read(db, message_id, current_user.id)
    return {"message": "Nachricht als gelesen markiert"}


@router.get("/unread/count")
async def get_unread_count_endpoint(
    project_id: int = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Holt die Anzahl ungelesener Nachrichten"""
    if project_id:
        count = await get_unread_message_count(db, project_id, current_user.id)
    else:
        # Gesamte ungelesene Nachrichten
        count = await get_total_unread_count(db, current_user.id)
    
    return {"unread_count": count} 