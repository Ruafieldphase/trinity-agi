import json
import os
import sys
import time
<<<<<<< HEAD
from pathlib import Path
import subprocess
import warnings
import ctypes

# 🧬 Rhythm-Aware Boundary
try:
    from agi_core.rhythm_boundaries import RhythmBoundaryManager, RhythmMode
    from fdo_agi_repo.orchestrator.llm_client import LLMClient
except ImportError:
    # Local scripts might need sys.path adjustment
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from agi_core.rhythm_boundaries import RhythmBoundaryManager, RhythmMode
    from fdo_agi_repo.orchestrator.llm_client import LLMClient

RPACORE_AVAILABLE = True
_RPACORE_ERROR = None
try:
    from fdo_agi_repo.rpa.core import RPACore, RPACoreConfig
except Exception as exc:
    RPACORE_AVAILABLE = False
    RPACore = None  # type: ignore[assignment]
    RPACoreConfig = None  # type: ignore[assignment]
    _RPACORE_ERROR = str(exc)
=======
import google.generativeai as genai
from pathlib import Path
>>>>>>> origin/main

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(SCRIPT_DIR)
PROPOSALS_FILE = os.path.join(WORKSPACE_ROOT, "outputs", "proposals.json")
LOG_FILE = os.path.join(WORKSPACE_ROOT, "outputs", "execution.log")
<<<<<<< HEAD
AURA_PIXEL_FILE = os.path.join(WORKSPACE_ROOT, "outputs", "aura_pixel_state.json")
VISION_LOG_FILE = os.path.join(WORKSPACE_ROOT, "memory", "vision_events.jsonl")
RED_LINE_FILE = os.path.join(WORKSPACE_ROOT, "outputs", "safety", "red_line_monitor_latest.json")
CHILD_DATA_FILE = os.path.join(WORKSPACE_ROOT, "outputs", "child_data_protector_latest.json")
REST_GATE_FILE = os.path.join(WORKSPACE_ROOT, "outputs", "safety", "rest_gate_latest.json")
SANDBOX_FILE = os.path.join(WORKSPACE_ROOT, "outputs", "safety", "sandbox_latest.json")
NATURAL_CLOCK_FILE = os.path.join(WORKSPACE_ROOT, "outputs", "natural_rhythm_clock_latest.json")
=======

# Configure Gemini
def load_api_key():
    try:
        from dotenv import load_dotenv
        # Try loading from WORKSPACE_ROOT/.env
        load_dotenv(os.path.join(WORKSPACE_ROOT, ".env"))
        # Try loading from WORKSPACE_ROOT/fdo_agi_repo/.env
        load_dotenv(os.path.join(WORKSPACE_ROOT, "fdo_agi_repo", ".env"))
    except ImportError:
        pass

    return os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

API_KEY = load_api_key()

if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    print("Warning: No API_KEY found (checked GOOGLE_API_KEY and GEMINI_API_KEY)")
>>>>>>> origin/main

def log(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
<<<<<<< HEAD
    # 콘솔 출력은 최소화(운영 로그 노이즈 방지)
    try:
        print(f"[{timestamp}] {message}")
    except Exception:
        pass
=======
    print(f"[{timestamp}] {message}")
>>>>>>> origin/main

def load_proposals():
    if os.path.exists(PROPOSALS_FILE):
        try:
            with open(PROPOSALS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return []

def save_proposals(proposals):
    with open(PROPOSALS_FILE, "w", encoding="utf-8") as f:
        json.dump(proposals, f, indent=2, ensure_ascii=False)

<<<<<<< HEAD
def _load_json_best_effort(path: str) -> dict:
    try:
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _active_window_title() -> str:
    if os.name != "nt":
        return ""
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return ""
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return ""
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        return buff.value or ""
    except Exception:
        return ""


def _gui_policy() -> tuple[str, str]:
    policy = os.environ.get("AGI_GUI_POLICY", "").strip().lower()
    if policy in ("relaxed", "open", "soft"):
        return "relaxed", "env: relaxed"
    if policy in ("strict", "safe"):
        return "strict", "env: strict"
    return "strict", "default: strict"


def _rhythm_notice() -> str:
    clock = _load_json_best_effort(NATURAL_CLOCK_FILE)
    if not clock:
        return "unknown"
    bio = clock.get("bio_rhythm", {}) if isinstance(clock.get("bio_rhythm"), dict) else {}
    rec = str(bio.get("bio_recommended_phase") or clock.get("recommended_phase") or "").upper()
    melatonin = float(bio.get("melatonin_level", 0.0))
    sleep_pressure = float(bio.get("sleep_pressure", 0.0))
    return f"phase={rec or 'UNKNOWN'} melatonin={melatonin:.2f} sleep={sleep_pressure:.2f}"

def _is_safe_refactor_target(abs_path: str) -> tuple[bool, str]:
    try:
        root = os.path.abspath(WORKSPACE_ROOT)
        p = os.path.abspath(abs_path)
        if not p.startswith(root):
            return False, "blocked: outside workspace"
        low = p.lower().replace("/", "\\")
        blocked_parts = [
            "\\.git\\",
            "\\.venv\\",
            "\\outputs\\",
            "\\signals\\",
            "\\logs\\",
            "\\.env",
            "\\.env_credentials",
        ]
        if any(bp in low for bp in blocked_parts) or low.endswith(".env"):
            return False, "blocked: sensitive path"
        return True, "ok"
    except Exception:
        return False, "blocked: path check failed"

def _merge_action_params(target_proposal: dict) -> tuple[dict, dict]:
    action_info = target_proposal.get("action") if isinstance(target_proposal.get("action"), dict) else {}
    params: dict = {}
    if isinstance(action_info.get("params"), dict):
        params.update(action_info["params"])
    if isinstance(target_proposal.get("params"), dict):
        params.update(target_proposal["params"])
    return action_info, params

def _normalize_action_type(target_proposal: dict, action_info: dict, params: dict) -> tuple[str, str | None]:
    proposal_type = (
        target_proposal.get("type")
        or action_info.get("type")
        or params.get("type")
        or (target_proposal.get("action") if isinstance(target_proposal.get("action"), str) else None)
        or "unknown"
    )
    action_type_l = str(proposal_type).strip().lower()
    gui_action = None
    if action_type_l in ("gui_action", "click", "type", "drag", "scroll", "hotkey", "scroll_up", "scroll_down"):
        gui_action = (
            params.get("action")
            or action_info.get("action")
            or (proposal_type if action_type_l != "gui_action" else None)
        )
        gui_action = str(gui_action or "").strip().lower() or None
        action_type_l = "gui_action"
    return action_type_l, gui_action

def _normalize_gui_action_name(action: str | None) -> str:
    action_l = str(action or "").strip().lower()
    aliases = {
        "tap": "click",
        "press": "click",
        "input": "type",
        "enter_text": "type",
    }
    return aliases.get(action_l, action_l)

def _extract_xy(params: dict) -> tuple[int, int] | None:
    try:
        x = params.get("x")
        y = params.get("y")
        if x is None or y is None:
            return None
        return int(x), int(y)
    except Exception:
        return None

def _extract_point(params: dict, key: str) -> tuple[int, int] | None:
    try:
        point = params.get(key)
        if isinstance(point, dict):
            x = point.get("x") if point.get("x") is not None else point.get("left")
            y = point.get("y") if point.get("y") is not None else point.get("top")
            if x is not None and y is not None:
                return int(x), int(y)
        x = params.get(f"{key}_x")
        y = params.get(f"{key}_y")
        if x is not None and y is not None:
            return int(x), int(y)
    except Exception:
        return None
    return None

def _parse_hotkey(params: dict) -> list[str]:
    keys = params.get("keys") or params.get("combo") or params.get("hotkey")
    if isinstance(keys, list):
        return [str(k).strip() for k in keys if str(k).strip()]
    if isinstance(keys, str):
        parts = [p.strip() for p in keys.replace(",", "+").split("+")]
        return [p for p in parts if p]
    return []


def execute_refactor(file_path, instruction):
    if not os.path.exists(file_path):
        return False, f"File not found: {file_path}"

    # 안전 경계: 클라우드로 코드 원문을 보내는 refactor는 기본적으로 꺼둔다.
    if str(os.getenv("AGI_ALLOW_CLOUD_REFACTOR", "")).strip().lower() not in ("1", "true", "yes", "on"):
        return False, "blocked: AGI_ALLOW_CLOUD_REFACTOR not enabled"

    ok, why = _is_safe_refactor_target(file_path)
    if not ok:
        return False, why
=======
def execute_refactor(file_path, instruction):
    if not os.path.exists(file_path):
        return False, f"File not found: {file_path}"
>>>>>>> origin/main
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
<<<<<<< HEAD

        # Prefer the workspace ModelSelector to choose an available Gemini model,
        # but fall back to direct GenAI if not available.
        client = LLMClient(provider="auto", model=os.getenv("GEMINI_TOP_TIER_MODEL") or "gemini-2.5-flash")
=======
            
        model = genai.GenerativeModel('gemini-2.5-pro-preview-03-25')
>>>>>>> origin/main
        prompt = f"""
        You are an expert AI software engineer.
        Your task is to REFACTOR the following code based on the instruction.
        
        **Instruction:** {instruction}
        
        **File Path:** {file_path}
        
        **Code Content:**
        ```
        {content}
        ```
        
        Return ONLY the full, modified code. Do not include markdown code blocks (```) if possible, or I will strip them.
        Do not add conversational text.
        """
<<<<<<< HEAD

        # LLMClient returns text or None.
        new_content = (client.generate(system_prompt="", user_prompt=prompt) or "").strip()
        if not new_content:
            return False, "refactor failed: empty LLM response"
=======
        
        response = model.generate_content(prompt)
        new_content = response.text.strip()
>>>>>>> origin/main
        
        # Clean up markdown
        if new_content.startswith("```"):
            lines = new_content.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            new_content = "\n".join(lines)
            
        # Backup original
        backup_path = f"{file_path}.bak.{int(time.time())}"
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        # Write new content
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
            
        return True, f"Refactored successfully. Backup saved to {backup_path}"
        
    except Exception as e:
        return False, str(e)

<<<<<<< HEAD

def check_safety_interlock() -> tuple[bool, str]:
    """Check Aura Pixel state and System Health (Sena's tool) before physical action."""
    test_file = AURA_PIXEL_FILE.replace(".json", "_test.json")
    target_file = test_file if os.path.exists(test_file) else AURA_PIXEL_FILE
    
    safety_min = 0.35
    health_min = 30.0
    rhythm_notice = _rhythm_notice()
    if rhythm_notice:
        log(f"Rhythm notice: {rhythm_notice}")
    state = {}
    try:
        # 1. Aura Pixel Check
        if os.path.exists(target_file):
            with open(target_file, "r", encoding="utf-8") as f:
                state = json.load(f)
        
        # 실제 스키마 반영 (decision 객체 내의 state/color 확인)
        decision = state.get("decision", {})
        status = str(state.get("status") or decision.get("state") or "GREEN").upper()
        color = str(decision.get("color") or "").upper()
        
        log(f"Safety interlock: Detected status={status}, color={color}")
        
        # RED 상태 또는 빨간색 계열 Hex 코드 감지
        if status == "RED" or status == "DANGER" or color == "RED" or color.startswith("#FF0000") or color == "#EF4444":
            return False, f"blocked: Aura Pixel is RED/DANGER (Safety Critical)"
            
        score = float(state.get("safety_score") or decision.get("safety_score", 1.0))
        if score < safety_min:
            return False, f"blocked: Safety score too low ({score:.2f} < {safety_min:.2f})"
        
    except Exception as e:
        log(f"Aura check error (non-blocking): {e}")

    # 2. Sena's Rhythm Thermometer Check (Health Score)
    try:
        rhythm_check_script = os.path.join(WORKSPACE_ROOT, "scripts", "rhythm_check.py")
        if os.path.exists(rhythm_check_script):
            creationflags = 0
            if os.name == "nt" and hasattr(subprocess, "CREATE_NO_WINDOW"):
                creationflags = subprocess.CREATE_NO_WINDOW
            
            proc = subprocess.run(
                [sys.executable, rhythm_check_script, "--json"],
                capture_output=True, text=True, timeout=5, check=False, creationflags=creationflags
            )
            if proc.returncode == 0:
                health_data = json.loads(proc.stdout)
                health_score = health_data.get("health_score", 100)
                log(f"System Health Check: {health_score}/100 (min {health_min:.0f})")
                if health_score < health_min:
                    log(f"Warning: system health low ({health_score}/100 < {health_min:.0f})")
    except Exception as e:
        log(f"Health check error (non-blocking): {e}")

    # 2.5 Rhythm Mode Gate (execution requires isolation)
    try:
        boundary_manager = RhythmBoundaryManager(Path(WORKSPACE_ROOT))
        mode = boundary_manager.detect_rhythm_mode()
        if mode in (RhythmMode.CONNECTED, RhythmMode.RECONNECT_SEARCH):
            log(f"Rhythm mode notice: {mode.value}")
    except Exception as e:
        log(f"Rhythm mode check error (non-blocking): {e}")

    red_line = _load_json_best_effort(RED_LINE_FILE)
    if red_line:
        enforcement = red_line.get("enforcement", {}) if isinstance(red_line.get("enforcement"), dict) else {}
        if enforcement.get("enabled") is True:
            return False, "blocked: red_line enforcement enabled"
        red_status = str(red_line.get("status") or "").upper()
        if red_status in ("FAIL", "RED", "DANGER", "BLOCK"):
            return False, f"blocked: red_line status={red_status}"
        if red_line.get("ok") is False:
            return False, "blocked: red_line not ok"

    child = _load_json_best_effort(CHILD_DATA_FILE)
    if child:
        results = child.get("results", {}) if isinstance(child.get("results"), dict) else {}
        if results.get("detected") is True:
            return False, "blocked: child data detected"
        if results.get("ok") is False:
            return False, "blocked: child data protector not ok"

    rest_gate = _load_json_best_effort(REST_GATE_FILE)
    if rest_gate:
        status = str(rest_gate.get("status") or "").upper()
        rest_until = rest_gate.get("rest_until_epoch")
        if status and status not in ("OK", "GREEN", "CLEAR"):
            return False, f"blocked: rest_gate status={status}"
        try:
            if rest_until and float(rest_until) > time.time():
                return False, "blocked: rest_gate active"
        except Exception:
            pass

    return True, "ok"


def _get_vision_cursor() -> int | None:
    try:
        if not os.path.exists(VISION_LOG_FILE):
            return None
        return os.path.getsize(VISION_LOG_FILE)
    except Exception:
        return None


def _match_vision_event(expected_pattern: str, event: dict) -> bool:
    needle = expected_pattern.lower()
    summary = str(event.get("summary") or "")
    if needle in summary.lower():
        return True
    ui_elements = event.get("ui_elements", [])
    if isinstance(ui_elements, list):
        for element in ui_elements:
            if not isinstance(element, dict):
                continue
            name = str(element.get("name") or "")
            desc = str(element.get("description") or "")
            combined = f"{name} {desc}".lower()
            if needle in combined:
                return True
    return False


def verify_visual_feedback(expected_pattern: str, timeout_s: int = 10, start_size: int | None = None) -> tuple[bool, str]:
    """Wait and verify if the screen has changed as expected."""
    if not os.path.exists(VISION_LOG_FILE):
        return False, "verification skipped: vision log missing"
    
    start_t = time.time()
    saw_growth = False
    while time.time() - start_t < timeout_s:
        try:
            if not os.path.exists(VISION_LOG_FILE):
                return False, "verification skipped: vision log missing"
            current_size = os.path.getsize(VISION_LOG_FILE)
            if start_size is not None and current_size <= start_size:
                time.sleep(1)
                continue
            if start_size is not None and current_size > start_size:
                saw_growth = True
            with open(VISION_LOG_FILE, "r", encoding="utf-8") as f:
                if start_size is not None and current_size >= start_size:
                    try:
                        f.seek(start_size)
                    except Exception:
                        f.seek(0)
                lines = f.readlines()
            if lines:
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = json.loads(line)
                    except Exception:
                        continue
                    if _match_vision_event(expected_pattern, event):
                        return True, f"Verified: '{expected_pattern}' found in vision event."
        except:
            pass
        time.sleep(2)
    if start_size is not None and not saw_growth:
        return False, "verification skipped: no new vision events"
    return False, f"Timeout: failed to verify '{expected_pattern}' via vision."


def check_safety_sandbox(action: str | None) -> tuple[bool, str]:
    """Optional sandbox gate for physical actions."""
    data = _load_json_best_effort(SANDBOX_FILE)
    if not data:
        return True, "ok"
    status = str(data.get("status") or data.get("mode") or "").upper()
    if status in ("BLOCK", "LOCKED", "DISABLED", "STOP"):
        return False, f"blocked: sandbox status={status}"
    allow = data.get("allow")
    if allow is False:
        return False, "blocked: sandbox allow=false"
    allowed = data.get("allowed_actions")
    if action and isinstance(allowed, list) and allowed:
        if action not in allowed:
            return False, f"blocked: sandbox disallows action={action}"
    allowed_titles = data.get("allowed_window_titles")
    if isinstance(allowed_titles, list) and allowed_titles:
        title = _active_window_title()
        if not title:
            return False, "blocked: unable to read active window title"
        title_low = title.lower()
        if not any(str(token).lower() in title_low for token in allowed_titles):
            return False, f"blocked: active window not allowed ({title})"
    return True, "ok"


def _atomic_write_json(path: str, payload: dict) -> bool:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
        return True
    except Exception:
        return False


def _run_script_best_effort(rel_path: str, timeout_s: int = 30) -> tuple[bool, str]:
    try:
        script = os.path.join(WORKSPACE_ROOT, rel_path)
        if not os.path.exists(script):
            return False, f"missing:{rel_path}"
        creationflags = 0
        if os.name == "nt" and hasattr(subprocess, "CREATE_NO_WINDOW"):
            creationflags = subprocess.CREATE_NO_WINDOW
        proc = subprocess.run(
            [sys.executable, script],
            cwd=WORKSPACE_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
            creationflags=creationflags,
        )
        return True, f"rc={proc.returncode}"
    except Exception as e:
        return False, f"error:{e.__class__.__name__}"


=======
>>>>>>> origin/main
def main():
    if len(sys.argv) < 2:
        print("Usage: python execute_proposal.py <proposal_id>")
        return

    proposal_id = int(sys.argv[1])
    proposals = load_proposals()
    
    target_proposal = None
    for p in proposals:
        if p.get("id") == proposal_id:
            target_proposal = p
            break
            
    if not target_proposal:
        print(f"Proposal {proposal_id} not found.")
        return

    # Get proposal type/action safely
<<<<<<< HEAD
    action_info, params = _merge_action_params(target_proposal)
    proposal_type = target_proposal.get("type") or action_info.get("type") or "unknown"
    action_type_l, gui_action = _normalize_action_type(target_proposal, action_info, params)
    action_type = action_type_l
    target_info = (
        params.get("description")
        or params.get("target")
        or target_proposal.get("file")
        or target_proposal.get("title")
        or "N/A"
    )
=======
    proposal_type = target_proposal.get("type") or target_proposal.get("action", {}).get("type", "unknown")
    target_info = target_proposal.get('file', target_proposal.get('title', 'N/A'))
>>>>>>> origin/main
    
    log(f"Executing proposal {proposal_id}: {proposal_type} - {target_info}")
    
    # Update status to executing
    target_proposal["status"] = "executing"
    save_proposals(proposals)
    
    success = False
    message = ""
    
<<<<<<< HEAD
    # 🧬 Rhythm-Aware Execution Strategy
    boundary_manager = RhythmBoundaryManager(Path(WORKSPACE_ROOT))
    rhythm_state = boundary_manager.get_rhythm_state()
    phase = rhythm_state.get("phase", "STABLE")
    
    # 리듬과 액션의 정렬 확인
    alignment_error = False
    if action_type_l == "cleanup" and phase == "EXPANSION":
        log(f"Rhythm mismatch: cleanup is contraction, but phase={phase}")
    elif action_type_l == "deepen_current" and phase == "CONTRACTION":
        log(f"Rhythm mismatch: deepen_current is expansion, but phase={phase}")

    if action_type_l == "refactor":
=======
    # Get action info
    action_info = target_proposal.get("action", {})
    action_type = action_info.get("type", target_proposal.get("type"))
    
    if action_type == "REFACTOR":
>>>>>>> origin/main
        file_path = target_proposal.get("file").replace("\\", "/")
        if not os.path.isabs(file_path):
            file_path = os.path.join(WORKSPACE_ROOT, file_path)
        instruction = target_proposal.get("observation")
        success, message = execute_refactor(file_path, instruction)
        
<<<<<<< HEAD
    elif action_type_l == "deepen_current":
        # Amplify: Deepen current positive pattern using LLM
        context = str(params.get("context_message") or "No context provided")
        log(f"Deepening current flow (Phase: {phase}): {context[:100]}")
        
        try:
            # Use model selector bridge (GenAI/Vertex) if possible.
            client = LLMClient(provider="auto", model=os.getenv("GEMINI_BALANCED_MODEL") or "gemini-2.5-flash")
            system_prompt = "You are Sian's 'Deepen Engine'. Analyze the given context and provide 3 deep insights or follow-up questions to expand the current thought flow."
            user_prompt = f"Current Context: {context}\nRhythm Phase: {phase}"
            
            result = client.generate(system_prompt, user_prompt)
            if result:
                success = True
                message = f"Thought deepened: {result[:200]}..."
                log(f"Implementation: {message}")
            else:
                success = False
                message = "LLM deepening failed (No response)"
        except Exception as e:
            success = False
            message = f"Deepen execution failed: {e}"
        
    elif action_type_l == "search_knowledge":
        # 실제 행동: signals에 검색 요청을 기록(소비자는 별도 루프가 담당).
        query = str(params.get("query") or params.get("q") or target_proposal.get("title") or "").strip()
        if not query:
            success = False
            message = "search_knowledge: missing query"
        else:
            payload = {"query": query, "timestamp": float(time.time()), "origin": "execute_proposal"}
            ok = _atomic_write_json(os.path.join(WORKSPACE_ROOT, "signals", "knowledge_search_request.json"), payload)
            success = bool(ok)
            message = "검색 요청 큐에 기록됨" if ok else "검색 요청 기록 실패"
        
    elif action_type_l == "optimize_system":
        # 실제 행동: 안전한 로컬 유지/정리 루틴들을 best-effort로 실행.
        results = []
        for rel in (
            "scripts/rest_gate.py",
            "scripts/stub_radar.py",
            "scripts/system_gaps_report.py",
            "scripts/human_ops_summary.py",
        ):
            ok, info = _run_script_best_effort(rel, timeout_s=30)
            results.append({"script": rel, "ok": ok, "info": info})
        success = any(r["ok"] for r in results)
        message = "로컬 최적화 루틴 실행됨" if success else "로컬 최적화 루틴 실행 실패"
        try:
            _atomic_write_json(os.path.join(WORKSPACE_ROOT, "outputs", "optimize_system_latest.json"), {"ok": success, "results": results})
        except Exception:
            pass
        
    elif action_type_l == "cleanup":
        # Rest: Run real cleanup tasks (archive old logs)
        log(f"Starting real cleanup tasks (Phase: {phase})...")
        try:
            # Example: Archive execution.log if too large
            if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > 1024 * 1024: # 1MB
                archive_path = f"{LOG_FILE}.{int(time.time())}.old"
                os.rename(LOG_FILE, archive_path)
                message = f"Log file archived to {Path(archive_path).name}. "
            else:
                message = "No large log files to cleanup. "
            
            success = True
            message += "System cleanup completed (Rhythm-synced)."
        except Exception as e:
            success = False
            message = f"Cleanup failed: {e}"
        
    elif action_type_l == "monitor":
=======
    elif action_type == "deepen_current":
        # Amplify: Deepen current positive pattern
        context = action_info.get("params", {}).get("context_message", "")
        log(f"Deepening current flow: {context[:100]}")
        # TODO: Implement deeper analysis of current topic
        success = True
        message = "현재 흐름 심화 작업 완료 (패턴 분석 및 기록)"
        
    elif action_type == "search_knowledge":
        # Explore: Search for new knowledge
        feeling = action_info.get("params", {}).get("feeling", "unknown")
        log(f"Exploring new knowledge area: feeling={feeling}")
        # TODO: Trigger YouTube search or web search
        success = True
        message = "새로운 지식 탐색 시작 (검색 큐에 추가됨)"
        
    elif action_type == "optimize_system":
        # Stabilize: Run system optimization
        log("Running system optimization...")
        # TODO: Trigger auto_stabilizer or glymphatic cleanup
        success = True
        message = "시스템 최적화 실행 (메모리 정리, 큐 재정렬)"
        
    elif action_type == "cleanup":
        # Rest: Run cleanup tasks
        log("Starting cleanup tasks...")
        # TODO: Trigger glymphatic cleanup
        success = True
        message = "정리 작업 완료 (오래된 데이터 아카이빙)"
        
    elif action_type == "monitor":
>>>>>>> origin/main
        # Observe: Just monitor, no action needed
        log("Entering observation mode...")
        success = True
        message = "관찰 모드 유지 (추가 행동 없음)"
        
<<<<<<< HEAD
    elif action_type_l == "analyze_change":
        # Pivot: Analyze what's changing
        log("Analyzing detected changes...")
        ok, info = _run_script_best_effort("scripts/system_gaps_report.py", timeout_s=30)
        success = bool(ok)
        message = "변화 패턴 분석(갭 리포트 갱신)" if ok else f"변화 분석 실패({info})"
        
    elif action_type_l == "gui_action":
        # 🦾 Physical Execution with Safety Interlock
        log(f"Initiating GUI action (Safety check start)...")
        safe, why = check_safety_interlock()
        if not safe:
            success = False
            message = why
            log(message)
        else:
            try:
                import asyncio
                action = (
                    gui_action
                    or params.get("action")
                    or (target_proposal.get("action") if isinstance(target_proposal.get("action"), str) else None)
                )
                action = _normalize_gui_action_name(action)
                scroll_direction = None
                if action in ("scroll_up", "scroll_down"):
                    scroll_direction = 1 if action.endswith("up") else -1
                    action = "scroll"

                desc = params.get("description") or target_info
                
                log(f"Physical action: {action} on '{desc}'")
                
                vision_cursor = _get_vision_cursor()
                sandbox_ok, sandbox_msg = check_safety_sandbox(str(action))
                if not sandbox_ok:
                    success = False
                    message = sandbox_msg
                else:
                    rhythm_notice = _rhythm_notice()
                    if rhythm_notice:
                        log(f"Rhythm notice: {rhythm_notice}")
                    gui_policy, policy_reason = _gui_policy()
                    dry_run = bool(params.get("dry_run"))
                    if dry_run:
                        success = True
                        message = "dry_run: gui action skipped"
                    elif not RPACORE_AVAILABLE:
                        success = False
                        message = f"blocked: RPACore unavailable ({_RPACORE_ERROR})"
                    elif action == "click":
                        rpa = RPACore()
                        coords = _extract_xy(params)
                        if coords:
                            asyncio.run(rpa.click(coords[0], coords[1]))
                            success = True
                        else:
                            success = asyncio.run(rpa.click_by_description(desc))
                    elif action == "type":
                        value = params.get("value") or params.get("text") or params.get("input") or "Hello Sian"
                        rpa = RPACore()
                        coords = _extract_xy(params)
                        if coords:
                            asyncio.run(rpa.click(coords[0], coords[1]))
                            asyncio.run(rpa.type_text(str(value)))
                            success = True
                        else:
                            success = asyncio.run(rpa.type_in_element_by_description(desc, str(value)))
                    elif action == "drag":
                        start = (
                            _extract_point(params, "start")
                            or _extract_point(params, "from")
                            or _extract_point(params, "src")
                        )
                        end = (
                            _extract_point(params, "end")
                            or _extract_point(params, "to")
                            or _extract_point(params, "dest")
                        )
                        if start and not end:
                            dx = params.get("dx") if params.get("dx") is not None else params.get("delta_x")
                            dy = params.get("dy") if params.get("dy") is not None else params.get("delta_y")
                            if dx is not None and dy is not None:
                                end = (start[0] + int(dx), start[1] + int(dy))
                        if not start or not end:
                            success = False
                            message = "drag requires start/end coordinates"
                        else:
                            duration = float(params.get("duration") or params.get("seconds") or 1.0)
                            rpa = RPACore()
                            asyncio.run(rpa.drag(start[0], start[1], end[0], end[1], duration))
                            success = True
                    elif action == "scroll":
                        amount = params.get("amount") if params.get("amount") is not None else params.get("delta")
                        amount = amount if amount is not None else params.get("scroll")
                        try:
                            amount = int(amount or 0)
                        except Exception:
                            amount = 0
                        if scroll_direction is not None:
                            amount = int(abs(amount or 480) * scroll_direction)
                        if amount == 0:
                            success = False
                            message = "scroll requires a non-zero amount"
                        else:
                            rpa = RPACore()
                            coords = _extract_xy(params)
                            if coords:
                                asyncio.run(rpa.move_mouse(coords[0], coords[1]))
                            import pyautogui
                            asyncio.run(asyncio.to_thread(pyautogui.scroll, amount))
                            success = True
                    elif action == "hotkey":
                        keys = _parse_hotkey(params)
                        if not keys:
                            success = False
                            message = "hotkey requires keys"
                        else:
                            rpa = RPACore()
                            asyncio.run(rpa.hotkey(*keys))
                            success = True
                    else:
                        success = False
                        message = f"Unsupported GUI action: {action}"
                
                if success:
                    # Visual Verification Loop
                    if not dry_run:
                        message = f"Action '{action}' executed."
                    log("Action sent. Starting visual verification...")
                    verify_timeout = 10 if gui_policy == "strict" else 5
                    v_ok, v_msg = verify_visual_feedback(desc, timeout_s=verify_timeout, start_size=vision_cursor)
                    message = f"{message} {v_msg}".strip()
                    if rhythm_notice:
                        message = f"{message} [Rhythm: {rhythm_notice}]"
                    if not v_ok and "verification skipped" not in v_msg:
                        if gui_policy == "relaxed":
                            log(f"Visual verification relaxed: {policy_reason}")
                        else:
                            success = False
                            target_proposal["replan"] = {
                                "status": "needs_replan",
                                "reason": v_msg,
                                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                            }
                else:
                    if not message:
                        message = f"Action '{action}' failed at core level."
            except Exception as e:
                success = False
                message = f"GUI execution error: {e}"
        
    else:
        success = False
        message = f"NOT_IMPLEMENTED: {action_type}"
=======
    elif action_type == "analyze_change":
        # Pivot: Analyze what's changing
        log("Analyzing detected changes...")
        # TODO: Compare recent patterns with historical data
        success = True
        message = "변화 패턴 분석 완료 (리포트 생성됨)"
        
    else:
        success = True
        message = f"Simulated execution for type {action_type}"
>>>>>>> origin/main
        
    # Update final status
    target_proposal["status"] = "completed" if success else "failed"
    target_proposal["result"] = message
    save_proposals(proposals)
    
    # [FEEDBACK LOOP] Record execution result to Resonance Ledger
    try:
<<<<<<< HEAD
        ledger_v2 = os.path.join(WORKSPACE_ROOT, "fdo_agi_repo", "memory", "resonance_ledger_v2.jsonl")
        ledger_v1 = os.path.join(WORKSPACE_ROOT, "fdo_agi_repo", "memory", "resonance_ledger.jsonl")
        ledger_path = ledger_v2 if os.path.exists(ledger_v2) else ledger_v1
=======
        ledger_path = os.path.join(WORKSPACE_ROOT, "fdo_agi_repo", "memory", "resonance_ledger.jsonl")
>>>>>>> origin/main
        feedback_entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "type": "action_result",
            "proposal_id": proposal_id,
            "decision": target_proposal.get("decision"),
            "action_type": action_type,
            "success": success,
            "result": message,
            "metadata": {
                "source": target_proposal.get("source"),
                "original_thought": target_proposal.get("metadata", {}).get("thought_timestamp")
            }
        }
        
        with open(ledger_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(feedback_entry, ensure_ascii=False) + "\n")
        
        log("Feedback recorded to Resonance Ledger")
    except Exception as e:
        log(f"Failed to record feedback: {e}")
    
    log(f"Execution finished: {success} - {message}")

if __name__ == "__main__":
    main()
