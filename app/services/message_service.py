from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from typing import List, Optional
from datetime import datetime

from ..models import Message, MessageType
from ..schemas.message import MessageCreate


async def create_message(db: AsyncSession, message_in: MessageCreate, sender_id: int) -> Message:
    message = Message(
        project_id=message_in.project_id,
        sender_id=sender_id,
        recipient_id=message_in.recipient_id,
        message_type=message_in.message_type,
        content=message_in.content,
        document_id=message_in.document_id
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def get_message_by_id(db: AsyncSession, message_id: int) -> Message | None:
    result = await db.execute(select(Message).where(Message.id == message_id))
    return result.scalars().first()


async def get_messages_for_project(db: AsyncSession, project_id: int) -> List[Message]:
    result = await db.execute(
        select(Message)
        .where(Message.project_id == project_id)
        .order_by(Message.created_at.desc())
    )
    return list(result.scalars().all())


async def update_message(db: AsyncSession, message_id: int, message_update: dict) -> Message | None:
    message = await get_message_by_id(db, message_id)
    if not message:
        return None
    
    if message_update:
        await db.execute(
            update(Message)
            .where(Message.id == message_id)
            .values(**message_update, updated_at=datetime.utcnow())
        )
        await db.commit()
        await db.refresh(message)
    
    return message


async def delete_message(db: AsyncSession, message_id: int) -> bool:
    message = await get_message_by_id(db, message_id)
    if not message:
        return False
    
    await db.delete(message)
    await db.commit()
    return True


async def mark_message_as_read(db: AsyncSession, message_id: int, user_id: int) -> bool:
    """Markiert eine Nachricht als gelesen"""
    message = await get_message_by_id(db, message_id)
    if not message:
        return False
    
    # Prüfe ob der Benutzer der Empfänger ist
    if message.recipient_id and message.recipient_id != user_id:
        return False
    
    await db.execute(
        update(Message)
        .where(Message.id == message_id)
        .values(is_read=True, read_at=datetime.utcnow(), updated_at=datetime.utcnow())
    )
    await db.commit()
    return True


async def get_unread_message_count(db: AsyncSession, project_id: int, user_id: int) -> int:
    """Holt die Anzahl ungelesener Nachrichten für einen Benutzer in einem Projekt"""
    result = await db.execute(
        select(func.count(Message.id))
        .where(
            Message.project_id == project_id,
            Message.recipient_id == user_id,
            Message.is_read == False
        )
    )
    return result.scalar() or 0


async def get_total_unread_count(db: AsyncSession, user_id: int) -> int:
    """Holt die Gesamtanzahl ungelesener Nachrichten für einen Benutzer"""
    result = await db.execute(
        select(func.count(Message.id))
        .where(
            Message.recipient_id == user_id,
            Message.is_read == False
        )
    )
    return result.scalar() or 0 