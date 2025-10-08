from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CostPositionBase(BaseModel):
    """Basis-Schema für Kostenpositionen in Rechnungen"""
    title: Optional[str] = None
    description: str
    amount: float
    position_order: Optional[int] = 0
    category: Optional[str] = "custom"  # material, labor, other, custom
    cost_type: Optional[str] = "standard"  # Hinzugefügtes Feld
    status: Optional[str] = "active"  # Status: active, deleted, etc.

class CostPositionCreate(CostPositionBase):
    """Schema für das Erstellen einer Kostenposition"""
    project_id: Optional[int] = None
    invoice_id: Optional[int] = None
    quote_id: Optional[int] = None
    milestone_id: Optional[int] = None
    contractor_name: Optional[str] = None

class CostPositionUpdate(BaseModel):
    """Schema für das Aktualisieren einer Kostenposition"""
    description: Optional[str] = None
    amount: Optional[float] = None
    position_order: Optional[int] = None

class CostPositionRead(CostPositionBase):
    """Schema für das Lesen einer Kostenposition"""
    id: int
    invoice_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class CostPositionSummary(BaseModel):
    """Schema für Zusammenfassung einer Kostenposition"""
    id: int
    title: Optional[str] = None
    description: str
    amount: float
    position_order: int

    class Config:
        from_attributes = True


class CostPositionListItem(BaseModel):
    """Erweitertes Listenelement für die Projekt-Ansicht"""
    id: int
    title: Optional[str] = None
    amount: float
    created_at: datetime
    category: Optional[str] = None
    milestone_id: Optional[int] = None
    milestone_title: Optional[str] = None
    service_provider_id: Optional[int] = None
    service_provider_name: Optional[str] = None
    contractor_name: Optional[str] = None
    quote_id: Optional[int] = None

class CostPositionStatistics(BaseModel):
    """Schema für Statistiken von Kostenpositionen"""
    total_positions: int
    total_amount: float
    average_amount: float 