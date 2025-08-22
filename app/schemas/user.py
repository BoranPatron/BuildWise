from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from pydantic.networks import EmailStr
from ..models.user import UserType, UserRole, SubscriptionPlan, SubscriptionStatus


class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None
    user_type: UserType = UserType.PRIVATE


class UserCreate(UserBase):
    password: str
    data_processing_consent: bool = False
    marketing_consent: bool = False
    privacy_policy_accepted: bool = False
    terms_accepted: bool = False


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    company_name: Optional[str] = None
    company_address: Optional[str] = None
    company_uid: Optional[str] = None
    company_phone: Optional[str] = None
    company_website: Optional[str] = None
    business_license: Optional[str] = None
    bio: Optional[str] = None
    profile_image: Optional[str] = None
    region: Optional[str] = None
    languages: Optional[str] = None
    language_preference: Optional[str] = None
    # Zusatzfelder für dynamische Client-Flags (z. B. Tutorial-/Tour-Status)
    consent_fields: Optional[dict] = None


class UserRead(UserBase):
    id: int
    company_name: Optional[str] = None
    company_address: Optional[str] = None
    company_uid: Optional[str] = None
    company_phone: Optional[str] = None
    company_website: Optional[str] = None
    business_license: Optional[str] = None
    bio: Optional[str] = None
    profile_image: Optional[str] = None
    region: Optional[str] = None
    languages: Optional[str] = None
    
    # Rollen-Felder
    user_role: Optional[UserRole] = None
    role_selected: bool = False
    role_selected_at: Optional[datetime] = None
    role_selection_modal_shown: bool = False
    
    # Onboarding-Felder
    first_login_completed: bool = False
    onboarding_completed: bool = False
    onboarding_step: int = 0
    onboarding_started_at: Optional[datetime] = None
    onboarding_completed_at: Optional[datetime] = None
    
    # Subscription-Felder
    subscription_plan: SubscriptionPlan = SubscriptionPlan.BASIS
    subscription_status: SubscriptionStatus = SubscriptionStatus.INACTIVE
    subscription_id: Optional[str] = None
    customer_id: Optional[str] = None
    subscription_start: Optional[datetime] = None
    subscription_end: Optional[datetime] = None
    max_gewerke: int = 3
    is_active: bool
    is_verified: bool
    email_verified: bool
    two_factor_enabled: bool
    language_preference: str
    # DSGVO-Erweiterung: dynamische Felder für Einwilligungen und Client-Flags
    consent_fields: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserProfile(BaseModel):
    id: int
    first_name: str
    last_name: str
    company_name: Optional[str] = None
    company_address: Optional[str] = None
    bio: Optional[str] = None
    profile_image: Optional[str] = None
    region: Optional[str] = None
    languages: Optional[str] = None
    is_verified: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class PasswordReset(BaseModel):
    email: EmailStr


class PasswordChange(BaseModel):
    current_password: str
    new_password: str
