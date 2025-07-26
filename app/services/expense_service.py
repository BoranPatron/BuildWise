from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime

from ..models.expense import Expense
from ..schemas.expense import ExpenseCreate, ExpenseUpdate, ExpenseRead
from ..models.project import Project
from ..services.security_service import SecurityService
from ..models.audit_log import AuditAction
from ..models.user import User

class ExpenseService:
    
    @staticmethod
    async def create_expense(
        db: AsyncSession, 
        expense_data: ExpenseCreate, 
        user_id: int,
        ip_address: Optional[str] = None
    ) -> ExpenseRead:
        """Erstellt eine neue Ausgabe mit automatischer Bauphasen-Speicherung"""
        
        # Prüfe ob Projekt existiert und User Zugriff hat
        project = await db.execute(
            select(Project).where(Project.id == expense_data.project_id)
        )
        project = project.scalar_one_or_none()
        
        if not project:
            raise ValueError("Projekt nicht gefunden")
        
        # Hole aktuelle Bauphase des Projekts
        current_construction_phase = project.construction_phase
        
        # Erstelle neue Ausgabe mit Bauphase
        expense = Expense(
            title=expense_data.title,
            description=expense_data.description,
            amount=expense_data.amount,
            category=expense_data.category,
            project_id=expense_data.project_id,
            date=expense_data.date,
            receipt_url=expense_data.receipt_url,
            construction_phase=current_construction_phase  # Speichere aktuelle Bauphase
        )
        
        db.add(expense)
        await db.flush()  # Für ID-Generierung
        await db.commit()
        await db.refresh(expense)
        
        # Audit-Log mit Bauphasen-Information
        audit_message = f"Ausgabe erstellt: {expense_data.title} ({expense_data.amount}€)"
        if current_construction_phase:
            audit_message += f" - Bauphase: {current_construction_phase}"
        
        await SecurityService.create_audit_log(
            db, user_id, AuditAction.DATA_CREATE,
            audit_message,
            resource_type="expense", resource_id=expense.id,
            ip_address=SecurityService.anonymize_ip_address(ip_address) if ip_address else None
        )
        
        # Credit-Zuordnung für Bauträger
        try:
            from ..services.credit_service import CreditService
            from ..models.credit_event import CreditEventType
            from ..models.user import UserRole
            
            # Prüfe ob User ein Bauträger ist
            user_result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()
            
            if user and user.user_role == UserRole.BAUTRAEGER:
                # Füge Credits für hinzugefügte Ausgabe hinzu
                await CreditService.add_credits_for_activity(
                    db=db,
                    user_id=user_id,
                    event_type=CreditEventType.EXPENSE_ADDED,
                    description=f"Ausgabe hinzugefügt: {expense_data.title}",
                    related_entity_type="expense",
                    related_entity_id=expense.id,
                    ip_address=ip_address
                )
                print(f"✅ Credits für Bauträger {user_id} hinzugefügt: Ausgabe hinzugefügt")
            else:
                print(f"ℹ️  User {user_id} ist kein Bauträger, keine Credits hinzugefügt")
                
        except Exception as e:
            print(f"❌ Fehler bei Credit-Zuordnung: {e}")
            # Fehler bei Credit-Zuordnung sollte nicht die Ausgabe-Erstellung blockieren
        
        return ExpenseRead.model_validate(expense)
    
    @staticmethod
    async def get_expenses_by_project(
        db: AsyncSession, 
        project_id: int
    ) -> List[ExpenseRead]:
        """Lädt alle Ausgaben für ein Projekt"""
        
        result = await db.execute(
            select(Expense)
            .where(Expense.project_id == project_id)
            .order_by(Expense.date.desc())
        )
        
        expenses = result.scalars().all()
        return [ExpenseRead.model_validate(expense) for expense in expenses]
    
    @staticmethod
    async def get_expense_by_id(
        db: AsyncSession, 
        expense_id: int
    ) -> Optional[ExpenseRead]:
        """Lädt eine spezifische Ausgabe"""
        
        result = await db.execute(
            select(Expense).where(Expense.id == expense_id)
        )
        
        expense = result.scalar_one_or_none()
        if not expense:
            return None
            
        return ExpenseRead.model_validate(expense)
    
    @staticmethod
    async def update_expense(
        db: AsyncSession, 
        expense_id: int, 
        expense_data: ExpenseUpdate,
        user_id: int,
        ip_address: Optional[str] = None
    ) -> Optional[ExpenseRead]:
        """Aktualisiert eine Ausgabe"""
        
        # Lade bestehende Ausgabe
        result = await db.execute(
            select(Expense).where(Expense.id == expense_id)
        )
        expense = result.scalar_one_or_none()
        
        if not expense:
            return None
        
        # Update-Felder
        update_data = expense_data.model_dump(exclude_unset=True)
        
        if update_data:
            await db.execute(
                update(Expense)
                .where(Expense.id == expense_id)
                .values(**update_data)
            )
            await db.commit()
            await db.refresh(expense)
            
            # Audit-Log
            await SecurityService.create_audit_log(
                db, user_id, AuditAction.DATA_UPDATE,
                f"Ausgabe aktualisiert: {expense.title}",
                resource_type="expense", resource_id=expense.id,
                ip_address=SecurityService.anonymize_ip_address(ip_address) if ip_address else None
            )
        
        return ExpenseRead.model_validate(expense)
    
    @staticmethod
    async def delete_expense(
        db: AsyncSession, 
        expense_id: int,
        user_id: int,
        ip_address: Optional[str] = None
    ) -> bool:
        """Löscht eine Ausgabe"""
        
        # Lade Ausgabe für Audit-Log
        result = await db.execute(
            select(Expense).where(Expense.id == expense_id)
        )
        expense = result.scalar_one_or_none()
        
        if not expense:
            return False
        
        # Audit-Log vor Löschung
        await SecurityService.create_audit_log(
            db, user_id, AuditAction.DATA_DELETE,
            f"Ausgabe gelöscht: {expense.title} ({expense.amount}€)",
            resource_type="expense", resource_id=expense.id,
            ip_address=SecurityService.anonymize_ip_address(ip_address) if ip_address else None
        )
        
        # Lösche Ausgabe
        await db.execute(
            delete(Expense).where(Expense.id == expense_id)
        )
        await db.commit()
        
        return True
    
    @staticmethod
    async def get_expense_summary_by_project(
        db: AsyncSession, 
        project_id: int
    ) -> dict:
        """Berechnet Zusammenfassung der Ausgaben für ein Projekt"""
        
        result = await db.execute(
            select(Expense).where(Expense.project_id == project_id)
        )
        expenses = result.scalars().all()
        
        total_amount = sum(expense.amount for expense in expenses)
        
        # Gruppierung nach Kategorie
        category_totals = {}
        for expense in expenses:
            if expense.category not in category_totals:
                category_totals[expense.category] = 0
            category_totals[expense.category] += expense.amount
        
        # Gruppierung nach Bauphase (für Analytics)
        phase_totals = {}
        for expense in expenses:
            if expense.construction_phase:
                if expense.construction_phase not in phase_totals:
                    phase_totals[expense.construction_phase] = 0
                phase_totals[expense.construction_phase] += expense.amount
        
        return {
            "total_amount": total_amount,
            "expense_count": len(expenses),
            "category_totals": category_totals,
            "phase_totals": phase_totals,  # Neue Bauphasen-Gruppierung
            "latest_expense": max(expenses, key=lambda x: x.date).date if expenses else None
        } 