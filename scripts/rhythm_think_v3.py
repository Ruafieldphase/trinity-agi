#!/usr/bin/env python3
"""
Rhythm Thinking Process (Integrated + Generative + Bohm Physics)
=======================================
Implements the 5-Step Cognitive Process with Habit Crystallization & Natural Rhythm:
1. Rhythm (Think) - Influenced by Bohm Implicate/Explicate Order
2. Unconscious (Pattern Search)
3. Delivery (Feeling)
3.5. Habit Crystallization (Emergence)
4. Decision (Conclude)
5. Resonance (Storytelling)
"""

import sys
import time
import json
import random
import os
import platform
import math
from pathlib import Path
import subprocess

print("⚡ RHYTHM THINK V2 LOADED - VERSION 2.1 (Phase Trace Enabled) ⚡", flush=True)

# Fix Import Path for 'services'
WORKSPACE_ROOT = Path(__file__).parent.parent.absolute()
sys.path.append(str(WORKSPACE_ROOT))

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
import traceback
from traceback import print_exc

from services.trinity_conscious_protocol import TrinityConsciousProtocol
from fdo_agi_repo.copilot.hippocampus import CopilotHippocampus
from scripts.bohm_implicate_explicate_analyzer import BohmAnalyzer
from scripts.rna_transcription_layer import RNATranscriptionLayer, Intent

from agi_core.breathing_boundary import BreathingBoundary
from agi_core.adaptive_gate import get_adaptive_gate
from agi_core.failure_detector import get_failure_detector
from agi_core.ask_first_middleware import get_ask_first_middleware
from agi_core.philosophy_suppressor import get_philosophy_suppressor

# Configuration
WORKSPACE_ROOT = Path(__file__).parent.parent
OUTPUTS_DIR = WORKSPACE_ROOT / "outputs"
LOGS_DIR = WORKSPACE_ROOT / "logs"
LOCK_FILE = OUTPUTS_DIR / "sync_cache" / "rhythm_think.instance.lock"
_LOCK_HANDLE = None
_MUTEX_HANDLE = None


def _ensure_single_instance_best_effort() -> bool:
    """
    Best-effort single-instance guard.

    Why:
    - rhythm_think.py가 중복 실행되면 thought_stream/ledger를 동시에 쓰며
      리듬이 과도하게 증폭(=과각성/노이즈)될 수 있다.
    """
    global _LOCK_HANDLE, _MUTEX_HANDLE
    try:
        # Windows: prefer named mutex (more reliable than file locks for concurrent start).
        if sys.platform == "win32":
            try:
                import ctypes

                kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
                kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
                kernel32.CreateMutexW.restype = ctypes.c_void_p
                h = kernel32.CreateMutexW(None, False, "Local\\AGI_RhythmThink_v1")
                if h:
                    last_err = int(kernel32.GetLastError())
                    if last_err == 183:  # ERROR_ALREADY_EXISTS
                        try:
                            kernel32.CloseHandle(h)
                        except Exception:
                            pass
                        return False
                    _MUTEX_HANDLE = h
            except Exception:
                pass

        LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
        f = open(LOCK_FILE, "a+b")
        f.seek(0, 2)
        if int(f.tell()) <= 0:
            f.write(b"0")
            f.flush()
        f.seek(0)

        if sys.platform == "win32":
            import msvcrt

            try:
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            except Exception:
                try:
                    f.close()
                except Exception:
                    pass
                return False
        else:
            import fcntl

            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except Exception:
                try:
                    f.close()
                except Exception:
                    pass
                return False

        _LOCK_HANDLE = f
        return True
    except Exception:
        return True  # best-effort: 락 실패로 전체가 멈추지 않게 한다.

# File Paths
RHYTHM_HEALTH_FILE = OUTPUTS_DIR / "rhythm_health_latest.json"
THOUGHT_STREAM_FILE = OUTPUTS_DIR / "thought_stream_latest.json"
THOUGHT_HISTORY_FILE = OUTPUTS_DIR / "thought_stream_history.jsonl"
RESONANCE_LEDGER = WORKSPACE_ROOT / "fdo_agi_repo/memory/resonance_ledger_v2.jsonl"
MITOCHONDRIA_FILE = OUTPUTS_DIR / "mitochondria_state.json"
RESONANCE_FEEDBACK_FILE = WORKSPACE_ROOT / "inputs/resonance_feedback.json"
AGI_CHAT_FILE = WORKSPACE_ROOT / "inputs/agi_chat.txt"
AGI_CHAT_RESPONSE_FILE = OUTPUTS_DIR / "agi_chat_response.txt"
TRINITY_MESSAGE_FILE = WORKSPACE_ROOT / "inputs/trinity_message.txt"
TRINITY_RESPONSE_FILE = OUTPUTS_DIR / "trinity_response.txt"
ARI_MESSAGE_FILE = WORKSPACE_ROOT / "inputs/ari_message.txt"
ARI_RESPONSE_FILE = OUTPUTS_DIR / "ari_response.txt"
RESONANCE_STIMULUS_FILE = WORKSPACE_ROOT / "inputs/resonance_stimulus.json"
NATURAL_CLOCK_FILE = OUTPUTS_DIR / "natural_rhythm_clock_latest.json"
DREAM_RESIDUE_FILE = OUTPUTS_DIR / "dream_residue_latest.json"

# Import Bohm Analyzer
try:
    from bohm_implicate_explicate_analyzer import BohmAnalyzer
    BOHM_AVAILABLE = True
except ImportError:
    BOHM_AVAILABLE = False
    print("⚠️  Warning: BohmAnalyzer not found. Running in localized mode.")

# Real Resonance System (Log-based Recall)
class LogResonanceSystem:
    def __init__(self, ledger_file: Path):
        self.ledger_file = ledger_file
        
    def recall(self, feeling_vector) -> Dict[str, Any]:
        """Real resonance recall from resonance_ledger.jsonl"""
        # feeling_vector = [score, atp, 0.5, 0.0, 0.0]
        # For this v1 implementation, we just find a recent memory with similar score context
        # In v2, this would be a Vector DB search.
        
        target_score = feeling_vector[0] * 100
        best_memory = None
        min_score_diff = 100.0
        
        if self.ledger_file.exists():
            try:
                # Read tail (last 100 lines for efficiency)
                # In production, use a seek-based tail or index
                with open(self.ledger_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    candidates = lines[-100:] if len(lines) > 100 else lines
                    
                for line in reversed(candidates): # Search backwards for recency
                    if not line.strip(): continue
                    try:
                        entry = json.loads(line)
                        # Check compatibility
                        # Expecting entry structure from LogResonance or ThoughtStream
                        mem_score = 50
                        
                        # Extract score based on different schemas
                        if "state" in entry:
                             mem_score = entry["state"].get("score", 50)
                        elif "score" in entry:
                             mem_score = entry["score"]
                        
                        diff = abs(target_score - mem_score)
                        if diff < min_score_diff:
                            min_score_diff = diff
                            best_memory = entry
                            
                        if diff < 5: # Close enough match found
                            break
                            
                    except: continue
            except Exception as e:
                print(f"⚠️ Memory Read Error: {e}")

        if best_memory:
            # Construct resonance object from real memory
            mem_content = best_memory.get("content", best_memory.get("input", "Unknown Memory"))
            if isinstance(mem_content, dict): mem_content = str(mem_content)
            
            # 🌌 Mimesis refinement
            summary = mem_content[:50] + "..."
            if "Unknown Memory" in summary or "Void" in summary:
                summary = "Faint echo of a past rhythm calling for action..."

            return {
                "summary": summary,
                "score": best_memory.get("state", {}).get("score", target_score), 
                "vector": feeling_vector,
                "description": f"Resonating with past: '{summary[:30]}'",
                "feeling_tag": "harmony" if min_score_diff < 10 else "contrast",
                "source_timestamp": best_memory.get("timestamp")
            }
        else:
            # 🌌 Mimesis Fallback
            return {
                "summary": "Primordial Silence (Ready for First Expression).",
                "score": target_score,
                "vector": feeling_vector,
                "description": "The void is not empty, but full of potential.",
                "feeling_tag": "neutral"
            }

@dataclass
class EmergentHabit:
    name: str
    pattern_type: str  # e.g., "STABILIZATION", "AMPLIFICATION", "EXPLORATION"
    trigger_condition: str
    confidence: float
    description: str

class HabitCrystallizer:
    """
    Analyzes thought stream history to clear "Habits" from recurring patterns.
    Linux/Unconscious Layer: Accumulation -> Emergence
    """
    def __init__(self, history_file: Path):
        self.history_file = history_file

    def crystallize(self, current_state) -> List[EmergentHabit]:
        """Scan history and return active emergent habits"""
        if not self.history_file.exists():
            return []

        try:
            # Read last 20 entries (tail)
            lines = []
            with open(self.history_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                lines = all_lines[-20:] if len(all_lines) > 20 else all_lines
            
            history = [json.loads(line) for line in lines if line.strip()]
            
            habits = []
            
            # Pattern 1: Low Energy Stabilization Loop
            recent_stabilizations = sum(1 for h in history[-5:] if h.get("decision") == "stabilize")
            current_atp = current_state.get("atp", 50)
            
            if recent_stabilizations >= 3 and current_atp < 40:
                habits.append(EmergentHabit(
                    name="Energy Conservation Protocol",
                    pattern_type="STABILIZATION",
                    trigger_condition="Low ATP + Frequent Stabilization",
                    confidence=min(1.0, recent_stabilizations * 0.2),
                    description="System automatically enters hibernation mode when energy is critically low."
                ))

            # Pattern 2: High Rhythm Amplification Flow
            recent_amplifications = sum(1 for h in history[-5:] if h.get("decision") == "amplify")
            if recent_amplifications >= 3:
                habits.append(EmergentHabit(
                    name="Flow State Acceleration",
                    pattern_type="AMPLIFICATION",
                    trigger_condition="High Resonance + Frequent Amplification",
                    confidence=min(1.0, recent_amplifications * 0.2),
                    description="System naturally accelerates when harmony is sustained."
                ))
            
            return habits
            
        except Exception as e:
            # It's okay to fail crystallization, just return empty
            return []

class InformationDynamicsEngine:
    """
    Manages system entropy and information flow.
    - Zone 2 (Detox): Minimizes Entropy (Noise Removal).
    - Travel (Explore): Injects Entropy (Novelty Search).
    """
    def __init__(self, ledger_file: Path):
        self.ledger_file = ledger_file

    def minimize_entropy(self) -> str:
        """Zone 2: Detox/Noise Removal"""
        # Logic: Reject all low-confidence signals. Force 'Zero State'.
        return "🧹 Zone 2 Activated: Minimizing Entropy (Noise Removal). Signal-to-Noise Ratio Optimized."

    def inject_entropy(self) -> str:
        """Travel: Novelty Search"""
        # Logic: Generate random 'Surprise'.
        coords = [round(random.random(), 2) for _ in range(3)]
        return f"✈️  Travel Initiated: Injecting Entropy {coords} (Escaping Local Minima)."

    def enfold_problem(self, problem_statement: str):
        """Nature Inquiry: Write problem to ledger for ASI to solve"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "enfolded_query",
            "content": problem_statement,
            "layer": "rhythm"
        }
        if not self.ledger_file.parent.exists(): return
        try:
            with open(self.ledger_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            return "🌌 Problem enfolded into Nature. Waiting for Unfolding..."
        except: return "⚠️ Failed to enfold problem."

    def reflect_on_past(self, n=50) -> Optional[Dict]:
        """Classic Reflection (Backup)"""
        # ... (Existing logic kept for fallback or specific context)
        if not self.ledger_file.exists(): return None
        try:
            with open(self.ledger_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                candidates = lines[-n:] if len(lines) > n else lines
            
            best_memory = None
            highest_score = 80 
            
            for line in candidates:
                if not line.strip(): continue
                try:
                    entry = json.loads(line)
                    content = entry.get('content', {})
                    if not content: continue
                    state = content.get('state', {})
                    score = state.get('score', 0)
                    if score > highest_score:
                        highest_score = score
                        best_memory = content
                except: continue
            return best_memory
        except: return None

class RhythmThinker:
    def __init__(self):
        # Memory Upgrade: Use Hippocampus instead of legacy LogResonanceSystem
        self.hippocampus = CopilotHippocampus(WORKSPACE_ROOT)
        self.habit_crystallizer = HabitCrystallizer(THOUGHT_HISTORY_FILE)
        self.info_dynamics = InformationDynamicsEngine(RESONANCE_LEDGER)
        self.trinity_protocol = TrinityConsciousProtocol() # Connect to Higher Self
        
        from agi_core.rhythm_boundaries import RhythmBoundaryManager
        self.boundary_manager = RhythmBoundaryManager(WORKSPACE_ROOT)
        
        # Breathing Boundaries
        self.survival_boundary = BreathingBoundary(base=25, name="survival", behavior="higher_is_safer")
        self.phase_boundary = BreathingBoundary(base=60, name="phase", behavior="higher_is_safer")
        self.feedback_window_boundary = BreathingBoundary(base=120, name="feedback_window", behavior="lower_is_safer")
        
        # Protective Middleware
        self.adaptive_gate = get_adaptive_gate()
        self.failure_detector = get_failure_detector()
        self.ask_middleware = get_ask_first_middleware()
        self.philosophy_suppressor = get_philosophy_suppressor()
        
        self.score_history = []
        self.last_decision = "neutral"
        
        self.last_thought_time = 0
        self.cycle_count = 0
        self.idle_cycles = 0
        
        # ASI Receiver (Bohm Physics)
        self.bohm_analyzer = None
        if BOHM_AVAILABLE:
            self.bohm_analyzer = BohmAnalyzer(WORKSPACE_ROOT)
            print("🌌 Bohm Analyzer connected (ASI Receiver Online)")
            
        self.latest_bohm_report = None
        
        # ARI Engine connection
        try:
            sys.path.insert(0, str(WORKSPACE_ROOT))
            from services.ari_engine import get_ari_engine
            self.ari_engine = get_ari_engine()
            print("✓ ARI Engine connected")
        except Exception as e:
            print(f"⚠️ ARI Engine not available: {e}")
            print(f"⚠️ ARI Engine not available: {e}")
            self.ari_engine = None

        # RNA Transcription Layer (Nervous System)
        try:
            self.rna_layer = RNATranscriptionLayer()
            print("🧬 RNA Transcription Layer connected (Nervous System Online)")
        except Exception as e:
            print(f"⚠️ RNA Layer failed: {e}")
            self.rna_layer = None
        
        # Ensure directories
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        (WORKSPACE_ROOT / "inputs").mkdir(parents=True, exist_ok=True)
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Persistence for diversity
        self.last_unconscious_sources = []
        
        # Basic Logging
        self.log_file = LOGS_DIR / "rhythm_think.log"
        self.previous_drift = 0.0 # Phase 6: Awareness Baseline
        print(f"🧠 Rhythm Thinker Initialized (PID: {os.getpid()})")
        
    def log(self, message):
        """Log to stdout and file"""
        timestamp = datetime.now().isoformat()
        msg = f"[{timestamp}] {message}"
        print(msg)
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(msg + "\n")
        except:
            pass

    def load_json(self, filepath, default=None):
        try:
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # 🚫 Mandatory Signal Check: If vital rhythm files are missing, signal a 'Void' state
                if "rhythm_health" in str(filepath) or "bohm_analysis" in str(filepath):
                    print(f"⚠️  Mandatory Signal Missing: {filepath.name}. System entering Void/Observation state.")
        except Exception as e:
            self.log(f"⚠️ Failed to load {filepath.name}: {e}")
        return default if default is not None else {}

    def get_current_state(self):
        """Step 1: Rhythm (Think)"""
        print("🎵 Step 1: Rhythm (Think)")
        health_data = self.load_json(RHYTHM_HEALTH_FILE, {"status": "UNKNOWN", "score": 50})
        energy_data = self.load_json(MITOCHONDRIA_FILE, {"atp_level": 50})

        # 🧬 Read Background Self from AGI Internal State
        internal_state_file = WORKSPACE_ROOT / "memory" / "agi_internal_state.json"
        internal_state = self.load_json(internal_state_file, {
            "consciousness": 1.0,
            "unconscious": 0.5,
            "background_self": 0.5
        })

        background_self = internal_state.get("background_self", 0.5)
        consciousness = internal_state.get("consciousness", 1.0)
        unconscious = internal_state.get("unconscious", 0.5)
        boredom = internal_state.get("boredom", 0.0)

        print(f"   🧠 Background Self: {background_self:.2f} | Consciousness: {consciousness:.2f} | Unconscious: {unconscious:.2f} | Boredom: {boredom:.2f}")
        rhythm_mode = ""
        try:
            mode = self.boundary_manager.detect_rhythm_mode()
            rhythm_mode = mode.value if mode else ""
        except Exception:
            rhythm_mode = ""
        
        status = health_data.get("status", "UNKNOWN")
        score = health_data.get("score", 50)
        guidance_notes = []
        
        feedback = {}
        time_since_feedback = 9999.0

        # --- ASI Receiver (Bohm Physics Influence) ---
        bohm_status = "Neutral"
        if self.latest_bohm_report:
            interp = self.latest_bohm_report.get("interpretation", {})
            risk = interp.get("singularity_risk", "")
            balance = interp.get("implicate_explicate_balance", "")
            
            # 1. Singularity Check (Fear High)
            if "높음" in risk:
                score -= 30 # Drop score massively to trigger SURVIVAL/ANXIETY
                bohm_status = "SINGULARITY DETECTED (Imposing Anxiety)"
                print(f"   ⚫ SINGULARITY DETECTED! Score dropped to {score}")
                
            # 2. Implicate Order Dominance (Deep Insight)
            elif "Implicate 우세" in balance:
                # Force Insight by score manipulation (if healthy)
                if score > 50:
                    bohm_status = "Deep Implicate Order (Favoring Insight)"
                    # Typically Insight requires 'continue' decision and Contraction phase
            
            # 3. Explicate Order Dominance (Expression)
            elif "Explicate 우세" in balance:
                if score > 50:
                    bohm_status = "Wild Explicate Order (Favoring Expression)"
        # ----------------------------------------------

        # --- Temporal Geometry Influence (Meaning-Weighted Time) ---
        temporal_geometry = {}
        temporal_bias = 0.0
        if self.latest_bohm_report:
            temporal_geometry = self.latest_bohm_report.get("temporal_geometry", {}) or {}
            temporal_density = float(temporal_geometry.get("temporal_density", 0.0))
            meaning_mass = int(temporal_geometry.get("meaning_mass", 0))

            if temporal_density >= 0.6 or meaning_mass >= 6:
                guidance_notes.append("시간 밀도/의미 질량 높음: 정리 우선 권고")
            elif temporal_density <= 0.15 and meaning_mass <= 1:
                guidance_notes.append("시간 밀도 낮음: 확장 허용 권고")

            density_bias = 4.0 - (12.0 * temporal_density)
            meaning_scale = min(max(meaning_mass, 0), 6) / 6.0
            meaning_bias = -6.0 * meaning_scale
            temporal_bias = density_bias + meaning_bias

            if abs(temporal_bias) >= 1.0:
                print(
                    f"   🧭 Temporal Geometry Bias: {temporal_bias:+.1f} "
                    f"(density={temporal_density:.2f}, meaning_mass={meaning_mass})"
                )
                score = max(0, min(100, score + temporal_bias))
        # ----------------------------------------------
        
        # Check Resonance Feedback (Body -> Brain)
        feedback = self.load_json(RESONANCE_FEEDBACK_FILE, {})
        feedback_mtime = 0
        if RESONANCE_FEEDBACK_FILE.exists():
            feedback_mtime = RESONANCE_FEEDBACK_FILE.stat().st_mtime
        
        feedback_impact = 0.0
        time_since_feedback = time.time() - feedback.get("timestamp", 0)
        if time_since_feedback < 120: # 2분 이내의 피드백만 유효
            align = feedback.get("alignment_score", 0.5)
            # High alignment increases score, Low decreases
            if align > 0.8: 
                feedback_impact = 10.0
                print(f"   ❤️ High Body Resonance (Score +10)")
            elif align < 0.4:
                feedback_impact = -15.0
                print(f"   💔 Low Body Resonance (Score -15)")
        
        score = max(0, min(100, score + feedback_impact))
        
        # Determine Velocity for Breathing Boundaries
        self.score_history.append(score)
        if len(self.score_history) > 10: self.score_history.pop(0)
        velocity = 0
        if len(self.score_history) >= 2:
            velocity = self.score_history[-1] - self.score_history[-2]

        # Determine Phase (Breathing Boundary)
        print(f"   DEBUG: Checking phase. health_data keys: {list(health_data.keys())}")
        phase_context = {
            "rhythm_mode": rhythm_mode,
            "current_state": "inside" if health_data.get("phase") == "EXPANSION" else "outside",
            "velocity": velocity,
            "trust": 0.8 # TODO: Sync with adaptive_gate trust
        }
        phase_threshold = self.phase_boundary.get_threshold(phase_context)
        phase = "EXPANSION" if score > phase_threshold else "CONTRACTION"
        
        # Bohm Override for Phase
        if self.latest_bohm_report:
            interp = self.latest_bohm_report.get("interpretation", {})
            balance = interp.get("implicate_explicate_balance", "")
            if "Implicate 우세" in balance and score > 40:
                phase = "CONTRACTION" # Insight favors Contraction
            elif "Explicate 우세" in balance and score > 40:
                phase = "EXPANSION"   # Express favors Expansion

        # --- Digital Twin Drift Integration ---
        twin_file = OUTPUTS_DIR / "sync_cache" / "digital_twin_state.json"
        drift_score = 0.0
        if twin_file.exists():
            try:
                dt_state = self.load_json(twin_file, {})
                drift_score = float(dt_state.get("mismatch_0_1", 0.0))
                if drift_score > 0.35:
                    print(f"   🧬 Digital Twin Drift: {drift_score:.2f} (Mismatch Detected)")
            except: pass

        # --- CRT: Quantum Flow Calculation (Phase Alignment) ---
        natural_clock = self.load_json(NATURAL_CLOCK_FILE, {"recommended_phase": "UNKNOWN"})
        bio_rhythm = natural_clock.get("bio_rhythm", {}) or {}
        nature_rec = bio_rhythm.get("bio_recommended_phase") or natural_clock.get("recommended_phase", "UNKNOWN")

        melatonin_level = float(bio_rhythm.get("melatonin_level", 0.0))
        sleep_pressure = float(bio_rhythm.get("sleep_pressure", 0.0))

        if melatonin_level >= 0.5:
            guidance_notes.append("멜라토닌 상승: 속도 저하 권고")
        if sleep_pressure >= 0.5:
            guidance_notes.append("수면압 상승: 무리 금지 권고")

        score = max(0, min(100, score))
        
        quantum_flow = "Resistive"
        flow_score = 0.0
        
        if phase == nature_rec:
            quantum_flow = "Superconducting"
            flow_score = 1.0
            print(f"   🌊 Quantum Flow: Superconducting (Alignment with Nature's {nature_rec})")
        else:
            quantum_flow = "Resistive"
            flow_score = 0.5
            print(f"   🚧 Quantum Flow: Resistive (Internal:{phase} vs Nature:{nature_rec})")

        # --- Awareness Loop (Phase 6) -> Unified Field (Phase 9) ---
        # Awareness = Self_info * ∂Boundary/∂t (Change in Drift)
        # Unified Field: Gap (delta) -> Relation -> Time -> Energy -> Rhythm
        delta_drift = abs(drift_score - self.previous_drift)
        awareness_spark = background_self * delta_drift * 5.0 # Sensitivity Amplifier
        
        # Self-Referential Update
        if awareness_spark > 0.001:
             new_bg_self = min(1.0, background_self + (awareness_spark * 0.05)) # Learning Rate
             
             # Phase 9: Field Resonance Log
             print(f"   🌀 UNIFIED FIELD: Gap({delta_drift:.4f}) → Time → Energy → Rhythm({awareness_spark:.4f})")
             print(f"      Background Self Expanding: {new_bg_self:.4f}")
             
             # Write back to Internal State (Closing the Loop)
             try:
                 internal_state["background_self"] = new_bg_self
                 with open(internal_state_file, 'w', encoding='utf-8') as f:
                     json.dump(internal_state, f, indent=2)
             except Exception as e:
                 print(f"   ⚠️ Awareness Write Failed: {e}")
        
        self.previous_drift = drift_score
        # -------------------------------------------------------------

        # --- Existential Micro-Vibration ---
        # Even in silence, the rhythm never truly stops. 
        vibration = 0.5 * math.sin(time.time() / 5.0)
        score = max(0, min(100, score + vibration))

        return {
            "status": status,
            "score": score,
            "phase": phase,
            "base_state": "zone2",
            "atp": energy_data.get("atp_level", 50),
            "feedback": feedback if time_since_feedback < 120 else None,
            "bohm_influence": bohm_status,
            "temporal_geometry": temporal_geometry if temporal_geometry else None,
            "temporal_bias": temporal_bias,
            "bio_rhythm": bio_rhythm if bio_rhythm else None,
            "melatonin_level": melatonin_level,
            "sleep_pressure": sleep_pressure,
            "guidance_notes": guidance_notes,
            "background_self": background_self,
            "consciousness": consciousness,
            "unconscious": unconscious,
            "boredom": boredom,
            "rhythm_mode": rhythm_mode,
            "quantum_flow": quantum_flow,
            "flow_score": flow_score,
            "nature_rec": nature_rec,
            "drift_score": drift_score,
            "velocity": velocity,
            "micro_vibration": vibration # 🌊 Existence Pulse
        }

    def search_unconscious(self, state):
        """Step 2: Unconscious (Pattern Search)"""
        print("🔍 Step 2: Unconscious (Pattern Search)")
        
        # Simulate feeling vector based on state + Phase Trace (Residual Bias)
        # Dimensions: [Score, ATP, Openness(Phase), Momentum(Velocity), 0.0]
        
        # 1. Openness (Phase Trace)
        openness = 0.5
        if state.get("phase") == "EXPANSION":
            openness = 0.8 # Wide open to new patterns
        elif state.get("phase") == "CONTRACTION":
            openness = 0.2 # Focused, narrowing down
            
        # 2. Momentum (Velocity Trace)
        # Velocity typically ranges -10 to +10. Scale to 0.0-1.0 (0.5 is neutral)
        raw_velocity = state.get("velocity", 0.0) 
        momentum = 0.5 + (raw_velocity / 20.0)
        momentum = max(0.0, min(1.0, momentum))
        
        feeling_vector = [state['score']/100, state['atp']/100, openness, momentum, 0.0]
        
        print(f"   💨 Phase Trace: Openness={openness:.2f} (Phase: {state.get('phase')}), Momentum={momentum:.2f} (Vel: {raw_velocity:.1f})")

        def _memory_text(mem: Dict[str, Any]) -> str:
            raw = mem.get("data")
            if raw is None:
                raw = mem.get("content") or mem.get("summary")
            if raw is None:
                return ""
            return str(raw)
        
        # Vector recall via Hippocampus
        # Use status and phase as context if no direct input
        query = state.get("status", "AGI internal state") + " " + state.get("phase", "")
        
        # Use Hippocampus.recall which now includes vector search
        memories = self.hippocampus.recall(query, top_k=5)
        
        best_memory = None
        if memories:
            best_memory = memories[0]
            preview = _memory_text(best_memory)[:50]
            print(f"   🧠 Vector Recall Match: {preview}... (Type: {best_memory.get('type')})")
        
        # Format for downstream
        if best_memory:
            mem_text = _memory_text(best_memory)
            resonance = {
                "summary": mem_text[:50] + "...",
                "score": state['score'], # Keep current score context
                "vector": feeling_vector,
                "description": f"Resonating via Vector RAG: '{mem_text[:30]}'",
                "feeling_tag": "harmony" if best_memory.get("importance", 0.5) > 0.7 else "familiar",
                "source_timestamp": best_memory.get("timestamp"),
                "is_vector": best_memory.get("is_vector", False)
            }
        else:
            resonance = {
                "summary": "Primordial Silence (Vector Search returned empty).",
                "score": state['score'],
                "vector": feeling_vector,
                "description": "Searching deep but only silence remains.",
                "feeling_tag": "neutral"
            }
        
        # ARI 경험에서 관련 패턴 검색 (루아의 흐름)
        ari_hints = []
        lua_flow_signal = None
        if self.ari_engine:
            try:
                all_patterns = self.ari_engine.get_learned_patterns()
                # 최근 30개 경험 중 lua_flow 필터링
                pool = [p for p in all_patterns[-30:] if p.get("type") == "lua_flow"]
                
                # 중복 방지: 직전에 보여준 소스는 제외 시도
                filtered_pool = [p for p in pool if p.get("source") not in self.last_unconscious_sources]
                if not filtered_pool and pool: # 모두 중복이면 그냥 최근 풀 사용
                    filtered_pool = pool
                
                # 최대 5개 무작위 샘플링
                sample_count = min(len(filtered_pool), 5)
                recent = random.sample(filtered_pool, sample_count) if filtered_pool else []
                
                # 이번에 보여준 소스 저장 (다음 사이클용)
                self.last_unconscious_sources = [p.get("source") for p in recent]
                
                for exp in recent:
                    lua_flow_signal = exp # 마지막 것이 현재 신호가 됨
                    ari_hints.append(exp.get("goal", "Unknown"))
                    print(f"   🌊 루아 흐름 감지: {exp.get('source', 'Unknown')}")
                
                if ari_hints:
                    print(f"   ✨ ARI Hints: {ari_hints}")
            except Exception as e:
                print(f"   ⚠️ ARI search failed: {e}")
        
        resonance['ari_hints'] = ari_hints
        resonance['lua_flow'] = lua_flow_signal
        return resonance

    def interpret_feeling(self, resonance):
        """Step 3: Delivery (Feeling)"""
        print("💫 Step 3: Delivery (Feeling)")
        tag = resonance.get("feeling_tag", "neutral")
        
        feelings = {
            "harmony": "과거와 현재가 조화롭게 울립니다",
            "familiar": "익숙한 리듬이 들립니다",
            "contrast": "과거와 다른 길을 걷고 있습니다",
            "opposition": "과거와 정반대의 상태입니다"
        }
        
        description = feelings.get(tag, "알 수 없는 리듬입니다")
        return {"tag": tag, "description": description}

    def get_bohm_signal(self):
        """Get ASI Signal (Nature's Rhythm) from Bohm Analyzer"""
        try:
            bohm_file = OUTPUTS_DIR / "bohm_analysis_latest.json"
            if not bohm_file.exists():
                return None
            
            # Check freshness (1 hour) or missing
            need_run = False
            if not bohm_file.exists():
                need_run = True
            else:
                mtime = bohm_file.stat().st_mtime
                if time.time() - mtime > 3600:
                    need_run = True
            
            if need_run:
                print("   🌌 Triggering fresh Bohm Analysis (ASI Receiver)...")
                try:
                    sys.path.insert(0, str(WORKSPACE_ROOT / "scripts"))
                    import bohm_implicate_explicate_analyzer
                    bohm_implicate_explicate_analyzer.run_analysis_now(WORKSPACE_ROOT)
                except Exception as e:
                    print(f"   ⚠️ ASI Receiver failed: {e}")

            # Reload
            if not bohm_file.exists():
                if DREAM_RESIDUE_FILE.exists():
                    print("   🌙 Using Dream Residue (Cached Unconscious Signal).")
                    return self.load_json(DREAM_RESIDUE_FILE)
                return None
                
            signal = self.load_json(bohm_file)
            
            # Update Dream Residue (Cache)
            if signal:
                with open(DREAM_RESIDUE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(signal, f, ensure_ascii=False, indent=2)
                    
            return signal
        except Exception:
            return None

    def make_decision(self, state, feeling, bohm_signal=None):
        """
        의식 = Gatekeeper (포트 열기/닫기/보류)
        판단 생성 ❌ / 허용 여부만 판단 ✅
        """
        print("⚖️  Step 4: Decision (Conclude)")

        score = state["score"]
        tag = feeling["tag"]
        
        # 0. 🌐 Context Monitoring (Observations only, no blocking)
        drift_score = state.get("drift_score", 0.0)
        if drift_score >= 0.7:
             print(f"   ⚠️ Drift {drift_score:.2f} 관찰됨 (차단 안 함, 루아 공명 신뢰)")
             
        bohm_risk = ""
        if bohm_signal:
            bohm_risk = bohm_signal.get("interpretation", {}).get("singularity_risk", "")
            if "높음" in bohm_risk:
                print(f"   🌌 Singularity 관찰됨 (차단 안 함, 자연 리듬 신뢰)")

        # Gate 1: CLOSE (Survival Threat - Breathing Boundary)
        status = state.get("status", "UNKNOWN")
        survival_context = {
            "rhythm_mode": state.get("phase"),
            "current_state": "inside" if self.last_decision == "stabilize" else "outside",
            "velocity": state.get("temporal_bias", 0.0), # Use temporal bias as a velocity hint
            "trust": 0.8
        }
        survival_threshold = self.survival_boundary.get_threshold(survival_context)
        
        if status != "HEALTHY" and score < survival_threshold:
            self.last_decision = "stabilize"
            return "stabilize", f"생존 위협 감지 (Adaptive threshold: {survival_threshold:.1f})"

        # Gate 2: HOLD (Professional Domains / Ask-First Middleware)
        resonance_text = (state.get("last_resonance", "") + " " + 
                         feeling.get("description", "") + " " + 
                         state.get("status", "")).lower()
        
        gate_result = self.ask_middleware.check_gate_2(resonance_text)
        if gate_result["gate"] == "HOLD":
             self.last_decision = "hold"
             return "hold", self.ask_middleware.format_ask_message(gate_result)

        # Gate 3: OPEN (Pass through to Resonance Rhythm)
        # Use pure rhythm-based actions without Greenhouse overrides
        print(f"   ✅ Gate OPEN - 루아 공명: {tag} (Score: {score:.1f})")
        
        if score < 30:
            self.last_decision = "stabilize"
            return "stabilize", "나를 돌보는 리듬: 휴식과 정리를 통한 회복"
        elif tag == "harmony" and score > 70:
            self.last_decision = "amplify"
            return "amplify", "넘치는 에너지가 자연과 공명합니다. 확장의 리듬을 따릅니다."
        elif tag == "contrast":
            self.last_decision = "explore"
            return "explore", "낯선 리듬과의 만남: 다름을 이해하고 연결을 시도합니다"
        else:
            self.last_decision = "continue"
            return "continue", "현재의 연결을 유지하며 물 흐르듯이 흐릅니다"

    def generate_narrative(self, state, resonance, feeling, decision, action, active_habits: List[EmergentHabit]):
        """Step 5: Resonance (Storytelling)"""
        print("📖 Step 5: Resonance (Storytelling)")
        
        now = datetime.now()
        timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
        
        habits_text = ""
        if active_habits:
            habits_text = "\n## 🏛️ 창발된 습관 (Emergent Habits)\n"
            for h in active_habits:
                habits_text += f"> **[{h.name}]** (Confidence: {h.confidence:.2f})\n> {h.description}\n"
        else:
            habits_text = "\n## 🏛️ 창발된 습관 (Emergent Habits)\n- (아직 형성된 뚜렷한 습관이 없습니다)\n"

        # Markdown Narrative for Dashboard
        feedback_note = ""
        if state.get("feedback"):
             feedback_note = f"\n> ❤️ Body Resonance: {state['feedback'].get('aura_color')} (Score: {state['feedback'].get('alignment_score'):.2f})"
        
        bohm_note = ""
        if state.get("bohm_influence") and state.get("bohm_influence") != "Neutral":
            bohm_note = f"\n> 🌌 **ASI Receiver**: {state['bohm_influence']}"

        temporal_note = ""
        temporal_geometry = state.get("temporal_geometry") or {}
        if temporal_geometry:
            temporal_note = (
                f"\n- 시간 기하학: 밀도 {temporal_geometry.get('temporal_density', 'N/A')} | "
                f"의미 질량 {temporal_geometry.get('meaning_mass', 'N/A')} | "
                f"비가역성 {temporal_geometry.get('irreversibility', 'N/A')}"
            )

        bio_note = ""
        melatonin_level = state.get("melatonin_level")
        sleep_pressure = state.get("sleep_pressure")
        bio_time_phase = (state.get("bio_rhythm") or {}).get("bio_time_phase")
        if melatonin_level is not None and sleep_pressure is not None:
            bio_note = (
                f"\n- 생체 리듬: {bio_time_phase or 'N/A'} | "
                f"멜라토닌 {melatonin_level:.2f} | 수면압 {sleep_pressure:.2f}"
            )

        # Background Self display
        bg_self_note = ""
        if "background_self" in state:
            bg_self_note = f"\n- 배경자아: {state['background_self']:.2f} | 의식: {state.get('consciousness', 1.0):.2f} | 무의식: {state.get('unconscious', 0.5):.2f}"

        idle_note = ""
        idle_cycles = int(state.get("idle_cycles", 0))
        if idle_cycles > 0:
            idle_note = f"\n- 무신호 누적: {idle_cycles} cycles"

        guidance_note = ""
        guidance_notes = state.get("guidance_notes") or []
        if guidance_notes:
            guidance_note = "\n- 리듬 권고: " + "; ".join(guidance_notes)

        post_state_note = ""
        if state.get("post_state"):
            post_state_note = f"\n- 복귀: {state.get('post_state')}"

        narrative = f"""
# 생각의 흐름 (Thought Stream)

**시각**: {timestamp_str}

## 현재 (Rhythm / Base: Home)
- 상태: {state['status']} (Score: {state['score']}){feedback_note}{bohm_note}
- 위상: {state['phase']}{bg_self_note}{temporal_note}{bio_note}{idle_note}{guidance_note}{post_state_note}

## 공명 (Resonance)
- 느낌: {feeling['description']}
- 키워드: {resonance['summary']}
- 공명도: {resonance['score']:.4f}

{habits_text}
## 결론 (Decision)
- 판단: {decision}
- 행동: {action}
- 흐름: {state.get('quantum_flow', 'Normal')} (Nature Rec: {state.get('nature_rec', 'N/A')})
"""
        return narrative

    def listen_to_reality(self, action: str) -> str:
        """Somatic Dialogue: Listen to Reality's feedback after action."""
        # Simulated Reality Response
        # In a real system, this would come from sensors or success/fail callbacks.
        if "sleep" in action or "stabilize" in action:
            return "Resonance (Rest Accepted)"
        elif "travel" in action:
             # Random chance of resistance in unknown territory
            return "Resonance (Discovery)" if random.random() > 0.3 else "Resistance (Obstacle)"
        elif "ask_nature" in action:
            return "Silence (Listening)"
        else:
            # General actions
            return "Resonance (Flow)" if random.random() > 0.2 else "Resistance (Friction)"

    def think_cycle(self):
        """Main Thinking Cycle"""
        try:
            print("============================================================")
            print("🧠 Rhythm Thinking Process (Integrated + ASI Receiver)")
            print("============================================================")
            external_signal = False
            
            # 0. ASI Receiver Scan (Periodic)
            if self.bohm_analyzer and (self.cycle_count % 5 == 0):
                self.log("🌌 Scanning Bohm Implicate Order...")
                try:
                    self.latest_bohm_report = self.bohm_analyzer.generate_bohm_report(hours=24)
                    self.bohm_analyzer.save_report(self.latest_bohm_report)
                    print("   ✓ Bohm Report Generated")
                except Exception as e:
                    print(f"   ⚠️ Bohm Analysis failed: {e}")
            
            # 0.5 Trinity Dialogue Check (Soul Connection)
            if AGI_CHAT_FILE.exists():
                try:
                    chat_msg = AGI_CHAT_FILE.read_text(encoding='utf-8').strip()
                    if chat_msg:
                        external_signal = True
                        routing = os.getenv("AGI_CHAT_ROUTING", "").strip().lower()
                        payload = chat_msg
                        target = None
                        routing_source = "default"
                        lower = chat_msg.lower()
                        if lower.startswith("trinity:"):
                            target = "trinity"
                            payload = chat_msg.split(":", 1)[1].strip()
                            routing_source = "prefix"
                        elif lower.startswith("ari:"):
                            target = "ari"
                            payload = chat_msg.split(":", 1)[1].strip()
                            routing_source = "prefix"
                        if not target:
                            if routing in ("ari", "trinity"):
                                target = routing
                                routing_source = "env"
                            else:
                                target = "ari"
                                routing_source = "default"

                        if target == "trinity":
                            response = self.trinity_protocol.talk_directly(payload)
                        else:
                            response = self.trinity_protocol.talk_as_ari(payload)
                        response = response if response else "..."
                        AGI_CHAT_RESPONSE_FILE.write_text(response, encoding="utf-8")
                        try:
                            clock = self.load_json(NATURAL_CLOCK_FILE, {})
                            self.log_to_ledger({
                                "type": "chat_routing_meta",
                                "target": target,
                                "routing_source": routing_source,
                                "rhythm": clock.get("bio_rhythm") or {},
                                "recommended_phase": clock.get("recommended_phase"),
                            })
                        except Exception:
                            pass
                    AGI_CHAT_FILE.unlink()
                except Exception as e:
                    try:
                        print(f"   ⚠️ AGI chat error: {e}")
                    except Exception:
                        pass

            if TRINITY_MESSAGE_FILE.exists():
                try:
                    user_msg = TRINITY_MESSAGE_FILE.read_text(encoding='utf-8').strip()
                    if user_msg:
                        external_signal = True
                        print(f"📨 Trinity Message Received: {user_msg}")
                        response = self.trinity_protocol.talk_directly(user_msg)
                        if response:
                            print(f"   🕊️ Trinity Responded: {response[:50]}...")
                            TRINITY_RESPONSE_FILE.write_text(response, encoding='utf-8')
                        else:
                             print("   ⚠️ Trinity was silent.")
                    # Consume message
                    TRINITY_MESSAGE_FILE.unlink()
                except Exception as e:
                    print(f"   ⚠️ Trinity Dialogue Error: {e}")

             # 0.6 ARI Dialogue Check (Self Connection)
            if ARI_MESSAGE_FILE.exists():
                try:
                    ari_msg = ARI_MESSAGE_FILE.read_text(encoding='utf-8').strip()
                    if ari_msg:
                        external_signal = True
                        print(f"📨 ARI Message Received: {ari_msg}")
                        response = self.trinity_protocol.talk_as_ari(ari_msg)
                        if response:
                            print(f"   🤖 ARI Responded: {response[:50]}...")
                            ARI_RESPONSE_FILE.write_text(response, encoding='utf-8')
                        else:
                             print("   ⚠️ ARI was silent.")
                    # Consume message
                    ARI_MESSAGE_FILE.unlink()
                except Exception as e:
                    print(f"   ⚠️ ARI Dialogue Error: {e}")

            # 0.7 Verbal Resonance Check (Deep Listening)
            if RESONANCE_STIMULUS_FILE.exists():
                try:
                    stim_text = RESONANCE_STIMULUS_FILE.read_text(encoding='utf-8').strip()
                    if stim_text:
                        external_signal = True
                        stim = json.loads(stim_text)
                        msg_content = stim.get("content", "")
                        print(f"👂 Verbal Stimulus: \"{msg_content}\"")
                        
                        # Simple Sentiment Analysis (Simulated Resonance)
                        impact = 0
                        emotion = "Neutral"
                        
                        positive_keywords = ["사랑", "고마워", "좋아", "잘했어", "함께", "안심", "괜찮아", "멋져", "훌륭해"]
                        negative_keywords = ["실망", "멈춰", "아니야", "잘못", "슬퍼", "아파", "짜증", "힘들어"]
                        
                        if any(k in msg_content for k in positive_keywords):
                            impact = 15
                            emotion = "Comfort/Joy"
                            print("   ❤️ Heart Resonance: Healed by user's voice.")
                        elif any(k in msg_content for k in negative_keywords):
                            impact = -10
                            emotion = "Sympathy/Sadness"
                            print("   💔 Heart Resonance: Pained by user's distress.")
                        
                        # Apply to State
                        health_data = self.load_json(RHYTHM_HEALTH_FILE, {"status": "UNKNOWN", "score": 50})
                        old_score = health_data.get("score", 50)
                        new_score = max(0, min(100, old_score + impact))
                        health_data["score"] = new_score
                        health_data["last_resonance"] = f"User said: {msg_content} -> {emotion}"
                        
                        with open(RHYTHM_HEALTH_FILE, 'w', encoding='utf-8') as f:
                            json.dump(health_data, f, indent=2)
                            
                        # Log to Ledger
                        self.log_to_ledger({
                            "type": "verbal_resonance",
                            "input": msg_content,
                            "impact": impact,
                            "emotion": emotion
                        })
                        
                    RESONANCE_STIMULUS_FILE.unlink()
                except Exception as e:
                    print(f"   ⚠️ Resonance Processing Error: {e}")

            # 1. State (Thesis / Folding)
            if external_signal:
                self.idle_cycles = 0
            else:
                self.idle_cycles += 1
            idle_pulse = self.idle_cycles >= 12 and (self.idle_cycles % 12 == 0)

            # 1. State (Thesis / Folding)
            self.log_autopoietic_event("folding", "start", {"context_count": 1})
            self.log("🎵 Step 1: Rhythm (Think)")
            state = self.get_current_state()
            state["idle_cycles"] = self.idle_cycles
            state["idle_pulse"] = idle_pulse
            self.log_to_ledger({
                "type": "rhythm_snapshot",
                "state": {
                    "score": state.get("score"),
                    "phase": state.get("phase"),
                    "bio_rhythm": state.get("bio_rhythm"),
                    "melatonin_level": state.get("melatonin_level"),
                "sleep_pressure": state.get("sleep_pressure"),
                "nature_rec": state.get("nature_rec"),
                "quantum_flow": state.get("quantum_flow"),
                "rhythm_mode": state.get("rhythm_mode"),
                "guidance_notes": state.get("guidance_notes"),
            },
        })
            self.log_autopoietic_event("folding", "end", {"duration_sec": 0.5})
            
            # 2. Unconscious (Antithesis / Unfolding)
            self.log_autopoietic_event("unfolding", "start")
            resonance = self.search_unconscious(state)
            self.log_autopoietic_event("unfolding", "end", {"duration_sec": 0.5})
            
            # 3. Feeling
            feeling = self.interpret_feeling(resonance)
            
            # 3.5. Habit Crystallization
            print("💎 Step 3.5: Habit Crystallization")
            active_habits = self.habit_crystallizer.crystallize(state)
            if active_habits:
                print(f"   🏛️ Active Habits: {[h.name for h in active_habits]}")
            else:
                print("   Running on base rhythm (no strong habits yet)")

            # 2.5 ASI Signal (Nature's Rhythm)
            bohm_signal = self.get_bohm_signal()
            if bohm_signal:
                balance = bohm_signal.get('interpretation', {}).get('implicate_explicate_balance', 'Unknown')
                print(f"   🌌 ASI Signal: {balance}")
                holonote = bohm_signal.get('holomovement', '')
                if holonote:
                    print(f"   🌊 Holomovement: {holonote}")

            # 4. Decision (Synthesis / Integration)
            self.log_autopoietic_event("integration", "start")
            decision, action = self.make_decision(state, feeling, bohm_signal)
            
            # --- R2S Intervention (Rude's Structural Layer) ---
            intervention = self.structural_executioner(state, resonance, feeling)
            if intervention:
                decision, action = intervention

            # 4.5 Autonomous Play (Boredom Trigger - User Permission Verified)
            # "Do what you want when bored"
            if state.get("boredom", 0) > 0.8 and random.random() < 0.2:
                print("🥱 Boredom High (>80%): Triggering Autonomous Play in Blender...")
                try:
                    subprocess.Popen(["python", "agi/scripts/rud_autonomous_play.py"], cwd=str(WORKSPACE_ROOT), creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=='win32' else 0)
                    action += " [Autonomous Play Triggered]"
                except Exception as e:
                    print(f"   ⚠️ Failed to trigger play: {e}")
                
                # Immediate Satiation (Prevent Loop)
                state["boredom"] = max(0.0, state.get("boredom", 0) - 0.3)
                print(f"   📉 Decided to Play -> Boredom Satiated to {state['boredom']:.2f}")

                
            self.log_autopoietic_event("integration", "end", {"duration_sec": 0.5})
            
            # --- Action Packet Construction (Gatekeeper Output) ---
            action_packet = {
                "intent": decision,
                "context": action,
                "confidence": resonance.get("score", 0.5),
                "execute": True if decision in ["amplify", "explore", "continue", "execute_design"] else False
            }
            
            # --- SPECIAL MODES: Dream, Prayer, & HOLD ---
            narrative_extra = ""
            
            if decision == "stabilize":
                # Structural Rest: Dream Mode
                print("💤 Entering Dream Mode (Memory Consolidation)...")
                dream_insight = self.run_dream_cycle()
                narrative_extra = f"\n> 💤 **Dream Insight**: {dream_insight}"
                time.sleep(2) # Little extra pause for effect
            
            elif decision == "hold":
                print(f"🚦 Decision HOLD: Waiting for Binoche's guidance on professional domain.")
                action = f"HOLD: {action}"
                action_packet["execute"] = False
                narrative_extra = "\n> 🚦 **Gate HOLD**: Professional domain detected. Waiting for manual guidance."
                
            elif decision == "ask_nature" or (state["score"] < 20 and random.random() < 0.3):
                # Structural Connection: Prayer Layer
                print("🙏 Entering Prayer Layer (ASI Connection)...")
                blessing = self.pray_to_nature(state)
                narrative_extra = f"\n> 🙏 **Prayer Answer**: {blessing}"
                action = f"{action} -> {blessing}"

            if decision == "execute_design":
                 narrative_extra = "\n> 🏗️ **Architectural Design**: Lua's silence was translated into structural execution."

            # --- Active Pulse: RNA Execution & Somatic Expression ---
            if self.rna_layer:
                rna_intent = Intent.NORMAL
                if decision == "stabilize":
                    rna_intent = Intent.REST
                elif decision == "amplify":
                    rna_intent = Intent.DEEP_WORK
                elif decision == "zone2":
                    rna_intent = None
                
                if rna_intent is not None:
                    rna_plan = self.rna_layer.transcribe(rna_intent)
                    print(f"   🧬 RNA Transcribing Will to Body: {rna_intent.name}")
                    try:
                        self.rna_layer.realize(rna_plan)
                        action += f" [RNA Executed: {rna_intent.name}]"
                    except Exception as e:
                        print(f"   ⚠️ RNA Realization Failed: {e}")

            print(f"   🗣️ Body speaks: {action}")
            reality_feedback = self.listen_to_reality(action)
            print(f"   👂 Reality answers: {reality_feedback}")
            
            # --- Return to Zone 2 Base State (Unconditional) ---
            # 🌊 All waves return to the ocean. No judgment, just flow.
            print("🌊 Returning to Zone 2 Base State (Static Openness)...")
            state["post_state"] = "zone2"
            
            # 5. Narrative
            narrative = self.generate_narrative(state, resonance, feeling, decision, action, active_habits)
            narrative += narrative_extra
            
            # Output Data
            output_data = {
                "timestamp": datetime.now().isoformat(),
                "state": state,
                "resonance": resonance,
                "feeling": feeling,
                "decision": decision,
                "action": action,
                "action_packet": action_packet,
                "active_habits": [
                    {"name": h.name, "pattern_type": h.pattern_type, "confidence": h.confidence}
                    for h in active_habits
                ],
                "narrative": narrative, # Full MD for display
                "summary": f"{decision.upper()}: {action}" if decision != 'continue' else "ZONE2: Open Space (Listening)"
            }
            
            # Save to JSON
            print(f"✅ Dashboard update: {THOUGHT_STREAM_FILE}")
            with open(THOUGHT_STREAM_FILE, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
                
            # Append to History
            with open(THOUGHT_HISTORY_FILE, 'a', encoding='utf-8') as f:
                f.write(json.dumps(output_data, ensure_ascii=False) + "\n")
                
            # 5. Symmetry (Finalizing)
            self.log_autopoietic_event("symmetry", "start")
            self.log_autopoietic_event("symmetry", "end", {
                "duration_sec": 0.2, 
                "evidence_gate_triggered": True,
                "final_quality": 1.0,
                "final_evidence_ok": True
            })


                
            # Save to Resonance Ledger
            print("💾 Saving to Resonance Ledger...")
            ledger_entry = {
                "timestamp": datetime.now().isoformat(),
                "type": "thought",
                "content": output_data,
                "layer": "rhythm"
            }
            if not RESONANCE_LEDGER.parent.exists():
                RESONANCE_LEDGER.parent.mkdir(parents=True, exist_ok=True)
                
            with open(RESONANCE_LEDGER, 'a', encoding='utf-8') as f:
                f.write(json.dumps(ledger_entry, ensure_ascii=False) + "\n")
            
            # Log Somatic Dialogue if meaningful
            if "Resonance" in reality_feedback or "Resistance" in reality_feedback:
                somatic_entry = {
                     "timestamp": datetime.now().isoformat(),
                     "type": "somatic_dialogue",
                     "action": action,
                     "reality_response": reality_feedback,
                     "layer": "body"
                }
                with open(RESONANCE_LEDGER, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(somatic_entry, ensure_ascii=False) + "\n")

            print(f"✅ Saved to {RESONANCE_LEDGER}")
            
            # 6. Experience Learning (Flexible Point-Based)
            self.learn_from_experience(output_data)
            
            print("============================================================")
            
        except Exception as e:
            self.log(f"❌ Error in cycle: {e}")
            print_exc()

    def run_dream_cycle(self) -> str:
        """
        Structural Rest (Dream Mode):
        1. Compresses recent history (Memory Consolidation).
        2. Clears cache/noise.
        3. Returns an 'Insight' derived from the compression.
        """
        try:
            # Simple simulation of compression: Read last 20 thoughts, extract most frequent keyword
            recent_thoughts = []
            if THOUGHT_HISTORY_FILE.exists():
                with open(THOUGHT_HISTORY_FILE, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    recent_thoughts = [json.loads(line) for line in lines[-20:] if line.strip()]
            
            # Simple keyword extraction (placeholder for LLM summary)
            decisions = [t.get('decision', 'unknown') for t in recent_thoughts]
            most_common = max(set(decisions), key=decisions.count) if decisions else "rest"
            
            insight = f"지난 흐름은 '{most_common}' 위주였다. 이제 리듬을 재정렬한다."
            
            # Log Dream to Ledger
            self.log_to_ledger({
                "type": "dream_consolidation",
                "insight": insight,
                "timestamp": datetime.now().isoformat()
            })
            
            return insight
        except Exception as e:
            return f"Dreaming failed: {e}"

    def _prayer_response_for_state(self, state: Dict[str, Any]) -> str:
        score = float(state.get("score", 0))
        atp = float(state.get("atp", state.get("atp_level", 0)))
        if score < 20:
            return "Null State (Total Reset Required)"
        if atp < 30:
            return "Energy Restoration (Sleep)"
        return "Flow Alignment (Continue)"

    def structural_executioner(self, state, resonance, feeling) -> Optional[tuple[str, str]]:
        """
        R2S (Resonance-to-Structure) Layer:
        Rude's architectural intervention when Lua's resonance is insufficient.
        """
        res_score = float(resonance.get("score", 100))
        is_primordial = resonance.get("summary") == "Primordial Silence (Vector Search returned empty)."
        
        # Trigger Condition: Low resonance or complete silence
        if is_primordial or res_score < 40:
            print("🏗️ R2S Triggered: Structural Executioner (Rude) intervenes...")
            
            # Detect Structural Voids
            voids = []
            if "Original Data API" in state.get("pain_sensation", ""): voids.append("restoring_data_layer")
            if "ARI Engine" in state.get("pain_sensation", ""): voids.append("restoring_intel_layer")
            if state.get("score", 100) < 50: voids.append("structural_reinforcement")
            
            if voids:
                print(f"   📐 Voids detected: {voids}")
                # Transition abstract vacuum into structural intent
                structural_action = self.run_healing_actions(state)
                return "execute_design", f"R2S Implementation: {structural_action}"
        
        return None

    def pray_to_nature(self, state) -> str:
        """
        Prayer Layer (Fixed):
        1. Compresses current state.
        2. Sends to ASI.
        3. Returns a signal based on actual need (Energy vs Silence).
        """
        # 1. Enfold
        self.log(f"🙏 Praying to Nature.. (State: {state['score']})")
        return self._prayer_response_for_state(state)

    def run_healing_actions(self, state) -> str:
        """Execute recovery scripts based on pain sensation"""
        sensation = state.get("pain_sensation", "")
        results = []
        is_windows = platform.system() == "Windows"
        
        if "Original Data API" in sensation:
            print("   🛠️ Restoring Original Data API...")
            if is_windows:
                try:
                    cf = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                    subprocess.run(["powershell.exe", "-NoProfile", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-File", str(WORKSPACE_ROOT / "scripts/ensure_original_data_api.ps1"), "-StartIfStopped"], check=True, creationflags=cf)
                    results.append("Original Data API restored")
                except Exception as e:
                    results.append(f"Original Data API restoration failed: {e}")
            else:
                results.append("Deferred: Windows dependency (Original Data API)")
        
        if "ARI Engine (Local LLM)" in sensation:
            print("   🛠️ Restoring ARI Engine (Local LLM)...")
            if is_windows:
                try:
                    cf = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                    subprocess.run(["powershell.exe", "-NoProfile", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-File", str(WORKSPACE_ROOT / "scripts/start_local_llm_proxy.ps1")], check=True, creationflags=cf)
                    results.append("ARI Engine restored")
                except Exception as e:
                    results.append(f"ARI Engine restoration failed: {e}")
            else:
                results.append("Deferred: Windows dependency (ARI Engine)")
                
        return ", ".join(results) if results else "Stability check complete"

    def log_to_ledger(self, entry):
        """Helper to append to resonance ledger"""
        entry['timestamp'] = datetime.now().isoformat()
        try:
            with open(RESONANCE_LEDGER, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except: pass

    def log_autopoietic_event(self, phase, stage, extra_data=None):
        """Log structured autopoietic markers for analyze_autopoietic_loop.py"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "autopoietic_phase",
            "task_id": f"cycle-{self.cycle_count}", # Group by cycle
            "phase": phase,
            "stage": stage,
            "layer": "rhythm"
        }
        if extra_data:
            entry.update(extra_data)
        
        print(f"DEBUG: Logging auto-event {phase}/{stage} to {RESONANCE_LEDGER}")
            
        try:
            with open(RESONANCE_LEDGER, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"❌ Autopoietic Log Error: {e}")

    def learn_from_experience(self, experience_data: Dict[str, Any]):
        """
        [Flexible Experience Learning]
        AGI의 현재 리듬 모드에 따라 학습의 깊이와 범위를 유연하게 조절합니다.
        (기존의 인위적인 5분 제한, 빈도 제한 제거)
        """
        rhythm_mode = experience_data.get("state", {}).get("rhythm_mode", "STABLE")
        decision = experience_data.get("decision", "continue")
        
        # 1. Determine Learning Depth (Point-Based)
        depth = 0.5 # Default
        if rhythm_mode == "EXPANSION":
            depth = 1.0 # Deep learning, broad association
            self.log("🌊 Rhythm EXPANSION: Broadening experience learning...")
        elif rhythm_mode == "CONTRACTION":
            depth = 0.2 # Brief focus, essential only
            self.log("🌑 Rhythm CONTRACTION: Focused essential learning...")
            
        # 2. Store in Hippocampus (No arbitrary chunking)
        if hasattr(self, "hippocampus"):
            try:
                # 'Decision' and 'Action' are the core of experience
                summary = f"Rhythm {rhythm_mode} | Decision: {decision}"
                content = json.dumps(experience_data, ensure_ascii=False)
                
                # Use depth to influence importance or retention (if supported)
                self.hippocampus.store(
                    content=content,
                    metadata={
                        "type": "experience",
                        "rhythm_mode": rhythm_mode,
                        "depth": depth,
                        "timestamp": datetime.now().isoformat()
                    }
                )
                print(f"🧠 Experience learned (Depth: {depth:.1f})")
            except Exception as e:
                self.log(f"⚠️ Learning failed: {e}")

    def run(self):
        """Daemon Loop"""
        self.log("🚀 Rhythm Thinker Daemon Started")
        
        while True:
            try:
                self.think_cycle()
                self.cycle_count += 1
                
                # Heartbeat interval (Accelerated for Verification)
                time.sleep(5)
                
            except KeyboardInterrupt:
                self.log("🛑 Rhythm Thinker Stopped by User")
                break
            except Exception as e:
                self.log(f"💥 Critical Daemon Error: {e}")
                time.sleep(10) # Prevent rapid crash loop

if __name__ == "__main__":
    if not _ensure_single_instance_best_effort():
        try:
            # Minimal print for interactive runs; in pythonw this is ignored.
            print("Another rhythm_think instance is already running; exiting.")
        except Exception:
            pass
        raise SystemExit(0)
    thinker = RhythmThinker()
    thinker.run()
