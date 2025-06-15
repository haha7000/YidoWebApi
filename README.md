# OCR 처리 시스템 API

영수증과 여권 이미지 OCR을 통한 자동 매칭 및 수령증 생성 시스템의 백엔드 API입니다.

## 🚀 주요 기능

- **JWT 기반 사용자 인증**
- **면세점별 엑셀 데이터 업로드** (롯데/신라)
- **이미지 OCR 처리** (macOS Vision API + OpenAI GPT)
- **영수증-여권 자동 매칭**
- **매칭 결과 수정 기능**
- **수령증 자동 생성 및 다운로드**
- **처리 이력 관리 및 검색**

## 🏗️ 시스템 아키텍처

```
OcrMasterProject/
├── app/
│   ├── main.py                 # FastAPI 앱 진입점
│   ├── core/                   # 핵심 설정
│   │   ├── config.py          # 환경변수 설정
│   │   ├── database.py        # DB 연결 관리
│   │   └── dependencies.py    # 의존성 주입
│   ├── models/                # SQLAlchemy 모델
│   │   ├── user_model.py      # 사용자 모델
│   │   └── ocr_model.py       # OCR 관련 모델
│   ├── schemas/               # Pydantic 스키마
│   │   ├── user_schema.py     # 사용자 스키마
│   │   ├── token_schema.py    # JWT 토큰 스키마
│   │   └── ocr_schema.py      # OCR 요청/응답 스키마
│   ├── routers/               # API 라우터
│   │   ├── auth_router.py     # 인증 API
│   │   └── ocr_router.py      # OCR 처리 API
│   ├── services/              # 비즈니스 로직
│   │   ├── auth_service.py    # 인증 서비스
│   │   ├── ocr_service.py     # OCR 처리 서비스
│   │   ├── matching_service.py # 매칭 서비스
│   │   ├── archive_service.py # 아카이브 서비스
│   │   └── receipt_service.py # 수령증 생성 서비스
│   ├── repositories/          # 데이터 접근 계층
│   │   ├── user_repository.py # 사용자 데이터 CRUD
│   │   └── ocr_repository.py  # OCR 데이터 CRUD
│   └── utils/                 # 유틸리티
│       ├── vision_ocr.py      # macOS Vision OCR
│       ├── gpt_response.py    # GPT 응답 처리
│       └── excel_parser.py    # 엑셀 파싱
├── tests/                     # 테스트 코드
├── uploads/                   # 업로드 파일 저장
├── .env                       # 환경변수
└── requirements.txt           # 의존성 패키지
```

## 📋 시스템 요구사항

### 필수 요구사항
- **Python 3.9+**
- **PostgreSQL 12+**
- **macOS** (Vision 프레임워크 사용)
- **OpenAI API Key**

### 지원 면세점
- **롯데면세점**: 14자리 영수증 번호
- **신라면세점**: 13자리 영수증 번호

## 🛠️ 설치 및 실행

### 1. 프로젝트 클론
```bash
git clone <repository-url>
cd OcrMasterProject
```

### 2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 또는 venv\Scripts\activate  # Windows
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 환경변수 설정
```bash
cp .env.example .env
# .env 파일을 열어서 실제 값들로 수정
```

### 5. 데이터베이스 설정
```bash
# PostgreSQL에서 데이터베이스 생성
createdb my_test_db

# 테이블 생성 (개발용)
python -c "
from app.core.database import engine
from app.models.user_model import User
from app.models.ocr_model import *
Base.metadata.create_all(bind=engine)
print('데이터베이스 테이블 생성 완료')
"
```

### 6. 서버 실행
```bash
# 개발 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# 또는 Python으로 직접 실행
python -m app.main
```

### 7. API 문서 확인
브라우저에서 다음 URL로 접속:
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

## 📚 API 문서

### 인증 API

#### 1. 회원가입
```http
POST /auth/register
Content-Type: application/json

{
    "username": "string",
    "email": "string",
    "password": "string"
}
```

**응답**
```json
{
    "id": "integer",
    "username": "string",
    "email": "string",
    "created_at": "datetime"
}
```

**사용 예시**
```bash
curl -X POST "http://localhost:8001/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }'
```

#### 2. 로그인
```http
POST /auth/login
Content-Type: application/json

{
    "username": "string",
    "password": "string"
}
```

**응답**
```json
{
    "access_token": "string",
    "token_type": "bearer"
}
```

**사용 예시**
```bash
curl -X POST "http://localhost:8001/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

#### 3. 현재 사용자 정보 조회
```http
GET /auth/me
Authorization: Bearer <token>
```

**응답**
```json
{
    "id": "integer",
    "username": "string",
    "email": "string",
    "created_at": "datetime"
}
```

**사용 예시**
```bash
curl -X GET "http://localhost:8001/auth/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### 4. 비밀번호 변경
```http
PUT /auth/change-password
Authorization: Bearer <token>
Content-Type: application/json

{
    "current_password": "string",
    "new_password": "string"
}
```

**응답**
```json
{
    "message": "비밀번호가 성공적으로 변경되었습니다."
}
```

**사용 예시**
```bash
curl -X PUT "http://localhost:8001/auth/change-password" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "oldpassword123",
    "new_password": "newpassword123"
  }'
```

### OCR 처리 API

#### 1. 엑셀 데이터 업로드
```http
POST /ocr/upload-excel
Authorization: Bearer <token>
Content-Type: multipart/form-data

{
    "excel_file": "file",
    "duty_free_type": "lotte|shilla"
}
```

**응답**
```json
{
    "message": "string",
    "total_records": "integer",
    "processed_records": "integer"
}
```

**사용 예시**
```bash
curl -X POST "http://localhost:8001/ocr/upload-excel" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -F "excel_file=@/path/to/lotte_data.xlsx" \
  -F "duty_free_type=lotte"
```

#### 2. 이미지 OCR 처리
```http
POST /ocr/process-images
Authorization: Bearer <token>
Content-Type: multipart/form-data

{
    "zip_file": "file",
    "duty_free_type": "lotte|shilla"
}
```

**응답**
```json
{
    "message": "string",
    "total_images": "integer",
    "processed_images": "integer",
    "ocr_results": [
        {
            "image_name": "string",
            "receipt_number": "string",
            "passport_number": "string",
            "confidence": "float"
        }
    ]
}
```

**사용 예시**
```bash
curl -X POST "http://localhost:8001/ocr/process-images" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -F "zip_file=@/path/to/images.zip" \
  -F "duty_free_type=lotte"
```

#### 3. 매칭 결과 조회
```http
GET /ocr/results
Authorization: Bearer <token>
Query Parameters:
- page: integer (default: 1)
- limit: integer (default: 10)
- duty_free_type: string (optional)
- start_date: string (optional)
- end_date: string (optional)
- status: string (optional) - "matched", "unmatched", "error"
```

**응답**
```json
{
    "total": "integer",
    "page": "integer",
    "limit": "integer",
    "results": [
        {
            "id": "integer",
            "receipt_number": "string",
            "passport_number": "string",
            "duty_free_type": "string",
            "matched_at": "datetime",
            "confidence": "float",
            "status": "string"
        }
    ]
}
```

**사용 예시**
```bash
curl -X GET "http://localhost:8001/ocr/results?page=1&limit=10&duty_free_type=lotte&start_date=2024-01-01&end_date=2024-03-20" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### 4. 매칭 결과 수정
```http
PUT /ocr/results/{result_id}
Authorization: Bearer <token>
Content-Type: application/json

{
    "receipt_number": "string",
    "passport_number": "string"
}
```

**응답**
```json
{
    "id": "integer",
    "receipt_number": "string",
    "passport_number": "string",
    "updated_at": "datetime"
}
```

**사용 예시**
```bash
curl -X PUT "http://localhost:8001/ocr/results/123" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "receipt_number": "12345678901234",
    "passport_number": "M12345678"
  }'
```

#### 5. 수령증 생성 및 다운로드
```http
POST /ocr/generate-receipts
Authorization: Bearer <token>
Content-Type: application/json

{
    "start_date": "string",
    "end_date": "string",
    "duty_free_type": "string"
}
```

**응답**
- Content-Type: application/zip
- Content-Disposition: attachment; filename="receipts.zip"

**사용 예시**
```bash
curl -X POST "http://localhost:8001/ocr/generate-receipts" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01",
    "end_date": "2024-03-20",
    "duty_free_type": "lotte"
  }' \
  --output receipts.zip
```

#### 6. 매칭 결과 삭제
```http
DELETE /ocr/results/{result_id}
Authorization: Bearer <token>
```

**응답**
```json
{
    "message": "매칭 결과가 성공적으로 삭제되었습니다."
}
```

**사용 예시**
```bash
curl -X DELETE "http://localhost:8001/ocr/results/123" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 아카이브 API

#### 1. 처리 이력 조회
```http
GET /archive/history
Authorization: Bearer <token>
Query Parameters:
- page: integer (default: 1)
- limit: integer (default: 10)
- duty_free_type: string (optional)
- start_date: string (optional)
- end_date: string (optional)
```

**응답**
```json
{
    "total": "integer",
    "page": "integer",
    "limit": "integer",
    "results": [
        {
            "id": "integer",
            "duty_free_type": "string",
            "processed_at": "datetime",
            "total_records": "integer",
            "success_count": "integer",
            "error_count": "integer"
        }
    ]
}
```

**사용 예시**
```bash
curl -X GET "http://localhost:8001/archive/history?page=1&limit=10&duty_free_type=lotte" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### 2. 처리 이력 상세 조회
```http
GET /archive/history/{history_id}
Authorization: Bearer <token>
```

**응답**
```json
{
    "id": "integer",
    "duty_free_type": "string",
    "processed_at": "datetime",
    "total_records": "integer",
    "success_count": "integer",
    "error_count": "integer",
    "details": [
        {
            "receipt_number": "string",
            "passport_number": "string",
            "status": "string",
            "error_message": "string"
        }
    ]
}
```

**사용 예시**
```bash
curl -X GET "http://localhost:8001/archive/history/123" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### 3. 처리 이력 삭제
```http
DELETE /archive/history/{history_id}
Authorization: Bearer <token>
```

**응답**
```json
{
    "message": "처리 이력이 성공적으로 삭제되었습니다."
}
```

**사용 예시**
```bash
curl -X DELETE "http://localhost:8001/archive/history/123" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 통계 API

#### 1. 일일 처리 통계
```http
GET /stats/daily
Authorization: Bearer <token>
Query Parameters:
- start_date: string (required)
- end_date: string (required)
- duty_free_type: string (optional)
```

**응답**
```json
{
    "total_processed": "integer",
    "total_matched": "integer",
    "total_errors": "integer",
    "daily_stats": [
        {
            "date": "string",
            "processed": "integer",
            "matched": "integer",
            "errors": "integer"
        }
    ]
}
```

**사용 예시**
```bash
curl -X GET "http://localhost:8001/stats/daily?start_date=2024-01-01&end_date=2024-03-20&duty_free_type=lotte" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 에러 응답
모든 API는 에러 발생 시 다음과 같은 형식으로 응답합니다:

```json
{
    "detail": "string",
    "status_code": "integer"
}
```

### 상태 코드
- 200: 성공
- 201: 생성 성공
- 400: 잘못된 요청
- 401: 인증 실패
- 403: 권한 없음
- 404: 리소스를 찾을 수 없음
- 422: 유효성 검사 실패
- 500: 서버 내부 오류

### API 사용 팁
1. 모든 API 요청에는 JWT 토큰이 필요합니다 (로그인 API 제외)
2. 파일 업로드 시 multipart/form-data 형식을 사용합니다
3. 날짜 형식은 'YYYY-MM-DD'를 사용합니다
4. 페이지네이션은 page와 limit 파라미터로 제어합니다
5. 대용량 파일 처리 시 타임아웃이 발생할 수 있으니 주의하세요

## 🔧 환경변수 설정

`.env` 파일에서 다음 환경변수들을 설정해야 합니다:

```env
# 데이터베이스 설정
DATABASE_USER=test_user
DATABASE_PASSWORD=0000
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=my_test_db

# JWT 설정
SECRET_KEY=your-super-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# OpenAI API
OPENAI_API_KEY=your-openai-api-key

# 파일 경로
UPLOAD_DIR=uploads
LOTTE_PROMPT_PATH=/path/to/LottePrompt.txt
SHILLA_PROMPT_PATH=/path/to/ShillaPrompt.txt
RECEIPT_TEMPLATE_PATH=/path/to/수령증양식.xlsx
OUTPUT_DIR=/path/to/output/directory
```

## 🧪 테스트

```bash
# 단위 테스트 실행
pytest

# 특정 테스트 파일 실행
pytest tests/test_auth.py

# 커버리지 포함 테스트
pytest --cov=app tests/
```

## 📊 데이터베이스 스키마

### 주요 테이블
- **users**: 사용자 정보
- **receipts**: 롯데 영수증 정보
- **shilla_receipts**: 신라 영수증 정보
- **passports**: 여권 정보
- **receipt_match_log**: 매칭 로그
- **processing_archives**: 처리 아카이브
- **matching_history**: 매칭 이력

### 동적 테이블
- **lotte_excel_data**: 롯데 엑셀 데이터
- **shilla_excel_data**: 신라 엑셀 데이터

## 🚀 배포

### Docker를 사용한 배포
```bash
# Dockerfile 생성 후
docker build -t ocr-api .
docker run -p 8001:8001 ocr-api
```

### 프로덕션 서버 실행
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --workers 4
```

## 🔍 문제 해결

### 일반적인 문제들

#### 1. macOS Vision 모듈 오류
```bash
# PyObjC 재설치
pip uninstall pyobjc-core pyobjc-framework-Vision pyobjc-framework-Quartz
pip install pyobjc-core pyobjc-framework-Vision pyobjc-framework-Quartz
```

#### 2. 데이터베이스 연결 오류
- PostgreSQL 서비스가 실행 중인지 확인
- 데이터베이스 자격증명이 올바른지 확인
- 방화벽 설정 확인

#### 3. OpenAI API 오류
- API 키가 올바른지 확인
- API 할당량이 남아있는지 확인

## 📝 라이센스

MIT License

## 🤝 기여하기

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📞 지원

문제가 발생하거나 질문이 있으시면 이슈를 생성해주세요.

---

**주의**: 이 시스템은 macOS Vision 프레임워크를 사용하므로 macOS 환경에서만 완전히 작동합니다.