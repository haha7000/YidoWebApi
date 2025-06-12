# app/repositories/ocr_repository.py
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any

from ..models.ocr_model import (
    Receipt, ShillaReceipt, Passport, ReceiptMatchLog, 
    UnrecognizedImage, ProcessingArchive, MatchingHistory
)

class OcrRepository:
    def __init__(self, db: Session):
        self.db = db
    
    # === 영수증 관련 메서드 ===
    def create_receipt(self, user_id: int, receipt_number: str, file_path: str) -> Receipt:
        """롯데 영수증 생성"""
        receipt = Receipt(
            user_id=user_id,
            receipt_number=receipt_number,
            file_path=file_path
        )
        self.db.add(receipt)
        self.db.commit()
        self.db.refresh(receipt)
        return receipt
    
    def create_shilla_receipt(self, user_id: int, receipt_number: str, 
                            passport_number: Optional[str], file_path: str) -> ShillaReceipt:
        """신라 영수증 생성"""
        receipt = ShillaReceipt(
            user_id=user_id,
            receipt_number=receipt_number,
            passport_number=passport_number,
            file_path=file_path
        )
        self.db.add(receipt)
        self.db.commit()
        self.db.refresh(receipt)
        return receipt
    
    def get_user_receipts(self, user_id: int) -> List[Receipt]:
        """사용자의 롯데 영수증 목록 조회"""
        return self.db.query(Receipt).filter(Receipt.user_id == user_id).all()
    
    def get_user_shilla_receipts(self, user_id: int) -> List[ShillaReceipt]:
        """사용자의 신라 영수증 목록 조회"""
        return self.db.query(ShillaReceipt).filter(ShillaReceipt.user_id == user_id).all()
    
    def update_receipt(self, receipt_id: int, user_id: int, **kwargs) -> Optional[Receipt]:
        """영수증 정보 업데이트"""
        receipt = self.db.query(Receipt).filter(
            Receipt.id == receipt_id, 
            Receipt.user_id == user_id
        ).first()
        
        if not receipt:
            return None
        
        for key, value in kwargs.items():
            if hasattr(receipt, key):
                setattr(receipt, key, value)
        
        self.db.commit()
        self.db.refresh(receipt)
        return receipt
    
    def update_shilla_receipt(self, receipt_id: int, user_id: int, **kwargs) -> Optional[ShillaReceipt]:
        """신라 영수증 정보 업데이트"""
        print(f"🔍 Repository - update_shilla_receipt 시작")
        print(f"🔍 receipt_id: {receipt_id}, user_id: {user_id}")
        print(f"🔍 업데이트 데이터: {kwargs}")
        
        try:
            # 영수증 조회
            receipt = self.db.query(ShillaReceipt).filter(
                ShillaReceipt.id == receipt_id,
                ShillaReceipt.user_id == user_id
            ).first()
            
            print(f"🔍 조회된 영수증: {receipt}")
            
            if not receipt:
                print(f"❌ 영수증을 찾을 수 없음!")
                return None
            
            print(f"🔍 수정 전 영수증 정보:")
            print(f"  - ID: {receipt.id}")
            print(f"  - 기존 영수증번호: {receipt.receipt_number}")
            print(f"  - 기존 여권번호: {receipt.passport_number}")
            
            # 필드 업데이트
            for key, value in kwargs.items():
                if hasattr(receipt, key):
                    old_value = getattr(receipt, key)
                    setattr(receipt, key, value)
                    print(f"🔍 {key}: {old_value} -> {value}")
                else:
                    print(f"⚠️ 알 수 없는 필드: {key}")
            
            self.db.commit()
            self.db.refresh(receipt)
            
            print(f"✅ 영수증 업데이트 완료!")
            print(f"  - 새 영수증번호: {receipt.receipt_number}")
            print(f"  - 새 여권번호: {receipt.passport_number}")
            
            return receipt
            
        except Exception as e:
            print(f"❌ Repository 오류: {e}")
            import traceback
            traceback.print_exc()
            self.db.rollback()
            return None
    
    # === 여권 관련 메서드 ===
    def create_passport(self, user_id: int, name: str, passport_number: str, 
                       birthday: Optional[str], file_path: str) -> Passport:
        """여권 정보 생성"""
        passport = Passport(
            user_id=user_id,
            name=name,
            passport_number=passport_number,
            birthday=birthday,
            file_path=file_path
        )
        self.db.add(passport)
        self.db.commit()
        self.db.refresh(passport)
        return passport
    
    def get_user_passports(self, user_id: int) -> List[Passport]:
        """사용자의 여권 목록 조회"""
        return self.db.query(Passport).filter(Passport.user_id == user_id).all()
    
    def get_unmatched_passports(self, user_id: int) -> List[Passport]:
        """매칭되지 않은 여권 목록 조회"""
        return self.db.query(Passport).filter(
            Passport.user_id == user_id,
            Passport.is_matched == False
        ).all()
    
    def update_passport(self, passport_id: int, user_id: int, **kwargs) -> Optional[Passport]:
        """여권 정보 업데이트"""
        passport = self.db.query(Passport).filter(
            Passport.id == passport_id,
            Passport.user_id == user_id
        ).first()
        
        if not passport:
            return None
        
        for key, value in kwargs.items():
            if hasattr(passport, key):
                setattr(passport, key, value)
        
        self.db.commit()
        self.db.refresh(passport)
        return passport
    
    def update_passport_matching_status(self, passport_name: str, user_id: int, is_matched: bool) -> bool:
        """여권 매칭 상태 업데이트"""
        passport = self.db.query(Passport).filter(
            Passport.name == passport_name,
            Passport.user_id == user_id
        ).first()
        
        if passport:
            passport.is_matched = is_matched
            self.db.commit()
            return True
        return False
    
    # === 매칭 로그 관련 메서드 ===
    def create_match_log(self, user_id: int, receipt_number: str, is_matched: bool, **kwargs) -> ReceiptMatchLog:
        """매칭 로그 생성"""
        match_log = ReceiptMatchLog(
            user_id=user_id,
            receipt_number=receipt_number,
            is_matched=is_matched,
            **kwargs
        )
        self.db.add(match_log)
        self.db.commit()
        self.db.refresh(match_log)
        return match_log
    
    def get_match_logs(self, user_id: int) -> List[ReceiptMatchLog]:
        """사용자의 매칭 로그 조회"""
        return self.db.query(ReceiptMatchLog).filter(ReceiptMatchLog.user_id == user_id).all()
    
    # === 인식되지 않은 이미지 관련 메서드 ===
    def create_unrecognized_image(self, user_id: int, file_path: str) -> UnrecognizedImage:
        """인식되지 않은 이미지 생성"""
        unrecognized = UnrecognizedImage(
            user_id=user_id,
            file_path=file_path
        )
        self.db.add(unrecognized)
        self.db.commit()
        self.db.refresh(unrecognized)
        return unrecognized
    
    # === 데이터 삭제 관련 메서드 ===
    def clear_user_session_data(self, user_id: int) -> bool:
        """사용자의 현재 세션 데이터 삭제"""
        try:
            # 매칭 로그 삭제
            self.db.query(ReceiptMatchLog).filter(ReceiptMatchLog.user_id == user_id).delete()
            
            # 영수증 데이터 삭제
            self.db.query(Receipt).filter(Receipt.user_id == user_id).delete()
            self.db.query(ShillaReceipt).filter(ShillaReceipt.user_id == user_id).delete()
            
            # 여권 데이터 삭제
            self.db.query(Passport).filter(Passport.user_id == user_id).delete()
            
            # 인식되지 않은 이미지 삭제
            self.db.query(UnrecognizedImage).filter(UnrecognizedImage.user_id == user_id).delete()
            
            # 신라 엑셀 데이터에서 여권번호 초기화
            try:
                self.db.execute(text("""
                    UPDATE shilla_excel_data 
                    SET passport_number = NULL 
                    WHERE passport_number IS NOT NULL
                """))
            except Exception as e:
                print(f"신라 엑셀 데이터 초기화 오류: {e}")
            
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"데이터 삭제 오류: {e}")
            return False
    
    # === 통계 관련 메서드 ===
    def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        """사용자 통계 조회"""
        try:
            # 신라와 롯데 데이터 개수 확인
            shilla_count = self.db.query(ShillaReceipt).filter(ShillaReceipt.user_id == user_id).count()
            lotte_count = self.db.query(Receipt).filter(Receipt.user_id == user_id).count()
            
            duty_free_type = "shilla" if shilla_count >= lotte_count else "lotte"
            
            if duty_free_type == "shilla":
                # 신라 데이터 통계
                stats_sql = text("""
                SELECT 
                    COUNT(DISTINCT sr.id) as total_receipts,
                    COUNT(DISTINCT CASE WHEN se."receiptNumber" IS NOT NULL THEN sr.id END) as matched_receipts,
                    COUNT(DISTINCT p.id) as total_passports,
                    COUNT(DISTINCT CASE WHEN p.is_matched = TRUE THEN p.id END) as matched_passports
                FROM shilla_receipts sr
                LEFT JOIN shilla_excel_data se ON se."receiptNumber"::text = sr.receipt_number
                LEFT JOIN passports p ON p.user_id = sr.user_id
                WHERE sr.user_id = :user_id
                """)
            else:
                # 롯데 데이터 통계
                stats_sql = text("""
                SELECT 
                    COUNT(DISTINCT r.id) as total_receipts,
                    COUNT(DISTINCT CASE WHEN rml.is_matched = TRUE THEN r.id END) as matched_receipts,
                    COUNT(DISTINCT p.id) as total_passports,
                    COUNT(DISTINCT CASE WHEN p.is_matched = TRUE THEN p.id END) as matched_passports
                FROM receipts r
                LEFT JOIN receipt_match_log rml ON r.receipt_number = rml.receipt_number AND rml.user_id = r.user_id
                LEFT JOIN passports p ON p.user_id = r.user_id
                WHERE r.user_id = :user_id
                """)
            
            result = self.db.execute(stats_sql, {"user_id": user_id}).first()
            
            if result:
                return {
                    "total_receipts": result[0] or 0,
                    "matched_receipts": result[1] or 0,
                    "total_passports": result[2] or 0,
                    "matched_passports": result[3] or 0,
                    "unmatched_receipts": (result[0] or 0) - (result[1] or 0),
                    "unmatched_passports": (result[2] or 0) - (result[3] or 0),
                    "duty_free_type": duty_free_type
                }
            else:
                return {
                    "total_receipts": 0, "matched_receipts": 0,
                    "total_passports": 0, "matched_passports": 0,
                    "unmatched_receipts": 0, "unmatched_passports": 0,
                    "duty_free_type": duty_free_type
                }
        except Exception as e:
            print(f"통계 조회 오류: {e}")
            return {
                "total_receipts": 0, "matched_receipts": 0,
                "total_passports": 0, "matched_passports": 0,
                "unmatched_receipts": 0, "unmatched_passports": 0,
                "duty_free_type": "lotte"
            }
    
    # === 아카이브 관련 메서드 ===
    def create_archive(self, user_id: int, session_name: str, **kwargs) -> ProcessingArchive:
        """아카이브 생성"""
        archive = ProcessingArchive(
            user_id=user_id,
            session_name=session_name,
            **kwargs
        )
        self.db.add(archive)
        self.db.commit()
        self.db.refresh(archive)
        return archive
    
    def get_user_archives(self, user_id: int, limit: int = 50) -> List[ProcessingArchive]:
        """사용자 아카이브 목록 조회"""
        return self.db.query(ProcessingArchive).filter(
            ProcessingArchive.user_id == user_id
        ).order_by(ProcessingArchive.archive_date.desc()).limit(limit).all()
    
    def create_matching_history(self, user_id: int, archive_id: int, **kwargs) -> MatchingHistory:
        """매칭 히스토리 생성"""
        history = MatchingHistory(
            user_id=user_id,
            archive_id=archive_id,
            **kwargs
        )
        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)
        return history