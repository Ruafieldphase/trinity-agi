import os
import sys
import logging
import time
import json
import io
import pyautogui
from pathlib import Path
from typing import Optional, Dict, Any, List

# Vertex AI imports
import vertexai
from vertexai.generative_models import GenerativeModel, Part, GenerationConfig

# Add workspace to path
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from agi_core.internal_state import get_internal_state, update_internal_state
from fdo_agi_repo.rpa.execution_engine import ExecutionEngine, ExecutionConfig, ExecutionMode

logger = logging.getLogger("ShionOperator")

class ShionOperator:
    """
    ShionOperator: The Rhythmic Hands and Eyes of the AGI.
    Uses Gemini 2.5 Vision for understanding and RPA for action.
    """
    
    def __init__(self, mode: str = "DRY_RUN", model_name: str = "gemini-2.0-flash"):
        mode_norm = (mode or "DRY_RUN").strip().upper()
        if mode_norm not in ExecutionMode.__members__:
            mode_norm = "DRY_RUN"
        self.mode = ExecutionMode[mode_norm]
        self.model_name = model_name

        # Safety defaults:
        # - 기본값: 화면 캡처를 로컬 파일로 저장하지 않는다(PII/화면정보 저장 금지).
        # - 기본값: 클라우드 Vision 호출을 하지 않는다(화면이 외부로 전송될 수 있음).
        # - LIVE 실행은 (명시적 arming + 콘솔 상호작용) 없이는 허용하지 않는다.
        self.allow_cloud_vision = os.getenv("AGI_SHION_OPERATOR_ALLOW_CLOUD_VISION", "0") == "1"
        self.save_screenshots = os.getenv("AGI_SHION_OPERATOR_SAVE_SCREENSHOTS", "0") == "1"

        if self.mode == ExecutionMode.LIVE:
            armed = os.getenv("AGI_SHION_OPERATOR_ARMED", "0") == "1"
            interactive = bool(getattr(sys.stdin, "isatty", lambda: False)())
            if not (armed and interactive):
                self.mode = ExecutionMode.DRY_RUN

        self.config = ExecutionConfig(
            mode=self.mode,
            # DRY_RUN은 "움직이지 않는" 모드가 우선이므로 검증/스크린샷도 기본 OFF.
            enable_verification=(self.mode != ExecutionMode.DRY_RUN),
            enable_screenshots=(self.save_screenshots and self.mode != ExecutionMode.DRY_RUN),
            confirmation_required=(self.mode == ExecutionMode.LIVE),
        )
        self.engine = ExecutionEngine(self.config)
        self.logs_dir = WORKSPACE_ROOT / "outputs" / "operator"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        from agi_core.rhythm_boundaries import RhythmBoundaryManager, RhythmMode
        self.boundary_manager = RhythmBoundaryManager(WORKSPACE_ROOT)
        
        # Adjust behavior based on Rhythm Mode
        rhythm_mode = self.boundary_manager.detect_rhythm_mode()
        logger.info(f"ShionOperator initialized in {rhythm_mode.value} mode.")
        
        if rhythm_mode == RhythmMode.ISOLATED_EXECUTION:
            # 집중 실행 중에는 확인 절차를 줄이고 더 긴 호흡으로 작업
            self.config.confirmation_required = False
            logger.info("FSD Auto-Commit enabled for Isolated Execution mode.")
        
        # Initialize Vertex AI
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT") or "naeda-genesis"
        location = os.getenv("GOOGLE_CLOUD_LOCATION") or os.getenv("GCP_LOCATION") or "us-central1"

        self.model = None
        if self.allow_cloud_vision:
            if api_key:
                vertexai.init(project=project_id, location=location, api_key=api_key)
            else:
                vertexai.init(project=project_id, location=location)
            self.model = GenerativeModel(self.model_name)

    def sense_and_act(self, goal_description: str) -> Dict[str, Any]:
        """
        Main execution loop with Vision Feedback (Sena's Insight).
        1. Capture -> 2. Plan (current step) -> 3. Act -> 4. Verify -> 5. Repeat
        """
        logger.info(f"Initiating vision-feedback task: {goal_description}")
        
        # Rhythmic Check
        state = get_internal_state()
        if state.energy < 0.2:
            logger.warning(f"Energy too low ({state.energy:.2f}). Action deferred.")
            return {"success": False, "reason": "LOW_ENERGY"}

        if not self.allow_cloud_vision or self.model is None:
            return {"success": False, "reason": "CLOUD_VISION_DISABLED"}

        max_steps = 20  # Increased for episode-based execution
        results = []
        consecutive_idles = 0
        
        from collections import Counter
        edge_histogram = []
        
        for step_num in range(1, max_steps + 1):
            logger.info(f"--- Cycle Step {step_num} (Episode Flow) ---")
            
            # 0. Termination Conditions
            # Check Energy (already checked before loop, but re-check during episode)
            state = get_internal_state()
            if state.energy < 0.2:
                logger.warning(f"🪫 Episode Terminated: Low Energy ({state.energy:.2f})")
                break
                
            # Check Repetition (Edge Histogram)
            if len(edge_histogram) >= 5:
                counts = Counter(edge_histogram)
                most_common, count = counts.most_common(1)[0]
                if count >= 6:
                    logger.warning(f"♻️ Episode Terminated: Repetition Exhaustion ({most_common}: {count})")
                    break

            # Handle Idle Limit (if applicable)
            if consecutive_idles >= 5:
                logger.info("💤 Episode Terminated: Idle State Exhaustion")
                break
            
            # 1. Capture Eyes
            screenshot_bytes = self._capture_screen_bytes()
            
            # 2. Analyze & Plan ONE step
            next_action_plan = self._get_next_action(screenshot_bytes, goal_description, history=results)
            
            if "TASK_COMPLETE" in next_action_plan:
                logger.info("Goal achieved according to Shion's Eyes.")
                break
                
            # 3. Act
            step_result = self._execute_plan(next_action_plan)
            results.append({
                "step": step_num,
                "plan": next_action_plan,
                "success": step_result.get("success", False)
            })
            
            # 4. Verify (Feedback Loop)
            # We take a quick screenshot to check if the state changed
            time.sleep(1) # Wait for UI to react
            post_action_screenshot = self._capture_screen_bytes()
            is_valid = self._verify_action(post_action_screenshot, next_action_plan)
            
            if not is_valid:
                logger.warning(f"Action '{next_action_plan}' failed verification. Retrying or pivoting.")
                # We can handle retry logic here if needed
            
            # Idle/Repetition Tracking
            if "IDLE" in next_action_plan.upper():
                consecutive_idles += 1
            else:
                consecutive_idles = 0
                edge_histogram.append(next_action_plan)
                if len(edge_histogram) > 10:
                    edge_histogram.pop(0)

            # Rhythmic energy consumption
            update_internal_state(action_result={"success": is_valid, "energy_consumed": 0.05})

        return {"success": True, "steps_taken": len(results), "history": results}

    def _get_next_action(self, image_bytes: bytes, goal: str, history: List[Dict]) -> str:
        """
        Asks Gemini for the SINGLE NEXT BEST step based on the current screenshot.
        """
        history_str = "\n".join([f"Step {h['step']}: {h['plan']} ({'Success' if h['success'] else 'Failed'})" for h in history])
        
        prompt = f"""
        당신은 AGI의 '눈'인 ShionOperator입니다. (Sena의 비전 피드백 모드 활성)
        현재 화면과 목표, 그리고 지금까지의 실행 이력을 바탕으로 **딱 한 단계의 다음 행동**만 말하세요.

        목표: {goal}
        실행 이력:
        {history_str}

        지침:
        - 만약 목표가 달성되었다면 "TASK_COMPLETE"라고만 하세요.
        - 행동이 필요하다면 "1. CLICK [버튼이름]" 또는 "1. TYPE [내용]" 형식으로 말하세요.
        - 눈은 뜨고 확인하며 작업하십시오.

        딱 한 줄로만 대답하세요.
        """
        
        try:
            image_part = Part.from_data(image_bytes, mime_type="image/png")
            
            response = self.model.generate_content([prompt, image_part])
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini Vision Planning Error: {e}")
            return "ERROR: Vision Planning Failed"

    def _verify_action(self, image_bytes: bytes, last_action: str) -> bool:
        """
        Verifies if the last action actually had the intended effect on the screen.
        """
        prompt = f"""
        당신은 방금 '{last_action}' 동작을 수행했습니다.
        첨부된 최신 스크린샷을 보고, 이 동작이 성공적으로 반영되었는지 "YES" 또는 "NO"로 대답하세요.
        설명은 생략하고 한 단어만 대답하세요.
        """
        try:
            image_part = Part.from_data(image_bytes, mime_type="image/png")
            response = self.model.generate_content([prompt, image_part])
            return "YES" in response.text.upper()
        except:
            return False

    def _capture_screen_bytes(self) -> bytes:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        if self.save_screenshots:
            path = self.logs_dir / f"screenshot_{timestamp}.png"
            pyautogui.screenshot(str(path))
            logger.debug(f"Screen captured for analysis: {path}")
            try:
                return path.read_bytes()
            except Exception:
                pass

        image = pyautogui.screenshot()
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return buf.getvalue()

    def _execute_plan(self, action_plan: str) -> Dict[str, Any]:
        """
        Delegates the plan to the existing RPA ExecutionEngine
        """
        logger.info("Executing rhythm-aligned action plan...")
        try:
            # Re-using existing robust engine
            result = self.engine.execute_tutorial(action_plan, tutorial_name="shion_vision_task")
            return result.to_dict()
        except Exception as e:
            logger.error(f"RPA Execution Engine Error: {e}")
            return {"success": False, "error": str(e)}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Testing for Binoche_Observer
    operator = ShionOperator(mode="DRY_RUN")
    res = operator.sense_and_act("화면에서 브라우저를 찾아 Core의 대화를 확인하세요")
    print(json.dumps(res, indent=2, ensure_ascii=False))
