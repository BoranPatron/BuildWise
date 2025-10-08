from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..api.deps import get_current_user
from ..models import User
from ..schemas.audit_log import AuditLogRead
from ..services.audit_service import (
    get_audit_logs_for_user, get_audit_logs_for_project, get_all_audit_logs
)

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/user", response_model=List[AuditLogRead])
async def read_user_audit_logs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Holt Audit-Logs für den aktuellen Benutzer"""
    print(f"[INFO] API: Lade Audit-Logs für User {current_user.id}")
    
    audit_logs = await get_audit_logs_for_user(db, current_user.id)
    print(f"[SUCCESS] API: {len(audit_logs)} Audit-Logs zurückgegeben")
    return audit_logs


@router.get("/project/{project_id}", response_model=List[AuditLogRead])
async def read_project_audit_logs(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Holt Audit-Logs für ein bestimmtes Projekt"""
    print(f"[INFO] API: Lade Audit-Logs für Projekt {project_id}")
    
    audit_logs = await get_audit_logs_for_project(db, project_id)
    print(f"[SUCCESS] API: {len(audit_logs)} Audit-Logs für Projekt {project_id} zurückgegeben")
    return audit_logs


@router.get("/all", response_model=List[AuditLogRead])
async def read_all_audit_logs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Holt alle Audit-Logs (nur für Admin)"""
    print(f"[INFO] API: Lade alle Audit-Logs für Admin {current_user.id}")
    
    # Prüfe Admin-Berechtigung
    if current_user.email != "admin@buildwise.de":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nur Administratoren können alle Audit-Logs einsehen"
        )
    
    audit_logs = await get_all_audit_logs(db)
    print(f"[SUCCESS] API: {len(audit_logs)} Audit-Logs insgesamt zurückgegeben")
    return audit_logs 