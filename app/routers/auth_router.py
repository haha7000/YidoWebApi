# app/routers/auth_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.dependencies import get_current_user
from ..services.auth_service import AuthService
from ..schemas.user_schema import UserCreate, UserLogin, UserResponse
from ..schemas.token_schema import Token

router = APIRouter(
    prefix="/auth",
    tags=["인증"]
)

@router.post("/register", response_model=UserResponse, summary="회원가입")
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    새 사용자를 등록합니다.
    
    - **username**: 사용자명 (고유값)
    - **email**: 이메일 주소 (고유값)
    - **password**: 비밀번호
    """
    auth_service = AuthService(db)
    user = auth_service.register_user(user_data)
    return user

@router.post("/login", response_model=Token, summary="로그인")
async def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    사용자 로그인을 수행하고 JWT 토큰을 반환합니다.
    
    - **username**: 사용자명
    - **password**: 비밀번호
    
    Returns:
    - **access_token**: JWT 액세스 토큰
    - **token_type**: 토큰 타입 (bearer)
    """
    auth_service = AuthService(db)
    token = auth_service.login_user(login_data)
    return token

@router.get("/me", response_model=UserResponse, summary="현재 사용자 정보")
async def get_current_user_info(
    current_user = Depends(get_current_user)
):
    """
    현재 인증된 사용자의 정보를 반환합니다.
    
    헤더에 Bearer 토큰이 필요합니다.
    """
    return current_user

@router.post("/logout", summary="로그아웃")
async def logout():
    """
    로그아웃 처리 (클라이언트 측에서 토큰 삭제 필요)
    """
    return {"message": "로그아웃되었습니다. 클라이언트에서 토큰을 삭제해주세요."}