"""remove confidence and ocr_text fields

Revision ID: 936edbc6c5b4
Revises: 
Create Date: 2025-06-12 10:54:57.191273

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '936edbc6c5b4'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('shilla_excel_data')
    op.drop_table('lotte_excel_data')
    op.drop_index(op.f('idx_history_archive'), table_name='matching_history')
    op.drop_index(op.f('idx_history_created_at'), table_name='matching_history')
    op.drop_index(op.f('idx_history_passport'), table_name='matching_history')
    op.drop_index(op.f('idx_history_receipt_search'), table_name='matching_history', postgresql_using='gin')
    op.drop_index(op.f('idx_history_user_customer'), table_name='matching_history')
    op.drop_constraint(op.f('matching_history_user_id_fkey'), 'matching_history', type_='foreignkey')
    op.drop_constraint(op.f('matching_history_archive_id_fkey'), 'matching_history', type_='foreignkey')
    op.create_foreign_key(None, 'matching_history', 'processing_archives', ['archive_id'], ['id'])
    op.create_foreign_key(None, 'matching_history', 'users', ['user_id'], ['id'])
    op.alter_column('passports', 'file_path',
               existing_type=sa.TEXT(),
               nullable=True)
    op.drop_index(op.f('idx_passports_user_id'), table_name='passports')
    op.drop_index(op.f('idx_passports_user_matched'), table_name='passports')
    op.drop_index(op.f('idx_archives_user_date'), table_name='processing_archives')
    op.drop_constraint(op.f('processing_archives_user_id_fkey'), 'processing_archives', type_='foreignkey')
    op.create_foreign_key(None, 'processing_archives', 'users', ['user_id'], ['id'])
    op.drop_index(op.f('idx_receipt_match_log_user_id'), table_name='receipt_match_log')
    op.drop_index(op.f('idx_receipt_match_log_user_receipt'), table_name='receipt_match_log')
    op.drop_index(op.f('idx_receipts_user_id'), table_name='receipts')
    op.drop_index(op.f('idx_shilla_receipts_user_id'), table_name='shilla_receipts')
    op.alter_column('unrecognized_images', 'file_path',
               existing_type=sa.TEXT(),
               nullable=True)
    op.drop_index(op.f('idx_unrecognized_images_user_id'), table_name='unrecognized_images')
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('idx_unrecognized_images_user_id'), 'unrecognized_images', ['user_id'], unique=False)
    op.alter_column('unrecognized_images', 'file_path',
               existing_type=sa.TEXT(),
               nullable=False)
    op.create_index(op.f('idx_shilla_receipts_user_id'), 'shilla_receipts', ['user_id'], unique=False)
    op.create_index(op.f('idx_receipts_user_id'), 'receipts', ['user_id'], unique=False)
    op.create_index(op.f('idx_receipt_match_log_user_receipt'), 'receipt_match_log', ['user_id', 'receipt_number'], unique=False)
    op.create_index(op.f('idx_receipt_match_log_user_id'), 'receipt_match_log', ['user_id'], unique=False)
    op.drop_constraint(None, 'processing_archives', type_='foreignkey')
    op.create_foreign_key(op.f('processing_archives_user_id_fkey'), 'processing_archives', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_index(op.f('idx_archives_user_date'), 'processing_archives', ['user_id', sa.literal_column('archive_date DESC')], unique=False)
    op.create_index(op.f('idx_passports_user_matched'), 'passports', ['user_id', 'is_matched'], unique=False)
    op.create_index(op.f('idx_passports_user_id'), 'passports', ['user_id'], unique=False)
    op.alter_column('passports', 'file_path',
               existing_type=sa.TEXT(),
               nullable=False)
    op.drop_constraint(None, 'matching_history', type_='foreignkey')
    op.drop_constraint(None, 'matching_history', type_='foreignkey')
    op.create_foreign_key(op.f('matching_history_archive_id_fkey'), 'matching_history', 'processing_archives', ['archive_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key(op.f('matching_history_user_id_fkey'), 'matching_history', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_index(op.f('idx_history_user_customer'), 'matching_history', ['user_id', 'customer_name'], unique=False)
    op.create_index(op.f('idx_history_receipt_search'), 'matching_history', [sa.literal_column("to_tsvector('simple'::regconfig, receipt_numbers)")], unique=False, postgresql_using='gin')
    op.create_index(op.f('idx_history_passport'), 'matching_history', ['passport_number'], unique=False)
    op.create_index(op.f('idx_history_created_at'), 'matching_history', [sa.literal_column('created_at DESC')], unique=False)
    op.create_index(op.f('idx_history_archive'), 'matching_history', ['archive_id'], unique=False)
    op.create_table('lotte_excel_data',
    sa.Column('점구분', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('원매출일자', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('매출일자', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('단체번호', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('name', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('VIP번호', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('receiptNumber', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('교환권상태', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('카테고리', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('브랜드', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('상품명', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('상품구분', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('상품코드', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('Ref.No', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('Color', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('배송구분', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('판매방식', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('판매수량', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('판매가($)', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('총매출액($)', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('순매출액($)', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('할인액($)', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('총매출액(\\)', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('순매출액(\\)', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('할인액(\\)', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('PayBack', sa.BIGINT(), autoincrement=False, nullable=True)
    )
    op.create_table('shilla_excel_data',
    sa.Column('No', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('점', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('원매출일자', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('매출일자', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('여행사명', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('여행사코드', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('그룹번호', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('대표가이드', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('출생연도', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('name', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('receiptNumber', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('BILL 상태', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('상품위치', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('카테고리', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('브랜드명', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('상품명', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('상품코드', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('REF NO', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('Aging', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('판매형태', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('판매수량', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('판매가($)', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('총매출액($)', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('총매출액(￦)', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('순매출액($)', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('순매출액(￦)', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('할인액($)', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('할인액(￦)', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('Unnamed: 28', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('PayBack', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('passport_number', sa.TEXT(), autoincrement=False, nullable=True)
    )
    # ### end Alembic commands ###
