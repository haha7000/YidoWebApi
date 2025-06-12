# app/services/ocr_service.py
import json
import os
import tempfile
import zipfile
import shutil
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from ..core.config import settings
from ..repositories.ocr_repository import OcrRepository
from ..schemas.ocr_schema import DutyFreeType, OcrProcessResponse
from ..utils.vision_ocr import VisionOcr
from ..utils.gpt_response import LotteClassificationUseGpt, ShillaClassificationUseGpt

# 전역 진행상황 변수 (기존 코드와 동일하게 유지)
progress = {"done": 0, "total": 0}

class OcrService:
    def __init__(self, db: Session):
        self.db = db
        self.ocr_repo = OcrRepository(db)
        self.vision_ocr = VisionOcr()
    
    def process_images_from_zip(self, zip_file_path: str, user_id: int, duty_free_type: DutyFreeType) -> OcrProcessResponse:
        """ZIP 파일에서 이미지 추출 및 OCR 처리"""
        global progress
        
        # 임시 디렉토리 생성
        temp_dir = tempfile.mkdtemp()
        user_uploads_dir = f"{settings.UPLOAD_DIR}/user_{user_id}"
        os.makedirs(user_uploads_dir, exist_ok=True)
        
        try:
            # ZIP 파일 해제
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # 이미지 파일 목록 추출 (macOS 메타데이터 파일 제외)
            image_files = []
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if (not file.startswith('._') and 
                        not root.endswith('__MACOSX') and 
                        file.lower().endswith((".jpg", ".png", ".jpeg"))):
                        # 이미지를 uploads 디렉토리로 복사
                        src_path = os.path.join(root, file)
                        dst_path = os.path.join(settings.UPLOAD_DIR, file)
                        shutil.copy2(src_path, dst_path)
                        image_files.append(dst_path)
            
            if not image_files:
                raise ValueError("ZIP 파일에 처리 가능한 이미지가 없습니다.")
            
            # 진행상황 초기화
            progress["total"] = len(image_files)
            progress["done"] = 0
            
            print(f"전체 이미지 수: {progress['total']}")
            
            # 각 이미지 OCR 처리
            for img_path in image_files:
                try:
                    if duty_free_type == DutyFreeType.LOTTE:
                        self._process_lotte_image(img_path, user_id)
                    else:
                        self._process_shilla_image(img_path, user_id)
                except Exception as e:
                    print(f"이미지 처리 중 오류 발생: {img_path} - {str(e)}")
                finally:
                    progress["done"] += 1
                    print(f"처리 완료: {progress['done']}/{progress['total']}")
            
            # 처리 완료 후 매칭 실행
            if duty_free_type == DutyFreeType.LOTTE:
                matched_count = self._execute_lotte_matching(user_id)
            else:
                matched_count = self._execute_shilla_matching(user_id)
            
            # 통계 조회
            stats = self.ocr_repo.get_user_statistics(user_id)
            
            return OcrProcessResponse(
                success=True,
                total_images=len(image_files),
                processed_images=progress["done"],
                matched_receipts=stats["matched_receipts"],
                unmatched_receipts=stats["unmatched_receipts"],
                processing_time=f"{len(image_files)}개 이미지 처리 완료"
            )
            
        finally:
            # 임시 디렉토리 정리
            shutil.rmtree(temp_dir)
    
    def _process_lotte_image(self, image_path: str, user_id: int):
        """롯데 면세점 이미지 처리 (기존 LotteAiOcr 로직)"""
        try:
            # OCR 및 GPT 처리
            ocr_result = self.vision_ocr.process_image(image_path)
            gpt_result = LotteClassificationUseGpt(ocr_result)
            
            # JSON 파싱
            parsed_result = json.loads(gpt_result)
            print(f"롯데 파싱 결과: {image_path}")
            print(json.dumps(parsed_result, indent=2, ensure_ascii=False))
            
            # 영수증 처리
            if "receipts" in parsed_result:
                for receipt in parsed_result["receipts"]:
                    receipt_number = receipt.get('receiptNumber', '')
                    if receipt_number:
                        self.ocr_repo.create_receipt(user_id, receipt_number, image_path)
            
            # 여권 처리
            if "passports" in parsed_result:
                for passport in parsed_result["passports"]:
                    passport_name = passport.get('name', '')
                    passport_number = passport.get('passportNumber', '')
                    passport_birthday = passport.get('birthDay', '')
                    
                    if passport_name or passport_number:
                        self.ocr_repo.create_passport(
                            user_id, passport_name, passport_number, 
                            passport_birthday, image_path
                        )
            
        except Exception as e:
            print(f"롯데 이미지 처리 오류: {e}")
            # 인식되지 않은 이미지로 저장
            self.ocr_repo.create_unrecognized_image(user_id, image_path)
    
    def _process_shilla_image(self, image_path: str, user_id: int):
        """신라 면세점 이미지 처리 (기존 ShillaAiOcr 로직)"""
        try:
            # OCR 및 GPT 처리
            ocr_result = self.vision_ocr.process_image(image_path)
            gpt_result = ShillaClassificationUseGpt(ocr_result)
            
            # JSON 파싱
            parsed_result = json.loads(gpt_result)
            print(f"신라 파싱 결과: {image_path}")
            print(json.dumps(parsed_result, indent=2, ensure_ascii=False))
            
            # 데이터 저장 여부 확인
            saved_data = False
            
            # 영수증 처리 (신라용)
            if "receipts" in parsed_result and parsed_result["receipts"]:
                for receipt in parsed_result["receipts"]:
                    receipt_number = receipt.get('receiptNumber', '')
                    passport_number = receipt.get('passportNumber', '')
                    
                    if receipt_number:
                        self.ocr_repo.create_shilla_receipt(
                            user_id, str(receipt_number), 
                            passport_number if passport_number else None, 
                            image_path
                        )
                        saved_data = True
                        print(f"신라 영수증 저장: {receipt_number}, 여권번호: {passport_number}")
            
            # 여권 처리
            if "passports" in parsed_result and parsed_result["passports"]:
                for passport in parsed_result["passports"]:
                    passport_name = passport.get('name', '')
                    passport_number = passport.get('passportNumber', '')
                    passport_birthday = passport.get('birthDay', '')
                    
                    if passport_name or passport_number:
                        self.ocr_repo.create_passport(
                            user_id, passport_name, passport_number, 
                            passport_birthday, image_path
                        )
                        saved_data = True
                        print(f"여권 저장: {passport_name}, 번호: {passport_number}")
            
            if not saved_data:
                # 인식된 데이터가 없는 경우
                print(f"인식된 데이터가 없어서 unrecognized_images에 저장: {image_path}")
                self.ocr_repo.create_unrecognized_image(user_id, image_path)
                
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 오류: {e}")
            self.ocr_repo.create_unrecognized_image(user_id, image_path)
        except Exception as e:
            print(f"신라 이미지 처리 오류: {e}")
            self.ocr_repo.create_unrecognized_image(user_id, image_path)
    
    def _execute_lotte_matching(self, user_id: int) -> int:
        """롯데 매칭 실행 (기존 matchingResult 로직)"""
        from sqlalchemy import text
        
        sql = """
        SELECT DISTINCT r.receipt_number,
               CASE
                   WHEN e."receiptNumber" IS NOT NULL THEN TRUE
                   ELSE FALSE 
               END AS is_matched
        FROM receipts r
        LEFT JOIN lotte_excel_data e
          ON r.receipt_number = e."receiptNumber"
        WHERE r.user_id = :user_id
        """
        
        results = self.db.execute(text(sql), {"user_id": user_id}).fetchall()
        matched_count = 0
        
        for row in results:
            match_log = self.ocr_repo.create_match_log(
                user_id=user_id,
                receipt_number=row[0],
                is_matched=row[1]
            )
            if row[1]:  # is_matched가 True인 경우
                matched_count += 1
        
        print(f"롯데 매칭 결과 저장 완료: {matched_count}개 매칭")
        return matched_count
    
    def _execute_shilla_matching(self, user_id: int) -> int:
        """신라 매칭 실행 (기존 shilla_matching_result 로직)"""
        from sqlalchemy import text
        
        print(f"신라 매칭 시작 - 사용자 {user_id}")
        
        # 1단계: 영수증 번호 매칭 및 여권번호 업데이트
        sql_update_passport = text("""
        UPDATE shilla_excel_data se
        SET passport_number = sr.passport_number
        FROM shilla_receipts sr
        WHERE se."receiptNumber"::text = sr.receipt_number  
        AND sr.user_id = :user_id
        AND sr.passport_number IS NOT NULL
        AND sr.passport_number != ''
        AND (se.passport_number IS NULL OR se.passport_number = '' OR se.passport_number != sr.passport_number)
        """)
        updated_rows = self.db.execute(sql_update_passport, {"user_id": user_id}).rowcount
        print(f"신라 엑셀 데이터에 여권번호 업데이트: {updated_rows}행")
        
        # 2단계: 여권 매칭 상태 업데이트
        sql_update_passport_status = text("""
        UPDATE passports p
        SET is_matched = TRUE
        FROM shilla_excel_data se
        WHERE p.passport_number = se.passport_number
        AND p.user_id = :user_id
        AND se.passport_number IS NOT NULL
        AND se.passport_number != ''
        AND p.is_matched = FALSE
        """)
        passport_updated = self.db.execute(sql_update_passport_status, {"user_id": user_id}).rowcount
        print(f"자동 여권 매칭 상태 업데이트: {passport_updated}개")
        
        # 3단계: 매칭 결과 로그 저장
        sql_matching = text("""
        SELECT DISTINCT 
            sr.receipt_number,
            CASE
                WHEN se."receiptNumber" IS NOT NULL THEN TRUE
                ELSE FALSE 
            END AS is_matched,
            se.name as excel_name,
            sr.passport_number as receipt_passport_number,
            se.passport_number as excel_passport_number,
            p.name as passport_name,
            p.birthday as passport_birthday
        FROM shilla_receipts sr
        LEFT JOIN shilla_excel_data se
          ON se."receiptNumber"::text = sr.receipt_number
        LEFT JOIN passports p
          ON (sr.passport_number = p.passport_number OR se.passport_number = p.passport_number) 
          AND p.user_id = :user_id
        WHERE sr.user_id = :user_id
        ORDER BY sr.receipt_number
        """)
        
        results = self.db.execute(sql_matching, {"user_id": user_id}).fetchall()
        matched_count = 0
        
        for row in results:
            receipt_number, is_matched, excel_name, receipt_passport_number, excel_passport_number, passport_name, passport_birthday = row
            final_passport_number = receipt_passport_number or excel_passport_number
            
            self.ocr_repo.create_match_log(
                user_id=user_id,
                receipt_number=receipt_number,
                is_matched=is_matched,
                excel_name=excel_name if is_matched else None,
                passport_number=final_passport_number,
                birthday=passport_birthday
            )
            
            if is_matched:
                matched_count += 1
        
        self.db.commit()
        print(f"신라 매칭 결과 저장 완료: {matched_count}개 매칭")
        return matched_count
    
    def get_progress(self) -> Dict[str, int]:
        """현재 처리 진행상황 반환"""
        global progress
        return progress.copy()