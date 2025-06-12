# app/core/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from typing import Optional

from .database import get_db
from .config import settings
from ..repositories.user_repository import UserRepository

security = HTTPBearer()

def get_current_user(
    token: str = Depends(security), 
    db: Session = Depends(get_db)
):
    """현재 인증된 사용자 반환"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Bearer 토큰에서 실제 토큰 추출
        token_str = token.credentials if hasattr(token, 'credentials') else str(token)
        
        payload = jwt.decode(token_str, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user_repo = UserRepository(db)
    user = user_repo.get_user_by_username(username)
    if user is None:
        raise credentials_exception
    
    return user

def get_current_user_optional(
    token: Optional[str] = Depends(security), 
    db: Session = Depends(get_db)
):
    """선택적 사용자 인증 (로그인 안해도 되는 엔드포인트용)"""
    if not token:
        return None
    
    try:
        return get_current_user(token, db)
    except HTTPException:
        return None