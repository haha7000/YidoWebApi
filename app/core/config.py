# app/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # 데이터베이스 설정
    DATABASE_USER: str = "test_user"
    DATABASE_PASSWORD: str = "0000"
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: str = "5432"
    DATABASE_NAME: str = "my_test_db"
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
    
    # JWT 설정
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24시간
    
    # OpenAI 설정
    OPENAI_API_KEY: Optional[str] = None
    
    # 파일 업로드 설정
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    
    # 템플릿 경로 설정
    LOTTE_PROMPT_PATH: str = "/Users/gimdonghun/Documents/DbTest/LottePrompt.txt"
    SHILLA_PROMPT_PATH: str = "/Users/gimdonghun/Documents/DbTest/ShillaPrompt.txt"
    RECEIPT_TEMPLATE_PATH: str = "/Users/gimdonghun/Downloads/수령증양식.xlsx"
    OUTPUT_DIR: str = "/Users/gimdonghun/Downloads/수령증_완성본"
    
    class Config:
        env_file = ".env"

settings = Settings()