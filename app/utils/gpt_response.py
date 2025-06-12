# app/utils/gpt_response.py
import openai
import os
from ..core.config import settings

def LotteClassificationUseGpt(ocr_text: str) -> str:
    """롯데 면세점 OCR 텍스트를 GPT로 분류 (기존 로직 100% 보존)"""
    try:
        with open(settings.LOTTE_PROMPT_PATH, "r", encoding="utf-8") as f:
            SYSTEM_PROMPT = f.read()
    except FileNotFoundError:
        # 기본 프롬프트 사용
        SYSTEM_PROMPT = """
        Please convert the LOTTE duty-free receipt OCR results into the JSON format below.
        Include only the specified keys, and do not include any keys other than those mentioned.
        
        The conditions for each field are as follows:
        - "receiptNumber": Must be exactly 14 digits for LOTTE receipts
        - If multiple receipts are found, extract all of them
        
        Output format:
        {
          "receipts": [
            {"receiptNumber": "90208724000593"}
          ],
          "passports": [
            {
              "name": "ZHANG SAN",
              "passportNumber": "AS1234567",
              "birthDay": "09 Jun 1994"
            }
          ]
        }
        """
    
    openai.api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY_COMPANY")
    
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": ocr_text}
        ],
        temperature=0.0
    )
    return response['choices'][0]['message']['content']

def ShillaClassificationUseGpt(ocr_text: str) -> str:
    """신라 면세점 OCR 텍스트를 GPT로 분류 (기존 로직 100% 보존)"""
    try:
        with open(settings.SHILLA_PROMPT_PATH, "r", encoding="utf-8") as f:
            SYSTEM_PROMPT = f.read()
    except FileNotFoundError:
        # 기본 프롬프트 사용
        SYSTEM_PROMPT = """
        Please convert the SHILLA duty-free receipt OCR results into the JSON format below.
        Include only the specified keys, and do not include any keys other than those mentioned.
        
        The conditions for each field are as follows:
        - "receiptNumber": Must be exactly 13 digits for SHILLA receipts
        - "passportNumber": May be included in receipts for SHILLA
        
        Output format:
        {
          "receipts": [
            {
              "receiptNumber": "0124507700631",
              "passportNumber": "MZ9268755"
            }
          ],
          "passports": [
            {
              "name": "ZHANG SAN",
              "passportNumber": "AS1234567",
              "birthDay": "09 Jun 1994"
            }
          ]
        }
        """
    
    openai.api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY_COMPANY")
    
    response = openai.ChatCompletion.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": ocr_text}
        ],
        temperature=0.0
    )
    return response['choices'][0]['message']['content']