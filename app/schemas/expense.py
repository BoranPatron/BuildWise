from pydantic import BaseModel, Field, field_validator
from typing import Optional, Union
from datetime import datetime, date

class ExpenseBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    amount: float = Field(..., gt=0)
    category: str = Field(..., pattern="^(material|labor|equipment|services|permits|property|legal|planning|other)$")
    project_id: int = Field(..., gt=0)
    date: Union[date, datetime, str]
    receipt_url: Optional[str] = None
    construction_phase: Optional[str] = None  # Bauphase zum Zeitpunkt der Ausgabe
    
    @field_validator('date')
    @classmethod
    def validate_date(cls, v):
        if isinstance(v, str):
            try:
                # Versuche das String-Datum zu parsen
                return datetime.fromisoformat(v).date()
            except ValueError:
                try:
                    # Fallback für andere Datumsformate
                    return datetime.strptime(v, '%Y-%m-%d').date()
                except ValueError:
                    raise ValueError(f"Invalid date format: {v}")
        elif isinstance(v, datetime):
            return v.date()
        elif isinstance(v, date):
            return v
        else:
            raise ValueError(f"Invalid date type: {type(v)}")

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    amount: Optional[float] = Field(None, gt=0)
    category: Optional[str] = Field(None, pattern="^(material|labor|equipment|services|permits|property|legal|planning|other)$")
    date: Optional[Union[date, datetime, str]] = None
    receipt_url: Optional[str] = None
    construction_phase: Optional[str] = None

class ExpenseRead(ExpenseBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    @field_validator('date', mode='before')
    @classmethod
    def convert_datetime_to_date(cls, v):
        if isinstance(v, datetime):
            return v.date()
        return v
    
    class Config:
        from_attributes = True 