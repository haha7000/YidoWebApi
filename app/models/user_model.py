# app/models/user_model.py
from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, func
from sqlalchemy.orm import relationship
from passlib.context import CryptContext

from ..core.database import Base

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # 관계 설정 (기존과 동일)
    receipts = relationship("Receipt", back_populates="user")
    passports = relationship("Passport", back_populates="user")
    shilla_receipts = relationship("ShillaReceipt", back_populates="user")
    archives = relationship("ProcessingArchive", back_populates="user")
    
    def verify_password(self, password: str) -> bool:
        """비밀번호 검증"""
        return pwd_context.verify(password, self.hashed_password)
    
    @classmethod
    def hash_password(cls, password: str) -> str:
        """비밀번호 해시화"""
        return pwd_context.hash(password)