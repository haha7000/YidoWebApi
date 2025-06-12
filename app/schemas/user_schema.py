# app/schemas/user_schema.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    """사용자 생성 스키마"""
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    """사용자 로그인 스키마"""
    username: str
    password: str

class UserResponse(BaseModel):
    """사용자 응답 스키마"""
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    """사용자 정보 수정 스키마"""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    
class PasswordChange(BaseModel):
    """비밀번호 변경 스키마"""
    current_password: str
    new_password: str