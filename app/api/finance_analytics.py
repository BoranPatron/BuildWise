from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select, func, and_, extract
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from datetime import datetime, date, timedelta
import calendar

from ..core.database import get_db
from ..models.cost_position import CostPosition, CostCategory, CostStatus
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
    """Holt Kostenverteilung nach Bauphasen für ein Projekt"""
    
    # Prüfe Projektzugriff
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    
    # Hole Kostenpositionen nach Bauphasen gruppiert
    result = await db.execute(
        select(
            CostPosition.construction_phase,
            func.count(CostPosition.id).label('count'),
            func.sum(CostPosition.amount).label('total_amount'),
            func.sum(CostPosition.paid_amount).label('total_paid'),
            func.avg(CostPosition.progress_percentage).label('avg_progress')
        )
        .where(CostPosition.project_id == project_id)
        .group_by(CostPosition.construction_phase)
        .order_by(CostPosition.construction_phase)
    )
    
    phases_data = []
    for row in result:
        if row.construction_phase:  # Nur Phasen mit Daten
            phases_data.append({
                "phase": row.construction_phase,
                "count": int(row.count),
                "total_amount": float(row.total_amount or 0),
                "total_paid": float(row.total_paid or 0),
                "remaining_amount": float((row.total_amount or 0) - (row.total_paid or 0)),
                "avg_progress": round(float(row.avg_progress or 0), 1),
                "completion_percentage": round((row.total_paid or 0) / (row.total_amount or 1) * 100, 1)
            })
    
    return {
        "project_id": project_id,
        "project_name": project.name,
        "phases": phases_data,
        "total_cost_positions": sum(p["count"] for p in phases_data),
        "total_amount": sum(p["total_amount"] for p in phases_data),
        "total_paid": sum(p["total_paid"] for p in phases_data),
        "total_remaining": sum(p["remaining_amount"] for p in phases_data)
    }


@router.get("/project/{project_id}/costs-over-time")
async def get_costs_over_time(
    project_id: int,
    period: str = "monthly",  # monthly, weekly, quarterly
    months: int = 12,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Holt Kostenentwicklung über die Zeit"""
    
    # Prüfe Projektzugriff
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    
    # Berechne Zeitraum
    end_date = datetime.now()
    if period == "monthly":
        start_date = end_date - timedelta(days=months * 30)
        group_by = extract('month', CostPosition.created_at)
        year_group = extract('year', CostPosition.created_at)
    elif period == "weekly":
        start_date = end_date - timedelta(weeks=months * 4)
        group_by = extract('week', CostPosition.created_at)
        year_group = extract('year', CostPosition.created_at)
    else:  # quarterly
        start_date = end_date - timedelta(days=months * 90)
        group_by = extract('quarter', CostPosition.created_at)
        year_group = extract('year', CostPosition.created_at)
    
    # Hole Kostenpositionen über Zeit gruppiert
    result = await db.execute(
        select(
            year_group.label('year'),
            group_by.label('period'),
            func.count(CostPosition.id).label('count'),
            func.sum(CostPosition.amount).label('total_amount'),
            func.sum(CostPosition.paid_amount).label('total_paid'),
            func.avg(CostPosition.progress_percentage).label('avg_progress')
        )
        .where(
            and_(
                CostPosition.project_id == project_id,
                CostPosition.created_at >= start_date
            )
        )
        .group_by(year_group, group_by)
        .order_by(year_group, group_by)
    )
    
    time_data = []
    for row in result:
        time_data.append({
            "year": int(row.year),
            "period": int(row.period),
            "count": int(row.count),
            "total_amount": float(row.total_amount or 0),
            "total_paid": float(row.total_paid or 0),
            "remaining_amount": float((row.total_amount or 0) - (row.total_paid or 0)),
            "avg_progress": round(float(row.avg_progress or 0), 1)
        })
    
    return {
        "project_id": project_id,
        "project_name": project.name,
        "period": period,
        "time_data": time_data
    }


@router.get("/project/{project_id}/costs-by-category")
async def get_costs_by_category(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Holt Kostenverteilung nach Kategorien"""
    
    # Prüfe Projektzugriff
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    
    # Hole Kostenpositionen nach Kategorien gruppiert
    result = await db.execute(
        select(
            CostPosition.category,
            func.count(CostPosition.id).label('count'),
            func.sum(CostPosition.amount).label('total_amount'),
            func.sum(CostPosition.paid_amount).label('total_paid'),
            func.avg(CostPosition.progress_percentage).label('avg_progress')
        )
        .where(CostPosition.project_id == project_id)
        .group_by(CostPosition.category)
        .order_by(func.sum(CostPosition.amount).desc())
    )
    
    categories_data = []
    for row in result:
        categories_data.append({
            "category": row.category.value,
            "category_name": row.category.value.replace('_', ' ').title(),
            "count": int(row.count),
            "total_amount": float(row.total_amount or 0),
            "total_paid": float(row.total_paid or 0),
            "remaining_amount": float((row.total_amount or 0) - (row.total_paid or 0)),
            "avg_progress": round(float(row.avg_progress or 0), 1),
            "percentage_of_total": 0  # Wird später berechnet
        })
    
    # Berechne Prozentsätze
    total_amount = sum(c["total_amount"] for c in categories_data)
    for category in categories_data:
        if total_amount > 0:
            category["percentage_of_total"] = round((category["total_amount"] / total_amount) * 100, 1)
    
    return {
        "project_id": project_id,
        "project_name": project.name,
        "categories": categories_data,
        "total_amount": total_amount
    }


@router.get("/project/{project_id}/costs-by-status")
async def get_costs_by_status(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Holt Kostenverteilung nach Status"""
    
    # Prüfe Projektzugriff
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    
    # Hole Kostenpositionen nach Status gruppiert
    result = await db.execute(
        select(
            CostPosition.status,
            func.count(CostPosition.id).label('count'),
            func.sum(CostPosition.amount).label('total_amount'),
            func.sum(CostPosition.paid_amount).label('total_paid'),
            func.avg(CostPosition.progress_percentage).label('avg_progress')
        )
        .where(CostPosition.project_id == project_id)
        .group_by(CostPosition.status)
        .order_by(func.sum(CostPosition.amount).desc())
    )
    
    status_data = []
    for row in result:
        status_data.append({
            "status": row.status.value,
            "status_name": row.status.value.replace('_', ' ').title(),
            "count": int(row.count),
            "total_amount": float(row.total_amount or 0),
            "total_paid": float(row.total_paid or 0),
            "remaining_amount": float((row.total_amount or 0) - (row.total_paid or 0)),
            "avg_progress": round(float(row.avg_progress or 0), 1)
        })
    
    return {
        "project_id": project_id,
        "project_name": project.name,
        "statuses": status_data
    }


@router.get("/project/{project_id}/milestone-costs")
async def get_milestone_costs(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Holt Kostenverteilung nach Gewerken (Milestones)"""
    
    # Prüfe Projektzugriff
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    
    # Hole Kostenpositionen nach Gewerken gruppiert
    result = await db.execute(
        select(
            Milestone.id,
            Milestone.title,
            Milestone.construction_phase,
            func.count(CostPosition.id).label('cost_count'),
            func.sum(CostPosition.amount).label('total_amount'),
            func.sum(CostPosition.paid_amount).label('total_paid'),
            func.avg(CostPosition.progress_percentage).label('avg_progress')
        )
        .outerjoin(CostPosition, Milestone.id == CostPosition.milestone_id)
        .where(Milestone.project_id == project_id)
        .group_by(Milestone.id, Milestone.title, Milestone.construction_phase)
        .order_by(func.sum(CostPosition.amount).desc())
    )
    
    milestones_data = []
    for row in result:
        milestones_data.append({
            "milestone_id": row.id,
            "milestone_title": row.title,
            "construction_phase": row.construction_phase,
            "cost_count": int(row.cost_count or 0),
            "total_amount": float(row.total_amount or 0),
            "total_paid": float(row.total_paid or 0),
            "remaining_amount": float((row.total_amount or 0) - (row.total_paid or 0)),
            "avg_progress": round(float(row.avg_progress or 0), 1)
        })
    
    return {
        "project_id": project_id,
        "project_name": project.name,
        "milestones": milestones_data
    }


@router.get("/project/{project_id}/payment-timeline")
async def get_payment_timeline(
    project_id: int,
    months: int = 6,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Holt Zahlungszeitplan für ein Projekt"""
    
    # Prüfe Projektzugriff
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    
    # Hole Kostenpositionen mit Zahlungsdaten
    result = await db.execute(
        select(
            CostPosition.id,
            CostPosition.title,
            CostPosition.amount,
            CostPosition.paid_amount,
            CostPosition.start_date,
            CostPosition.completion_date,
            CostPosition.construction_phase,
            CostPosition.status
        )
        .where(CostPosition.project_id == project_id)
        .order_by(CostPosition.start_date)
    )
    
    timeline_data = []
    for row in result:
        if row.start_date:
            timeline_data.append({
                "cost_position_id": row.id,
                "title": row.title,
                "amount": float(row.amount),
                "paid_amount": float(row.paid_amount or 0),
                "remaining_amount": float(row.amount - (row.paid_amount or 0)),
                "start_date": row.start_date.isoformat() if row.start_date else None,
                "completion_date": row.completion_date.isoformat() if row.completion_date else None,
                "construction_phase": row.construction_phase,
                "status": row.status.value
            })
    
    return {
        "project_id": project_id,
        "project_name": project.name,
        "timeline": timeline_data
    }


@router.get("/project/{project_id}/summary")
async def get_finance_summary(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Holt eine Zusammenfassung aller Finanzdaten für ein Projekt"""
    
    # Prüfe Projektzugriff
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    
    # Hole Gesamtstatistiken
    stats_result = await db.execute(
        select(
            func.count(CostPosition.id).label('total_count'),
            func.sum(CostPosition.amount).label('total_amount'),
            func.sum(CostPosition.paid_amount).label('total_paid'),
            func.avg(CostPosition.progress_percentage).label('avg_progress'),
            func.count(CostPosition.id).filter(CostPosition.status == CostStatus.COMPLETED).label('completed_count'),
            func.count(CostPosition.id).filter(CostPosition.status == CostStatus.ACTIVE).label('active_count')
        )
        .where(CostPosition.project_id == project_id)
    )
    
    stats = stats_result.first()
    
    # Hole Daten für verschiedene Diagramme
    phases_data = await get_costs_by_construction_phase(project_id, db, current_user)
    categories_data = await get_costs_by_category(project_id, db, current_user)
    status_data = await get_costs_by_status(project_id, db, current_user)
    
    return {
        "project_id": project_id,
        "project_name": project.name,
        "summary": {
            "total_cost_positions": int(stats.total_count or 0),
            "total_amount": float(stats.total_amount or 0),
            "total_paid": float(stats.total_paid or 0),
            "total_remaining": float((stats.total_amount or 0) - (stats.total_paid or 0)),
            "avg_progress": round(float(stats.avg_progress or 0), 1),
            "completed_count": int(stats.completed_count or 0),
            "active_count": int(stats.active_count or 0),
            "completion_percentage": round((stats.total_paid or 0) / (stats.total_amount or 1) * 100, 1)
        },
        "phases": phases_data,
        "categories": categories_data,
        "statuses": status_data
    } 

@router.get("/project/{project_id}/expense-analytics")
async def get_expense_analytics_by_phase(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lädt Ausgaben-Analytics nach Bauphasen"""
    
    try:
        analytics = await FinanceAnalyticsService.get_expense_analytics_by_phase(
            db=db,
            project_id=project_id
        )
        
        return analytics
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Laden der Ausgaben-Analytics: {str(e)}"
        )

@router.get("/project/{project_id}/comprehensive")
async def get_comprehensive_finance_analytics(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lädt umfassende Finanz-Analytics mit allen Komponenten"""
    
    try:
        analytics = await FinanceAnalyticsService.get_comprehensive_finance_analytics(
            db=db,
            project_id=project_id
        )
        
        return analytics
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Laden der Finanz-Analytics: {str(e)}"
        )

@router.get("/project/{project_id}/expense-trends")
async def get_expense_trends_by_phase(
    project_id: int,
    months: int = 6,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lädt Ausgaben-Trends nach Bauphasen über Zeit"""
    
    try:
        trends = await FinanceAnalyticsService.get_expense_trends_by_phase(
            db=db,
            project_id=project_id,
            months=months
        )
        
        return trends
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Laden der Ausgaben-Trends: {str(e)}"
        )

@router.get("/project/{project_id}/phase-comparison")
async def get_phase_comparison_analytics(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lädt Vergleichs-Analytics zwischen Bauphasen"""
    
    try:
        comparison = await FinanceAnalyticsService.get_phase_comparison_analytics(
            db=db,
            project_id=project_id
        )
        
        return comparison
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Laden der Phasen-Vergleichs-Analytics: {str(e)}"
        ) 