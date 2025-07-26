from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from ..models.expense import Expense
from ..models.project import Project
from ..models.cost_position import CostPosition
from ..models.buildwise_fee import BuildWiseFee

class FinanceAnalyticsService:
    """Service für erweiterte Finanz-Analytics mit Bauphasen-Berücksichtigung"""
    
    @staticmethod
    async def get_expense_analytics_by_phase(
        db: AsyncSession, 
        project_id: int
    ) -> Dict:
        """Analysiert Ausgaben nach Bauphasen"""
        
        # Lade alle Ausgaben für das Projekt
        result = await db.execute(
            select(Expense)
            .where(Expense.project_id == project_id)
            .order_by(Expense.date.desc())
        )
        expenses = result.scalars().all()
        
        # Gruppierung nach Bauphase
        phase_analytics = {}
        total_amount = 0
        
        for expense in expenses:
            phase = expense.construction_phase or "Unbekannt"
            total_amount += expense.amount
            
            if phase not in phase_analytics:
                phase_analytics[phase] = {
                    "total_amount": 0,
                    "count": 0,
                    "categories": {},
                    "latest_expense": None
                }
            
            phase_analytics[phase]["total_amount"] += expense.amount
            phase_analytics[phase]["count"] += 1
            
            # Kategorie-Gruppierung pro Phase
            if expense.category not in phase_analytics[phase]["categories"]:
                phase_analytics[phase]["categories"][expense.category] = 0
            phase_analytics[phase]["categories"][expense.category] += expense.amount
            
            # Neueste Ausgabe pro Phase
            if not phase_analytics[phase]["latest_expense"] or expense.date > phase_analytics[phase]["latest_expense"]:
                phase_analytics[phase]["latest_expense"] = expense.date
        
        # Berechne Prozentsätze
        for phase_data in phase_analytics.values():
            if total_amount > 0:
                phase_data["percentage"] = (phase_data["total_amount"] / total_amount) * 100
            else:
                phase_data["percentage"] = 0
        
        return {
            "total_amount": total_amount,
            "total_count": len(expenses),
            "phase_breakdown": phase_analytics,
            "phases_with_expenses": len([p for p in phase_analytics.values() if p["total_amount"] > 0])
        }
    
    @staticmethod
    async def get_comprehensive_finance_analytics(
        db: AsyncSession, 
        project_id: int
    ) -> Dict:
        """Umfassende Finanz-Analytics mit allen Komponenten"""
        
        # Lade Projekt-Informationen
        project_result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = project_result.scalar_one_or_none()
        
        if not project:
            raise ValueError("Projekt nicht gefunden")
        
        # Ausgaben-Analytics
        expense_analytics = await FinanceAnalyticsService.get_expense_analytics_by_phase(db, project_id)
        
        # Cost Positions Analytics
        cost_positions_result = await db.execute(
            select(CostPosition).where(CostPosition.project_id == project_id)
        )
        cost_positions = cost_positions_result.scalars().all()
        
        cost_positions_total = sum(cp.amount for cp in cost_positions)
        cost_positions_paid = sum(cp.paid_amount for cp in cost_positions)
        
        # BuildWise Fees Analytics
        fees_result = await db.execute(
            select(BuildWiseFee).where(BuildWiseFee.project_id == project_id)
        )
        fees = fees_result.scalars().all()
        
        fees_total = sum(fee.fee_amount for fee in fees)
        fees_paid = sum(fee.fee_amount for fee in fees if fee.status == 'paid')
        
        # Budget-Analysis
        budget = project.budget or 0
        total_expenses = expense_analytics["total_amount"]
        total_costs = cost_positions_total + total_expenses
        budget_utilization = (total_costs / budget * 100) if budget > 0 else 0
        
        return {
            "project_info": {
                "id": project.id,
                "name": project.name,
                "construction_phase": project.construction_phase,
                "budget": budget,
                "progress_percentage": project.progress_percentage
            },
            "expense_analytics": expense_analytics,
            "cost_positions": {
                "total_amount": cost_positions_total,
                "paid_amount": cost_positions_paid,
                "remaining_amount": cost_positions_total - cost_positions_paid,
                "count": len(cost_positions)
            },
            "buildwise_fees": {
                "total_amount": fees_total,
                "paid_amount": fees_paid,
                "remaining_amount": fees_total - fees_paid,
                "count": len(fees)
            },
            "budget_analysis": {
                "total_costs": total_costs,
                "budget_utilization_percentage": budget_utilization,
                "remaining_budget": budget - total_costs,
                "over_budget": total_costs > budget
            },
            "phase_performance": await FinanceAnalyticsService._calculate_phase_performance(
                db, project_id, expense_analytics
            )
        }
    
    @staticmethod
    async def _calculate_phase_performance(
        db: AsyncSession, 
        project_id: int, 
        expense_analytics: Dict
    ) -> Dict:
        """Berechnet Performance-Metriken für jede Bauphase"""
        
        phase_performance = {}
        
        for phase, data in expense_analytics["phase_breakdown"].items():
            if data["total_amount"] > 0:
                # Durchschnittliche Ausgaben pro Tag in dieser Phase
                if data["latest_expense"]:
                    # Schätze die Dauer der Phase basierend auf den Ausgaben
                    days_in_phase = max(1, (data["latest_expense"] - datetime.now()).days)
                    avg_daily_expense = data["total_amount"] / days_in_phase
                else:
                    avg_daily_expense = 0
                
                phase_performance[phase] = {
                    "total_amount": data["total_amount"],
                    "count": data["count"],
                    "percentage": data["percentage"],
                    "avg_daily_expense": avg_daily_expense,
                    "top_category": max(data["categories"].items(), key=lambda x: x[1])[0] if data["categories"] else None,
                    "category_distribution": data["categories"]
                }
        
        return phase_performance
    
    @staticmethod
    async def get_expense_trends_by_phase(
        db: AsyncSession, 
        project_id: int, 
        months: int = 6
    ) -> Dict:
        """Analysiert Ausgaben-Trends nach Bauphasen über Zeit"""
        
        # Berechne Zeitraum
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)
        
        # Lade Ausgaben im Zeitraum
        result = await db.execute(
            select(Expense)
            .where(
                and_(
                    Expense.project_id == project_id,
                    Expense.date >= start_date,
                    Expense.date <= end_date
                )
            )
            .order_by(Expense.date.asc())
        )
        expenses = result.scalars().all()
        
        # Gruppierung nach Monat und Phase
        trends = {}
        
        for expense in expenses:
            month_key = expense.date.strftime("%Y-%m")
            phase = expense.construction_phase or "Unbekannt"
            
            if month_key not in trends:
                trends[month_key] = {}
            
            if phase not in trends[month_key]:
                trends[month_key][phase] = 0
            
            trends[month_key][phase] += expense.amount
        
        return {
            "period_months": months,
            "start_date": start_date,
            "end_date": end_date,
            "monthly_trends": trends
        }
    
    @staticmethod
    async def get_phase_comparison_analytics(
        db: AsyncSession, 
        project_id: int
    ) -> Dict:
        """Vergleicht Performance zwischen verschiedenen Bauphasen"""
        
        expense_analytics = await FinanceAnalyticsService.get_expense_analytics_by_phase(db, project_id)
        
        phases = list(expense_analytics["phase_breakdown"].keys())
        comparison_data = {}
        
        for i, phase1 in enumerate(phases):
            for j, phase2 in enumerate(phases):
                if i < j:  # Vergleiche nur einmal
                    comparison_key = f"{phase1}_vs_{phase2}"
                    
                    data1 = expense_analytics["phase_breakdown"][phase1]
                    data2 = expense_analytics["phase_breakdown"][phase2]
                    
                    # Berechne Vergleichsmetriken
                    amount_diff = data1["total_amount"] - data2["total_amount"]
                    percentage_diff = data1["percentage"] - data2["percentage"]
                    
                    comparison_data[comparison_key] = {
                        "phase1": {
                            "name": phase1,
                            "amount": data1["total_amount"],
                            "percentage": data1["percentage"],
                            "count": data1["count"]
                        },
                        "phase2": {
                            "name": phase2,
                            "amount": data2["total_amount"],
                            "percentage": data2["percentage"],
                            "count": data2["count"]
                        },
                        "differences": {
                            "amount_diff": amount_diff,
                            "percentage_diff": percentage_diff,
                            "more_expensive_phase": phase1 if amount_diff > 0 else phase2
                        }
                    }
        
        return {
            "total_phases": len(phases),
            "comparisons": comparison_data
        } 