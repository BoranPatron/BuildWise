from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select, func, and_, extract
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from datetime import datetime, date, timedelta
import calendar

from ..core.database import get_db
from ..models.cost_position import CostPosition
from ..models.milestone import Milestone
from ..models.project import Project
from ..api.deps import get_current_user
from ..models.user import User
from ..services.finance_analytics_service import FinanceAnalyticsService

router = APIRouter(prefix="/finance-analytics", tags=["Finance Analytics"])


@router.get("/project/{project_id}/costs-by-phase")
async def get_costs_by_construction_phase(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Holt Kostenverteilung nach Bauphasen für ein Projekt (Legacy-Funktion)"""
    
    # Prüfe Projektzugriff
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    
    # Da wir jetzt einfache CostPosition für Rechnungen haben,
    # geben wir leere Daten zurück für die Abwärtskompatibilität
    return {
        "project_id": project_id,
        "project_name": project.name,
        "phases": [],
        "total_cost_positions": 0,
        "total_amount": 0.0,
        "total_paid": 0.0,
        "total_remaining": 0.0
    }


@router.get("/project/{project_id}/costs-over-time")
async def get_costs_over_time(
    project_id: int,
    period: str = "monthly",  # monthly, weekly, quarterly
    months: int = 12,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Holt Kostenentwicklung über die Zeit (Legacy-Funktion)"""
    
    # Prüfe Projektzugriff
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    
    # Da wir jetzt einfache CostPosition für Rechnungen haben,
    # geben wir leere Daten zurück für die Abwärtskompatibilität
    return {
        "project_id": project_id,
        "project_name": project.name,
        "period": period,
        "months": months,
        "data": []
    }


@router.get("/project/{project_id}/costs-by-category")
async def get_costs_by_category(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Holt Kostenverteilung nach Kategorien (Legacy-Funktion)"""
    
    # Prüfe Projektzugriff
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    
    # Da wir jetzt einfache CostPosition für Rechnungen haben,
    # geben wir leere Daten zurück für die Abwärtskompatibilität
    return {
        "project_id": project_id,
        "project_name": project.name,
        "categories": [],
        "total_cost_positions": 0,
        "total_amount": 0.0
    }


@router.get("/project/{project_id}/costs-by-status")
async def get_costs_by_status(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Holt Kostenverteilung nach Status (Legacy-Funktion)"""
    
    # Prüfe Projektzugriff
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    
    # Da wir jetzt einfache CostPosition für Rechnungen haben,
    # geben wir leere Daten zurück für die Abwärtskompatibilität
    return {
        "project_id": project_id,
        "project_name": project.name,
        "statuses": [],
        "total_cost_positions": 0,
        "total_amount": 0.0
    }


@router.get("/project/{project_id}/milestone-costs")
async def get_milestone_costs(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Holt Kostenverteilung nach Meilensteinen (Legacy-Funktion)"""
    
    # Prüfe Projektzugriff
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    
    # Da wir jetzt einfache CostPosition für Rechnungen haben,
    # geben wir leere Daten zurück für die Abwärtskompatibilität
    return {
        "project_id": project_id,
        "project_name": project.name,
        "milestones": [],
        "total_cost_positions": 0,
        "total_amount": 0.0
    }


@router.get("/project/{project_id}/payment-timeline")
async def get_payment_timeline(
    project_id: int,
    months: int = 6,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Holt Zahlungszeitlinie (Legacy-Funktion)"""
    
    # Prüfe Projektzugriff
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    
    # Da wir jetzt einfache CostPosition für Rechnungen haben,
    # geben wir leere Daten zurück für die Abwärtskompatibilität
    return {
        "project_id": project_id,
        "project_name": project.name,
        "months": months,
        "timeline": []
    }


@router.get("/project/{project_id}/summary")
async def get_finance_summary(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Holt Finanzzusammenfassung (Legacy-Funktion)"""
    
    # Prüfe Projektzugriff
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    
    # Da wir jetzt einfache CostPosition für Rechnungen haben,
    # geben wir leere Daten zurück für die Abwärtskompatibilität
    return {
        "project_id": project_id,
        "project_name": project.name,
        "total_cost_positions": 0,
        "total_amount": 0.0,
        "total_paid": 0.0,
        "total_remaining": 0.0,
        "completion_percentage": 0.0
    }


@router.get("/project/{project_id}/expense-analytics")
async def get_expense_analytics_by_phase(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Holt Ausgabenanalysen nach Phasen (Legacy-Funktion)"""
    
    # Prüfe Projektzugriff
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    
    # Da wir jetzt einfache CostPosition für Rechnungen haben,
    # geben wir leere Daten zurück für die Abwärtskompatibilität
    return {
        "project_id": project_id,
        "project_name": project.name,
        "phases": []
    }


@router.get("/project/{project_id}/comprehensive")
async def get_comprehensive_finance_analytics(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Holt umfassende Finanzanalysen (Legacy-Funktion)"""
    
    # Prüfe Projektzugriff
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    
    # Da wir jetzt einfache CostPosition für Rechnungen haben,
    # geben wir leere Daten zurück für die Abwärtskompatibilität
    return {
        "project_id": project_id,
        "project_name": project.name,
        "summary": {
            "total_cost_positions": 0,
            "total_amount": 0.0,
            "total_paid": 0.0,
            "total_remaining": 0.0
        },
        "phases": [],
        "categories": [],
        "statuses": [],
        "milestones": []
    }


@router.get("/project/{project_id}/expense-trends")
async def get_expense_trends_by_phase(
    project_id: int,
    months: int = 6,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Holt Ausgabentrends nach Phasen (Legacy-Funktion)"""
    
    # Prüfe Projektzugriff
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    
    # Da wir jetzt einfache CostPosition für Rechnungen haben,
    # geben wir leere Daten zurück für die Abwärtskompatibilität
    return {
        "project_id": project_id,
        "project_name": project.name,
        "months": months,
        "trends": []
    }


@router.get("/project/{project_id}/phase-comparison")
async def get_phase_comparison_analytics(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Holt Phasenvergleichsanalysen (Legacy-Funktion)"""
    
    # Prüfe Projektzugriff
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    
    # Da wir jetzt einfache CostPosition für Rechnungen haben,
    # geben wir leere Daten zurück für die Abwärtskompatibilität
    return {
        "project_id": project_id,
        "project_name": project.name,
        "comparisons": []
    } 