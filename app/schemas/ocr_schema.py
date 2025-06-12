# app/schemas/ocr_schema.py
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum

class DutyFreeType(str, Enum):
    LOTTE = "lotte"
    SHILLA = "shilla"

# === 업로드 관련 스키마 ===
class ExcelUploadResponse(BaseModel):
    """엑셀 업로드 응답"""
    success: bool
    records_added: int
    total_records: int
    processing_time: str
    duty_free_type: str

class OcrProcessRequest(BaseModel):
    """OCR 처리 요청"""
    duty_free_type: DutyFreeType

class OcrProcessResponse(BaseModel):
    """OCR 처리 응답"""
    success: bool
    total_images: int
    processed_images: int
    matched_receipts: int
    unmatched_receipts: int
    processing_time: str
    
# === 영수증 관련 스키마 ===
class ReceiptResponse(BaseModel):
    """영수증 응답 스키마"""
    id: int
    receipt_number: Optional[str]
    file_path: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class ShillaReceiptResponse(BaseModel):
    """신라 영수증 응답 스키마"""
    id: int
    receipt_number: Optional[str]
    passport_number: Optional[str]
    file_path: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class ReceiptUpdate(BaseModel):
    """영수증 수정 스키마"""
    new_receipt_number: str
    passport_number: Optional[str] = None

# === 여권 관련 스키마 ===
class PassportResponse(BaseModel):
    """여권 응답 스키마"""
    id: int
    name: Optional[str]
    passport_number: Optional[str]
    birthday: Optional[date]
    file_path: str
    is_matched: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class PassportUpdate(BaseModel):
    """여권 수정 스키마"""
    name: Optional[str] = None
    passport_number: Optional[str] = None
    birthday: Optional[date] = None

# === 매칭 결과 관련 스키마 ===
class CustomerMatchResult(BaseModel):
    """고객 매칭 결과"""
    name: str
    excel_name: Optional[str] = None
    passport_name: Optional[str] = None
    receipt_numbers: List[str]
    receipt_ids: Optional[List[int]] = None
    passport_number: Optional[str] = None
    birthday: Optional[date] = None
    needs_update: bool = False
    passport_match_status: str = "확인 필요"
    passport_status: str = "unknown"

class MatchingResults(BaseModel):
    """전체 매칭 결과"""
    matched_customers: List[CustomerMatchResult]
    unmatched_receipts: List[ReceiptResponse]
    duty_free_type: str
    statistics: Dict[str, Any]

# === 아카이브 관련 스키마 ===
class SessionCompleteRequest(BaseModel):
    """세션 완료 요청"""
    session_name: Optional[str] = None
    save_to_history: bool = False

class ArchiveResponse(BaseModel):
    """아카이브 응답"""
    id: int
    session_name: str
    archive_date: datetime
    total_receipts: int
    matched_receipts: int
    total_passports: int
    matched_passports: int
    duty_free_type: Optional[str]
    completion_rate: float
    
    class Config:
        from_attributes = True

class HistorySearchRequest(BaseModel):
    """이력 검색 요청"""
    query: str
    search_type: str = "all"  # all, customer, passport, receipt

class HistorySearchResponse(BaseModel):
    """이력 검색 응답"""
    success: bool
    results: List[Dict[str, Any]]
    total: int

# === 수령증 생성 관련 스키마 ===
class ReceiptGenerationResponse(BaseModel):
    """수령증 생성 응답"""
    success: bool
    generated_count: int
    download_path: str

# === 진행상황 관련 스키마 ===
class ProgressResponse(BaseModel):
    """처리 진행상황 응답"""
    done: int
    total: int
    percentage: float = 0.0
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.total > 0:
            self.percentage = round((self.done / self.total) * 100, 1)

# === 통계 관련 스키마 ===
class UserStatistics(BaseModel):
    """사용자 통계"""
    total_receipts: int
    matched_receipts: int
    total_passports: int
    matched_passports: int
    unmatched_receipts: int
    unmatched_passports: int
    duty_free_type: str