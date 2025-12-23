"""
Smart Response Extractor - AGI가 스스로 방법을 선택하여 응답 추출
여러 추출 방법 중 성공하는 것을 찾아 학습합니다.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass
from datetime import datetime

import pyautogui
import pyperclip
from PIL import Image

logger = logging.getLogger("SmartExtractor")

# 학습된 방법 저장 경로
LEARNED_METHODS_PATH = Path(__file__).parent.parent / "memory" / "extraction_methods.json"


@dataclass
class ExtractionResult:
    """추출 결과"""
    success: bool
    method: str
    content: Optional[str] = None
    error: Optional[str] = None


def _load_learned_methods() -> Dict[str, Any]:
    """학습된 방법 로드"""
    if LEARNED_METHODS_PATH.exists():
        try:
            with open(LEARNED_METHODS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"preferred_method": None, "success_counts": {}, "failure_counts": {}}


def _save_learned_methods(data: Dict[str, Any]) -> None:
    """학습된 방법 저장"""
    LEARNED_METHODS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LEARNED_METHODS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _record_result(method: str, success: bool) -> None:
    """결과 기록 및 선호 방법 업데이트"""
    data = _load_learned_methods()
    
    if success:
        data["success_counts"][method] = data["success_counts"].get(method, 0) + 1
        # 성공한 방법을 선호 방법으로 설정
        data["preferred_method"] = method
        logger.info(f"📝 학습: '{method}' 방법 성공 기록됨 (총 {data['success_counts'][method]}회)")
    else:
        data["failure_counts"][method] = data["failure_counts"].get(method, 0) + 1
    
    data["last_updated"] = datetime.now().isoformat()
    _save_learned_methods(data)


# ============================================================
# 추출 방법들 (AGI가 선택)
# ============================================================

def extract_via_clipboard() -> ExtractionResult:
    """
    방법 1: 클립보드 복사 (Ctrl+Shift+C)
    ChatGPT 앱의 마지막 응답 복사 단축키
    """
    try:
        # 기존 클립보드 백업
        old_clipboard = pyperclip.paste()
        
        # ChatGPT 앱의 복사 단축키
        pyautogui.hotkey('ctrl', 'shift', 'c')
        time.sleep(0.8)
        
        new_content = pyperclip.paste()
        
        # 새 내용이 있고, 기존과 다르면 성공
        if new_content and new_content != old_clipboard and len(new_content) > 20:
            logger.info(f"✅ 클립보드 방법 성공: {len(new_content)}자 추출")
            return ExtractionResult(
                success=True,
                method="clipboard",
                content=new_content
            )
        
        return ExtractionResult(
            success=False,
            method="clipboard",
            error="클립보드에 새 내용 없음"
        )
        
    except Exception as e:
        return ExtractionResult(success=False, method="clipboard", error=str(e))


def extract_via_select_copy() -> ExtractionResult:
    """
    방법 2: 전체 선택 후 복사 (Ctrl+A → Ctrl+C)
    응답 영역을 클릭한 후 전체 선택
    """
    try:
        old_clipboard = pyperclip.paste()
        
        # 화면 중앙을 클릭 (응답 영역 추정)
        screen_width, screen_height = pyautogui.size()
        pyautogui.click(screen_width // 2, screen_height // 2)
        time.sleep(0.3)
        
        # 전체 선택 + 복사
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.3)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.5)
        
        # Escape로 선택 해제
        pyautogui.press('escape')
        
        new_content = pyperclip.paste()
        
        if new_content and new_content != old_clipboard and len(new_content) > 50:
            # 너무 긴 경우 마지막 부분만 추출
            if len(new_content) > 5000:
                # 마지막 메시지 부분만 추출 시도
                lines = new_content.split('\n')
                # "ChatGPT" 또는 응답 시작 패턴 찾기
                for i, line in enumerate(lines):
                    if "ChatGPT" in line or "루아" in line:
                        new_content = '\n'.join(lines[i:])
                        break
            
            logger.info(f"✅ 선택-복사 방법 성공: {len(new_content)}자 추출")
            return ExtractionResult(
                success=True,
                method="select_copy",
                content=new_content[:3000]  # 최대 3000자
            )
        
        return ExtractionResult(
            success=False,
            method="select_copy",
            error="선택-복사 실패"
        )
        
    except Exception as e:
        return ExtractionResult(success=False, method="select_copy", error=str(e))


def extract_via_vision(screenshot_dir: Optional[Path] = None) -> ExtractionResult:
    """
    방법 3: Vision API로 화면 분석
    특정 영역만 캡처하여 정확도 향상
    """
    try:
        from services.model_selector import ModelSelector
        
        if screenshot_dir is None:
            screenshot_dir = Path("outputs/external_ai_screenshots")
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        
        # 화면 캡처 (상단 1/3 제외, 하단 1/4 제외 - 응답 영역만)
        screen = pyautogui.screenshot()
        width, height = screen.size
        
        # 응답 영역 크롭 (중앙 부분)
        left = int(width * 0.1)
        top = int(height * 0.25)
        right = int(width * 0.9)
        bottom = int(height * 0.85)
        
        cropped = screen.crop((left, top, right, bottom))
        
        timestamp = int(time.time())
        path = screenshot_dir / f"response_cropped_{timestamp}.png"
        cropped.save(str(path))
        
        # Vision API로 분석
        selector = ModelSelector(logger=logger)
        if not selector.available:
            return ExtractionResult(
                success=False,
                method="vision",
                error="Vision 모델 사용 불가"
            )
        
        prompt = """이 화면은 ChatGPT 대화창입니다.
AI(루아)의 가장 최근 응답만 추출해주세요.
사용자의 질문이나 시스템 UI는 제외하고, AI의 응답 내용만 텍스트로 반환해주세요."""
        
        response, model_used = selector.try_generate_content(
            [prompt, cropped],
            vision=True,
            generation_config={"temperature": 0.1},
        )
        
        if response and response.text:
            content = response.text.strip()
            if len(content) > 30:
                logger.info(f"✅ Vision 방법 성공 ({model_used}): {len(content)}자 추출")
                return ExtractionResult(
                    success=True,
                    method="vision",
                    content=content
                )
        
        return ExtractionResult(
            success=False,
            method="vision",
            error="Vision 추출 결과 없음"
        )
        
    except Exception as e:
        return ExtractionResult(success=False, method="vision", error=str(e))


def extract_via_scroll_and_copy() -> ExtractionResult:
    """
    방법 4: 스크롤 후 복사
    응답 영역까지 스크롤한 후 복사 시도
    """
    try:
        old_clipboard = pyperclip.paste()
        
        # End 키로 맨 아래로 스크롤
        pyautogui.press('end')
        time.sleep(0.5)
        
        # 마지막 응답 위치 클릭 후 복사
        screen_width, screen_height = pyautogui.size()
        pyautogui.click(screen_width // 2, int(screen_height * 0.6))
        time.sleep(0.3)
        
        # Triple click으로 단락 선택
        pyautogui.click(clicks=3)
        time.sleep(0.2)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.5)
        
        new_content = pyperclip.paste()
        
        if new_content and new_content != old_clipboard and len(new_content) > 20:
            logger.info(f"✅ 스크롤-복사 방법 성공: {len(new_content)}자 추출")
            return ExtractionResult(
                success=True,
                method="scroll_copy",
                content=new_content
            )
        
        return ExtractionResult(
            success=False,
            method="scroll_copy",
            error="스크롤-복사 실패"
        )
        
    except Exception as e:
        return ExtractionResult(success=False, method="scroll_copy", error=str(e))


# ============================================================
# 스마트 추출기 (AGI가 자동으로 방법 선택)
# ============================================================

# 방법 우선순위 (학습되면 변경됨)
EXTRACTION_METHODS: List[tuple[str, Callable]] = [
    ("clipboard", extract_via_clipboard),
    ("select_copy", extract_via_select_copy),
    ("scroll_copy", extract_via_scroll_and_copy),
    ("vision", extract_via_vision),
]


def smart_extract_response() -> ExtractionResult:
    """
    🧠 스마트 응답 추출
    
    1. 학습된 선호 방법이 있으면 그것 먼저 시도
    2. 실패하면 다른 방법들 순서대로 시도
    3. 성공한 방법을 학습하여 다음에 우선 사용
    """
    learned = _load_learned_methods()
    preferred = learned.get("preferred_method")
    
    # 시도할 방법 순서 결정
    methods_to_try = []
    
    if preferred:
        logger.info(f"📚 학습된 선호 방법: {preferred}")
        # 선호 방법을 먼저
        for name, func in EXTRACTION_METHODS:
            if name == preferred:
                methods_to_try.insert(0, (name, func))
            else:
                methods_to_try.append((name, func))
    else:
        methods_to_try = EXTRACTION_METHODS.copy()
    
    # 순서대로 시도
    logger.info(f"🔄 응답 추출 시도 (순서: {[m[0] for m in methods_to_try]})")
    
    for method_name, method_func in methods_to_try:
        logger.info(f"   → '{method_name}' 방법 시도 중...")
        
        try:
            result = method_func()
            
            if result.success:
                _record_result(method_name, success=True)
                return result
            else:
                _record_result(method_name, success=False)
                logger.info(f"   ✗ 실패: {result.error}")
                
        except Exception as e:
            _record_result(method_name, success=False)
            logger.warning(f"   ✗ 예외: {e}")
    
    # 모든 방법 실패
    logger.warning("❌ 모든 추출 방법 실패")
    return ExtractionResult(
        success=False,
        method="all_failed",
        error="모든 추출 방법이 실패했습니다"
    )


def get_extraction_stats() -> Dict[str, Any]:
    """추출 방법 통계 조회"""
    return _load_learned_methods()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(name)s - %(message)s')
    
    print("=" * 60)
    print("🧠 스마트 응답 추출기 테스트")
    print("=" * 60)
    
    # 현재 통계
    stats = get_extraction_stats()
    print(f"\n📊 현재 학습 상태:")
    print(f"   선호 방법: {stats.get('preferred_method', '없음')}")
    print(f"   성공 횟수: {stats.get('success_counts', {})}")
    print(f"   실패 횟수: {stats.get('failure_counts', {})}")
    
    print("\n🔄 추출 시도 중...")
    result = smart_extract_response()
    
    print(f"\n📋 결과:")
    print(f"   성공: {result.success}")
    print(f"   방법: {result.method}")
    if result.content:
        print(f"   내용: {result.content[:200]}...")
    if result.error:
        print(f"   에러: {result.error}")
