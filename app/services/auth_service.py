# app/services/auth_service.py
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..core.config import settings
from ..repositories.user_repository import UserRepository
from ..schemas.user_schema import UserCreate, UserLogin
from ..schemas.token_schema import Token
from ..models.user_model import User

class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
    
    def register_user(self, user_data: UserCreate) -> User:
        """사용자 회원가입"""
        # 중복 체크
        existing_user = self.user_repo.get_user_by_username(user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 존재하는 사용자명입니다."
            )
        
        existing_email = self.user_repo.get_user_by_email(user_data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 존재하는 이메일입니다."
            )
        
        # 사용자 생성
        return self.user_repo.create_user(user_data)
    
    def login_user(self, login_data: UserLogin) -> Token:
        """사용자 로그인 및 토큰 생성"""
        user = self.user_repo.authenticate_user(login_data.username, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="사용자명 또는 비밀번호가 잘못되었습니다.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="비활성화된 사용자입니다."
            )
        
        access_token = self.create_access_token(data={"sub": user.username})
        return Token(access_token=access_token)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """JWT 액세스 토큰 생성"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[str]:
        """토큰 검증 및 사용자명 반환"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            username: str = payload.get("sub")
            return username
        except jwt.JWTError:
            return None
    
    def get_current_user(self, token: str) -> User:
        """토큰으로부터 현재 사용자 반환"""
        username = self.verify_token(token)
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 토큰입니다.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = self.user_repo.get_user_by_username(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="사용자를 찾을 수 없습니다.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user