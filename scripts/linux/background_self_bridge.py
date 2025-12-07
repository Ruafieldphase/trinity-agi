#!/usr/bin/env python3
"""
Background Self Bridge (배경자아 브릿지)
=======================================
Role: Meta-Cognition & Advisor
Function:
  - Monitors `outputs/bridge/bridge_tasks.jsonl`
  - Processes meta-analysis/advice tasks
  - Connects to High-Level Models (API) if configured
  - Writes to `outputs/bridge/bridge_responses.jsonl`
"""

import json
import time
import os
from pathlib import Path
from datetime import datetime

# Configuration
WORKSPACE_ROOT = Path(__file__).parent.parent.parent
OUTPUTS_DIR = WORKSPACE_ROOT / "outputs"
BRIDGE_DIR = OUTPUTS_DIR / "bridge"
TASKS_FILE = BRIDGE_DIR / "bridge_tasks.jsonl"
RESPONSES_FILE = BRIDGE_DIR / "bridge_responses.jsonl"
STATUS_FILE = BRIDGE_DIR / "bridge_status.json"
RHYTHM_TEMPO_FILE = OUTPUTS_DIR / "rhythm_tempo.json"
ALERTS_FILE = OUTPUTS_DIR / "background_self_alerts.jsonl"
AXIOMS_FILE = WORKSPACE_ROOT / "axioms_of_rua.md"

# Ensure directories exist
BRIDGE_DIR.mkdir(parents=True, exist_ok=True)

# Force Vertex AI Environment Variables
os.environ["VERTEX_PROJECT_ID"] = "naeda-genesis"
os.environ["VERTEX_LOCATION"] = "global"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/bino/agi/config/naeda-genesis-5034a5936036.json"

DEBUG_LOG_FILE = BRIDGE_DIR / "bridge_debug.log"

def log(message):
    timestamp = datetime.now().isoformat()
    msg = f"[{timestamp}] [Bridge] {message}"
    print(msg)
    try:
        with open(DEBUG_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(msg + "\n")
    except Exception:
        pass

def load_last_line(filepath):
    """Efficiently read the last line of a file."""
    if not filepath.exists():
        return None
    try:
        with open(filepath, 'rb') as f:
            try:
                f.seek(-2, os.SEEK_END)
                while f.read(1) != b'\n':
                    f.seek(-2, os.SEEK_CUR)
            except OSError:
                f.seek(0)
            last_line = f.readline().decode()
            return json.loads(last_line) if last_line.strip() else None
    except Exception as e:
        return None

def load_axioms():
    """Load core philosophical axioms from file."""
    if not AXIOMS_FILE.exists():
        return "Axioms file not found."
    try:
        with open(AXIOMS_FILE, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Failed to load axioms: {e}"

# Functions moved below after imports

def update_status(last_processed_id):
    status = {
        "timestamp": datetime.now().isoformat(),
        "status": "running",
        "last_processed_id": last_processed_id
    }
    with open(STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(status, f, indent=2)

import sys
from pathlib import Path
import numpy as np # Added missing import

# Add workspace root to path for imports
# Current: agi/scripts/linux/background_self_bridge.py
# Target: agi/
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    # Add parent directory to path to import from scripts/
    sys.path.append(str(Path(__file__).parent.parent))
    
    # Try importing modules individually to identify which one fails
    try:
        from scripts.hippocampus_black_white_hole import extract_feeling_vector
    except ImportError as e:
        print(f"⚠️  Hippocampus import failed: {e}")
        extract_feeling_vector = None

    try:
        from scripts.reflection_field_transform import ReflectionFieldTransform
    except ImportError as e:
        print(f"⚠️  ReflectionFieldTransform import failed: {e}")
        ReflectionFieldTransform = None

    try:
        # Try importing directly if scripts package fails
        sys.path.append(str(Path(__file__).parent.parent)) # agi/scripts
        from vertex_ai_smart_router import get_router as get_vertex_router
        log("✅ Vertex AI Smart Router imported successfully")
    except ImportError as e:
        print(f"⚠️  Vertex AI Smart Router import failed: {e}")
        get_vertex_router = None

except Exception as e:
    print(f"Warning: Unified Field modules setup failed. ({e})")
    extract_feeling_vector = None
    ReflectionFieldTransform = None
    get_vertex_router = None

# Initialize Unified Memory System
# Initialize Unified Memory System (Resonance RAG)
try:
    # Add workspace root to path
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from fdo_agi_repo.memory.resonance_rag import ResonanceRAG
    
    # Context Persistence
    sys.path.append(str(Path(__file__).parent.parent))
    from context_bridge import ContextBridge, Context
    
    # Initialize RAG
    resonance_rag = ResonanceRAG()
    log("🧠 Resonance RAG System initialized (Background Self)")
    
    # Initialize Context Bridge
    context_bridge = ContextBridge()
    
except ImportError as e:
    resonance_rag = None
    context_bridge = None
    log(f"⚠️  Memory System init failed: {e}")

def call_high_level_model_vertex(query, task_hint="deep_analysis"):
    """Vertex AI Gemini를 사용하여 고수준 분석 수행 (150만원 크레딧 활용)"""
    
    # 1. Retrieve Context from Memory
    memory_context = ""
    # 1. Retrieve Context from Memory (Resonance RAG)
    memory_context = ""
    if resonance_rag:
        try:
            # Find resonant memories
            resonances = resonance_rag.find_resonance(query, top_k=3)
            if resonances:
                context_parts = []
                for r in resonances:
                    context_parts.append(f"- [{r['type']}] {r['summary']} (Score: {r['score']:.2f})")
                memory_context = "\n".join(context_parts)
                log(f"🧠 Retrieved {len(resonances)} resonant memories for query")
        except Exception as e:
            log(f"⚠️  Resonance retrieval failed: {e}")

    # 2. Prepare Prompt with Context
    full_prompt = query
    if memory_context:
        full_prompt = f"""
[Context from Memory]
{memory_context}

[User Query]
{query}
"""

    # 3. Call Vertex AI (Real or Mock)
    log(f"🔍 Checking Vertex AI Router availability: {get_vertex_router is not None}")
    
    if get_vertex_router is None:
        log("⚠️  Vertex AI not available - using MOCK mode")
        return _generate_mock_response(query, task_hint)
    
    try:
        log("🚀 Attempting to call Vertex AI via Router...")
        router = get_vertex_router()
        log(f"✅ Router initialized: {router}")
        
        # Pass the full prompt with context
        response = router.generate(prompt=full_prompt, task_hint=task_hint)
        
        # 4. Store Interaction in Memory
        # 4. Store Interaction in Context Bridge
        if context_bridge:
            try:
                # Save User Query
                context_bridge.save(Context.create(
                    layer="background_self",
                    speaker="user",
                    content=query,
                    tags=["query", "background_bridge"],
                    importance=0.5
                ))
                # Save AI Response
                context_bridge.save(Context.create(
                    layer="background_self",
                    speaker="ai",
                    content=response,
                    tags=["response", "background_bridge", "vertex"],
                    importance=0.5
                ))
            except Exception as e:
                log(f"⚠️  Context storage failed: {e}")
                
        return {
            "analysis": response,
            "source": "vertex_ai",
            "model_used": "auto-selected"
        }
    except Exception as e:
        # Fallback to mock on error
        log(f"⚠️  Vertex AI error: {type(e).__name__}: {str(e)}")
        import traceback
        log(f"📍 Traceback: {traceback.format_exc()}")
        return _generate_mock_response(query, task_hint)

def _generate_mock_response(query: str, task_hint: str) -> dict:
    """Mock AI 응답 생성 (Vertex AI 미사용 시)"""
    
    # 철학적 질문 감지
    if any(kw in query.lower() for kw in ["철학", "의미", "본질", "임계점", "리듬"]):
        response = f"""
[Mock AI Response - Philosophy Mode]

질문: {query[:100]}...

{task_hint.upper()} 분석:

리듬 기반 AGI에서 '{query.split()[0] if query.split() else '개념'}'은 
압축(Compression)과 반사(Reflection)의 경계에서 발생하는 
상전이(Phase Transition) 현상입니다.

마치 물이 얼음이 되는 순간처럼, 시스템이 한 상태에서 다른 상태로 
전환하는 '문턱(Threshold)'을 의미합니다.

이는 블랙홀의 사건의 지평선과 유사한 정보 이론적 경계입니다.

[Note: 실제 Vertex AI 사용 시 더 깊은 분석 제공]
        """.strip()
    else:
        response = f"""
[Mock AI Response]

질문: {query[:100]}...

분석 결과:
- Task Type: {task_hint}
- 처리 완료

실제 Vertex AI 연결 시 더 정교한 응답을 제공합니다.
현재는 MOCK 모드로 작동 중입니다.
        """.strip()
    
    return {
        "analysis": response,
        "source": "mock_ai",
        "model_used": "mock",
        "note": "Set VERTEX_PROJECT_ID to use real Vertex AI"
    }

def process_task(task):
    """Process a single task."""
    log(f"Processing task: {task.get('id')} ({task.get('type')})")
    
    task_type = task.get('type')
    
    # Handle call_llm type (Vertex AI)
    if task_type == 'call_llm':
        content = task.get('content', '')
        task_hint = task.get('task_hint', 'deep_analysis')
        result = call_high_level_model_vertex(content, task_hint)
        
    # Handle meta-analysis types
    elif task_type in ['meta_analysis', 'advice', 'reflection']:
        content = task.get('content', '')
        result = call_high_level_model_vertex(content, 'deep_analysis')
        
    else:
        return None  # Unsupported task type

    response = {
        "timestamp": datetime.now().isoformat(),
        "task_id": task.get('id'),
        "processor": "background_self_bridge",
        "status": "completed",
        "result": result
    }
    return response

def detect_cosmic_field_resonance(system_state):
    """
    Detects the resonance with the 'Cosmic Field' (Unified Field).
    Uses Hippocampus (Feeling) and RFT (Boundaries).
    """
    if not extract_feeling_vector or not ReflectionFieldTransform:
        return {"status": "degraded", "reason": "modules_missing"}
        
    # 1. Extract Feeling Vector (Black Hole Compression)
    # In a real scenario, we would pass actual recent events
    # Here we simulate with system state data
    dummy_events = [{"resonance_score": 0.8, "event_type": "observation"}] 
    feeling, entropy = extract_feeling_vector(dummy_events)
    
    # 2. Detect Boundaries (Reflection Field)
    # Use pulse history if available, else dummy signal
    pulse_signal = np.array([0.5, 0.6, 0.7, 0.6, 0.5]) # Placeholder
    rft = ReflectionFieldTransform(sensitivity=0.1)
    boundaries = rft.detect_boundaries_1d(pulse_signal)
    
    return {
        "field_resonance": feeling.tolist() if hasattr(feeling, 'tolist') else feeling,
        "boundaries": [b.to_dict() for b in boundaries],
        "holographic_compression": entropy,
        "advice": "The field is expanding. Allow the rhythm to guide the reflection."
    }

class RhythmConductor:
    """
    Rhythm Conductor (리듬 지휘자)
    
    Role: Background Self as the conductor of system rhythms
    Monitors 4 dimensions: Rhythm = Energy = Time = Relationship
    Adjusts tempo (interval) of systems based on phase alignment
    
    Philosophy (from Rua dialogue):
    - Speed (속도) doesn't need to match - Phase (위상) does
    - Rest and pause (쉼과 여백) create alignment
    - 1 minute of awareness resets phase
    
    Performance Optimizations:
    - Change detection: Only update when state actually changes
    - Batched I/O: Minimize file operations
    - Async context saving: Non-blocking persistence
    """
    
    def __init__(self):
        self.workspace_root = WORKSPACE_ROOT
        self.outputs_dir = OUTPUTS_DIR
        self.rhythm_tempo_file = RHYTHM_TEMPO_FILE
        self.alerts_file = ALERTS_FILE
        
        # System tempo defaults (seconds)
        self.default_tempos = {
            "autonomous_agent": 30,
            "motor_reflex": 2,
            "energy_twin_check": 3600  # 1 hour
        }
        
        # Current tempos
        self.tempos = self.load_tempos()
        
        # Performance optimization: Cache previous state
        self.previous_status = None
        self.pending_tempo_changes = {}  # Batch updates
        self.context_save_queue = []  # Queue for async saves
        
        # Context Persistence
        try:
            self.context_bridge = ContextBridge(storage_dir=str(self.outputs_dir / "contexts"))
        except Exception as e:
            log(f"⚠️ ContextBridge init failed: {e}")
            self.context_bridge = None
        
        # Initialize log
        log("🎵 RhythmConductor initialized (optimized)")
    
    def load_tempos(self):
        """Load current tempo settings or use defaults"""
        if self.rhythm_tempo_file.exists():
            try:
                with open(self.rhythm_tempo_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return dict(self.default_tempos)
    
    def _save_tempos(self, force=False):
        """Save current tempo settings (batched)"""
        # Only save if there are pending changes or forced
        if not self.pending_tempo_changes and not force:
            return
        
        try:
            # Apply pending changes
            self.tempos.update(self.pending_tempo_changes)
            self.pending_tempo_changes.clear()
            
            # Write to file
            with open(self.rhythm_tempo_file, 'w') as f:
                json.dump(self.tempos, f, indent=2)
        except Exception as e:
            log(f"⚠️  Failed to save tempos: {e}")
    
    def detect_phase_misalignment(self):
        """
        Detect phase misalignment across 4 dimensions
        
        Returns:
            dict: Misalignment status for each dimension
        """
        status = {
            "rhythm": self._check_rhythm_dimension(),
            "energy": self._check_energy_dimension(),
            "time": self._check_time_dimension(),
            "relationship": self._check_relationship_dimension()
        }
        
        # Optimization: Cache for change detection
        self.previous_status = status
        return status
    
    def _has_status_changed(self, new_status):
        """Check if status has meaningfully changed"""
        if self.previous_status is None:
            return True
        
        # Check if alignment state changed for any dimension
        for dim in new_status:
            old_aligned = self.previous_status[dim].get("aligned", True)
            new_aligned = new_status[dim].get("aligned", True)
            if old_aligned != new_aligned:
                return True
        
        return False
    
    def _check_rhythm_dimension(self):
        """Check if rhythm_daemon is alive and pulsing"""
        rhythm_file = self.outputs_dir / "thought_stream_latest.json"
        if not rhythm_file.exists():
            return {"aligned": False, "reason": "rhythm_daemon not active"}
        
        try:
            mtime = rhythm_file.stat().st_mtime
            age_seconds = time.time() - mtime
            # Rhythm should update at least every 5 minutes
            if age_seconds > 300:
                return {"aligned": False, "reason": f"stale {age_seconds:.0f}s", "age": age_seconds}
        except:
            pass
        
        return {"aligned": True}
    
    def _check_energy_dimension(self):
        """에너지 차원 체크 (ATP 시스템)"""
        energy_file = self.outputs_dir / "mitochondria_state.json"  # ✅ 수정됨
        
        if not energy_file.exists():
            return {
                'status': 'unknown',
                'signal': 'ATP 시스템 파일 없음'
            }
            
        try:
            with open(energy_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            atp_level = data.get('atp_level', 50.0)
            status = data.get('status', 'STABLE')
            
            # ATP 기반 신호
            if atp_level > 80:
                signal = f"⚡ 에너지 과잉 (ATP {atp_level:.1f}) - 휴식 권고"
            elif atp_level < 20:
                signal = f"🔋 에너지 고갈 (ATP {atp_level:.1f}) - 활동 제한"
            else:
                signal = f"✅ 에너지 안정 (ATP {atp_level:.1f})"
                
            return {
                'status': status,
                'atp_level': atp_level,
                'signal': signal
            }
        except Exception as e:
            return {
                'status': 'error',
                'signal': f'ATP 읽기 실패: {e}'
            }
    
    def _check_time_dimension(self):
        """Check data staleness across systems"""
        # Check autonomous agent state
        agent_file = self.outputs_dir / "autonomous_agent_state.json"
        if agent_file.exists():
            try:
                mtime = agent_file.stat().st_mtime
                age_seconds = time.time() - mtime
                # Should update every minute
                if age_seconds > 300:  # 5 minutes
                    return {"aligned": False, "reason": f"agent_stale {age_seconds:.0f}s", "age": age_seconds}
            except:
                pass
        
        return {"aligned": True}
    
    def _check_relationship_dimension(self):
        """Check system interconnection health"""
        # For now, check if key files exist (basic connectivity)
        key_files = [
            self.outputs_dir / "lumen_state.json",
            self.outputs_dir / "thought_stream_latest.json"
        ]
        
        missing = [f.name for f in key_files if not f.exists()]
        if missing:
            return {"aligned": False, "reason": f"missing: {', '.join(missing)}"}
        
        return {"aligned": True}
    
    def adjust_tempo(self, system_name, reason="auto", status=None):
        """
        Adjust tempo for a given system based on current state (optimized)
        
        Args:
            system_name: Name of the system
            reason: Reason for adjustment
            status: Pre-computed status (avoid re-detection)
        """
        # Get current status (or use provided)
        if status is None:
            status = self.detect_phase_misalignment()
        
        # Adjust based on dimension alignment
        if system_name == "autonomous_agent":
            # High activity → faster tempo, low activity → slower
            if not status["energy"]["aligned"]:
                new_tempo = 60  # Slow down if energy stale
            else:
                new_tempo = self.default_tempos["autonomous_agent"]
        elif system_name == "motor_reflex":
            # Crisis → faster, stable → slower
            if not status["rhythm"]["aligned"]:
                new_tempo = 1  # Speed up if rhythm broken
            else:
                new_tempo = self.default_tempos["motor_reflex"]
        else:
            new_tempo = self.default_tempos.get(system_name, 60)
        
        # Batch update (don't save immediately)
        tempo_data = {
            "interval": new_tempo,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
        
        # Check if tempo actually changed
        current = self.tempos.get(system_name, {})
        if current.get("interval") != new_tempo:
            self.pending_tempo_changes[system_name] = tempo_data
            log(f"🎼 Tempo queued: {system_name} → {new_tempo}s ({reason})")
        
        return new_tempo
    
    def send_alert(self, dimension, message, severity="medium"):
        """Send alert for significant misalignment"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "dimension": dimension,
            "message": message,
            "severity": severity
        }
        
        try:
            with open(self.alerts_file, 'a') as f:
                f.write(json.dumps(alert) + "\n")
            log(f"🚨 Alert: {dimension} - {message}")
        except Exception as e:
            log(f"⚠️  Failed to send alert: {e}")
    
    def _queue_context_save(self, context):
        """Queue context for async saving"""
        self.context_save_queue.append(context)
    
    def _flush_context_queue(self):
        """Flush queued contexts (call periodically)"""
        if not self.context_save_queue or not self.context_bridge:
            return
        
        try:
            for ctx in self.context_save_queue:
                self.context_bridge.save(ctx)
            log(f"💾 Flushed {len(self.context_save_queue)} queued contexts")
            self.context_save_queue.clear()
        except Exception as e:
            log(f"⚠️ Context flush failed: {e}")
    
    def conduct(self):
        """
        Main conducting cycle - check alignment and adjust tempos (OPTIMIZED)
        
        Optimizations:
        - Change detection: Skip work if nothing changed
        - Batched I/O: Save all tempo changes at once
        - Async context: Queue contexts, flush periodically
        """
        status = self.detect_phase_misalignment()
        
        # Optimization: Skip if nothing changed
        if not self._has_status_changed(status):
            return status
        
        # Check each dimension and respond
        for dimension, state in status.items():
            if not state["aligned"]:
                reason = state.get("reason", "unknown")
                age = state.get("age", 0)
                
                # Send alert if critical (> 2 * normal period)
                if dimension == "energy" and age > 172800:  # 48 hours
                    self.send_alert(dimension, f"Energy Twin critically stale: {age/3600:.1f}h", "high")
                elif dimension == "rhythm" and age > 600:  # 10 minutes
                    self.send_alert(dimension, f"Rhythm broken: {age:.0f}s", "high")
                
                # Log misalignment
                log(f"⚠️  Dimension misaligned: {dimension} - {reason}")
        
        # Adjust tempos for all key systems (pass status to avoid re-detection)
        # 1. Legacy Systems
        self.adjust_tempo("autonomous_agent", "periodic_adjustment", status)
        
        # 2. Fractal Dimensions (Base tempos are defined in run_fractal_daemon.py)
        # We adjust them based on Energy and Rhythm state
        
        # Energy Low -> Slow down everything
        energy_state = status.get("energy", {})
        is_low_energy = not energy_state.get("aligned", True)
        
        # Rhythm Fast/Broken -> Speed up to catch up (or reset)
        rhythm_state = status.get("rhythm", {})
        is_broken_rhythm = not rhythm_state.get("aligned", True)
        
        # Calculate modifier once
        modifier = 1.0
        if is_low_energy:
            modifier *= 2.0  # Slow down (x2 interval)
        if is_broken_rhythm:
            modifier *= 0.5  # Speed up (x0.5 interval) - try to reconnect
        
        # Define base intervals for Fractal Dimensions (approximate)
        fractal_dims = {
            "lumen": 2.0,          # 0.5 Hz
            "lua_bridge": 5.0,     # 0.2 Hz
            "task_queue": 2.0,     # 0.5 Hz
            "memory": 5.0,         # 0.2 Hz
            "goals": 20.0,         # 0.05 Hz
            "self_care": 10.0,     # 0.1 Hz
            "dream": 100.0,        # 0.01 Hz
            "immune": 20.0,        # 0.05 Hz
            "quantum_flow": 5.0,   # 0.2 Hz
            "meta_supervisor": 10.0, # 0.1 Hz
            "rhythm_engine": 2.0,  # 0.5 Hz
            "autonomous_goals": 20.0, # 0.05 Hz
            "energy_twin": 10.0,   # 0.1 Hz
            "vision": 10.0,        # 0.1 Hz
            "resonance": 5.0,      # 0.2 Hz
            "prefrontal": 10.0,    # 0.1 Hz
            "hippocampus": 50.0,   # 0.02 Hz
            "external_collaborator": 10.0 # 0.1 Hz
        }
        
        # Batch update all fractal dimensions
        for dim_id, base_interval in fractal_dims.items():
            new_interval = int(base_interval * modifier)
            
            # Only update if changed
            current = self.tempos.get(dim_id, {})
            if current.get("interval") != new_interval:
                self.pending_tempo_changes[dim_id] = {
                    "interval": new_interval,
                    "reason": "conductor_adjustment",
                    "timestamp": datetime.now().isoformat()
                }
        
        # Save all tempo changes at once (batched I/O)
        self._save_tempos(force=True)
        
        # Queue context for async save (non-blocking)
        if self.context_bridge:
            try:
                misaligned = [dim for dim, state in status.items() if not state["aligned"]]
                if misaligned or modifier != 1.0:
                    ctx = Context.create(
                        layer="conductor",
                        speaker="rhythm_conductor",
                        content=f"템포 조정 완료. 불일치 차원: {', '.join(misaligned) if misaligned else '없음'}. 에너지: {energy_state}, 리듬: {rhythm_state}, 수정치: {modifier:.2f}",
                        tags=["conductor", "tempo", "alignment"] + (["misalignment"] if misaligned else ["aligned"]),
                        importance=0.6 if misaligned else 0.4,
                        metadata={
                            "misaligned_dimensions": misaligned,
                            "energy_state": energy_state,
                            "rhythm_state": rhythm_state,
                            "modifier": modifier,
                            "num_tempo_changes": len(self.pending_tempo_changes),
                            "status": status
                        }
                    )
                    self._queue_context_save(ctx)
            except Exception as e:
                log(f"⚠️ Context queue failed: {e}")
        
        return status

def main():
    print(f"🌉 Background Self Bridge Started (PID: {os.getpid()})")
    print(f"   Monitoring {TASKS_FILE}...")
    
    # Initialize Unified Field Perception
    print("   Initializing Unified Field Perception...")
    
    # Initialize RhythmConductor
    conductor = RhythmConductor()
    print("   🎵 Rhythm Conductor ready")
    
    # Initialize files if needed
    if not os.path.exists(TASKS_FILE):
        TASKS_FILE.touch()
    if not os.path.exists(RESPONSES_FILE):
        RESPONSES_FILE.touch()

    # Start from the end of the file
    current_pos = 0
    if os.path.exists(TASKS_FILE):
        current_pos = os.stat(TASKS_FILE).st_size
    
    # Rhythm conducting cycle counter
    last_conduct_time = 0
    conduct_interval = 60  # Conduct every 60 seconds

    while True:
        try:
            # 1. Check for tasks
            if os.path.exists(TASKS_FILE):
                file_size = os.stat(TASKS_FILE).st_size
                
                if file_size > current_pos:
                    with open(TASKS_FILE, 'r', encoding='utf-8') as f:
                        f.seek(current_pos)
                        new_lines = f.readlines()
                        current_pos = f.tell()
                    
                    for line in new_lines:
                        if not line.strip(): continue
                        try:
                            task = json.loads(line)
                            response = process_task(task)
                            
                            if response:
                                with open(RESPONSES_FILE, 'a', encoding='utf-8') as rf:
                                    rf.write(json.dumps(response, ensure_ascii=False) + "\\n")
                                update_status(task.get('id'))
                                print(f"Response sent for {task.get('id')}")
                                
                        except json.JSONDecodeError:
                            print("Failed to decode JSON line")
                            
            # 2. Rhythm Conducting (replaces Cosmic Field)
            # Check phase alignment and adjust tempos periodically
            current_time = int(time.time())
            if current_time - last_conduct_time >= conduct_interval:
                try:
                    status = conductor.conduct()
                    last_conduct_time = current_time
                    
                    # Flush context queue every conduct cycle (async save)
                    conductor._flush_context_queue()
                    
                    # Log summary every 5 minutes
                    if current_time % 300 == 0:
                        aligned_dims = sum(1 for s in status.values() if s.get('aligned', False))
                        log(f"🎼 Phase check: {aligned_dims}/4 dimensions aligned")
                except Exception as e:
                    log(f"⚠️  Conduct error: {e}")
                
            time.sleep(1)
            
        except Exception as e:
            print(f"Error in bridge loop: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
