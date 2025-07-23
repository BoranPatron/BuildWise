from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime

from ..core.database import get_db
from ..api.deps import get_current_user
from ..models.user import User
from ..schemas.expense import ExpenseCreate, ExpenseUpdate, ExpenseRead
from ..services.expense_service import ExpenseService

router = APIRouter(prefix="/expenses", tags=["expenses"])

@router.post("/", response_model=ExpenseRead, status_code=status.HTTP_201_CREATED)
async def create_expense(
    expense_data: ExpenseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Erstellt eine neue Ausgabe"""
    
    try:
        # Prüfe ob User Zugriff auf das Projekt hat
        # TODO: Implementiere Projekt-Zugriffsberechtigung
        
        expense = await ExpenseService.create_expense(
            db=db,
            expense_data=expense_data,
            user_id=current_user.id,
            ip_address=request.client.host if request else None
        )
        
        return expense
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Erstellen der Ausgabe: {str(e)}"
        )

@router.get("/project/{project_id}", response_model=List[ExpenseRead])
async def get_expenses_by_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lädt alle Ausgaben für ein Projekt"""
    
    try:
        # Prüfe ob User Zugriff auf das Projekt hat
        # TODO: Implementiere Projekt-Zugriffsberechtigung
        
        expenses = await ExpenseService.get_expenses_by_project(
            db=db,
            project_id=project_id
        )
        
        return expenses
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Laden der Ausgaben: {str(e)}"
        )

@router.get("/{expense_id}", response_model=ExpenseRead)
async def get_expense(
    expense_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lädt eine spezifische Ausgabe"""
    
    try:
        expense = await ExpenseService.get_expense_by_id(
            db=db,
            expense_id=expense_id
        )
        
        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ausgabe nicht gefunden"
            )
        
        return expense
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Laden der Ausgabe: {str(e)}"
        )

@router.put("/{expense_id}", response_model=ExpenseRead)
async def update_expense(
    expense_id: int,
    expense_data: ExpenseUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Aktualisiert eine Ausgabe"""
    
    try:
        expense = await ExpenseService.update_expense(
            db=db,
            expense_id=expense_id,
            expense_data=expense_data,
            user_id=current_user.id,
            ip_address=request.client.host if request else None
        )
        
        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ausgabe nicht gefunden"
            )
        
        return expense
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Aktualisieren der Ausgabe: {str(e)}"
        )

@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Löscht eine Ausgabe"""
    
    try:
        success = await ExpenseService.delete_expense(
            db=db,
            expense_id=expense_id,
            user_id=current_user.id,
            ip_address=request.client.host if request else None
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ausgabe nicht gefunden"
            )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Löschen der Ausgabe: {str(e)}"
        )

@router.get("/project/{project_id}/summary")
async def get_expense_summary(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lädt eine Zusammenfassung der Ausgaben für ein Projekt"""
    
    try:
        summary = await ExpenseService.get_expense_summary_by_project(
            db=db,
            project_id=project_id
        )
        
        return summary
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Laden der Ausgaben-Zusammenfassung: {str(e)}"
        ) 