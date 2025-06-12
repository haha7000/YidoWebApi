# app/services/matching_service.py
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..repositories.ocr_repository import OcrRepository
from ..schemas.ocr_schema import (
    MatchingResults, CustomerMatchResult, ReceiptResponse, 
    ReceiptUpdate, PassportUpdate, UserStatistics  # ← UserStatistics 추가
)

class MatchingService:
    """매칭 관련 비즈니스 로직 (기존 로직 100% 보존)"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ocr_repo = OcrRepository(db)
    
    # app/services/matching_service.py

    def get_user_matching_results(self, user_id: int) -> MatchingResults:
        """사용자의 매칭 결과 조회"""
        # 면세점 타입 자동 감지
        duty_free_type = self._detect_duty_free_type(user_id)
        
        if duty_free_type == "shilla":
            matched_customers, unmatched_receipts = self._get_shilla_results(user_id)
        else:
            matched_customers, unmatched_receipts = self._get_lotte_results(user_id)
        
        # 통계 계산
        stats_dict = self.ocr_repo.get_user_statistics(user_id)
        
        # 방법 1: UserStatistics 객체로 변환 (스키마도 UserStatistics로 변경해야 함)
        # stats = UserStatistics(**stats_dict)
        
        # 방법 2: Dict 그대로 사용 (현재 스키마에 맞춤)
        stats = stats_dict
        
        return MatchingResults(
            matched_customers=matched_customers,
            unmatched_receipts=unmatched_receipts,
            duty_free_type=duty_free_type,
            statistics=stats  # ← Dict 전달
    )
    
    def _detect_duty_free_type(self, user_id: int) -> str:
        """사용자의 면세점 타입 감지"""
        try:
            shilla_count_sql = text("SELECT COUNT(*) FROM shilla_receipts WHERE user_id = :user_id")
            lotte_count_sql = text("SELECT COUNT(*) FROM receipts WHERE user_id = :user_id")
            
            shilla_count = self.db.execute(shilla_count_sql, {"user_id": user_id}).scalar() or 0
            lotte_count = self.db.execute(lotte_count_sql, {"user_id": user_id}).scalar() or 0
            
            return "shilla" if shilla_count >= lotte_count else "lotte"
        except Exception:
            return "lotte"
    
    def _get_shilla_results(self, user_id: int) -> tuple:
        """신라 면세점 매칭 결과 조회 (기존 fetch_shilla_results_with_receipt_ids 로직)"""
        matched_sql = text("""
        SELECT DISTINCT 
            sr.id as receipt_id,
            sr.receipt_number,
            se.name as excel_name,
            sr.passport_number as receipt_passport_number,
            se.passport_number as excel_passport_number,
            p.name as passport_name,
            p.birthday as passport_birthday,
            p.is_matched as passport_is_matched,
            CASE 
                WHEN p.passport_number IS NOT NULL AND p.is_matched = TRUE THEN 'passport_matched'
                WHEN p.passport_number IS NOT NULL AND p.is_matched = FALSE THEN 'passport_needs_update'  
                WHEN p.passport_number IS NULL AND (sr.passport_number IS NOT NULL OR se.passport_number IS NOT NULL) THEN 'passport_missing'
                WHEN p.passport_number IS NULL AND sr.passport_number IS NULL AND se.passport_number IS NULL THEN 'passport_not_provided'
                ELSE 'passport_unknown'
            END as passport_status,
            COALESCE(p.name, se.name) as order_name,
            se."PayBack" as payback_amount
        FROM shilla_receipts sr
        JOIN shilla_excel_data se ON se."receiptNumber"::text = sr.receipt_number
        LEFT JOIN passports p ON (sr.passport_number = p.passport_number OR se.passport_number = p.passport_number) 
                               AND p.user_id = :user_id
        WHERE sr.user_id = :user_id
        ORDER BY order_name, sr.receipt_number
        """)
        
        matched = self.db.execute(matched_sql, {"user_id": user_id}).fetchall()
        
        # 매칭되지 않은 영수증 조회
        unmatched_sql = text("""
        SELECT DISTINCT sr.id, sr.receipt_number, sr.file_path, sr.created_at
        FROM shilla_receipts sr
        LEFT JOIN shilla_excel_data se ON se."receiptNumber"::text = sr.receipt_number
        WHERE se."receiptNumber" IS NULL AND sr.user_id = :user_id
        ORDER BY sr.receipt_number
        """)
        unmatched = self.db.execute(unmatched_sql, {"user_id": user_id}).fetchall()
        
        # 고객별 그룹화
        customer_data = {}
        receipt_id_mapping = {}
        
        for row in matched:
            (receipt_id, receipt_number, excel_name, receipt_passport_number, 
             excel_passport_number, passport_name, passport_birthday, 
             passport_is_matched, passport_status, order_name, payback_amount) = row
            
            receipt_id_mapping[receipt_number] = receipt_id
            final_passport_number = receipt_passport_number or excel_passport_number
            display_name = passport_name if passport_name else excel_name
            
            if final_passport_number:
                group_key = f"passport_{final_passport_number}"
            else:
                group_key = f"excel_{excel_name}_{receipt_number}"
            
            if group_key not in customer_data:
                # 매칭 상태 판단
                if passport_status == 'passport_matched':
                    match_status = '매칭됨'
                    needs_update = False
                elif passport_status == 'passport_needs_update':
                    match_status = '여권번호 수정 필요'
                    needs_update = True
                elif passport_status == 'passport_missing':
                    match_status = '여권 정보 없음'
                    needs_update = True
                elif passport_status == 'passport_not_provided':
                    match_status = '여권번호 미제공'
                    needs_update = True
                else:
                    match_status = '확인 필요'
                    needs_update = True
                
                customer_data[group_key] = CustomerMatchResult(
                    name=display_name,
                    excel_name=excel_name,
                    passport_name=passport_name,
                    receipt_numbers=[],
                    receipt_ids=[],
                    passport_number=final_passport_number,
                    birthday=passport_birthday,
                    needs_update=needs_update,
                    passport_match_status=match_status,
                    passport_status=passport_status
                )
            
            customer_data[group_key].receipt_numbers.append(receipt_number)
            customer_data[group_key].receipt_ids.append(receipt_id)
        
        matched_customers = list(customer_data.values())
        
        # 매칭되지 않은 영수증 변환
        unmatched_receipts = [
            ReceiptResponse(
                id=row[0],
                receipt_number=row[1],
                file_path=row[2],
                created_at=row[3]
            ) for row in unmatched
        ]
        
        return matched_customers, unmatched_receipts
    
    def _get_lotte_results(self, user_id: int) -> tuple:
        """롯데 면세점 매칭 결과 조회 (기존 fetch_results + matching_passport 로직)"""
        # 매칭된 영수증 조회
        matched_sql = text("""
        SELECT r.receipt_number, e.name
        FROM receipts r
        JOIN receipt_match_log m ON r.receipt_number = m.receipt_number
        JOIN lotte_excel_data e ON r.receipt_number = e."receiptNumber"
        WHERE m.is_matched = TRUE AND r.user_id = :user_id AND m.user_id = :user_id
        """)
        matched = self.db.execute(matched_sql, {"user_id": user_id}).fetchall()
        
        # 매칭되지 않은 영수증 조회
        unmatched_sql = text("""
        SELECT r.id, r.receipt_number, r.file_path, r.created_at
        FROM receipts r
        JOIN receipt_match_log rml ON r.receipt_number = rml.receipt_number
        WHERE rml.is_matched = FALSE AND r.user_id = :user_id AND rml.user_id = :user_id
        """)
        unmatched = self.db.execute(unmatched_sql, {"user_id": user_id}).fetchall()
        
        # 고객별 그룹화
        customer_receipts = {}
        for receipt_number, excel_name in matched:
            if excel_name not in customer_receipts:
                customer_receipts[excel_name] = []
            customer_receipts[excel_name].append(receipt_number)
        
        matched_customers = []
        for excel_name, receipt_numbers in customer_receipts.items():
            # 여권 정보 조회
            passport_sql = text("""
            SELECT passport_number, birthday, name
            FROM passports
            WHERE name = :name AND user_id = :user_id
            """)
            passport_result = self.db.execute(passport_sql, {"name": excel_name, "user_id": user_id}).first()
            
            customer = CustomerMatchResult(
                name=excel_name,
                receipt_numbers=receipt_numbers,
                passport_number=passport_result[0] if passport_result else None,
                birthday=passport_result[1] if passport_result else None,
                needs_update=passport_result is None or (passport_result and passport_result[2] != excel_name)
            )
            matched_customers.append(customer)
        
        # 매칭되지 않은 영수증 변환
        unmatched_receipts = [
            ReceiptResponse(
                id=row[0],
                receipt_number=row[1],
                file_path=row[2],
                created_at=row[3]
            ) for row in unmatched
        ]
        
        return matched_customers, unmatched_receipts
    
    def update_receipt(self, receipt_id: int, user_id: int, receipt_data: ReceiptUpdate) -> bool:
        """영수증 정보 수정 (기존 edit_unmatched 로직)"""
        # 🔍 디버깅 정보 추가
        print(f"🔍 영수증 수정 요청 - receipt_id: {receipt_id}, user_id: {user_id}")
        
        # 면세점 타입 감지
        duty_free_type = self._detect_duty_free_type(user_id)
        print(f"🔍 감지된 면세점 타입: {duty_free_type}")
        
        # 🔍 현재 사용자의 영수증 목록 확인
        if duty_free_type == "shilla":
            # 신라 영수증 확인
            shilla_receipts = self.db.execute(text("""
                SELECT id, receipt_number FROM shilla_receipts WHERE user_id = :user_id
            """), {"user_id": user_id}).fetchall()
            print(f"🔍 사용자의 신라 영수증 목록: {shilla_receipts}")
            
            # 특정 ID 영수증 확인
            target_receipt = self.db.execute(text("""
                SELECT id, receipt_number FROM shilla_receipts 
                WHERE id = :receipt_id AND user_id = :user_id
            """), {"receipt_id": receipt_id, "user_id": user_id}).first()
            print(f"🔍 요청된 영수증 {receipt_id} 존재 여부: {target_receipt}")
            
            return self._update_shilla_receipt(receipt_id, user_id, receipt_data)
        else:
            # 롯데 영수증 확인
            lotte_receipts = self.db.execute(text("""
                SELECT id, receipt_number FROM receipts WHERE user_id = :user_id
            """), {"user_id": user_id}).fetchall()
            print(f"🔍 사용자의 롯데 영수증 목록: {lotte_receipts}")
            
            # 특정 ID 영수증 확인
            target_receipt = self.db.execute(text("""
                SELECT id, receipt_number FROM receipts 
                WHERE id = :receipt_id AND user_id = :user_id
            """), {"receipt_id": receipt_id, "user_id": user_id}).first()
            print(f"🔍 요청된 영수증 {receipt_id} 존재 여부: {target_receipt}")
            
            return self._update_lotte_receipt(receipt_id, user_id, receipt_data)
    
    def _update_shilla_receipt(self, receipt_id: int, user_id: int, receipt_data: ReceiptUpdate) -> bool:
        """신라 영수증 수정 - 디버깅 추가"""
        print(f"🔍 _update_shilla_receipt 시작 - receipt_id: {receipt_id}, user_id: {user_id}")
        print(f"🔍 수정 데이터: {receipt_data}")

        # ocr_repo.update_shilla_receipt 메서드 호출 전 확인
        print(f"🔍 ocr_repo.update_shilla_receipt 호출 시도...")

        try:
            receipt = self.ocr_repo.update_shilla_receipt(
                receipt_id, user_id,
                receipt_number=receipt_data.new_receipt_number,
                passport_number=receipt_data.passport_number
            )
            print(f"🔍 update_shilla_receipt 결과: {receipt}")
            
            if not receipt:
                print(f"❌ update_shilla_receipt에서 None 반환!")
                return False
            
            print(f"✅ 영수증 업데이트 성공: {receipt.receipt_number}")
            
            # 엑셀 데이터 매칭 확인 및 업데이트
            print(f"🔍 엑셀 데이터 매칭 확인 중...")
            excel_sql = text("""
            SELECT "receiptNumber", name, "PayBack"
            FROM shilla_excel_data
            WHERE "receiptNumber"::text = :receipt_number
            """)
            excel_result = self.db.execute(excel_sql, {"receipt_number": receipt_data.new_receipt_number}).first()
            print(f"🔍 엑셀 매칭 결과: {excel_result}")
            
            # 여권 정보 처리
            if receipt_data.passport_number:
                print(f"🔍 여권번호 업데이트 시작: {receipt_data.passport_number}")
                passport_sql = text("""
                UPDATE passports 
                SET is_matched = TRUE
                WHERE passport_number = :passport_number AND user_id = :user_id
                """)
                passport_result = self.db.execute(passport_sql, {
                    "passport_number": receipt_data.passport_number,
                    "user_id": user_id
                })
                print(f"🔍 여권 업데이트 결과: {passport_result.rowcount}행 영향")
                
                # 엑셀 데이터에 여권번호 업데이트
                if excel_result:
                    print(f"🔍 엑셀 데이터에 여권번호 업데이트 중...")
                    update_excel_sql = text("""
                    UPDATE shilla_excel_data 
                    SET passport_number = :passport_number
                    WHERE "receiptNumber"::text = :receipt_number
                    """)
                    excel_update_result = self.db.execute(update_excel_sql, {
                        "passport_number": receipt_data.passport_number,
                        "receipt_number": receipt_data.new_receipt_number
                    })
                    print(f"🔍 엑셀 여권번호 업데이트 결과: {excel_update_result.rowcount}행 영향")
            
            # 매칭 로그 업데이트
            print(f"🔍 매칭 로그 생성 중...")
            match_log = self.ocr_repo.create_match_log(
                user_id=user_id,
                receipt_number=receipt_data.new_receipt_number,
                is_matched=excel_result is not None,
                excel_name=excel_result[1] if excel_result else None,
                passport_number=receipt_data.passport_number
            )
            print(f"🔍 매칭 로그 생성 완료: {match_log.id}")
            
            self.db.commit()
            print(f"✅ 신라 영수증 수정 완료!")
            return True
            
        except Exception as e:
            print(f"❌ _update_shilla_receipt 오류: {e}")
            import traceback
            traceback.print_exc()
            self.db.rollback()
            return False
    
    def _update_lotte_receipt(self, receipt_id: int, user_id: int, receipt_data: ReceiptUpdate) -> bool:
        """롯데 영수증 수정"""
        old_receipt = self.db.execute(text("""
        SELECT receipt_number FROM receipts WHERE id = :receipt_id AND user_id = :user_id
        """), {"receipt_id": receipt_id, "user_id": user_id}).first()
        
        if not old_receipt:
            return False
        
        old_receipt_number = old_receipt[0]
        
        # 영수증 업데이트
        receipt = self.ocr_repo.update_receipt(
            receipt_id, user_id,
            receipt_number=receipt_data.new_receipt_number
        )
        
        if not receipt:
            return False
        
        # 엑셀 데이터 매칭 확인
        excel_sql = text("""
        SELECT "receiptNumber"
        FROM lotte_excel_data
        WHERE "receiptNumber" = :receipt_number
        """)
        excel_result = self.db.execute(excel_sql, {"receipt_number": receipt_data.new_receipt_number}).first()
        
        # 매칭 로그 업데이트
        match_log_sql = text("""
        UPDATE receipt_match_log 
        SET receipt_number = :new_receipt_number, is_matched = :is_matched
        WHERE receipt_number = :old_receipt_number AND user_id = :user_id
        """)
        self.db.execute(match_log_sql, {
            "new_receipt_number": receipt_data.new_receipt_number,
            "old_receipt_number": old_receipt_number,
            "is_matched": excel_result is not None,
            "user_id": user_id
        })
        
        self.db.commit()
        return True
    
    def update_passport(self, passport_id: int, user_id: int, passport_data: PassportUpdate) -> bool:
        """여권 정보 수정"""
        passport = self.ocr_repo.update_passport(passport_id, user_id, **passport_data.dict(exclude_unset=True))
        
        if not passport:
            return False
        
        # 엑셀 데이터와 매칭 확인 (면세점 타입에 따라)
        duty_free_type = self._detect_duty_free_type(user_id)
        
        if duty_free_type == "shilla" and passport_data.name:
            excel_sql = text("""
            SELECT "receiptNumber", name, "PayBack" 
            FROM shilla_excel_data 
            WHERE name = :name
            """)
        elif passport_data.name:
            excel_sql = text("""
            SELECT "receiptNumber", name, "PayBack" 
            FROM lotte_excel_data 
            WHERE name = :name
            """)
        else:
            self.db.commit()
            return True
        
        excel_result = self.db.execute(excel_sql, {"name": passport_data.name}).first()
        
        if excel_result:
            # 여권 매칭 상태 업데이트
            passport.is_matched = True
            
            # 매칭 로그 업데이트
            self.ocr_repo.create_match_log(
                user_id=user_id,
                receipt_number=excel_result[0],
                is_matched=True,
                excel_name=excel_result[1],
                passport_number=passport_data.passport_number,
                birthday=passport_data.birthday
            )
        
        self.db.commit()
        return True
    
    def get_unmatched_passports(self, user_id: int) -> List[Dict[str, Any]]:
        """매칭되지 않은 여권 목록 조회"""
        try:
            sql = text("""
            SELECT DISTINCT p.name as passport_name, p.passport_number, p.birthday, p.file_path
            FROM passports p
            WHERE p.user_id = :user_id
            AND p.is_matched = FALSE
            AND NOT EXISTS (
                SELECT 1 FROM lotte_excel_data le WHERE le.name = p.name
                UNION ALL
                SELECT 1 FROM shilla_excel_data se WHERE se.name = p.name
            )
            ORDER BY p.name
            """)
            
            unmatched = self.db.execute(sql, {"user_id": user_id}).fetchall()
            
            return [{
                "passport_name": row[0],
                "passport_number": row[1],
                "birthday": row[2],
                "file_path": row[3]
            } for row in unmatched]
            
        except Exception as e:
            print(f"매칭되지 않은 여권 조회 오류: {e}")
            # 기본 조회로 fallback
            passports = self.ocr_repo.get_unmatched_passports(user_id)
            
            return [{
                "passport_name": passport.name,
                "passport_number": passport.passport_number,
                "birthday": passport.birthday,
                "file_path": passport.file_path
            } for passport in passports]
    
    def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        """사용자 통계 조회"""
        return self.ocr_repo.get_user_statistics(user_id)