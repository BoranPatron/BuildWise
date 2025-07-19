from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, validator
from ..models.user import UserType, SubscriptionPlan, UserStatus


class UserBase(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=2, max_length=50)
    last_name: str = Field(..., min_length=2, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    user_type: UserType = UserType.PRIVATE


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)
    subscription_plan: SubscriptionPlan = SubscriptionPlan.BASIS
    
    # DSGVO-Einwilligungen (erforderlich)
    data_processing_consent: bool = Field(..., description="Einwilligung zur Datenverarbeitung erforderlich")
    privacy_policy_accepted: bool = Field(..., description="Datenschutzerklärung akzeptiert erforderlich")
    terms_accepted: bool = Field(..., description="AGB akzeptiert erforderlich")
    marketing_consent: bool = Field(False, description="Marketing-Einwilligung (optional)")
    
    # Dienstleister-spezifische Felder (optional)
    company_name: Optional[str] = Field(None, max_length=100)
    company_address: Optional[str] = Field(None, max_length=500)
    company_phone: Optional[str] = Field(None, max_length=20)
    company_website: Optional[str] = Field(None, max_length=200)
    business_license: Optional[str] = Field(None, max_length=100)
    tax_id: Optional[str] = Field(None, max_length=50)
    vat_id: Optional[str] = Field(None, max_length=50)
    
    # Profilinformationen (optional)
    bio: Optional[str] = Field(None, max_length=1000)
    region: Optional[str] = Field(None, max_length=100)
    languages: Optional[str] = Field(None, max_length=200)
    
    @validator('password')
    def validate_password(cls, v):
        """Validiert Passwort-Stärke"""
        if len(v) < 8:
            raise ValueError('Passwort muss mindestens 8 Zeichen lang sein')
        if not any(c.isupper() for c in v):
            raise ValueError('Passwort muss mindestens einen Großbuchstaben enthalten')
        if not any(c.islower() for c in v):
            raise ValueError('Passwort muss mindestens einen Kleinbuchstaben enthalten')
        if not any(c.isdigit() for c in v):
            raise ValueError('Passwort muss mindestens eine Zahl enthalten')
        return v
    
    @validator('user_type')
    def validate_user_type_subscription(cls, v, values):
        """Validiert User-Type und Subscription-Kombination"""
        if 'subscription_plan' in values:
            if v == UserType.SERVICE_PROVIDER and values['subscription_plan'] == SubscriptionPlan.PRO:
                raise ValueError('Dienstleister können nur das Basis-Modell wählen')
        return v


class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=2, max_length=50)
    last_name: Optional[str] = Field(None, min_length=2, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    company_name: Optional[str] = Field(None, max_length=100)
    company_address: Optional[str] = Field(None, max_length=500)
    company_phone: Optional[str] = Field(None, max_length=20)
    company_website: Optional[str] = Field(None, max_length=200)
    business_license: Optional[str] = Field(None, max_length=100)
    tax_id: Optional[str] = Field(None, max_length=50)
    vat_id: Optional[str] = Field(None, max_length=50)
    bio: Optional[str] = Field(None, max_length=1000)
    profile_image: Optional[str] = Field(None, max_length=500)
    region: Optional[str] = Field(None, max_length=100)
    languages: Optional[str] = Field(None, max_length=200)
    language_preference: Optional[str] = Field(None, max_length=10)
    subscription_plan: Optional[SubscriptionPlan] = None


class UserRead(UserBase):
    id: int
    subscription_plan: SubscriptionPlan
    subscription_start_date: Optional[date] = None
    subscription_end_date: Optional[date] = None
    subscription_active: bool
    status: UserStatus
    company_name: Optional[str] = None
    company_address: Optional[str] = None
    company_phone: Optional[str] = None
    company_website: Optional[str] = None
    business_license: Optional[str] = None
    tax_id: Optional[str] = None
    vat_id: Optional[str] = None
    bio: Optional[str] = None
    profile_image: Optional[str] = None
    region: Optional[str] = None
    languages: Optional[str] = None
    is_active: bool
    is_verified: bool
    email_verified: bool
    two_factor_enabled: bool
    language_preference: str
    permissions: Dict[str, Any] = {}
    roles: List[str] = []
    data_processing_consent: bool
    marketing_consent: bool
    privacy_policy_accepted: bool
    terms_accepted: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserProfile(BaseModel):
    id: int
    first_name: str
    last_name: str
    company_name: Optional[str] = None
    bio: Optional[str] = None
    profile_image: Optional[str] = None
    region: Optional[str] = None
    languages: Optional[str] = None
    is_verified: bool
    subscription_plan: SubscriptionPlan
    created_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class PasswordReset(BaseModel):
    email: EmailStr


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validiert neue Passwort-Stärke"""
        if len(v) < 8:
            raise ValueError('Passwort muss mindestens 8 Zeichen lang sein')
        if not any(c.isupper() for c in v):
            raise ValueError('Passwort muss mindestens einen Großbuchstaben enthalten')
        if not any(c.islower() for c in v):
            raise ValueError('Passwort muss mindestens einen Kleinbuchstaben enthalten')
        if not any(c.isdigit() for c in v):
            raise ValueError('Passwort muss mindestens eine Zahl enthalten')
        return v


class EmailVerification(BaseModel):
    token: str


class ConsentUpdate(BaseModel):
    data_processing_consent: Optional[bool] = None
    marketing_consent: Optional[bool] = None
    privacy_policy_accepted: Optional[bool] = None
    terms_accepted: Optional[bool] = None


class SubscriptionUpdate(BaseModel):
    subscription_plan: SubscriptionPlan
    subscription_start_date: Optional[date] = None
    subscription_end_date: Optional[date] = None
