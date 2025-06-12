# tests/test_auth.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.models.user_model import User

# 테스트용 인메모리 SQLite 데이터베이스
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    """각 테스트 전에 데이터베이스 테이블을 생성하고 후에 삭제"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

class TestAuth:
    """인증 관련 테스트"""
    
    def test_register_success(self):
        """회원가입 성공 테스트"""
        response = client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "id" in data
    
    def test_register_duplicate_username(self):
        """중복 사용자명 회원가입 실패 테스트"""
        # 첫 번째 사용자 등록
        client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test1@example.com",
                "password": "password123"
            }
        )
        
        # 같은 사용자명으로 두 번째 등록 시도
        response = client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test2@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 400
        assert "이미 존재하는 사용자명입니다" in response.json()["detail"]
    
    def test_register_duplicate_email(self):
        """중복 이메일 회원가입 실패 테스트"""
        # 첫 번째 사용자 등록
        client.post(
            "/auth/register",
            json={
                "username": "testuser1",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        
        # 같은 이메일로 두 번째 등록 시도
        response = client.post(
            "/auth/register",
            json={
                "username": "testuser2",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 400
        assert "이미 존재하는 이메일입니다" in response.json()["detail"]
    
    def test_login_success(self):
        """로그인 성공 테스트"""
        # 사용자 등록
        client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        
        # 로그인
        response = client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "password123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_wrong_username(self):
        """잘못된 사용자명으로 로그인 실패 테스트"""
        response = client.post(
            "/auth/login",
            json={
                "username": "nonexistent",
                "password": "password123"
            }
        )
        assert response.status_code == 401
        assert "사용자명 또는 비밀번호가 잘못되었습니다" in response.json()["detail"]
    
    def test_login_wrong_password(self):
        """잘못된 비밀번호로 로그인 실패 테스트"""
        # 사용자 등록
        client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        
        # 잘못된 비밀번호로 로그인
        response = client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
        assert "사용자명 또는 비밀번호가 잘못되었습니다" in response.json()["detail"]
    
    def test_get_current_user_success(self):
        """현재 사용자 정보 조회 성공 테스트"""
        # 사용자 등록
        client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        
        # 로그인하여 토큰 획득
        login_response = client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "password123"
            }
        )
        token = login_response.json()["access_token"]
        
        # 현재 사용자 정보 조회
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
    
    def test_get_current_user_no_token(self):
        """토큰 없이 현재 사용자 정보 조회 실패 테스트"""
        response = client.get("/auth/me")
        assert response.status_code == 403  # FastAPI HTTPBearer는 403 반환
    
    def test_get_current_user_invalid_token(self):
        """잘못된 토큰으로 현재 사용자 정보 조회 실패 테스트"""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401

class TestHealthCheck:
    """기본 엔드포인트 테스트"""
    
    def test_root_endpoint(self):
        """루트 엔드포인트 테스트"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
    
    def test_health_check(self):
        """헬스 체크 엔드포인트 테스트"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "services" in data