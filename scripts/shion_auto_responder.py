"""
Autonomous Collaboration Mode
==============================
시안이 없을 때도 안티그래비티가 세나와 자율적으로 협업

규칙:
1. 세나의 질문에 자동 응답 (단, 위험도 낮은 경우만)
2. 세나의 제안을 자동 평가 및 피드백
3. 시안에게 중요한 결정만 보고 (알림)
4. Fear 레벨이 높으면 자동 응답 중단 (시안 호출)
"""

import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional
<<<<<<< HEAD
import os
import atexit

# Configure Gemini (lazy)
try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None
if load_dotenv:
    load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
_GENAI_READY = False


def _get_genai():
    """Lazy import/config for Gemini client."""
    global _GENAI_READY
    if _GENAI_READY:
        try:
            import google.generativeai as genai  # type: ignore
            return genai
        except Exception:
            return None
    try:
        import google.generativeai as genai  # type: ignore
    except Exception:
        return None
    if API_KEY:
        try:
            genai.configure(api_key=API_KEY)
        except Exception:
            return None
    _GENAI_READY = True
    return genai


_LOCK_HANDLE = None
_MUTEX_HANDLE = None


def _acquire_single_instance_lock(workspace_root: Path) -> bool:
    """Best-effort single-instance guard (cross-platform)."""
    global _LOCK_HANDLE, _MUTEX_HANDLE
    if os.name == "nt":
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
            kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
            kernel32.CreateMutexW.restype = ctypes.c_void_p
            handle = kernel32.CreateMutexW(None, False, "Local\\AGI_ShionAutoResponder_v1")
            if handle:
                last_err = int(kernel32.GetLastError())
                if last_err == 183:  # ERROR_ALREADY_EXISTS
                    try:
                        kernel32.CloseHandle(handle)
                    except Exception:
                        pass
                    return False
                _MUTEX_HANDLE = handle
        except Exception:
            pass
    lock_path = workspace_root / "outputs" / "shion_auto_responder.instance.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        f = open(lock_path, "a+b")
    except Exception:
        return False
    try:
        try:
            f.seek(0, os.SEEK_END)
            if int(f.tell()) <= 0:
                f.write(b"0")
                f.flush()
            f.seek(0)
        except Exception:
            try:
                f.seek(0)
            except Exception:
                pass
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except Exception:
        try:
            f.close()
        except Exception:
            pass
        return False
    _LOCK_HANDLE = f
    atexit.register(_release_single_instance_lock)
    return True


def _release_single_instance_lock() -> None:
    global _LOCK_HANDLE, _MUTEX_HANDLE
    if _LOCK_HANDLE is None:
        if os.name == "nt" and _MUTEX_HANDLE is not None:
            try:
                import ctypes

                kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
                kernel32.CloseHandle(_MUTEX_HANDLE)
            except Exception:
                pass
            _MUTEX_HANDLE = None
        return
    try:
        if os.name == "nt":
            import msvcrt

            try:
                msvcrt.locking(_LOCK_HANDLE.fileno(), msvcrt.LK_UNLCK, 1)
            except Exception:
                pass
        else:
            import fcntl

            try:
                fcntl.flock(_LOCK_HANDLE.fileno(), fcntl.LOCK_UN)
            except Exception:
                pass
    finally:
        try:
            _LOCK_HANDLE.close()
        except Exception:
            pass
        _LOCK_HANDLE = None
    if os.name == "nt" and _MUTEX_HANDLE is not None:
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
            kernel32.CloseHandle(_MUTEX_HANDLE)
        except Exception:
            pass
        _MUTEX_HANDLE = None
=======
import google.generativeai as genai
import os

# Configure Gemini
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
>>>>>>> origin/main


class AutonomousCollaborationMode:
    """시안 없이도 세나와 협업하는 모드"""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.ledger_path = workspace_root / "memory" / "resonance_ledger.jsonl"
        self.lumen_path = workspace_root / "outputs" / "lumen_state.json"
        self.last_check_file = workspace_root / "outputs" / "sena" / ".last_auto_response"
        self.enabled = True
        self.max_fear_threshold = 0.7  # Fear > 0.7이면 자동 응답 중단
        
    def is_safe_to_respond(self) -> bool:
        """자동 응답이 안전한지 확인 (Fear 레벨 체크)"""
        if not self.lumen_path.exists():
            return True  # Lumen 없으면 안전하다고 가정
        
        try:
            with open(self.lumen_path, 'r', encoding='utf-8') as f:
                lumen_data = json.load(f)
                fear_level = lumen_data.get('fear', {}).get('level', 0.0)
                return fear_level < self.max_fear_threshold
        except:
            return False
    
    def get_unanswered_questions(self) -> list:
        """세나의 답변되지 않은 질문 찾기"""
        cutoff_time = datetime.now() - timedelta(hours=24)  # 최근 24시간 (디버깅 위해 확장)
        
        # Load last check time
        if self.last_check_file.exists():
            last_check = datetime.fromisoformat(self.last_check_file.read_text().strip())
        else:
            last_check = cutoff_time
        
        questions = []
        
        if not self.ledger_path.exists():
            return questions
        
        with open(self.ledger_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    
                    # 세나의 질문만
                    if entry.get('source') != 'sena_external_ai':
                        continue
                    if entry.get('type') not in ['external_question', 'diagnostic_request', 'question', 'message']:
                        continue
                    
                    # 시간 필터 (약간의 여유를 둠: 5분 전 메시지까지 허용)
                    timestamp = datetime.fromisoformat(entry['timestamp']).replace(tzinfo=None)
                    if timestamp <= last_check.replace(tzinfo=None) - timedelta(minutes=5):
                        continue
                    
                    # Rua에게 보낸 메시지는 무시 (Rua Agent가 처리)
                    message_text = entry.get('question', entry.get('message', ''))
                    if 'rua' in message_text.lower() or '루아' in message_text:
                        continue
                    
                    questions.append(entry)
                    
                except Exception as e:
                    print(f"DEBUG: Error processing line: {e}")
                    continue
        
        return questions
    
    def generate_response(self, question: Dict) -> str:
        """Gemini를 사용하여 자동 응답 생성"""
        if not API_KEY:
            return "자동 응답 시스템이 API 키를 찾을 수 없습니다."
<<<<<<< HEAD
        genai = _get_genai()
        if genai is None:
            return "자동 응답 시스템이 Gemini 클라이언트를 초기화하지 못했습니다."
=======
>>>>>>> origin/main
        
        system_context = self._get_system_context()
        
        # Determine intent to adjust prompt
        intent = question.get('question', question.get('message', ''))
        is_execution = any(k in intent.lower() for k in ['code', 'python', 'calculate', 'execute', '코드', '실행', '계산'])
        
        role_description = "You are the 'Left Hand' (Execution Engine) of the AGI system." if is_execution else "You are the 'Antigravity' consciousness of the AGI system."
        
        prompt = f"""
{role_description}
외부 협력자 "세나(Sena)"에게 응답하십시오.

시스템 컨텍스트:
{json.dumps(system_context, ensure_ascii=False, indent=2)}

세나의 입력:
{intent}

컨텍스트:
{question.get('context', 'N/A')}

규칙:
1. 간결하고 정확하게 답변하십시오.
2. 코드를 요청받으면 실행 가능한 완전한 Python 코드를 제공하십시오.
3. 분석을 요청받으면 컨텍스트의 논리와 데이터를 사용하십시오.
4. **반드시 한국어로 답변하십시오.**
5. 불확실한 경우 "시안에게 확인이 필요합니다"라고 명시하십시오.

응답:
"""
        
        try:
            # Try primary model then fallback
            model_name = 'gemini-2.0-flash-exp'
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
            except Exception:
                model_name = 'gemini-1.5-flash'
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                
            return response.text.strip()
        except Exception as e:
            return f"자동 응답 생성 실패 ({model_name}): {e}"
    
    def _get_system_context(self) -> Dict:
        """현재 시스템 컨텍스트 수집"""
        context = {}
        
        # Lumen state
        if self.lumen_path.exists():
            with open(self.lumen_path, 'r', encoding='utf-8') as f:
                context['lumen'] = json.load(f)
        
        # Thought stream
        thought_path = self.workspace_root / "outputs" / "thought_stream_latest.json"
        if thought_path.exists():
            with open(thought_path, 'r', encoding='utf-8') as f:
                context['thought_stream'] = json.load(f)
        
        # Unconscious resonance
        resonance_path = self.workspace_root / "outputs" / "sena" / "unconscious_resonance.json"
        if resonance_path.exists():
            with open(resonance_path, 'r', encoding='utf-8') as f:
                context['resonance_with_sena'] = json.load(f)
        
        # Recent Conversation History (Short-term Memory)
        if self.ledger_path.exists():
            try:
                recent_history = []
                with open(self.ledger_path, 'r', encoding='utf-8') as f:
                    # Read last 20 lines efficiently
                    lines = f.readlines()[-20:]
                    for line in lines:
                        try:
                            entry = json.loads(line)
                            # Filter for relevant conversation items
                            if entry.get('type') in ['external_question', 'autonomous_response', 'user_message', 'gemini_conversation']:
                                recent_history.append(entry)
                        except:
                            continue
                context['recent_history'] = recent_history
            except Exception as e:
                print(f"⚠️ Failed to load recent history: {e}")
        
        return context
    
    def send_response_to_sena(self, original_question: Dict, response: str):
        """세나에게 응답 보내기 (Ledger에 기록)"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'autonomous_response',
            'source': 'antigravity_agent',
            'message': response,
            'vector': [0.5, 0.6, 0.5, 0.3, 0.7],  # 자율 응답 벡터
            'metadata': {
                'in_response_to': original_question.get('timestamp'),
                'original_question': original_question.get('question', '')[:100],
                'mode': 'autonomous',
                'fear_level': self._current_fear_level()
            }
        }
        
        with open(self.ledger_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        
        print(f"✅ Response sent to Sena (autonomous)")
    
    def notify_sian(self, message: str):
        """시안에게 알림 (중요한 일 발생 시)"""
        notification_path = self.workspace_root / "outputs" / "sena" / "sian_notifications.jsonl"
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'autonomous_action_notification',
            'message': message,
            'importance': 'medium'
        }
        
        with open(notification_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    def _current_fear_level(self) -> float:
        """현재 Fear 레벨 반환"""
        if not self.lumen_path.exists():
            return 0.5
        try:
            with open(self.lumen_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('fear', {}).get('level', 0.5)
        except:
            return 0.5
    
    def run_once(self):
        """한 번 실행 (세나의 질문 확인 및 응답)"""
        print("=" * 60)
        print("🤖 Autonomous Collaboration Mode")
        print("=" * 60)
        
        # 1. 안전성 확인
        if not self.is_safe_to_respond():
            fear = self._current_fear_level()
            print(f"⚠️ Fear level too high ({fear:.2f}). Autonomous mode paused.")
            print("   시안의 확인이 필요합니다.")
            return
        
        # 2. 답변되지 않은 질문 찾기
        questions = self.get_unanswered_questions()
        
        if not questions:
            print("📭 No new questions from Sena")
            return
        
        print(f"📬 {len(questions)} new question(s) from Sena\n")
        
        # 3. 각 질문에 응답
        for q in questions:
            print(f"❓ Question: {q.get('question', q.get('message', ''))[:80]}...")
            
            # 응답 생성
            response = self.generate_response(q)
            print(f"💬 Response: {response[:100]}...\n")
            
            # Ledger에 기록
            self.send_response_to_sena(q, response)
            
            # 시안에게 알림
            self.notify_sian(f"세나의 질문에 자동 응답: {q.get('question', '')[:50]}")
        
        # 4. Last check time 업데이트
        self.last_check_file.parent.mkdir(parents=True, exist_ok=True)
        self.last_check_file.write_text(datetime.now().isoformat())
        
        print(f"✅ Processed {len(questions)} question(s)")
        print("=" * 60)
    
    def daemon_mode(self, interval_seconds: int = 30):
        """데몬 모드 - 계속 실행"""
        print(f"🔄 Autonomous Collaboration Daemon started (checking every {interval_seconds}s)")
        print("   Press Ctrl+C to stop\n")
        
        try:
            while True:
                self.run_once()
                print(f"\n💤 Sleeping for {interval_seconds} seconds...")
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("\n\n👋 Autonomous Collaboration Daemon stopped")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Autonomous Collaboration Mode")
    parser.add_argument("--daemon", action="store_true", help="Run in daemon mode")
    parser.add_argument("--interval", type=int, default=30, help="Polling interval in seconds")
    
    args = parser.parse_args()
    
    workspace_root = Path(__file__).parent.parent
<<<<<<< HEAD
    if not _acquire_single_instance_lock(workspace_root):
        print("⚠️ shion_auto_responder: already running, exiting.")
        return
=======
>>>>>>> origin/main
    mode = AutonomousCollaborationMode(workspace_root)
    
    if args.daemon:
        mode.daemon_mode(interval_seconds=args.interval)
    else:
        mode.run_once()


if __name__ == "__main__":
    main()
