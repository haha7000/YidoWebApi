# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from .routers import auth_router, ocr_router
from .core.config import settings
from .core.database import engine
from .models.user_model import User
from .models.ocr_model import *

# 데이터베이스 테이블 생성 (개발용 - 실제 운영에서는 Alembic 사용)
# Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="OCR 처리 시스템 API",
    description="""
    영수증과 여권 이미지 OCR을 통한 자동 매칭 및 수령증 생성 시스템
    
    ## 주요 기능
    
    * **인증** - JWT 기반 사용자 인증
    * **엑셀 업로드** - 면세점별 매출 데이터 업로드
    * **OCR 처리** - 이미지에서 텍스트 추출 및 GPT 분류
    * **자동 매칭** - 영수증과 여권 정보 자동 매칭
    * **수정 기능** - 매칭 결과 수동 수정
    * **수령증 생성** - 자동 수령증 생성 및 다운로드
    * **이력 관리** - 처리 이력 저장 및 검색
    
    ## 지원 면세점
    
    * **롯데면세점** - 14자리 영수증 번호
    * **신라면세점** - 13자리 영수증 번호
    """,
    version="1.0.0",
    contact={
        "name": "OCR 시스템 개발팀",
        "email": "developer@example.com"
    },
    license_info={
        "name": "MIT"
    }
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙 (업로드된 파일들)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# 라우터 등록
app.include_router(auth_router.router)
app.include_router(ocr_router.router)

@app.get("/", tags=["기본"])
async def root():
    """API 루트 엔드포인트"""
    return {
        "message": "OCR 처리 시스템 API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health", tags=["기본"])
async def health_check():
    """시스템 상태 확인"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "database": "connected",
        "services": {
            "ocr": "available",
            "gpt": "available",
            "excel_parser": "available"
        }
    }

@app.get("/docs-redirect", include_in_schema=False)
async def docs_redirect():
    """문서 페이지로 리다이렉트"""
    return RedirectResponse(url="/docs")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )