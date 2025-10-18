from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

class BuildWiseFeeStatus(str, Enum):
    OPEN = "open"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class BuildWiseFeeItemBase(BaseModel):
    quote_id: int
    cost_position_id: int
    quote_amount: Decimal = Field(..., ge=0)
    fee_amount: Decimal = Field(..., ge=0)
    fee_percentage: Decimal = Field(default=Decimal("1.00"), ge=0, le=100)
    description: Optional[str] = None

class BuildWiseFeeItemCreate(BuildWiseFeeItemBase):
    pass

class BuildWiseFeeItemUpdate(BaseModel):
    quote_amount: Optional[Decimal] = Field(None, ge=0)
    fee_amount: Optional[Decimal] = Field(None, ge=0)
    fee_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    description: Optional[str] = None

class BuildWiseFeeItem(BuildWiseFeeItemBase):
    id: int
    buildwise_fee_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class BuildWiseFeeBase(BaseModel):
    project_id: int
    quote_id: int
    cost_position_id: int
    service_provider_id: int
    fee_amount: Decimal = Field(..., ge=0)
    fee_percentage: Decimal = Field(default=Decimal("1.00"), ge=0, le=100)
    quote_amount: Decimal = Field(..., ge=0)
    currency: str = Field(default="CHF", max_length=3)
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    payment_date: Optional[date] = None
    status: BuildWiseFeeStatus = BuildWiseFeeStatus.OPEN
    invoice_pdf_path: Optional[str] = None
    invoice_pdf_generated: bool = False
    tax_rate: Decimal = Field(default=Decimal("8.10"), ge=0, le=100)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    net_amount: Optional[Decimal] = Field(None, ge=0)
    gross_amount: Optional[Decimal] = Field(None, ge=0)
    fee_details: Optional[str] = None
    notes: Optional[str] = None

    @validator('fee_amount')
    def validate_fee_amount(cls, v, values):
        if 'quote_amount' in values and v > values['quote_amount']:
            raise ValueError('Gebührenbetrag darf nicht höher als Angebotsbetrag sein')
        return v

    @validator('tax_amount', 'net_amount', 'gross_amount', pre=True)
    def calculate_amounts(cls, v, values):
        if v is None and 'fee_amount' in values and 'tax_rate' in values:
            fee_amount = values['fee_amount']
            tax_rate = values['tax_rate']
            net_amount = fee_amount
            tax_amount = net_amount * (tax_rate / 100)
            gross_amount = net_amount + tax_amount
            return {
                'tax_amount': tax_amount,
                'net_amount': net_amount,
                'gross_amount': gross_amount
            }
        return v

class BuildWiseFeeCreate(BuildWiseFeeBase):
    pass

class BuildWiseFeeUpdate(BaseModel):
    fee_amount: Optional[Decimal] = Field(None, ge=0)
    fee_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    quote_amount: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    payment_date: Optional[date] = None
    status: Optional[BuildWiseFeeStatus] = None
    invoice_pdf_path: Optional[str] = None
    invoice_pdf_generated: Optional[bool] = None
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    net_amount: Optional[Decimal] = Field(None, ge=0)
    gross_amount: Optional[Decimal] = Field(None, ge=0)
    fee_details: Optional[str] = None
    notes: Optional[str] = None

class BuildWiseFee(BuildWiseFeeBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class BuildWiseFeeStatistics(BaseModel):
    total_fees: int
    total_amount: Decimal
    total_paid: Decimal
    total_open: Decimal
    total_overdue: Decimal
    monthly_breakdown: List[dict]
    status_breakdown: dict

class BuildWiseFeeList(BaseModel):
    fees: List[BuildWiseFee]
    total: int
    page: int
    size: int 