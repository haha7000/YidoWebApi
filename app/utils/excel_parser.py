# app/utils/excel_parser.py
import pandas as pd
from sqlalchemy import create_engine, text
from typing import Tuple, Dict, Any
from ..core.config import settings

class ExcelParser:
    """엑셀 파싱 유틸리티 클래스 (기존 로직 100% 보존)"""
    
    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL)
    
    def parse_lotte_excel(self, excel_path: str) -> Tuple[pd.DataFrame, int, int]:
        """롯데 면세점 엑셀 파싱 (기존 로직 보존)"""
        try:
            # 멀티헤더 엑셀 파일 읽기
            df = pd.read_excel(excel_path, header=[0, 1])
            
            # 병합된 멀티헤더를 1단 컬럼으로 변환
            df.columns = [f"{str(a).strip()}_{str(b).strip()}" if 'Unnamed' not in str(b) else str(a).strip()
                        for a, b in df.columns]
            
            print(f"원본 컬럼들: {list(df.columns)}")
            
            # "매출_" 접두어 제거
            df.columns = [col.replace("매출_", "") for col in df.columns]
            
            # 불필요한 컬럼 제거
            columns_to_remove = ['순번', '0', '여행사', '여행사코드', '수입/로컬']
            df = df.drop(columns=[col for col in columns_to_remove if col in df.columns], errors='ignore')
            
            # 컬럼명 변경 - 핵심 컬럼들만 확인
            rename_mapping = {}
            for col in df.columns:
                if '교환권번호' in col or 'receiptNumber' in col:
                    rename_mapping[col] = 'receiptNumber'
                elif '고객명' in col or 'name' in col:
                    rename_mapping[col] = 'name'
                elif 'PayBack' in col or '환급' in col or '페이백' in col or '수수료' in col:
                    rename_mapping[col] = 'PayBack'
            
            print(f"컬럼 매핑: {rename_mapping}")
            df = df.rename(columns=rename_mapping)
            
            # 필수 컬럼 확인
            required_columns = ['receiptNumber', 'name']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise Exception(f"필수 컬럼이 없습니다: {missing_columns}")
            
            # PayBack 컬럼이 없으면 기본값 설정
            if 'PayBack' not in df.columns:
                df['PayBack'] = 0
            
            print(f"최종 컬럼들: {list(df.columns)}")
            print(f"데이터 샘플: {df.head()}")
            
            return df, 0, len(df)
            
        except Exception as e:
            # 단순 헤더 파일로 다시 시도
            print(f"멀티헤더 처리 실패, 단순 헤더로 재시도: {e}")
            df = pd.read_excel(excel_path)
            print(f"단순 헤더 컬럼들: {list(df.columns)}")
            
            # 컬럼명 변경
            rename_mapping = {}
            for col in df.columns:
                if '교환권번호' in str(col) or 'receiptNumber' in str(col):
                    rename_mapping[col] = 'receiptNumber'
                elif '고객명' in str(col) or 'name' in str(col):
                    rename_mapping[col] = 'name'
                elif 'PayBack' in str(col) or '환급' in str(col) or '페이백' in str(col) or '수수료' in str(col):
                    rename_mapping[col] = 'PayBack'
            
            df = df.rename(columns=rename_mapping)
            
            # 필수 컬럼 확인
            if 'receiptNumber' not in df.columns or 'name' not in df.columns:
                raise Exception("필수 컬럼(receiptNumber, name)을 찾을 수 없습니다.")
            
            # PayBack 컬럼이 없으면 기본값 설정
            if 'PayBack' not in df.columns:
                df['PayBack'] = 0
            
            return df, 0, len(df)
    
    def parse_shilla_excel(self, excel_path: str) -> Tuple[pd.DataFrame, int, int]:
        """신라 면세점 엑셀 파싱 (기존 로직 보존)"""
        # 신라 엑셀 데이터 처리 (단순한 헤더 구조)
        df = pd.read_excel(excel_path, dtype={'BILL 번호': str})
        print(f"신라 엑셀 원본 컬럼들: {list(df.columns)}")

        # 컬럼명 변경
        df.rename(columns={'BILL 번호': 'receiptNumber', '고객명': 'name', '수수료': 'PayBack'}, inplace=True)
        
        # 필수 컬럼 확인
        if 'receiptNumber' not in df.columns:
            raise Exception("영수증 번호 컬럼(BILL 번호)을 찾을 수 없습니다.")
        if 'name' not in df.columns:
            raise Exception("고객명 컬럼을 찾을 수 없습니다.")
        
        # receiptNumber를 문자열로 변환 (중요!)
        df['receiptNumber'] = df['receiptNumber'].astype(str)
        
        # PayBack 컬럼이 없으면 기본값 설정
        if 'PayBack' not in df.columns:
            df['PayBack'] = 0
            print("PayBack 컬럼이 없어서 기본값 0으로 설정")
        
        # 신라 전용: passport_number 컬럼 추가 (매칭 시 업데이트용)
        df['passport_number'] = None
        
        # 중복 컬럼 제거 (같은 이름으로 매핑된 컬럼들)
        df = df.loc[:, ~df.columns.duplicated()]
        
        print(f"신라 최종 컬럼들: {list(df.columns)}")
        print(f"신라 데이터 샘플:\n{df.head()}")
        print(f"receiptNumber 타입: {df['receiptNumber'].dtype}")
        
        return df, 0, len(df)
    
    def save_to_database(self, df: pd.DataFrame, table_name: str) -> Tuple[int, int]:
        """데이터베이스에 엑셀 데이터 저장 (기존 로직 보존)"""
        with self.engine.connect() as connection:
            connection.execute(text("BEGIN"))
            
            try:
                # 기존 데이터 수 조회
                try:
                    count_sql = text(f"SELECT COUNT(*) FROM {table_name}")
                    records_before = connection.execute(count_sql).scalar()
                    print(f"기존 레코드 수: {records_before}")
                except Exception as count_error:
                    print(f"기존 데이터 조회 실패 (테이블이 없을 수 있음): {count_error}")
                    records_before = 0
                    connection.execute(text("ROLLBACK"))
                    connection.execute(text("BEGIN"))
                
                # 기존 데이터와 중복 체크
                existing_receipts = set()
                try:
                    existing_sql = text(f'SELECT "receiptNumber" FROM {table_name}')
                    existing_data = connection.execute(existing_sql).fetchall()
                    existing_receipts = {row[0] for row in existing_data if row[0]}
                    print(f"기존 영수증 번호 수: {len(existing_receipts)}")
                except Exception as existing_error:
                    print(f"기존 데이터 조회 실패 (테이블이 없을 수 있음): {existing_error}")
                    existing_receipts = set()
                    connection.execute(text("ROLLBACK"))
                    connection.execute(text("BEGIN"))
                
                # 중복되지 않은 데이터만 필터링
                if existing_receipts:
                    df_new = df[~df['receiptNumber'].isin(existing_receipts)]
                else:
                    df_new = df.copy()
                
                records_added = len(df_new)
                print(f"추가할 레코드 수: {records_added}")
                
                if records_added > 0:
                    try:
                        # 먼저 append로 시도
                        df_new.to_sql(table_name, connection, if_exists='append', index=False)
                        print(f"✅ {table_name} 테이블에 {records_added}개 레코드 추가 완료")
                    except Exception as append_error:
                        print(f"append 실패, replace로 재시도: {append_error}")
                        connection.execute(text("ROLLBACK"))
                        connection.execute(text("BEGIN"))
                        
                        # 전체 데이터로 테이블 새로 생성
                        df.to_sql(table_name, connection, if_exists='replace', index=False)
                        records_added = len(df)
                        print(f"✅ {table_name} 테이블을 새로 생성하고 {records_added}개 레코드 추가 완료")
                        records_before = 0
                else:
                    print("추가할 새로운 데이터가 없습니다.")
                
                connection.execute(text("COMMIT"))
                print("✅ 트랜잭션 커밋 완료")
                
                return records_added, records_before + records_added
                
            except Exception as e:
                print(f"데이터베이스 작업 중 오류: {e}")
                connection.execute(text("ROLLBACK"))
                raise e