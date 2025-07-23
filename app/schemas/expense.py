from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ExpenseBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    amount: float = Field(..., gt=0)
    category: str = Field(..., pattern="^(material|labor|equipment|services|permits|other)$")
    project_id: int = Field(..., gt=0)
    date: datetime
    receipt_url: Optional[str] = None

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    amount: Optional[float] = Field(None, gt=0)
    category: Optional[str] = Field(None, pattern="^(material|labor|equipment|services|permits|other)$")
    date: Optional[datetime] = None
    receipt_url: Optional[str] = None

class ExpenseRead(ExpenseBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True 