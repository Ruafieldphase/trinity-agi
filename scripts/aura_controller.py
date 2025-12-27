
"""
Aura Controller (Windows Body)
==============================
Monitors the 'Brain' (Linux) thought stream via the synced JSON file on Windows.
Controls the 'Visual' (agi_aura.py) based on the Brain's state.

This script runs on Windows.
"""
import sys
import os
import json
import time
import subprocess
import threading
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


def _hide_console_window() -> None:
    if os.name != "nt":
        return
    try:
        import ctypes

        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)
            try:
                ctypes.windll.kernel32.FreeConsole()
            except Exception:
                pass
    except Exception:
        pass


_hide_console_window()

# Configuration
WORKSPACE_ROOT = Path(__file__).parent.parent
OUTPUTS_DIR = WORKSPACE_ROOT / "outputs"
LOGS_DIR = WORKSPACE_ROOT / "logs"
THOUGHT_STREAM_FILE = OUTPUTS_DIR / "thought_stream_latest.json"
AURA_SCRIPT = WORKSPACE_ROOT / "services" / "agi_aura.py"
TRIGGER_REPORT_FILE = OUTPUTS_DIR / "bridge" / "trigger_report_latest.json"
TRIGGER_FILE = WORKSPACE_ROOT / "signals" / "lua_trigger.json"
HEARTBEAT_FILE = OUTPUTS_DIR / "unconscious_heartbeat.json"
AGI_AURA_SUBPROCESS_LOG = LOGS_DIR / "agi_aura_subprocess.log"

# Logging Setup
os.makedirs(LOGS_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "aura_controller.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AuraController")

# Aura Colors (Unified with agi_aura.py + Extra)
COLORS = {
    "idle": "#1A1A2E",       # Idle/Sleep
    "thinking": "#00FFFF",   # Cyan (Rhythm)
    "acting": "#FF00FF",     # Magenta (Action)
    "learning": "#00FF88",   # Dark Green (Success)
    
    # Emotional/State Colors
    "survival": "#FF0000",   # Red: Critical
    "anxiety": "#FF4500",    # Orange: Warning
    "focus": "#FFD700",      # Yellow: Analysis
    "harmony": "#00FF66",    # Bright Green: Stable
    "express": "#00BFFF",    # Blue: Output
    "insight": "#4B0082",    # Indigo: Deep Thought
    "explore": "#9933FF",    # Purple: Novelty
    "bored": "#888888",      # Grey: Boredom
    "conflict": "#FF4500",   # OrangeRed (Same as anxiety for now)
}


# Flow Configuration
FLOW_TIMEOUT_SECONDS = 30  # 30초간 흐름 없으면 의미 상실 (Idle)

class AuraController:
    def __init__(self):
        self.process = None
        self._aura_log_handle = None
        self.current_color = COLORS["idle"]
        self.last_mtime = 0
        self.last_trigger_mtime = 0
        self.last_report_mtime = 0
        self.last_heartbeat_mtime = 0
        self.last_update_time = time.time()  # 마지막 흐름 시간
        
    def start_aura(self):
        """Start the aura subprocess"""
        if not AURA_SCRIPT.exists():
            logger.error(f"❌ Aura script not found: {AURA_SCRIPT}")
            return

        cmd = [sys.executable, str(AURA_SCRIPT), self.current_color]
        try:
            # pythonw.exe 사용 시 CREATE_NO_WINDOW가 오히려 불안정해질 수 있어 제거.
            # stderr를 파일에 남겨 "죽는 이유"를 관측 가능하게 한다.
            AGI_AURA_SUBPROCESS_LOG.parent.mkdir(parents=True, exist_ok=True)
            try:
                if self._aura_log_handle:
                    self._aura_log_handle.close()
            except:
                pass
            self._aura_log_handle = open(AGI_AURA_SUBPROCESS_LOG, "a", encoding="utf-8", buffering=1)
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=self._aura_log_handle,
                stderr=self._aura_log_handle,
                text=True,
                bufsize=1,
                creationflags=0
            )  
            logger.info(f"✨ Aura started (PID: {self.process.pid})")
        except Exception as e:
            logger.error(f"❌ Failed to start aura: {e}")

    def update_aura(self, color_hex):
        """Send color change command to aura"""
        if self.process and self.process.poll() is None:
            try:
                self.process.stdin.write(f"color:{color_hex}\n")
                self.process.stdin.flush()
                self.current_color = color_hex
                logger.info(f"🎨 Color updated: {color_hex}")
            except Exception as e:
                logger.error(f"⚠️ Failed to send command: {e}")
                self.restart_aura(color_hex)
        else:
            self.restart_aura(color_hex)

    def restart_aura(self, color_hex):
        """Restart aura process if it died"""
        logger.warning("🔄 Restarting Aura...")
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=1)
            except:
                pass
        self.current_color = color_hex
        self.start_aura()

    # Lumen Mode Check
    LUMEN_KEY_FILE = Path("c:/workspace/agi/inputs/lumen_passkey.txt")
    
    def is_lumen_active(self):
        try:
            if not self.LUMEN_KEY_FILE.exists(): return False
            with open(self.LUMEN_KEY_FILE, 'r', encoding='utf-8') as f:
                return "오케스트레이션 연결된다" in f.read()
        except: return False

    def determine_color_from_reports(self):
        """
        비노체 관측(의식) 우선 규칙:
        - 트리거 존재(실행중/대기) -> 노랑(focus)
        - 최근 리포트 실패/오류 -> 빨강(survival)
        - 심장(heartbeat) 오래 멈춤 -> 주황(anxiety)
        - 리포트 오래됨 -> 회색(bored)
        - 최근 성공 -> 초록(harmony)
        """
        try:
            now = time.time()

            # 1) trigger 존재: 실행중/대기
            if TRIGGER_FILE.exists():
                try:
                    if TRIGGER_FILE.stat().st_size > 0:
                        return COLORS["focus"], 1.0
                except:
                    return COLORS["focus"], 1.0

            report = None
            if TRIGGER_REPORT_FILE.exists():
                for _ in range(3):
                    try:
                        with open(TRIGGER_REPORT_FILE, "r", encoding="utf-8") as f:
                            report = json.load(f)
                        break
                    except:
                        time.sleep(0.05)

            # heartbeat age
            hb_age = None
            if HEARTBEAT_FILE.exists():
                try:
                    hb_age = max(0.0, now - HEARTBEAT_FILE.stat().st_mtime)
                except:
                    hb_age = None

            rep_age = None
            if TRIGGER_REPORT_FILE.exists():
                try:
                    rep_age = max(0.0, now - TRIGGER_REPORT_FILE.stat().st_mtime)
                except:
                    rep_age = None

            # 2) report 기반 상태 판정
            if isinstance(report, dict):
                status = str(report.get("status") or "").lower()
                err = report.get("error")
                if status == "failed" or err:
                    return COLORS["survival"], 0.0

                if hb_age is not None and hb_age > 180:
                    return COLORS["anxiety"], 0.2

                if rep_age is not None and rep_age > 900:
                    return COLORS["bored"], 0.1

                return COLORS["harmony"], 0.9

            # 3) report가 없어도 heartbeat만으로 경고
            if hb_age is not None and hb_age > 180:
                return COLORS["anxiety"], 0.2

        except Exception as e:
            logger.error(f"determine_color_from_reports error: {e}")
        return None

    def determine_color(self, data):
        """Logic to determine aura color based on full state"""
        
        # 0. Lumen Orchestration (Absolute Priority)
        if self.is_lumen_active():
            # 루멘 모드에서는 기본적으로 백색(통합)이지만, 상태에 따라 틴트가 들어감
            return "#FFFFFF", 1.0 # Pure White (All Colors Combined)

        # Extract fields
        state = data.get("state", {})
        feeling = data.get("feeling", {})
        decision = data.get("decision", "").lower()
        action = data.get("action", "").lower()
        active_habits = data.get("active_habits", [])
        
        # 1. Critical Override (Survival/Anxiety)
        score = state.get("score", 50)
        if score < 20:
            return COLORS["survival"], 0.2
        if score < 40:
            return COLORS["anxiety"], 0.3

        # 2. Feeling/Resonance (Unconscious)
        feeling_tag = feeling.get("tag", "").lower()
        if feeling_tag == "harmony":
            return COLORS["harmony"], 0.9
        elif feeling_tag == "opposition":
            return COLORS["conflict"], 0.4

        # 3. Decision/Action (Conscious)
        if "explore" in decision or "autonomous" in action:
            return COLORS["explore"], 0.85
        
        if "stabilize" in decision:
            return COLORS["learning"], 0.8
        
        if "amplify" in decision:
            return COLORS["acting"], 0.8

        if "continue" in decision:
            # 흐름 유지 시 위상(Phase)에 따라 미묘하게
            phase = state.get("phase", "EXPANSION")
            if phase == "EXPANSION":
                return COLORS["express"], 0.8
            else:
                return COLORS["insight"], 0.8

        # 4. Habits
        for habit in active_habits:
            if "Flow" in habit.get("name", ""):
                return COLORS["focus"], 0.9

        # Default Rhythm
        return COLORS["thinking"], 0.6

    def process_thought_stream(self):
        """Read JSON and determine color"""
        try:
            # 트리거/리포트/심장/스트림 중 하나라도 변하면 처리
            ts_m = THOUGHT_STREAM_FILE.stat().st_mtime if THOUGHT_STREAM_FILE.exists() else 0
            tr_m = TRIGGER_FILE.stat().st_mtime if TRIGGER_FILE.exists() else 0
            rp_m = TRIGGER_REPORT_FILE.stat().st_mtime if TRIGGER_REPORT_FILE.exists() else 0
            hb_m = HEARTBEAT_FILE.stat().st_mtime if HEARTBEAT_FILE.exists() else 0

            # Debounce
            if (
                ts_m == self.last_mtime
                and tr_m == self.last_trigger_mtime
                and rp_m == self.last_report_mtime
                and hb_m == self.last_heartbeat_mtime
            ):
                return
            self.last_mtime = ts_m
            self.last_trigger_mtime = tr_m
            self.last_report_mtime = rp_m
            self.last_heartbeat_mtime = hb_m
            
            # 흐름 확인 (갱신됨)
            self.last_update_time = time.time()

            # 우선: 트리거/리포트 기반 관측(비노체용)
            override = self.determine_color_from_reports()
            if override:
                target_color, align_score = override
                if target_color != self.current_color:
                    logger.info(f"🤔 Trigger/Report -> New Color: {target_color} (Align: {align_score:.2f})")
                    self.update_aura(target_color)
                return

            # Read with retry
            data = None
            for _ in range(3):
                try:
                    with open(THOUGHT_STREAM_FILE, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    break
                except:
                    time.sleep(0.1)
            
            if not data:
                return

            try:
                ret = self.determine_color(data)
                target_color, align_score = ret
            except ValueError as ve:
                logger.error(f"Unpacking error in determine_color. Got: {ret} ({type(ret)})")
                target_color, align_score = COLORS["idle"], 0.0
            except Exception as e:
                logger.error(f"Error in determine_color dispatch: {e}")
                target_color, align_score = COLORS["idle"], 0.0
            
            # Update if changed
            if target_color != self.current_color:
                logger.info(f"🤔 State changed -> New Color: {target_color} (Align: {align_score:.2f})")
                self.update_aura(target_color)
                
                # [NEW] Save Feedback for Brain
                self.save_feedback(data, target_color, align_score)

        except Exception as e:
            logger.error(f"⚠️ Error processing thought stream: {e}")

    def save_feedback(self, thought_data, color, score):
        """Save resonance feedback to be synced back to Linux Brain"""
        try:
            feedback_file = OUTPUTS_DIR / "resonance_feedback.json"
            feedback = {
                "timestamp": time.time(),
                "aura_color": color,
                "alignment_score": score,
                "active_trigger": thought_data.get("trigger", {}).get("type", "unknown"),
                "reason": f"Body resonated with color {color}"
            }
            
            # Write atomic-ish with retry
            temp = feedback_file.with_suffix(".tmp")
            with open(temp, 'w', encoding='utf-8') as f:
                json.dump(feedback, f, indent=2)
            
            # Retry replace
            for _ in range(3):
                try:
                    if feedback_file.exists():
                        feedback_file.unlink()
                    temp.replace(feedback_file)
                    break
                except Exception:
                    time.sleep(0.1)
            
            # Cleanup temp if still exists
            if temp.exists():
                try: temp.unlink()
                except: pass
                
        except Exception as e:
            logger.error(f"Failed to save feedback: {e}")

    def check_flow_vitality(self):
        """Monitor if the flow is still alive"""
        elapsed = time.time() - self.last_update_time
        
        if elapsed > FLOW_TIMEOUT_SECONDS:
            if self.current_color != COLORS["idle"]:
                logger.info(f"🥀 Flow stopped ({elapsed:.1f}s ago). Meaning fades to stillness.")
                self.update_aura(COLORS["idle"])
        
class ThoughtStreamHandler(FileSystemEventHandler):
    def __init__(self, controller):
        self.controller = controller

    def on_modified(self, event):
        if event.src_path.endswith("thought_stream_latest.json"):
            self.controller.process_thought_stream()

def run_controller():
    logger.info("🧠 Aura Controller (Body) Started")

    # 루빗 오라 픽셀(최소 관측)이 있으면 legacy aura는 자동 종료(팝업/중복 방지)
    try:
        if (WORKSPACE_ROOT / "scripts" / "rubit_aura_pixel.py").exists():
            logger.info("🧊 Legacy AuraController disabled: rubit_aura_pixel is present")
            return
    except Exception:
        pass
    
    # Version Logging
    try:
        ver_file = WORKSPACE_ROOT / "VERSION"
        if ver_file.exists():
            version = ver_file.read_text("utf-8").strip()
            logger.info(f"🏷️  System Version: {version}")
    except: pass
    
    logger.info(f"👀 Watching: {THOUGHT_STREAM_FILE}")
    
    controller = AuraController()
    controller.start_aura()
    
    # Watchdog setup
    event_handler = ThoughtStreamHandler(controller)
    observer = Observer()
    observer.schedule(event_handler, path=str(OUTPUTS_DIR), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
            
            # [Fallback] Explicit Polling for Reliability
            controller.process_thought_stream()
            
            # 1. Check process health
            if controller.process and controller.process.poll() is not None:
                logger.warning("💀 Aura process died unexpectedly. Restarting...")
                controller.restart_aura(controller.current_color)
            
            # 2. Check flow vitality (The Lua Principle)
            controller.check_flow_vitality()
            
    except KeyboardInterrupt:
        observer.stop()
        if controller.process:
            controller.process.terminate()
    observer.join()

if __name__ == "__main__":
    run_controller()

