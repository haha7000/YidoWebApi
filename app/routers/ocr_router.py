# app/routers/ocr_router.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import tempfile
import os
import time

from ..core.database import get_db
from ..core.dependencies import get_current_user
from ..services.ocr_service import OcrService
from ..services.matching_service import MatchingService
from ..services.archive_service import ArchiveService
from ..utils.excel_parser import ExcelParser
from ..schemas.ocr_schema import (
    DutyFreeType, OcrProcessResponse, ExcelUploadResponse,
    MatchingResults, ProgressResponse, UserStatistics,
    ReceiptUpdate, PassportUpdate, SessionCompleteRequest,
    HistorySearchRequest, HistorySearchResponse
)
from ..models.user_model import User

router = APIRouter(
    prefix="/ocr",
    tags=["OCR 처리"]
)

@router.post("/upload-excel", response_model=ExcelUploadResponse, summary="엑셀 데이터 업로드")
async def upload_excel(
    excel_file: UploadFile = File(..., description="엑셀 파일 (.xlsx, .xls)"),
    duty_free_type: DutyFreeType = Form(..., description="면세점 타입"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    매출 내역 엑셀 파일을 업로드하고 데이터베이스에 저장합니다.
    
    - **excel_file**: 엑셀 파일 (롯데: 교환권번호/고객명/PayBack, 신라: BILL번호/고객명/수수료)
    - **duty_free_type**: 면세점 타입 (lotte 또는 shilla)
    """
    if not excel_file.filename.lower().endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="엑셀 파일만 업로드 가능합니다 (.xlsx, .xls)"
        )
    
    # 임시 파일 저장
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
        tmp_file.write(await excel_file.read())
        tmp_path = tmp_file.name
    
    try:
        start_time = time.time()
        
        # 엑셀 파싱
        excel_parser = ExcelParser()
        
        if duty_free_type == DutyFreeType.LOTTE:
            df, records_before, total_records = excel_parser.parse_lotte_excel(tmp_path)
            table_name = 'lotte_excel_data'
        else:
            df, records_before, total_records = excel_parser.parse_shilla_excel(tmp_path)
            table_name = 'shilla_excel_data'
        
        # 데이터베이스 저장
        records_added, final_total = excel_parser.save_to_database(df, table_name)
        
        processing_time = f"{time.time() - start_time:.2f}초"
        
        return ExcelUploadResponse(
            success=True,
            records_added=records_added,
            total_records=final_total,
            processing_time=processing_time,
            duty_free_type=duty_free_type.value
        )
        
    finally:
        # 임시 파일 삭제
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@router.post("/process-images", response_model=OcrProcessResponse, summary="이미지 OCR 처리")
async def process_images(
    zip_file: UploadFile = File(..., description="이미지들이 포함된 ZIP 파일"),
    duty_free_type: DutyFreeType = Form(..., description="면세점 타입"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ZIP 파일에 포함된 이미지들을 OCR 처리하고 자동 매칭을 수행합니다.
    
    - **zip_file**: 영수증과 여권 이미지가 포함된 ZIP 파일
    - **duty_free_type**: 면세점 타입 (lotte 또는 shilla)
    """
    if not zip_file.filename.lower().endswith('.zip'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ZIP 파일만 업로드 가능합니다"
        )
    
    # 임시 파일 저장
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
        tmp_file.write(await zip_file.read())
        tmp_path = tmp_file.name
    
    try:
        ocr_service = OcrService(db)
        result = ocr_service.process_images_from_zip(tmp_path, current_user.id, duty_free_type)
        return result
        
    finally:
        # 임시 파일 삭제
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@router.get("/progress", response_model=ProgressResponse, summary="처리 진행상황")
async def get_progress():
    """
    현재 OCR 처리 진행상황을 반환합니다.
    """
    from ..services.ocr_service import progress
    
    return ProgressResponse(
        done=progress["done"],
        total=progress["total"]
    )

@router.get("/results", response_model=MatchingResults, summary="매칭 결과 조회")
async def get_matching_results(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    사용자의 영수증-여권 매칭 결과를 조회합니다.
    """
    matching_service = MatchingService(db)
    results = matching_service.get_user_matching_results(current_user.id)
    return results

@router.get("/statistics", response_model=UserStatistics, summary="사용자 통계")
async def get_user_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    사용자의 처리 통계 정보를 반환합니다.
    """
    matching_service = MatchingService(db)
    stats = matching_service.get_user_statistics(current_user.id)
    return UserStatistics(**stats)

@router.put("/receipt/{receipt_id}", summary="영수증 정보 수정")
async def update_receipt(
    receipt_id: int,
    receipt_data: ReceiptUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    영수증 정보를 수정합니다.
    
    - **receipt_id**: 수정할 영수증 ID
    - **new_receipt_number**: 새로운 영수증 번호
    - **passport_number**: 여권번호 (신라 면세점용, 선택사항)
    """
    matching_service = MatchingService(db)
    result = matching_service.update_receipt(receipt_id, current_user.id, receipt_data)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="영수증을 찾을 수 없습니다."
        )
    
    return {"message": "영수증이 성공적으로 수정되었습니다.", "updated": result}

@router.put("/passport/{passport_id}", summary="여권 정보 수정")
async def update_passport(
    passport_id: int,
    passport_data: PassportUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    여권 정보를 수정합니다.
    
    - **passport_id**: 수정할 여권 ID
    - **name**: 여권 소유자 이름
    - **passport_number**: 여권번호
    - **birthday**: 생년월일
    """
    matching_service = MatchingService(db)
    result = matching_service.update_passport(passport_id, current_user.id, passport_data)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="여권을 찾을 수 없습니다."
        )
    
    return {"message": "여권이 성공적으로 수정되었습니다.", "updated": result}

@router.get("/unmatched-passports", summary="매칭되지 않은 여권 목록")
async def get_unmatched_passports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    매칭되지 않은 여권 목록을 반환합니다.
    """
    matching_service = MatchingService(db)
    unmatched = matching_service.get_unmatched_passports(current_user.id)
    return {"unmatched_passports": unmatched}

@router.post("/complete-session", summary="처리 완료 및 세션 초기화")
async def complete_session(
    session_data: SessionCompleteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    현재 처리 세션을 완료하고 데이터를 초기화합니다.
    선택적으로 이력에 저장할 수 있습니다.
    
    - **session_name**: 세션명 (이력 저장 시 사용)
    - **save_to_history**: 이력 저장 여부
    """
    archive_service = ArchiveService(db)
    
    # 현재 상태 확인
    from ..repositories.ocr_repository import OcrRepository
    ocr_repo = OcrRepository(db)
    stats = ocr_repo.get_user_statistics(current_user.id)
    
    if stats["total_receipts"] == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="처리할 데이터가 없습니다."
        )
    
    # 이력 저장 (선택사항)
    if session_data.save_to_history:
        session_name = session_data.session_name or f"세션_{int(time.time())}"
        archive_success = archive_service.save_current_session_to_history(
            current_user.id, session_name
        )
        
        if not archive_success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="이력 저장 중 오류가 발생했습니다."
            )
    
    # 현재 세션 데이터 초기화
    clear_success = ocr_repo.clear_user_session_data(current_user.id)
    
    if not clear_success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="데이터 초기화 중 오류가 발생했습니다."
        )
    
    return {
        "message": "처리가 완료되었습니다.",
        "session_saved": session_data.save_to_history,
        "data_cleared": True
    }

@router.get("/history", summary="처리 이력 조회")
async def get_processing_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    사용자의 처리 이력을 조회합니다.
    
    - **limit**: 조회할 이력 개수 (기본: 50)
    """
    archive_service = ArchiveService(db)
    archives = archive_service.get_user_archives(current_user.id, limit)
    return {"archives": archives}

@router.post("/history/search", response_model=HistorySearchResponse, summary="이력 검색")
async def search_history(
    search_data: HistorySearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    처리 이력을 검색합니다.
    
    - **query**: 검색어 (고객명, 여권번호, 영수증번호)
    - **search_type**: 검색 타입 (all, customer, passport, receipt)
    """
    archive_service = ArchiveService(db)
    results = archive_service.search_matching_history(
        user_id=current_user.id,
        query=search_data.query,
        search_type=search_data.search_type
    )
    
    return HistorySearchResponse(
        success=True,
        results=results,
        total=len(results)
    )

@router.get("/available-passports", summary="매칭 가능한 여권 목록")
async def get_available_passports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    매칭 가능한 여권 목록을 반환합니다 (매칭되지 않은 여권들).
    """
    from sqlalchemy import text
    
    sql = text("""
    SELECT DISTINCT p.name, p.passport_number, p.birthday
    FROM passports p
    WHERE p.user_id = :user_id
    AND p.is_matched = FALSE
    ORDER BY p.name
    """)
    
    results = db.execute(sql, {"user_id": current_user.id}).fetchall()
    
    passports = []
    for row in results:
        passports.append({
            "name": row[0],
            "passport_number": row[1],
            "birthday": row[2].strftime('%Y-%m-%d') if row[2] else None
        })
    
    return {"passports": passports}

@router.post("/generate-receipts", summary="수령증 생성 및 다운로드")
async def generate_receipts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    매칭된 데이터를 기반으로 수령증을 생성하고 ZIP 파일로 반환합니다.
    """
    try:
        from ..services.receipt_service import ReceiptService
        
        receipt_service = ReceiptService(db)
        zip_path = receipt_service.generate_receipts_for_user(current_user.id)
        
        from fastapi.responses import FileResponse
        return FileResponse(
            path=zip_path,
            filename="수령증_모음.zip",
            media_type="application/zip"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"수령증 생성 중 오류가 발생했습니다: {str(e)}"
        )