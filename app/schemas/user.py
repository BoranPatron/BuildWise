from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from ..models.user import UserType


class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None
    user_type: UserType = UserType.PRIVATE

    class Config:
        orm_mode = True


class UserCreate(UserBase):
    password: str


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
    
    class Config:
        orm_mode = True


class UserRead(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


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
        orm_mode = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class PasswordReset(BaseModel):
    email: EmailStr


class PasswordChange(BaseModel):
    current_password: str
    new_password: str
