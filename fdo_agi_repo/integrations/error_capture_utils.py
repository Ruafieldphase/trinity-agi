"""
에러 발생 시 전체 화면을 캡처하고 OCR 결과를 outputs/에 저장하는 유틸리티
- cross-platform (pyautogui, pillow, pytesseract)
- outputs/error_capture_YYYYMMDD_HHMMSS.png, .txt로 저장
"""
import os
from datetime import datetime
from pathlib import Path

from PIL import Image
import pyautogui
import pytesseract

def capture_and_ocr_on_error(prefix: str = "error_capture") -> dict:
    out_dir = Path("outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    img_path = out_dir / f"{prefix}_{ts}.png"
    txt_path = out_dir / f"{prefix}_{ts}.txt"
    # 화면 캡처
    screenshot = pyautogui.screenshot()
    screenshot.save(img_path)
    # OCR
    try:
        text = pytesseract.image_to_string(screenshot, lang="eng+kor")
    except Exception as e:
        text = f"[OCR 실패: {e}]"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)
    return {
        "screenshot_path": str(img_path),
        "ocr_path": str(txt_path),
        "ocr_preview": text[:500],
    }
