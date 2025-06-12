# 테이블 생성
from app.core.database import engine
from app.models.user_model import User
from app.models.ocr_model import *
Base.metadata.create_all(bind=engine)