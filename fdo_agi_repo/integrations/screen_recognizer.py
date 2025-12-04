"""
Screen Recognizer Module
Phase 2.5 Day 4: 화면 인식 (OCR + Template Matching)

담당:
- 스크린샷 캡처 (전체/영역)
- OCR (Tesseract + EasyOCR 병합)
- 템플릿 매칭 (OpenCV)
- UI 요소 찾기 (버튼, 텍스트, 이미지)
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageGrab

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    logging.warning("EasyOCR not available. Install: pip install easyocr")


@dataclass
class OCRResult:
    """
    OCR 인식 결과
    
    Attributes:
        text: 인식된 텍스트
        confidence: 신뢰도 (0.0 ~ 1.0)
        bbox: 바운딩 박스 (x, y, width, height)
        engine: 사용된 엔진 (tesseract/easyocr)
    """
    text: str
    confidence: float
    bbox: Optional[Tuple[int, int, int, int]] = None
    engine: str = "tesseract"
    
    def to_dict(self) -> Dict:
        return {
            'text': self.text,
            'confidence': self.confidence,
            'bbox': self.bbox,
            'engine': self.engine
        }


@dataclass
class TemplateMatchResult:
    """
    템플릿 매칭 결과
    
    Attributes:
        found: 찾기 성공 여부
        location: 중심점 좌표 (x, y)
        bbox: 바운딩 박스 (x, y, width, height)
        confidence: 매칭 신뢰도 (0.0 ~ 1.0)
    """
    found: bool
    location: Optional[Tuple[int, int]] = None
    bbox: Optional[Tuple[int, int, int, int]] = None
    confidence: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'found': self.found,
            'location': self.location,
            'bbox': self.bbox,
            'confidence': self.confidence
        }


class ScreenRecognizer:
    """
    화면 인식 엔진
    
    Phase 2.5 Day 4: OCR + Template Matching
    
    Usage:
        recognizer = ScreenRecognizer()
        
        # 전체 화면 캡처
        screenshot = recognizer.capture_screen()
        
        # OCR (Tesseract)
        text = recognizer.ocr_tesseract(screenshot)
        print(text)
        
        # OCR (EasyOCR, 한국어)
        results = recognizer.ocr_easyocr(screenshot, languages=['ko', 'en'])
        for r in results:
            print(r.text, r.confidence)
        
        # 템플릿 찾기
        template_path = "button.png"
        match = recognizer.find_template(screenshot, template_path, threshold=0.8)
        if match.found:
            print(f"Found at: {match.location}")
    """
    
    def __init__(self):
        self.logger = logging.getLogger("ScreenRecognizer")
        
        # EasyOCR reader (lazy loading)
        self._easyocr_reader: Optional[Any] = None
        self._easyocr_languages: List[str] = []
    
    def capture_screen(
        self,
        region: Optional[Tuple[int, int, int, int]] = None,
        save_path: Optional[Union[str, Path]] = None
    ) -> np.ndarray:
        """
        화면 캡처
        
        Args:
            region: 캡처 영역 (x, y, width, height). None이면 전체 화면
            save_path: 저장 경로 (optional)
        
        Returns:
            numpy array (OpenCV format: BGR)
        
        Example:
            # 전체 화면
            screenshot = recognizer.capture_screen()
            
            # 특정 영역 (x=100, y=100, 가로=800, 세로=600)
            screenshot = recognizer.capture_screen(region=(100, 100, 800, 600))
            
            # 저장
            screenshot = recognizer.capture_screen(save_path="outputs/screen.png")
        """
        try:
            start_time = time.time()
            
            if region:
                x, y, w, h = region
                pil_image = ImageGrab.grab(bbox=(x, y, x + w, y + h))
            else:
                pil_image = ImageGrab.grab()
            
            # PIL → numpy (RGB → BGR for OpenCV)
            screenshot = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            if save_path:
                cv2.imwrite(str(save_path), screenshot)
                self.logger.info(f"[ScreenRecognizer] Screenshot saved: {save_path}")
            
            elapsed = time.time() - start_time
            self.logger.info(
                f"[ScreenRecognizer] Captured {screenshot.shape[1]}x{screenshot.shape[0]} "
                f"in {elapsed:.2f}s"
            )
            
            return screenshot
        
        except Exception as e:
            self.logger.error(f"[ScreenRecognizer] Capture failed: {e}")
            raise
    
    def ocr_tesseract(
        self,
        image: Union[np.ndarray, str, Path],
        lang: str = 'eng+kor',
        config: str = '--psm 6'
    ) -> str:
        """
        Tesseract OCR
        
        Args:
            image: 이미지 (numpy array 또는 파일 경로)
            lang: 언어 코드 (eng, kor, eng+kor 등)
            config: Tesseract 설정
                --psm 6: 단일 블록 (기본)
                --psm 11: 희소 텍스트
                --psm 3: 자동
        
        Returns:
            인식된 텍스트 (전체)
        
        Example:
            screenshot = recognizer.capture_screen()
            text = recognizer.ocr_tesseract(screenshot, lang='eng+kor')
            print(text)
        """
        try:
            start_time = time.time()
            
            if isinstance(image, (str, Path)):
                image = cv2.imread(str(image))
            
            # Tesseract 실행
            text = pytesseract.image_to_string(image, lang=lang, config=config)
            
            elapsed = time.time() - start_time
            self.logger.info(
                f"[ScreenRecognizer] Tesseract OCR: {len(text)} chars in {elapsed:.2f}s"
            )
            
            return text.strip()
        
        except Exception as e:
            self.logger.error(f"[ScreenRecognizer] Tesseract OCR failed: {e}")
            return ""
    
    def ocr_tesseract_detailed(
        self,
        image: Union[np.ndarray, str, Path],
        lang: str = 'eng+kor',
        config: str = '--psm 6'
    ) -> List[OCRResult]:
        """
        Tesseract OCR (상세 정보 포함)
        
        Returns:
            OCRResult 리스트 (bbox, confidence 포함)
        """
        try:
            start_time = time.time()
            
            if isinstance(image, (str, Path)):
                image = cv2.imread(str(image))
            
            # Tesseract 상세 데이터
            data = pytesseract.image_to_data(
                image,
                lang=lang,
                config=config,
                output_type=pytesseract.Output.DICT
            )
            
            results = []
            
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                conf = float(data['conf'][i])
                
                if not text or conf < 0:
                    continue
                
                bbox = (
                    data['left'][i],
                    data['top'][i],
                    data['width'][i],
                    data['height'][i]
                )
                
                results.append(OCRResult(
                    text=text,
                    confidence=conf / 100.0,  # 0-100 → 0.0-1.0
                    bbox=bbox,
                    engine="tesseract"
                ))
            
            elapsed = time.time() - start_time
            self.logger.info(
                f"[ScreenRecognizer] Tesseract detailed: {len(results)} words in {elapsed:.2f}s"
            )
            
            return results
        
        except Exception as e:
            self.logger.error(f"[ScreenRecognizer] Tesseract detailed failed: {e}")
            return []
    
    def ocr_easyocr(
        self,
        image: Union[np.ndarray, str, Path],
        languages: List[str] = ['en'],
        gpu: bool = False
    ) -> List[OCRResult]:
        """
        EasyOCR
        
        Args:
            image: 이미지
            languages: 언어 리스트 (['ko', 'en'] 등)
            gpu: GPU 사용 여부
        
        Returns:
            OCRResult 리스트
        
        Example:
            results = recognizer.ocr_easyocr(
                screenshot,
                languages=['ko', 'en'],
                gpu=False
            )
            
            for r in results:
                print(f"{r.text} (confidence: {r.confidence:.2f})")
        """
        if not EASYOCR_AVAILABLE:
            self.logger.error("[ScreenRecognizer] EasyOCR not available")
            return []
        
        try:
            start_time = time.time()
            
            # Reader 초기화 (언어 변경 시 재생성)
            if (
                self._easyocr_reader is None or
                set(self._easyocr_languages) != set(languages)
            ):
                self.logger.info(f"[ScreenRecognizer] Initializing EasyOCR: {languages}")
                self._easyocr_reader = easyocr.Reader(languages, gpu=gpu)
                self._easyocr_languages = languages
            
            if isinstance(image, (str, Path)):
                image = cv2.imread(str(image))
            
            # EasyOCR 실행
            raw_results = self._easyocr_reader.readtext(image)
            
            results = []
            
            for bbox_coords, text, conf in raw_results:
                # bbox: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                x_coords = [p[0] for p in bbox_coords]
                y_coords = [p[1] for p in bbox_coords]
                
                x = int(min(x_coords))
                y = int(min(y_coords))
                w = int(max(x_coords) - x)
                h = int(max(y_coords) - y)
                
                results.append(OCRResult(
                    text=text,
                    confidence=conf,
                    bbox=(x, y, w, h),
                    engine="easyocr"
                ))
            
            elapsed = time.time() - start_time
            self.logger.info(
                f"[ScreenRecognizer] EasyOCR: {len(results)} words in {elapsed:.2f}s"
            )
            
            return results
        
        except Exception as e:
            self.logger.error(f"[ScreenRecognizer] EasyOCR failed: {e}")
            return []
    
    def find_template(
        self,
        screen: Union[np.ndarray, str, Path],
        template: Union[np.ndarray, str, Path],
        threshold: float = 0.8,
        method: int = cv2.TM_CCOEFF_NORMED
    ) -> TemplateMatchResult:
        """
        템플릿 이미지 찾기 (OpenCV Template Matching)
        
        Args:
            screen: 대상 이미지 (스크린샷)
            template: 찾을 템플릿 이미지
            threshold: 매칭 임계값 (0.0 ~ 1.0, 높을수록 엄격)
            method: OpenCV 매칭 방법
                - cv2.TM_CCOEFF_NORMED (기본, 추천)
                - cv2.TM_CCORR_NORMED
                - cv2.TM_SQDIFF_NORMED
        
        Returns:
            TemplateMatchResult
        
        Example:
            screenshot = recognizer.capture_screen()
            match = recognizer.find_template(
                screenshot,
                "button_submit.png",
                threshold=0.8
            )
            
            if match.found:
                print(f"Found at: {match.location}")
                print(f"Bounding box: {match.bbox}")
        """
        try:
            start_time = time.time()
            
            # Load images
            if isinstance(screen, (str, Path)):
                screen = cv2.imread(str(screen))
            
            if isinstance(template, (str, Path)):
                template = cv2.imread(str(template))
            
            # Grayscale conversion
            screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            
            # Template matching
            result = cv2.matchTemplate(screen_gray, template_gray, method)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            # TM_SQDIFF_NORMED는 최소값이 최선의 매칭
            if method == cv2.TM_SQDIFF_NORMED:
                match_val = 1 - min_val
                top_left = min_loc
            else:
                match_val = max_val
                top_left = max_loc
            
            elapsed = time.time() - start_time
            
            if match_val >= threshold:
                h, w = template_gray.shape
                center_x = top_left[0] + w // 2
                center_y = top_left[1] + h // 2
                
                self.logger.info(
                    f"[ScreenRecognizer] ✅ Template found: "
                    f"confidence={match_val:.2f} at ({center_x}, {center_y}) "
                    f"in {elapsed:.2f}s"
                )
                
                return TemplateMatchResult(
                    found=True,
                    location=(center_x, center_y),
                    bbox=(top_left[0], top_left[1], w, h),
                    confidence=match_val
                )
            else:
                self.logger.info(
                    f"[ScreenRecognizer] ❌ Template not found: "
                    f"max_confidence={match_val:.2f} < threshold={threshold} "
                    f"in {elapsed:.2f}s"
                )
                
                return TemplateMatchResult(
                    found=False,
                    confidence=match_val
                )
        
        except Exception as e:
            self.logger.error(f"[ScreenRecognizer] Template matching failed: {e}")
            return TemplateMatchResult(found=False)
    
    def find_text(
        self,
        screen: Union[np.ndarray, str, Path],
        target_text: str,
        engine: str = 'tesseract',
        case_sensitive: bool = False
    ) -> Optional[Tuple[int, int]]:
        """
        화면에서 텍스트 찾기
        
        Args:
            screen: 대상 이미지
            target_text: 찾을 텍스트
            engine: OCR 엔진 ('tesseract' or 'easyocr')
            case_sensitive: 대소문자 구분
        
        Returns:
            텍스트 중심 좌표 (x, y) 또는 None
        
        Example:
            screenshot = recognizer.capture_screen()
            location = recognizer.find_text(screenshot, "Submit")
            
            if location:
                print(f"Found 'Submit' at: {location}")
        """
        try:
            if engine == 'easyocr':
                results = self.ocr_easyocr(screen, languages=['en', 'ko'])
            else:
                results = self.ocr_tesseract_detailed(screen)
            
            for r in results:
                text = r.text if case_sensitive else r.text.lower()
                target = target_text if case_sensitive else target_text.lower()
                
                if target in text and r.bbox:
                    x, y, w, h = r.bbox
                    center = (x + w // 2, y + h // 2)
                    
                    self.logger.info(
                        f"[ScreenRecognizer] ✅ Found text '{target_text}' at {center}"
                    )
                    
                    return center
            
            self.logger.info(f"[ScreenRecognizer] ❌ Text '{target_text}' not found")
            return None
        
        except Exception as e:
            self.logger.error(f"[ScreenRecognizer] Text search failed: {e}")
            return None


# Standalone Test
if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    
    print("\n" + "=" * 60)
    print("SCREEN RECOGNIZER TEST")
    print("=" * 60 + "\n")
    
    recognizer = ScreenRecognizer()
    
    # Test 1: Capture Screen
    print("TEST 1: Capture Screen")
    screenshot = recognizer.capture_screen(save_path="outputs/test_screenshot.png")
    print(f"✅ Captured: {screenshot.shape[1]}x{screenshot.shape[0]}\n")
    
    # Test 2: Tesseract OCR
    print("TEST 2: Tesseract OCR")
    text = recognizer.ocr_tesseract(screenshot, lang='eng')
    print(f"✅ Recognized {len(text)} characters")
    print(f"   Preview: {text[:200]}...\n")
    
    # Test 3: Tesseract Detailed
    print("TEST 3: Tesseract Detailed OCR")
    results = recognizer.ocr_tesseract_detailed(screenshot, lang='eng')
    print(f"✅ Found {len(results)} words")
    
    for i, r in enumerate(results[:5]):
        print(f"   [{i+1}] {r.text} (confidence: {r.confidence:.2f})")
    
    if len(results) > 5:
        print(f"   ... and {len(results) - 5} more\n")
    
    # Test 4: EasyOCR (if available)
    if EASYOCR_AVAILABLE:
        print("TEST 4: EasyOCR")
        results = recognizer.ocr_easyocr(screenshot, languages=['en'])
        print(f"✅ Found {len(results)} words")
        
        for i, r in enumerate(results[:5]):
            print(f"   [{i+1}] {r.text} (confidence: {r.confidence:.2f})")
        
        if len(results) > 5:
            print(f"   ... and {len(results) - 5} more")
    else:
        print("TEST 4: EasyOCR - SKIPPED (not installed)")
    
    print("\n" + "=" * 60)
    print("Test complete. Check 'outputs/test_screenshot.png'")
