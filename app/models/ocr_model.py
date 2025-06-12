# app/models/ocr_model.py
from sqlalchemy import Column, Integer, String, Text, Boolean, Date, ForeignKey, TIMESTAMP, func, Float, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
import enum

from ..core.database import Base

class DutyFreeType(enum.Enum):
    LOTTE = "lotte"
    SHILLA = "shilla"

class Receipt(Base):
    """롯데 면세점 영수증 모델"""
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_path = Column(Text, nullable=True)
    receipt_number = Column(String(50), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    user = relationship("User", back_populates="receipts")
    
    def __str__(self):
        return f"Receipt(receipt_number={self.receipt_number})"
    
    def __repr__(self):
        return f"Receipt(receipt_number={self.receipt_number})"

class ShillaReceipt(Base):
    """신라 면세점 영수증 모델"""
    __tablename__ = "shilla_receipts"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_path = Column(Text, nullable=True)
    receipt_number = Column(String(50), nullable=True)
    passport_number = Column(String(20), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    user = relationship("User", back_populates="shilla_receipts")

class Passport(Base):
    """여권 정보 모델"""
    __tablename__ = "passports"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_path = Column(Text, nullable=False)
    passport_number = Column(String(20), nullable=True)
    birthday = Column(Date, nullable=True)
    name = Column(String(100), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    is_matched = Column(Boolean, default=False)

    user = relationship("User", back_populates="passports")

class ReceiptMatchLog(Base):
    """영수증 매칭 로그 모델"""
    __tablename__ = "receipt_match_log"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receipt_number = Column(Text, nullable=True)
    is_matched = Column(Boolean, nullable=False)
    checked_at = Column(TIMESTAMP, server_default=func.now())
    excel_name = Column(String(100), nullable=True)
    passport_number = Column(String(20), nullable=True)
    birthday = Column(Date, nullable=True)

class UnrecognizedImage(Base):
    """인식되지 않은 이미지 모델"""
    __tablename__ = "unrecognized_images"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_path = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    def __str__(self):
        return f"UnrecognizedImage(file_path={self.file_path})"
    
    def __repr__(self):
        return f"UnrecognizedImage(file_path={self.file_path})"

class ProcessingArchive(Base):
    """처리 완료된 세션 아카이브"""
    __tablename__ = "processing_archives"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_name = Column(String(200), nullable=False)
    archive_date = Column(TIMESTAMP, server_default=func.now())
    
    # 통계 정보
    total_receipts = Column(Integer, default=0)
    matched_receipts = Column(Integer, default=0)
    total_passports = Column(Integer, default=0)
    matched_passports = Column(Integer, default=0)
    
    # 메타데이터
    duty_free_type = Column(String(20), nullable=True)
    notes = Column(Text, nullable=True)
    
    # 상세 데이터 (JSON)
    archive_data = Column(JSONB, nullable=True)
    
    user = relationship("User", back_populates="archives")
    matching_histories = relationship("MatchingHistory", back_populates="archive")

class MatchingHistory(Base):
    """매칭 이력 저장"""
    __tablename__ = "matching_history"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    archive_id = Column(Integer, ForeignKey("processing_archives.id"), nullable=True)
    
    # 매칭 정보
    customer_name = Column(String(100), nullable=True)
    passport_number = Column(String(20), nullable=True)
    receipt_numbers = Column(Text, nullable=True)  # JSON 문자열로 저장
    excel_data = Column(JSONB, nullable=True)
    
    # 매칭 상태
    match_status = Column(String(50), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    user = relationship("User")
    archive = relationship("ProcessingArchive", back_populates="matching_histories")