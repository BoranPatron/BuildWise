from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime

from ..models.audit_log import AuditLog
from ..schemas.audit_log import AuditLogCreate, AuditLogRead


async def create_audit_log(db: AsyncSession, audit_data: AuditLogCreate) -> AuditLog:
    """Erstellt einen neuen Audit-Log-Eintrag"""
    print(f"[INFO] Erstelle Audit-Log: {audit_data.action}")
    print(f"[INFO] Audit-Daten: {audit_data.dict()}")
    
    audit_log = AuditLog(**audit_data.dict())
    db.add(audit_log)
    
    try:
        await db.commit()
        print(f"[SUCCESS] Audit-Log erfolgreich in Datenbank gespeichert")
        await db.refresh(audit_log)
        print(f"[INFO] Audit-Log-ID: {audit_log.id}")
        return audit_log
    except Exception as e:
        print(f"[ERROR] Fehler beim Speichern des Audit-Logs: {e}")
        await db.rollback()
        raise


async def get_audit_logs_for_user(db: AsyncSession, user_id: int, limit: int = 100) -> List[AuditLog]:
    """Holt Audit-Logs für einen bestimmten Benutzer"""
    print(f"[INFO] Lade Audit-Logs für User {user_id}")
    
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.user_id == user_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    audit_logs = list(result.scalars().all())
    
    print(f"[SUCCESS] {len(audit_logs)} Audit-Logs für User {user_id} gefunden")
    return audit_logs


async def get_audit_logs_for_project(db: AsyncSession, project_id: int, limit: int = 100) -> List[AuditLog]:
    """Holt Audit-Logs für ein bestimmtes Projekt"""
    print(f"[INFO] Lade Audit-Logs für Projekt {project_id}")
    
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.project_id == project_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    audit_logs = list(result.scalars().all())
    
    print(f"[SUCCESS] {len(audit_logs)} Audit-Logs für Projekt {project_id} gefunden")
    return audit_logs


async def get_all_audit_logs(db: AsyncSession, limit: int = 1000) -> List[AuditLog]:
    """Holt alle Audit-Logs (für Admin)"""
    print(f"[INFO] Lade alle Audit-Logs")
    
    result = await db.execute(
        select(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    audit_logs = list(result.scalars().all())
    
    print(f"[SUCCESS] {len(audit_logs)} Audit-Logs insgesamt gefunden")
    return audit_logs 