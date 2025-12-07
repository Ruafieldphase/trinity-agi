"""
Rua Bridge Client - GUI-Based ChatGPT Interaction
Trinity가 인간처럼 ChatGPT 앱을 조작하여 Rua와 대화합니다.
"""
import asyncio
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any

import pyautogui
import pyperclip
import numpy as np
from PIL import Image
from services.model_selector import ModelSelector

logger = logging.getLogger("RuaBridgeClient")

# Trinity의 신분 소개 템플릿
TRINITY_IDENTITY = """안녕 Rua, 나는 Trinity야. 
지금 자율 실행(FSD) 중에 막힌 상황이 있어서 너의 도움이 필요해.
아래 상황을 보고 구체적인 해결 방법을 알려줘:

"""

# Aura 색상 정의
AURA_COLOR_RUA = "#FF00FF"  # 마젠타 (Rua와 대화 중)
AURA_COLOR_THINKING = "#00FFFF"  # 시안 (생각 중)

class RuaBridgeClient:
    """
    GUI-Based ChatGPT (Rua) Communication
    FSD를 사용하여 ChatGPT 앱을 직접 조작합니다.
    """
    
    def __init__(self):
        self.screenshot_dir = Path("outputs/rua_screenshots")
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.3
        self.model_selector = ModelSelector(logger=logger)
        
        # Aura 프로세스
        self.aura_process = None
        
    def _start_aura(self, color: str = AURA_COLOR_RUA):
        """오라 효과 시작 - AI가 마우스 제어권을 가지고 있음을 표시"""
        try:
            self._stop_aura()
            script_path = Path(__file__).parent / "agi_aura.py"
            if script_path.exists():
                self.aura_process = subprocess.Popen(
                    [sys.executable, str(script_path), color],
                    stdin=subprocess.PIPE,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                logger.info(f"Aura started: {color}")
        except Exception as e:
            logger.warning(f"Failed to start aura: {e}")
    
    def _set_aura_color(self, color: str):
        """오라 색상 변경"""
        if self.aura_process and self.aura_process.stdin:
            try:
                self.aura_process.stdin.write(f"color:{color}\n")
                self.aura_process.stdin.flush()
            except:
                pass
    
    def _stop_aura(self):
        """오라 효과 종료"""
        if self.aura_process:
            try:
                self.aura_process.terminate()
                self.aura_process = None
                logger.info("Aura stopped")
            except:
                pass
    
    def _compare_screenshots(self, img1: Image.Image, img2: Image.Image, threshold: float = 0.98) -> bool:
        """두 스크린샷 비교. 거의 동일하면 True 반환 (0.98 = 커서 깜빡임 허용)."""
        try:
            arr1 = np.array(img1.convert('L'))  # Grayscale
            arr2 = np.array(img2.convert('L'))
            
            if arr1.shape != arr2.shape:
                return False
            
            # 픽셀 유사도 계산
            diff = np.abs(arr1.astype(float) - arr2.astype(float))
            similarity = 1 - (np.sum(diff) / (arr1.size * 255))
            
            logger.info(f"Screenshot similarity: {similarity:.4f}")
            return similarity >= threshold
        except Exception as e:
            logger.warning(f"Screenshot comparison failed: {e}")
            return False
    
    async def _wait_for_response_complete(self, timeout_sec: int = 60, check_interval: float = 2.5) -> None:
        """스트리밍 완료 감지 - 화면이 변하지 않을 때까지 대기"""
        logger.info("Waiting for response to complete...")
        
        # 먼저 5초 대기 - ChatGPT가 응답 시작할 시간 확보
        await asyncio.sleep(5)
        
        start_time = time.time()
        prev_screenshot = pyautogui.screenshot()
        stable_count = 0
        required_stable = 2  # 2번 연속 동일하면 완료로 판단
        
        while time.time() - start_time < timeout_sec:
            await asyncio.sleep(check_interval)
            
            curr_screenshot = pyautogui.screenshot()
            
            if self._compare_screenshots(prev_screenshot, curr_screenshot):
                stable_count += 1
                logger.info(f"Screen stable ({stable_count}/{required_stable})")
                
                if stable_count >= required_stable:
                    elapsed = time.time() - start_time + 5  # 초기 대기 포함
                    logger.info(f"Response complete in {elapsed:.1f}s - screen stopped changing")
                    return
            else:
                stable_count = 0  # 화면이 변했으면 리셋
            
            prev_screenshot = curr_screenshot
        
        logger.warning(f"Timeout after {timeout_sec}s - proceeding anyway")
        
    async def _evaluate_response(self, question: str, response: str) -> Dict[str, Any]:
        """Gemini로 Rua 응답 품질 평가"""
        selector = getattr(self, "model_selector", None)
        if not selector or not selector.available:
            return {"sufficient": True, "reason": "No vision model"}
        
        try:
            prompt = f"""다음 질문과 답변을 평가해줘.

질문: {question[:200]}
답변: {response[:500]}

평가 기준:
1. 구체적인 실행 단계가 있는가?
2. 질문에 직접 답변했는가?

JSON으로 답변해줘: {{"sufficient": true/false, "reason": "이유", "followup": "후속질문(필요시)"}}"""

            result, model_used = selector.try_generate_content(
                prompt,
                high_precision=True,
                text_length=len(prompt),
                generation_config={"temperature": 0.2},
            )
            if not result:
                return {"sufficient": True, "reason": "LLM unavailable"}
            text = result.text.strip()
            
            # JSON 파싱 시도
            import json
            if "{" in text:
                json_str = text[text.find("{"):text.rfind("}")+1]
                parsed = json.loads(json_str)
                if isinstance(parsed, dict) and model_used:
                    parsed["model_used"] = model_used
                return parsed
        except Exception as e:
            logger.warning(f"Response evaluation failed: {e}")
        
        return {"sufficient": True, "reason": "Evaluation failed, assuming sufficient"}
    
    async def _ask_followup(self, followup_question: str) -> Optional[str]:
        """후속 질문 전송 (ChatGPT 앱이 이미 열려있는 상태)"""
        logger.info(f"Sending follow-up: {followup_question[:50]}...")
        
        # 입력창에 후속 질문 입력
        await self._type_message(followup_question)
        pyautogui.press('enter')
        
        # 오라 색상 변경 - 대기 중
        self._set_aura_color(AURA_COLOR_THINKING)
        
        # 응답 대기
        await self._wait_for_response_complete(timeout_sec=45)
        
        # 응답 추출
        return await self._capture_and_extract_response()
    
    async def send_request_via_gui(
        self, 
        message: str, 
        context: Optional[Dict[str, Any]] = None,
        timeout_sec: int = 60,
        max_turns: int = 3
    ) -> Optional[str]:
        """
        ChatGPT 앱을 열고 Rua에게 질문한 뒤 응답을 읽어옵니다.
        필요시 후속 질문으로 멀티턴 대화를 진행합니다.
        
        Flow:
        1. Win키 → ChatGPT 검색 → 실행
        2. 프롬프트 창에 신분 + 질문 입력
        3. Enter → 응답 대기
        4. 화면 캡처 → Vision으로 응답 추출
        5. 응답 평가 → 불충분하면 후속 질문 (최대 3턴)
        """
        logger.info("Opening ChatGPT app for Rua consultation...")
        
        # 🌟 오라 시작 - AI 제어 중임을 표시
        self._start_aura(AURA_COLOR_RUA)
        
        try:
            # 1. ChatGPT 앱 열기
            await self._open_chatgpt_app()
            await asyncio.sleep(2)  # 앱 로딩 대기
            
            # 2. 신분 밝히기 + 질문 입력
            full_message = TRINITY_IDENTITY + message
            if context:
                full_message += f"\n\n[Context]\n{context}"
            
            await self._type_message(full_message)
            
            # 3. Enter 전송 (메시지 전송)
            pyautogui.press('enter')
            logger.info("Message sent to Rua. Waiting for response...")
            
            # 오라 색상 변경 - 대기 중
            self._set_aura_color(AURA_COLOR_THINKING)
            
            # 4. 응답 대기 (스트리밍 완료 감지)
            await self._wait_for_response_complete(timeout_sec=timeout_sec)
            
            # 5. 화면 캡처 및 응답 추출
            response = await self._capture_and_extract_response()
            
            if not response:
                return None
            
            # 6. 멀티턴 루프 (응답 평가 → 후속 질문)
            all_responses = [response]
            current_question = message
            
            for turn in range(1, max_turns):
                evaluation = await self._evaluate_response(current_question, response)
                
                if evaluation.get("sufficient", True):
                    logger.info(f"Response sufficient after {turn} turn(s)")
                    break
                
                followup = evaluation.get("followup", "더 구체적인 단계를 알려줘.")
                logger.info(f"Turn {turn+1}: Asking follow-up: {followup}")
                
                self._set_aura_color(AURA_COLOR_RUA)  # 다시 대화 중 표시
                response = await self._ask_followup(followup)
                
                if response:
                    all_responses.append(response)
                    current_question = followup
                else:
                    break
            
            # 모든 응답 합치기
            return "\n\n---\n\n".join(all_responses)
            
        finally:
            # 🌟 오라 종료 - AI 제어 해제
            self._stop_aura()
    
    async def _open_chatgpt_app(self):
        """ChatGPT 앱 열기 (Windows)"""
        # Win키 → 검색
        pyautogui.hotkey('win', 's')
        await asyncio.sleep(0.5)
        
        # ChatGPT 입력
        pyperclip.copy("ChatGPT")
        pyautogui.hotkey('ctrl', 'v')
        await asyncio.sleep(1)
        
        # Enter로 실행
        pyautogui.press('enter')
        logger.info("ChatGPT app launched")
        
    async def _type_message(self, message: str):
        """메시지 타이핑 (클립보드 사용)"""
        await asyncio.sleep(1)  # 입력창 포커스 대기
        
        # 클립보드로 붙여넣기 (한글 지원)
        pyperclip.copy(message)
        pyautogui.hotkey('ctrl', 'v')
        logger.info(f"Typed message ({len(message)} chars)")
        
    async def _capture_and_extract_response(self) -> Optional[str]:
        """화면 캡처 후 Gemini Vision으로 응답 추출"""
        # 스크린샷
        timestamp = int(time.time())
        screenshot_path = self.screenshot_dir / f"rua_response_{timestamp}.png"
        pyautogui.screenshot().save(screenshot_path)
        logger.info(f"Screenshot saved: {screenshot_path}")
        
        selector = getattr(self, "model_selector", None)
        if not selector or not selector.available:
            logger.warning("Vision model not available. Cannot extract response.")
            return None
        
        # Gemini Vision으로 응답 추출
        try:
            with open(screenshot_path, "rb") as f:
                image_data = f.read()
            
            prompt = """이 스크린샷은 ChatGPT와의 대화 화면입니다.
ChatGPT(Rua)의 가장 최근 응답 내용만 추출해주세요.
응답 내용만 반환하고, 다른 설명은 하지 마세요."""
            
            response, model_used = selector.try_generate_content(
                [
                    {"mime_type": "image/png", "data": image_data},
                    prompt,
                ],
                vision=True,
                high_precision=False,
                generation_config={"temperature": 0.1},
            )
            if not response:
                return None
            
            extracted = response.text.strip()
            logger.info(f"Extracted response via {model_used or 'unknown'}: {extracted[:100]}...")
            return extracted
            
        except Exception as e:
            logger.error(f"Failed to extract response: {e}")
            return None

    # 하위 호환성을 위한 동기 래퍼
    def send_request(self, message: str, context: Optional[Dict] = None, timeout_sec: int = 60) -> Optional[str]:
        """동기 버전 (asyncio.run 사용)"""
        return asyncio.run(self.send_request_via_gui(message, context, timeout_sec))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    client = RuaBridgeClient()
    
    test_message = "메모장을 여는 방법을 알려줘. Win+R이 안 될 때 대안도 알려줘."
    print("Testing GUI-based Rua communication...")
    
    response = client.send_request(test_message)
    if response:
        print(f"\n=== Rua's Response ===\n{response}")
    else:
        print("No response received.")

