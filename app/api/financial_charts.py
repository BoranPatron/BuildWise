from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, extract, desc
from typing import List, Dict, Any
from datetime import datetime, date, timedelta
import calendar

from ..core.database import get_db
from ..models.cost_position import CostPosition
from ..models.invoice import Invoice, InvoiceStatus
from ..models.expense import Expense
from ..models.project import Project
from ..api.deps import get_current_user
from ..models.user import User

router = APIRouter(prefix="/financial-charts", tags=["Financial Charts"])

@router.get("/project/{project_id}/timeline-data")
async def get_financial_timeline_data(
    project_id: int,
    months: int = 12,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Holt zeitbasierte Finanzdaten für Timeline-Chart"""
    
    # Prüfe Projektzugriff
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    
    # Hole alle bezahlten Rechnungen für das Projekt
    invoices_result = await db.execute(
        select(Invoice)
        .where(
            and_(
                Invoice.project_id == project_id,
                Invoice.status == InvoiceStatus.PAID
            )
        )
        .order_by(Invoice.invoice_date)
    )
    invoices = invoices_result.scalars().all()
    
    # Hole alle Ausgaben für das Projekt
    expenses_result = await db.execute(
        select(Expense)
        .where(Expense.project_id == project_id)
        .order_by(Expense.date)
    )
    expenses = expenses_result.scalars().all()
    
    # Gruppiere Daten nach Monaten
    monthly_data = {}
    
    # Verarbeite Rechnungen
    for invoice in invoices:
        month_key = invoice.invoice_date.strftime('%Y-%m')
        if month_key not in monthly_data:
            monthly_data[month_key] = {
                'month': invoice.invoice_date.strftime('%b %Y'),
                'expenses': 0,
                'income': 0,
                'invoices_count': 0
            }
        monthly_data[month_key]['expenses'] += invoice.total_amount
        monthly_data[month_key]['invoices_count'] += 1
    
    # Verarbeite Ausgaben
    for expense in expenses:
        month_key = expense.date.strftime('%Y-%m')
        if month_key not in monthly_data:
            monthly_data[month_key] = {
                'month': expense.date.strftime('%b %Y'),
                'expenses': 0,
                'income': 0,
                'invoices_count': 0
            }
        monthly_data[month_key]['expenses'] += expense.amount
    
    # Sortiere nach Monaten und begrenze auf die letzten N Monate
    sorted_months = sorted(monthly_data.keys())[-months:]
    
    return {
        "project_id": project_id,
        "project_name": project.name,
        "months": months,
        "data": [
            {
                "month": monthly_data[month]['month'],
                "expenses": monthly_data[month]['expenses'],
                "income": monthly_data[month]['income'],
                "invoices_count": monthly_data[month]['invoices_count']
            }
            for month in sorted_months
        ]
    }

@router.get("/project/{project_id}/volume-data")
async def get_financial_volume_data(
    project_id: int,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Holt Volumendaten für Volume-Chart (Top Ausgaben)"""
    
    # Prüfe Projektzugriff
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    
    # Hole alle bezahlten Rechnungen mit Kostenpositionen
    invoices_result = await db.execute(
        select(Invoice, CostPosition)
        .join(CostPosition, Invoice.id == CostPosition.invoice_id)
        .where(
            and_(
                Invoice.project_id == project_id,
                Invoice.status == InvoiceStatus.PAID
            )
        )
        .order_by(desc(CostPosition.amount))
        .limit(limit)
    )
    invoice_costs = invoices_result.all()
    
    # Hole alle Ausgaben
    expenses_result = await db.execute(
        select(Expense)
        .where(Expense.project_id == project_id)
        .order_by(desc(Expense.amount))
        .limit(limit)
    )
    expenses = expenses_result.scalars().all()
    
    # Kombiniere und sortiere alle Ausgaben
    all_expenses = []
    
    # Verarbeite Rechnungs-Kostenpositionen
    for invoice, cost_position in invoice_costs:
        all_expenses.append({
            "description": cost_position.description,
            "amount": cost_position.amount,
            "category": cost_position.category,
            "type": "invoice",
            "date": invoice.invoice_date,
            "contractor": invoice.service_provider_id
        })
    
    # Verarbeite direkte Ausgaben
    for expense in expenses:
        all_expenses.append({
            "description": expense.title,
            "amount": expense.amount,
            "category": expense.category,
            "type": "expense",
            "date": expense.date,
            "contractor": None
        })
    
    # Sortiere nach Betrag und begrenze
    all_expenses.sort(key=lambda x: x['amount'], reverse=True)
    top_expenses = all_expenses[:limit]
    
    return {
        "project_id": project_id,
        "project_name": project.name,
        "limit": limit,
        "data": top_expenses
    }

@router.get("/project/{project_id}/category-data")
async def get_financial_category_data(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Holt Kategoriedaten für Category-Chart"""
    
    # Prüfe Projektzugriff
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    
    print(f"[DEBUG] Category data for project {project_id}: {project.name}")
    
    # Hole Kostenpositionen aus bezahlten Rechnungen
    cost_positions_result = await db.execute(
        select(CostPosition.category, func.sum(CostPosition.amount).label('total_amount'))
        .join(Invoice, CostPosition.invoice_id == Invoice.id)
        .where(
            and_(
                Invoice.project_id == project_id,
                Invoice.status == InvoiceStatus.PAID
            )
        )
        .group_by(CostPosition.category)
    )
    invoice_categories = cost_positions_result.all()
    print(f"[DEBUG] Invoice categories found: {len(invoice_categories)}")
    for cat in invoice_categories:
        print(f"[DEBUG] Invoice category: {cat.category} = {cat.total_amount}")
    
    # Hole direkte Kostenpositionen (ohne Rechnung)
    direct_cost_positions_result = await db.execute(
        select(CostPosition.category, func.sum(CostPosition.amount).label('total_amount'))
        .where(CostPosition.project_id == project_id)
        .group_by(CostPosition.category)
    )
    direct_cost_categories = direct_cost_positions_result.all()
    print(f"[DEBUG] Direct cost categories found: {len(direct_cost_categories)}")
    for cat in direct_cost_categories:
        print(f"[DEBUG] Direct cost category: {cat.category} = {cat.total_amount}")
    
    # Hole Ausgaben nach Kategorien
    expenses_result = await db.execute(
        select(Expense.category, func.sum(Expense.amount).label('total_amount'))
        .where(Expense.project_id == project_id)
        .group_by(Expense.category)
    )
    expense_categories = expenses_result.all()
    print(f"[DEBUG] Expense categories found: {len(expense_categories)}")
    for cat in expense_categories:
        print(f"[DEBUG] Expense category: {cat.category} = {cat.total_amount}")
    
    # Kombiniere Kategorien
    category_totals = {}
    
    # Verarbeite Rechnungs-Kategorien
    for category, total_amount in invoice_categories:
        if category not in category_totals:
            category_totals[category] = 0
        category_totals[category] += float(total_amount)
    
    # Verarbeite direkte Kostenpositionen-Kategorien
    for category, total_amount in direct_cost_categories:
        if category not in category_totals:
            category_totals[category] = 0
        category_totals[category] += float(total_amount)
    
    # Verarbeite Ausgaben-Kategorien
    for category, total_amount in expense_categories:
        if category not in category_totals:
            category_totals[category] = 0
        category_totals[category] += float(total_amount)
    
    # Berechne Gesamtsumme
    total_amount = sum(category_totals.values())
    print(f"[DEBUG] Combined categories: {category_totals}")
    print(f"[DEBUG] Total amount: {total_amount}")
    
    # Erstelle Kategoriedaten mit Prozenten
    category_data = []
    colors = [
        '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57',
        '#ff9ff3', '#54a0ff', '#5f27cd', '#00d2d3', '#ff9f43'
    ]
    
    for i, (category, amount) in enumerate(sorted(category_totals.items(), key=lambda x: x[1], reverse=True)):
        percentage = (amount / total_amount * 100) if total_amount > 0 else 0
        category_data.append({
            "category": category,
            "amount": amount,
            "percentage": round(percentage, 1),
            "color": colors[i % len(colors)]
        })
    
    print(f"[DEBUG] Final category data: {category_data}")
    
    return {
        "project_id": project_id,
        "project_name": project.name,
        "total_amount": total_amount,
        "categories": category_data
    }

@router.get("/project/{project_id}/summary")
async def get_financial_summary(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Holt Finanzzusammenfassung für das Projekt"""
    
    # Prüfe Projektzugriff
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    
    print(f"[DEBUG] Financial Summary for project {project_id}: {project.name}")
    
    # Berechne Gesamtausgaben aus bezahlten Rechnungen
    paid_invoices_result = await db.execute(
        select(func.sum(Invoice.total_amount))
        .where(
            and_(
                Invoice.project_id == project_id,
                Invoice.status == InvoiceStatus.PAID
            )
        )
    )
    paid_invoices_total = paid_invoices_result.scalar() or 0
    print(f"[DEBUG] Paid invoices total: {paid_invoices_total}")
    
    # Berechne Gesamtausgaben aus direkten Ausgaben
    expenses_total_result = await db.execute(
        select(func.sum(Expense.amount))
        .where(Expense.project_id == project_id)
    )
    expenses_total = expenses_total_result.scalar() or 0
    print(f"[DEBUG] Direct expenses total: {expenses_total}")
    
    # Berechne Gesamtausgaben aus direkten Kostenpositionen (CostPosition ohne Rechnung)
    cost_positions_total_result = await db.execute(
        select(func.sum(CostPosition.amount))
        .where(CostPosition.project_id == project_id)
    )
    cost_positions_total = cost_positions_total_result.scalar() or 0
    print(f"[DEBUG] Direct cost positions total: {cost_positions_total}")
    
    # Debug: Zähle alle Kostenpositionen für das Projekt (direkt über project_id)
    cost_positions_count_result = await db.execute(
        select(func.count(CostPosition.id))
        .where(CostPosition.project_id == project_id)
    )
    cost_positions_count = cost_positions_count_result.scalar() or 0
    print(f"[DEBUG] Cost positions count (direct): {cost_positions_count}")
    
    # Debug: Zähle alle Kostenpositionen für das Projekt (über Invoice JOIN)
    cost_positions_invoice_count_result = await db.execute(
        select(func.count(CostPosition.id))
        .join(Invoice, CostPosition.invoice_id == Invoice.id)
        .where(Invoice.project_id == project_id)
    )
    cost_positions_invoice_count = cost_positions_invoice_count_result.scalar() or 0
    print(f"[DEBUG] Cost positions count (via invoice): {cost_positions_invoice_count}")
    
    # Debug: Zähle alle direkten Ausgaben für das Projekt
    expenses_count_result = await db.execute(
        select(func.count(Expense.id))
        .where(Expense.project_id == project_id)
    )
    expenses_count = expenses_count_result.scalar() or 0
    print(f"[DEBUG] Direct expenses count: {expenses_count}")
    
    # Berechne ausstehende Rechnungen
    pending_invoices_result = await db.execute(
        select(func.sum(Invoice.total_amount))
        .where(
            and_(
                Invoice.project_id == project_id,
                Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.VIEWED])
            )
        )
    )
    pending_invoices_total = pending_invoices_result.scalar() or 0
    
    # Gesamtausgaben: Rechnungen + direkte Ausgaben + direkte Kostenpositionen
    total_expenses = float(paid_invoices_total) + float(expenses_total) + float(cost_positions_total)
    print(f"[DEBUG] Total expenses breakdown: invoices={paid_invoices_total}, expenses={expenses_total}, cost_positions={cost_positions_total}, total={total_expenses}")
    
    # Budget-Status
    budget = project.budget or 0
    remaining_budget = budget - total_expenses
    budget_percentage = (total_expenses / budget * 100) if budget > 0 else 0
    
    return {
        "project_id": project_id,
        "project_name": project.name,
        "budget": budget,
        "total_expenses": total_expenses,
        "paid_invoices": float(paid_invoices_total),
        "direct_expenses": float(expenses_total),
        "direct_cost_positions": float(cost_positions_total),
        "pending_invoices": float(pending_invoices_total),
        "remaining_budget": remaining_budget,
        "budget_percentage": round(budget_percentage, 1),
        "is_over_budget": total_expenses > budget
    }

@router.get("/project/{project_id}/cost-breakdown")
async def get_cost_breakdown(
    project_id: int,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Holt detaillierte Kostenaufschlüsselung mit Kostenpositionen"""
    
    # Prüfe Projektzugriff
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    
    print(f"[DEBUG] Cost breakdown for project {project_id}: {project.name}")
    
    # Hole alle Kostenpositionen aus bezahlten Rechnungen
    cost_positions_result = await db.execute(
        select(CostPosition, Invoice)
        .join(Invoice, CostPosition.invoice_id == Invoice.id)
        .where(
            and_(
                Invoice.project_id == project_id,
                Invoice.status == InvoiceStatus.PAID
            )
        )
        .order_by(desc(CostPosition.amount))
        .limit(limit)
    )
    invoice_costs = cost_positions_result.all()
    print(f"[DEBUG] Invoice costs found: {len(invoice_costs)}")
    
    # Hole alle direkten Kostenpositionen (ohne Rechnung)
    direct_cost_positions_result = await db.execute(
        select(CostPosition)
        .where(CostPosition.project_id == project_id)
        .order_by(desc(CostPosition.amount))
        .limit(limit)
    )
    direct_costs = direct_cost_positions_result.scalars().all()
    print(f"[DEBUG] Direct costs found: {len(direct_costs)}")
    
    # Hole alle direkten Ausgaben
    expenses_result = await db.execute(
        select(Expense)
        .where(Expense.project_id == project_id)
        .order_by(desc(Expense.amount))
        .limit(limit)
    )
    expenses = expenses_result.scalars().all()
    print(f"[DEBUG] Direct expenses found: {len(expenses)}")
    
    # Kombiniere alle Kostenpositionen
    all_costs = []
    
    # Verarbeite Rechnungs-Kostenpositionen
    for cost_position, invoice in invoice_costs:
        all_costs.append({
            "id": cost_position.id,
            "type": "invoice",
            "description": cost_position.description,
            "amount": cost_position.amount,
            "category": cost_position.category,
            "date": invoice.invoice_date,
            "contractor_name": invoice.service_provider_id,  # Könnte erweitert werden um Namen
            "invoice_number": invoice.invoice_number,
            "cost_type": cost_position.cost_type,
            "position_order": cost_position.position_order
        })
    
    # Verarbeite direkte Kostenpositionen
    for cost_position in direct_costs:
        all_costs.append({
            "id": cost_position.id,
            "type": "cost_position",
            "description": cost_position.description,
            "amount": cost_position.amount,
            "category": cost_position.category,
            "date": cost_position.created_at,
            "contractor_name": cost_position.contractor_name,
            "invoice_number": None,
            "cost_type": cost_position.cost_type,
            "position_order": cost_position.position_order
        })
    
    # Verarbeite direkte Ausgaben
    for expense in expenses:
        all_costs.append({
            "id": expense.id,
            "type": "expense",
            "description": expense.title,
            "amount": expense.amount,
            "category": expense.category,
            "date": expense.date,
            "contractor_name": None,
            "invoice_number": None,
            "cost_type": "direct",
            "position_order": 0
        })
    
    # Sortiere nach Betrag
    all_costs.sort(key=lambda x: x['amount'], reverse=True)
    print(f"[DEBUG] Final cost breakdown: {len(all_costs)} items")
    
    return {
        "project_id": project_id,
        "project_name": project.name,
        "total_items": len(all_costs),
        "costs": all_costs[:limit]
    }

@router.get("/project/{project_id}/cost-analysis")
async def get_cost_analysis(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Holt erweiterte Kostenanalyse mit verschiedenen Metriken"""
    
    # Prüfe Projektzugriff
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    
    print(f"[DEBUG] Cost analysis for project {project_id}: {project.name}")
    
    # Kosten nach Typ (Material, Arbeit, Sonstiges) - aus Rechnungen
    cost_by_type_result = await db.execute(
        select(CostPosition.cost_type, func.sum(CostPosition.amount).label('total_amount'))
        .join(Invoice, CostPosition.invoice_id == Invoice.id)
        .where(
            and_(
                Invoice.project_id == project_id,
                Invoice.status == InvoiceStatus.PAID
            )
        )
        .group_by(CostPosition.cost_type)
    )
    cost_by_type = {row.cost_type: float(row.total_amount) for row in cost_by_type_result.all()}
    print(f"[DEBUG] Cost by type (invoices): {cost_by_type}")
    
    # Kosten nach Typ - direkte Kostenpositionen
    direct_cost_by_type_result = await db.execute(
        select(CostPosition.cost_type, func.sum(CostPosition.amount).label('total_amount'))
        .where(CostPosition.project_id == project_id)
        .group_by(CostPosition.cost_type)
    )
    direct_cost_by_type = {row.cost_type: float(row.total_amount) for row in direct_cost_by_type_result.all()}
    print(f"[DEBUG] Cost by type (direct): {direct_cost_by_type}")
    
    # Kombiniere beide
    combined_cost_by_type = {}
    for cost_type, amount in cost_by_type.items():
        combined_cost_by_type[cost_type] = combined_cost_by_type.get(cost_type, 0) + amount
    for cost_type, amount in direct_cost_by_type.items():
        combined_cost_by_type[cost_type] = combined_cost_by_type.get(cost_type, 0) + amount
    print(f"[DEBUG] Combined cost by type: {combined_cost_by_type}")
    
    # Kosten nach Kategorie (Material, Arbeit, Ausrüstung, etc.) - aus Rechnungen
    cost_by_category_result = await db.execute(
        select(CostPosition.category, func.sum(CostPosition.amount).label('total_amount'))
        .join(Invoice, CostPosition.invoice_id == Invoice.id)
        .where(
            and_(
                Invoice.project_id == project_id,
                Invoice.status == InvoiceStatus.PAID
            )
        )
        .group_by(CostPosition.category)
    )
    cost_by_category = {row.category: float(row.total_amount) for row in cost_by_category_result.all()}
    print(f"[DEBUG] Cost by category (invoices): {cost_by_category}")
    
    # Kosten nach Kategorie - direkte Kostenpositionen
    direct_cost_by_category_result = await db.execute(
        select(CostPosition.category, func.sum(CostPosition.amount).label('total_amount'))
        .where(CostPosition.project_id == project_id)
        .group_by(CostPosition.category)
    )
    direct_cost_by_category = {row.category: float(row.total_amount) for row in direct_cost_by_category_result.all()}
    print(f"[DEBUG] Cost by category (direct): {direct_cost_by_category}")
    
    # Ausgaben nach Kategorie
    expense_by_category_result = await db.execute(
        select(Expense.category, func.sum(Expense.amount).label('total_amount'))
        .where(Expense.project_id == project_id)
        .group_by(Expense.category)
    )
    expense_by_category = {row.category: float(row.total_amount) for row in expense_by_category_result.all()}
    print(f"[DEBUG] Expense by category: {expense_by_category}")
    
    # Kombiniere Kategorien
    combined_categories = {}
    for category, amount in cost_by_category.items():
        combined_categories[category] = combined_categories.get(category, 0) + amount
    for category, amount in direct_cost_by_category.items():
        combined_categories[category] = combined_categories.get(category, 0) + amount
    for category, amount in expense_by_category.items():
        combined_categories[category] = combined_categories.get(category, 0) + amount
    print(f"[DEBUG] Combined categories: {combined_categories}")
    
    # Durchschnittliche Kostenposition - aus Rechnungen
    avg_cost_position_result = await db.execute(
        select(func.avg(CostPosition.amount))
        .join(Invoice, CostPosition.invoice_id == Invoice.id)
        .where(
            and_(
                Invoice.project_id == project_id,
                Invoice.status == InvoiceStatus.PAID
            )
        )
    )
    avg_cost_position_invoice = avg_cost_position_result.scalar() or 0
    print(f"[DEBUG] Average cost position (invoices): {avg_cost_position_invoice}")
    
    # Durchschnittliche Kostenposition - direkte Kostenpositionen
    avg_direct_cost_position_result = await db.execute(
        select(func.avg(CostPosition.amount))
        .where(CostPosition.project_id == project_id)
    )
    avg_cost_position_direct = avg_direct_cost_position_result.scalar() or 0
    print(f"[DEBUG] Average cost position (direct): {avg_cost_position_direct}")
    
    # Anzahl der Kostenpositionen - aus Rechnungen
    cost_position_count_result = await db.execute(
        select(func.count(CostPosition.id))
        .join(Invoice, CostPosition.invoice_id == Invoice.id)
        .where(
            and_(
                Invoice.project_id == project_id,
                Invoice.status == InvoiceStatus.PAID
            )
        )
    )
    cost_position_count_invoice = cost_position_count_result.scalar() or 0
    print(f"[DEBUG] Cost position count (invoices): {cost_position_count_invoice}")
    
    # Anzahl der Kostenpositionen - direkte Kostenpositionen
    direct_cost_position_count_result = await db.execute(
        select(func.count(CostPosition.id))
        .where(CostPosition.project_id == project_id)
    )
    cost_position_count_direct = direct_cost_position_count_result.scalar() or 0
    print(f"[DEBUG] Cost position count (direct): {cost_position_count_direct}")
    
    # Gesamtanzahl Kostenpositionen
    total_cost_positions = cost_position_count_invoice + cost_position_count_direct
    print(f"[DEBUG] Total cost positions: {total_cost_positions}")
    
    # Durchschnittliche Kostenposition (gewichtet)
    if total_cost_positions > 0:
        avg_cost_position = (avg_cost_position_invoice * cost_position_count_invoice + avg_cost_position_direct * cost_position_count_direct) / total_cost_positions
    else:
        avg_cost_position = 0
    print(f"[DEBUG] Weighted average cost position: {avg_cost_position}")
    
    # Anzahl der direkten Ausgaben
    expense_count_result = await db.execute(
        select(func.count(Expense.id))
        .where(Expense.project_id == project_id)
    )
    expense_count = expense_count_result.scalar() or 0
    print(f"[DEBUG] Expense count: {expense_count}")
    
    result = {
        "project_id": project_id,
        "project_name": project.name,
        "cost_by_type": combined_cost_by_type,
        "cost_by_category": combined_categories,
        "average_cost_position": float(avg_cost_position),
        "total_cost_positions": total_cost_positions,
        "total_expenses": expense_count,
        "total_cost_items": total_cost_positions + expense_count
    }
    print(f"[DEBUG] Final cost analysis result: {result}")
    return result

