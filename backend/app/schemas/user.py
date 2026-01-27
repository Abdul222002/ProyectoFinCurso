"""
Pydantic Schemas para Usuarios
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from enum import Enum


class UserRoleEnum(str, Enum):
    """Roles de usuario"""
    ADMIN = "admin"
    PREMIUM = "premium"
    FREE = "free"


class UserBase(BaseModel):
    """Schema base de usuario"""
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    
    class Config:
        from_attributes = True


class UserCreate(UserBase):
    """Schema para registro de usuario"""
    password: str = Field(min_length=6, max_length=100)


class UserLogin(BaseModel):
    """Schema para login"""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """Schema de respuesta de usuario"""
    id: int
    role: UserRoleEnum
    coins: int
    total_points: int
    level: int
    experience: int
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema de respuesta de autenticación"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
