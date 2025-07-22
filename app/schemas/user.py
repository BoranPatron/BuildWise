from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from pydantic.networks import EmailStr
from ..models.user import UserType


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
    company_phone: Optional[str] = None
    company_website: Optional[str] = None
    business_license: Optional[str] = None
    bio: Optional[str] = None
    profile_image: Optional[str] = None
    region: Optional[str] = None
    languages: Optional[str] = None
    language_preference: Optional[str] = None


class UserRead(UserBase):
    id: int
    company_name: Optional[str] = None
    company_address: Optional[str] = None
    company_phone: Optional[str] = None
    company_website: Optional[str] = None
    business_license: Optional[str] = None
    bio: Optional[str] = None
    profile_image: Optional[str] = None
    region: Optional[str] = None
    languages: Optional[str] = None
    is_active: bool
    is_verified: bool
    email_verified: bool
    two_factor_enabled: bool
    language_preference: str
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
    new_password: str
