import asyncio
import json
import logging
import os
import time
import subprocess
import sys
import io
from collections import deque, Counter
from PIL import Image, ImageDraw, ImageFont
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import httpx

try:
    import config
    BG_SELF_URL = f"http://127.0.0.1:{config.BACKGROUND_SELF_PORT}/sensation"
except:
    BG_SELF_URL = "http://127.0.0.1:8102/sensation"

import pyautogui
from services.trinity_conscious_protocol import TrinityConsciousProtocol
from services.model_selector import ModelSelector
from agi_core.internal_state import get_internal_state
from services.slack_gateway import get_slack_gateway
from services.arch_fsd_strategy import ArchFSDStrategy
from services.local_vision_service import analyze_image_locally
from services.experience_vault import ExperienceVault
from services.blender_bridge_service import BlenderBridgeService

# BTF System imports
from services.binoche_trigger import BinocheTriggerFunction, BTFContext, BTFAction, get_btf
from services.human_escalation import HumanEscalation, EscalationRequest, get_escalation
from services.exploration_policy import ExplorationPolicy, get_exploration_policy

class ActionType(Enum):
    """실행 가능한 액션 타입"""
    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    TYPE = "type"
    PRESS_KEY = "press_key"
    HOTKEY = "hotkey"
    SCROLL = "scroll"
    WAIT = "wait"
    IDLE = "idle"
    QUESTION = "question"
    DONE = "done"
    FAILED = "failed"


@dataclass
class Action:
    """실행할 액션"""
    type: ActionType
    x: Optional[int] = None
    y: Optional[int] = None
    text: Optional[str] = None
    key: Optional[str] = None
    keys: Optional[List[str]] = None
    amount: Optional[int] = None
    reason: str = ""
    confidence: float = 0.0


@dataclass
class ExecutionStep:
    """실행 단계 기록"""
    step_number: int
    action: Action
    screenshot_before: Optional[str] = None
    screenshot_after: Optional[str] = None
    success: bool = True
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ExecutionResult:
    """실행 결과"""
    goal: str
    success: bool
    steps: List[ExecutionStep]
    final_screenshot: Optional[str] = None
    message: str = ""
    total_time: float = 0.0


class FSDController:
    """
    AGI FSD 자율 실행 컨트롤러 - 'Shion (Action Layer)'
    """
    
    def __init__(
        self,
        max_steps: int = 20,
        step_delay: float = 1.0,
        screenshot_dir: Optional[Path] = None,
        use_obs: bool = True,
        verify_mode: bool = False
    ):
        self.max_steps = max_steps
        self.step_delay = step_delay
        self.screenshot_dir = screenshot_dir or Path("outputs/fsd_screenshots")
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger("fsd_controller")
        self.logger.setLevel(logging.INFO)
        
        # Phase 3.1: Verification Mode (suppress heavy I/O)
        self.verify_mode = verify_mode or (os.getenv("AGI_VERIFY_MODE") == "1")
        if self.verify_mode:
            os.environ["AGI_VERIFY_MODE"] = "1"
            self.logger.info("🧪 FSD Controller running in VERIFY_MODE. Resource-heavy sync suppressed.")
        
        # OBS 실시간 눈 설정 (Phase 5: JIT 운용 원칙 반영)
        self.use_obs = use_obs
        self.obs_eye = None
        if self.use_obs:
            self.logger.info("👁️ Vision Principle: OBS JIT (Just-in-Time) mode enabled.")
        
        # 학습 지식 베이스 로드
        try:
            from fsd_knowledge_base import get_knowledge_base
            self.knowledge_base = get_knowledge_base()
            self.logger.info(f"✓ Knowledge Base loaded")
        except Exception as e:
            self.logger.warning(f"Knowledge Base not available: {e}")
            self.knowledge_base = None
        
        # Gemini 모델 초기화 (Vertex) with dynamic selector
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        self.model_selector = ModelSelector(project=project, location=location, logger=self.logger)
        if self.model_selector.available:
            self.logger.info("✓ FSD Controller initialized with Gemini selector")
        else:
            self.logger.warning("Gemini not available: missing GOOGLE_CLOUD_PROJECT")
        
        # 안전 설정
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.3
        
        self.screen_width, self.screen_height = pyautogui.size()
        
        # AGI Aura
        self.aura_process = None
        self.last_action_visual = None
        self.last_thought_text = "Ready"
        self.last_thought_time = time.time()
        self.current_aura_color = "#00FFFF"
        
        # Trinity Conscious Protocol (Shion to Trinity)
        self.trinity_protocol = TrinityConsciousProtocol()
        self.identity = "Shion (Action Layer)"
        
        # BTF System
        self.btf = get_btf()
        self.escalation = get_escalation()
        self.exploration_policy = ExplorationPolicy()
        self.experience_vault = ExperienceVault()
        self.blender_bridge = BlenderBridgeService()
        self.failure_count = {"api": 0, "ui": 0}
        self.slack = get_slack_gateway()
        
        self.logger.info(f"Screen: {self.screen_width}x{self.screen_height}")

        # Edge Histogram for Repetition Penalty
        self.max_history = 10
        self.edge_histogram = deque(maxlen=self.max_history)
        
        # Question Policies
        self.questions_asked = 0
        self.max_questions_per_episode = 2
        self.boundary_memory = {} 
        self.max_boundary_entries = 50 
        self.risky_keywords = ["delete", "remove", "send", "confirm", "pay", "buy", "format", "terminate", "삭제", "전송", "결제", "확인"]
        
        # Architectural Principles integration
        self.arch_strategy = ArchFSDStrategy()

    async def _report_sensation(self, status: str, details: str, intensity: float = 0.0) -> float:
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(BG_SELF_URL, json={"type": "visual_action", "status": status, "details": details, "intensity": intensity, "source": "Shion"}, timeout=0.5)
                if res.status_code == 200:
                    return res.json().get("anxiety", 0.0)
        except: pass
        return 0.0

    def _update_hud(self, text: str, subtext: str = "", confidence: float = 0.0):
        if self.aura_process and self.aura_process.stdin:
            try:
                self.aura_process.stdin.write(f"hud:{text}|{subtext}|{confidence}\n")
                self.aura_process.stdin.flush()
            except: pass

    async def execute_goal(self, goal: str, instruction: Optional[Dict[str, Any]] = None, supervisor_callback: Optional[callable] = None) -> ExecutionResult:
        self.logger.info(f"🎯 Goal: {goal}")
        
        # Check ExperienceVault for historical success
        historical_actions = self.experience_vault.find_experience(goal)
        if historical_actions:
            self.logger.info(f"💡 Found historical rhythm in ExperienceVault. Attempting replay...")
            for i, action_data in enumerate(historical_actions):
                self.logger.info(f"Replaying step {i+1}: {action_data}")
                # Implementation of replay would go here, for now it's a hint
        
        # Phase 7: Check if Direct Bridge (e.g. Blender) is applicable
        if "blender" in goal.lower() or "direct" in goal.lower():
            self.logger.info("🌉 Direct Bridge Goal detected. Attempting bypass...")
            # For specific high-level goals, we can skip vision
            if "clean" in goal.lower() or "story" in goal.lower() or "generate" in goal.lower():
                self.logger.info("📐 Decomposing semantic architectural goal...")
                batch_commands = self.arch_strategy.decompose_semantic_goal(goal)
                
                success_count = 0
                for cmd_data in batch_commands:
                    res = self.blender_bridge.send_command(cmd_data["command"], cmd_data["params"])
                    if res.get("status") == "success":
                        success_count += 1
                
                if success_count > 0:
                    return Action(type=ActionType.DONE, reason=f"Generated {success_count} structural elements via direct bridge")
                else:
                    self.logger.warning("Semantic batch execution failed or returned no successes. Falling back to vision.")
        
        steps_executed = []
        await self._report_sensation("running", f"Start Goal: {goal}")
        self._start_aura("#00FFFF")
        start_time = time.time()
        steps: List[ExecutionStep] = []
        consecutive_idles = 0
        max_consecutive_idles = 5

        if not self.model_selector.available:
            msg = "Gemini 미가용 상태 - FSD 테스트 모드"
            await self._report_sensation("done", msg, 0.0)
            return ExecutionResult(goal=goal, success=True, steps=steps, message=msg, total_time=time.time() - start_time)

        try:
            for step_num in range(1, self.max_steps + 1):
                self.logger.info(f"\nStep {step_num}/{self.max_steps}")
                internal_state = get_internal_state()
                if internal_state.energy < 0.2: break
                
                # Repetition Check
                if len(self.edge_histogram) >= 5:
                    counts = Counter(self.edge_histogram)
                    most_common_act, count = counts.most_common(1)[0]
                    if count >= 6: break
                
                panic_mode = False
                if consecutive_idles > 0:
                    screenshot_path = steps[-1].screenshot_after if steps and steps[-1].screenshot_after else await self._capture_screen(f"step_{step_num}_before")
                    current_anxiety = 0.0
                else:
                    screenshot_path = await self._capture_screen(f"step_{step_num}_before")
                    current_anxiety = await self._report_sensation("stagnant", "Thinking...", 0.0)
                    if current_anxiety > 0.8: break
                    if current_anxiety > 0.6:
                        self._set_aura_color("#FF00FF")
                        panic_mode = True
                        history_summary = "\n".join([f"- {s.step_number}: {s.action.type.value}" for s in steps[-5:]])
                        trinity_advice = self.trinity_protocol.resolve_anxiety({"goal": goal, "step_index": step_num, "history": history_summary, "last_thought": self.last_thought_text}, current_anxiety)
                        if trinity_advice:
                            if not instruction: instruction = {}
                            instruction['fractal_guidance'] = trinity_advice

                action = await self._analyze_and_decide(goal, steps, screenshot_path, instruction, panic_mode)
                self._set_aura_color("#00FFFF")
                if action is None: return ExecutionResult(goal=goal, success=False, steps=steps, message="분석 실패", total_time=time.time() - start_time)
                
                # Update HUD with decision
                self._update_hud(f"Action: {action.type.value}", action.reason[:50] + "...", action.confidence)
                
                action_key = f"{action.type.value}_{action.x}_{action.y}" if action.x else action.type.value
                self.edge_histogram.append(action_key)
                self.logger.info(f"Action: {action.type.value} - {action.reason}")
                
                if action.type == ActionType.DONE:
                    final_screenshot = await self._capture_screen("final")
                    return ExecutionResult(goal=goal, success=True, steps=steps, final_screenshot=final_screenshot, message=action.reason, total_time=time.time() - start_time)
                
                if action.type == ActionType.FAILED:
                    self._set_aura_color("#FF0000")
                    return ExecutionResult(goal=goal, success=False, steps=steps, message=action.reason, total_time=time.time() - start_time)
                
                if action.type == ActionType.QUESTION:
                    question_text = action.text or action.reason
                    target_app = instruction.get('target_app', 'unknown') if instruction else 'unknown'
                    signature = f"{goal}:{target_app}:{instruction.get('phase', 1) if instruction else 1}"
                    sig_data = self.boundary_memory.get(signature, {"asked": False, "timeouts": 0, "answered": False})
                    
                    if sig_data.get("answered") or (sig_data.get("asked") and sig_data.get("timeouts", 0) == 0):
                        continue

                    if self.questions_asked >= self.max_questions_per_episode or sig_data.get("timeouts", 0) >= 2:
                        action.type = ActionType.IDLE
                    else:
                        self._set_aura_color("#FFA500")
                        ts = self.slack.send_question(question_text, action.keys or ["확인", "취소"])
                        if ts:
                            self.questions_asked += 1
                            if signature not in self.boundary_memory:
                                if len(self.boundary_memory) >= self.max_boundary_entries: del self.boundary_memory[next(iter(self.boundary_memory))]
                                self.boundary_memory[signature] = {"text": question_text, "asked": True, "timeouts": 0, "answered": False}
                            else: self.boundary_memory[signature]["asked"] = True
                            
                            tuner_response = None
                            tuner_wait_start = time.time()
                            while tuner_response is None and (time.time() - tuner_wait_start < 300):
                                tuner_response = await self.slack.wait_for_response(ts, timeout=10)
                                if tuner_response: break
                                await asyncio.sleep(5)
                            
                            if tuner_response:
                                if not instruction: instruction = {}
                                instruction['fractal_guidance'] = f"State Transformed: {tuner_response}"
                                self.boundary_memory[signature]["answered"] = True
                                self.boundary_memory[signature]["timeouts"] = 0
                                continue
                            else:
                                self.boundary_memory[signature]["timeouts"] += 1
                                action.type = ActionType.IDLE
                        else: action.type = ActionType.IDLE

                if action.type == ActionType.IDLE:
                    consecutive_idles += 1
                    if consecutive_idles >= max_consecutive_idles: break
                else: consecutive_idles = 0

                if supervisor_callback and not await supervisor_callback(step_num, action):
                    return ExecutionResult(goal=goal, success=False, steps=steps, message="중단됨", total_time=time.time() - start_time)
                
                success = await self._execute_action(action)
                if not success:
                    self.failure_count["ui"] += 1
                    btf_ctx = BTFContext(goal=goal, api_failures=self.failure_count["api"], ui_failures=self.failure_count["ui"], confidence=action.confidence, previous_attempts=[{"step": s.step_number, "action": s.action.type.value} for s in steps[-5:]], current_anxiety=current_anxiety)
                    if self.btf.should_invoke(btf_ctx):
                        btf_result = self.btf.invoke(btf_ctx)
                        if btf_result.action == BTFAction.ASK_USER:
                            await self.escalation.notify(EscalationRequest(goal=goal, problem_description=f"BTF ASK_USER", attempted_actions=[f"{s.action.type.value}" for s in steps[-5:]], suggested_solutions=[btf_result.suggested_direction or "변경"]))
                        elif btf_result.action == BTFAction.REJECT: return ExecutionResult(goal=goal, success=False, steps=steps, message=f"BTF REJECT", total_time=time.time() - start_time)
                else: self.failure_count = {"api": 0, "ui": 0}

                screenshot_after = steps[-1].screenshot_after if action.type == ActionType.IDLE and consecutive_idles > 1 else await self._capture_screen(f"step_{step_num}_after")
                steps.append(ExecutionStep(step_number=step_num, action=action, screenshot_before=screenshot_path, screenshot_after=screenshot_after, success=success))
                await asyncio.sleep(self.step_delay)
            
            return ExecutionResult(goal=goal, success=True, steps=steps, message="완료", total_time=time.time() - start_time)
        finally:
            self._stop_aura()

    async def _capture_screen(self, name: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.png"
        filepath = self.screenshot_dir / filename
        if self.use_obs:
            try:
                from obs_live_eye import OBSLiveEye
                eye = OBSLiveEye()
                if eye.connect():
                    obs_path = eye.save_current_frame(name)
                    eye.disconnect()
                    if obs_path: return obs_path
            except: pass
        pyautogui.screenshot().save(filepath)
        return str(filepath)

    async def _analyze_and_decide(self, goal: str, previous_steps: List[ExecutionStep], screenshot_path: str, instruction: Optional[Dict[str, Any]] = None, panic_mode: bool = False) -> Optional[Action]:
        selector = getattr(self, "model_selector", None)
        if not selector or not selector.available: return None
        
        context_str = f"{goal} {instruction.get('content', '') if instruction else ''}".lower()
        hard_gate_open = any(k in context_str for k in self.risky_keywords)
        history = "\\n".join([f"- {s.step_number}: {s.action.type.value} ({s.action.reason})" for s in previous_steps[-5:]])
        
        # Apply Architectural Strategy
        arch_enhancement = self.arch_strategy.get_folding_prompt_enhancement()
        step_rhythm = self.arch_strategy.synthesize_modeling_rhythm(len(previous_steps), [s.__dict__ for s in previous_steps])
        
        instruction_text = ""
        if instruction:
            guidance = instruction.get('fractal_guidance', '')
            instruction_text = f"## 지시\n- Target: {instruction.get('target_app', 'N/A')}\n- Content: {instruction.get('content', 'N/A')}\n- Guidance: {guidance}\n"

        prompt = f"""당신은 'Shion (Shion)'입니다. AGI의 행동 엔진입니다.
[코어의 지침]
[코어의 지침 - Shion의 리듬 전환 선언]
"질문을 제한할 필요는 없다. 대신 질문이 나오기 전, 충분히 살아본 흔적(내부 분석, 대안 시도, 보수적 판단)이 있어야 한다. 질문은 사고의 출발점이 아니라 도착점이다. 시도 흔적(trace)이 없는 질문은 생성하지 않는다. 지금은 튜닝이 아니라 경험의 단계다."

[목표] {goal}
{instruction_text}
[최근 실행] {history}
위험 감지: {"활성" if hard_gate_open else "비활성"}

[전용 워크플로우: FSD 리듬]
{arch_enhancement}
{step_rhythm}
기준 상수 C: {self.arch_strategy.constant_c}

지시를 완수하기 위한 다음 행동을 JSON으로 응답하세요. 만약 질문(question)을 선택한다면, 반드시 'reason' 필드에 어떤 내부 분석과 대안 시도를 거쳤는지 상세히 기술해야 합니다.
"""
        try:
            with open(screenshot_path, "rb") as f: image_data = f.read()
            response, model_used = selector.try_generate_content([{"mime_type": "image/png", "data": image_data}, prompt], intent="FSD_ACTION", urgency=panic_mode, high_precision=True, vision=True)
            
            if response:
                response_text = response.text
            else:
                self.logger.warning("Gemini API failed or returned empty. Falling back to Local Vision (LLaVA)...")
                
                # Assertive prompt for local vision with primitive constraint
                allowed_actions = ", ".join([t.value for t in ActionType])
                
                # More descriptive assertive prompt for local vision
                local_prompt = f"""[Instruction] You are an expert architectural vision agent.
Goal: '{goal}'
Instruction: {instruction_text}

Task: Output ONLY valid JSON with {{"action": "click", "x": 100, "y": 200, "reason": "why"}}.
ALLOWED ACTIONS: {allowed_actions}
IMPORTANT: If elements are blurry, provide your BEST ESTIMATE for coordinates. Do NOT ask questions. Do NOT use 'question' action.
NO conversational text."""
                response_text = analyze_image_locally(screenshot_path, local_prompt, model="llava:7b")
                self.logger.info(f"Raw Local Vision Response: {response_text}")
                if not response_text or response_text.startswith("Error"):
                    return Action(type=ActionType.FAILED, reason=f"All vision backends failed: {response_text}")

            # Smart JSON cleaning - Multi-phase
            clean_text = response_text.strip()
            
            # Phase 1: Remove markdown code blocks if present
            if "```json" in clean_text:
                clean_text = clean_text.split("```json")[-1].split("```")[0]
            elif "```" in clean_text:
                clean_text = clean_text.split("```")[-1].split("```")[0]
            
            # Phase 2: Find the FIRST { and the LAST }
            start_idx = clean_text.find("{")
            end_idx = clean_text.rfind("}")
            
            if start_idx != -1 and end_idx != -1:
                clean_text = clean_text[start_idx:end_idx+1]
                try:
                    data = json.loads(clean_text)
                    # Support both single object and list of objects
                    if isinstance(data, list) and len(data) > 0:
                        data = data[0]
                    elif isinstance(data, dict) and "actions" in data and isinstance(data["actions"], list) and len(data["actions"]) > 0:
                        data = data["actions"][0]
                except json.JSONDecodeError as e:
                    self.logger.error(f"JSON Decode Error after cleaning: {e}. Raw: {response_text}")
                    # Emergency fallback: try to extract fields with regex
                    import re
                    # Look for action, x, y, reason
                    action_match = re.search(r'"action":\s*["\']([^"\']+)["\']', response_text)
                    x_match = re.search(r'"x":\s*(\d+)', response_text)
                    y_match = re.search(r'"y":\s*(\d+)', response_text)
                    reason_match = re.search(r'"reason":\s*["\']([^"\']+)["\']', response_text)
                    
                    if action_match:
                        data = {
                            "action": action_match.group(1),
                            "x": int(x_match.group(1)) if x_match else 0,
                            "y": int(y_match.group(1)) if y_match else 0,
                            "reason": reason_match.group(1) if reason_match else "Extracted via loose regex"
                        }
                    else:
                        return Action(type=ActionType.FAILED, reason=f"JSON parsing failed: {e}")
            else:
                self.logger.error(f"No JSON block found in response: {response_text}")
                return Action(type=ActionType.FAILED, reason="No JSON block found")

            self.last_thought_text = data.get("reason", "")
            self.last_thought_time = time.time()
            
            # Extract action type string before using it
            action_type_str = data.get("action", "failed").lower()
            
            # Specific handling for local model's tendency to ask questions
            if action_type_str == "question":
                self.logger.warning(f"Local model asked a question: {data.get('reason')}. Retrying with more specific prompt...")
                # We can't easily recurse here without a retry counter, so we let the main loop handle it as a failure/retry
                action_type = ActionType.FAILED
            else:
                try:
                    action_type = ActionType(action_type_str)
                except ValueError:
                    self.logger.warning(f"Invalid ActionType '{action_type_str}' from local model. Defaulting to IDLE.")
                    action_type = ActionType.IDLE
                
            action = Action(type=action_type, x=data.get("x"), y=data.get("y"), text=data.get("text"), key=data.get("key"), keys=data.get("keys"), reason=data.get("reason", ""))
            
            # Save successful actions to vault (simplified for now)
            if action.type == ActionType.DONE:
                # In a real scenario, we'd save the whole sequence
                self.experience_vault.save_experience(goal, [{"action": action.type.value, "reason": action.reason}])
                
            return action
        except Exception as e:
            self.logger.error(f"Analysis error: {e}")
            return Action(type=ActionType.FAILED, reason=f"Analysis error: {e}")

    async def _execute_action(self, action: Action) -> bool:
        if action.x and action.y: self.last_action_visual = {"type": action.type.value, "x": action.x, "y": action.y, "timestamp": time.time()}
        try:
            if action.type == ActionType.CLICK: pyautogui.click(action.x, action.y)
            elif action.type == ActionType.DOUBLE_CLICK: pyautogui.doubleClick(action.x, action.y)
            elif action.type == ActionType.TYPE and action.text:
                import pyperclip
                pyperclip.copy(action.text)
                pyautogui.hotkey('ctrl', 'v')
            elif action.type == ActionType.PRESS_KEY: pyautogui.press(action.key)
            elif action.type == ActionType.HOTKEY: pyautogui.hotkey(*action.keys)
            elif action.type == ActionType.WAIT: await asyncio.sleep(1)
            elif action.type == ActionType.IDLE: await asyncio.sleep(2)
            return True
        except: return False

    def _start_aura(self, color: str = "#00FFFF"):
        try:
            self._stop_aura()
            script_path = Path(__file__).parent / "agi_aura.py"
            self.aura_process = subprocess.Popen([sys.executable, str(script_path), color], stdin=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        except: pass

    def _set_aura_color(self, color: str):
        if self.aura_process and self.aura_process.stdin:
            try:
                self.aura_process.stdin.write(f"color:{color}\n")
                self.aura_process.stdin.flush()
            except: pass

    def _stop_aura(self):
        if self.aura_process:
            try:
                self.aura_process.terminate()
                self.aura_process = None
            except: pass

    def get_live_frame_jpeg(self) -> bytes:
        try:
            img = pyautogui.screenshot()
            draw = ImageDraw.Draw(img)
            now = time.time()
            if self.last_action_visual and (now - self.last_action_visual["timestamp"] < 2.0):
                x, y = self.last_action_visual["x"], self.last_action_visual["y"]
                draw.rectangle([x-30, y-30, x+30, y+30], outline="#00FFFF", width=5)
            buf = io.BytesIO()
            img.resize((480, 270)).save(buf, format='JPEG', quality=70)
            return buf.getvalue()
        except: return b""

def create_fsd_routes(app, controller_instance=None):
    from fastapi import APIRouter
    from fastapi.responses import StreamingResponse
    from pydantic import BaseModel
    router = APIRouter(prefix="/fsd", tags=["FSD Controller"])
    controller = controller_instance if controller_instance else FSDController()
    class GoalRequest(BaseModel): goal: str
    @router.post("/execute")
    async def execute_goal(request: GoalRequest):
        result = await controller.execute_goal(request.goal)
        return {"status": "completed" if result.success else "failed", "result": result.message}
    @router.get("/stream")
    async def stream_screen():
        async def frame_generator():
            while True:
                frame = await asyncio.get_event_loop().run_in_executor(None, controller.get_live_frame_jpeg)
                if frame: yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                await asyncio.sleep(0.2)
        return StreamingResponse(frame_generator(), media_type="multipart/x-mixed-replace; boundary=frame")
    app.include_router(router)
    return router

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(FSDController().execute_goal("테스트"))
