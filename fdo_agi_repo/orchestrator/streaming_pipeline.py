"""
파동적 Pipeline: Streaming 중 다음 단계를 미리 준비
"멍한 존2 상태" - 연속적 흐름

편도체-mPFC 통합:
- 두려움 신호 감지 및 조절
- 적응적 파라미터 조정
"""

from __future__ import annotations
import time
import threading
from typing import Dict, Any, Optional, List
from queue import Queue

try:
    from fdo_agi_repo.orchestrator.contracts import TaskSpec, PersonaOutput
    from fdo_agi_repo.personas.thesis import run_thesis
    from fdo_agi_repo.personas.antithesis import run_antithesis
    from fdo_agi_repo.personas.synthesis import run_synthesis
    from fdo_agi_repo.orchestrator.memory_bus import append_ledger
    from fdo_agi_repo.orchestrator.amygdala import estimate_fear_level, get_fear_context
    from fdo_agi_repo.orchestrator.prefrontal import regulate_fear_response
    from fdo_agi_repo.orchestrator.rhythm_controller import estimate_signals, map_to_params
except ModuleNotFoundError:
    from orchestrator.contracts import TaskSpec, PersonaOutput  # type: ignore
    from personas.thesis import run_thesis  # type: ignore
    from personas.antithesis import run_antithesis  # type: ignore
    from personas.synthesis import run_synthesis  # type: ignore
    from orchestrator.memory_bus import append_ledger  # type: ignore
    from orchestrator.amygdala import estimate_fear_level, get_fear_context  # type: ignore
    from orchestrator.prefrontal import regulate_fear_response  # type: ignore
    from orchestrator.rhythm_controller import estimate_signals, map_to_params  # type: ignore


class StreamingBuffer:
    """Thesis Streaming 중 텍스트를 버퍼링"""
    def __init__(self):
        self.chunks: List[str] = []
        self.complete = False
        self.threshold_reached = False
        self.threshold_pct = 0.5  # 50% 도달 시 Antithesis 시작
    
    def add_chunk(self, chunk: str):
        self.chunks.append(chunk)
        # 임계값 체크 (예: 500자 이상)
        if not self.threshold_reached and len("".join(self.chunks)) >= 500:
            self.threshold_reached = True
    
    def get_partial_text(self) -> str:
        return "".join(self.chunks)
    
    def finalize(self):
        self.complete = True

_ACTIVE_TASKS: Dict[str, float] = {}


def run_streaming_thesis_with_callback(
    task: TaskSpec,
    plan: Dict[str, Any],
    tools,
    buffer: StreamingBuffer,
    conversation_context: str = ""
) -> PersonaOutput:
    """
    Thesis를 실행하되, Streaming 중 buffer에 텍스트 누적
    """
    # 기존 run_thesis와 동일하지만, Streaming 중 buffer.add_chunk() 호출
    # Background observer: when buffer crosses threshold, emit prefetch intent
    def _prefetch_observer():
        fired = False
        for _ in range(200):  # ~10s @50ms
            if buffer.threshold_reached and not fired:
                fired = True
                try:
                    append_ledger({
                        "event": "antithesis_prefetch_hint",
                        "task_id": getattr(task, "task_id", None),
                        "note": "Streaming 50% threshold reached; safe prefetch point.",
                    })
                except Exception:
                    pass
                break
            if buffer.complete:
                break
            time.sleep(0.05)
    try:
        threading.Thread(target=_prefetch_observer, daemon=True).start()
    except Exception:
        pass
    # 현재는 간단히 기존 함수 호출 후 buffer에 복사
    result = run_thesis(task, plan, tools, conversation_context)
    
    # TODO: 실제로는 thesis.py를 수정하여 Streaming 중 callback 호출
    buffer.add_chunk(result.summary)
    buffer.finalize()
    
    return result


def run_wave_pipeline(
    task: TaskSpec,
    plan: Dict[str, Any],
    tools,
    conversation_context: str = ""
) -> Dict[str, Any]:
    """
    파동적 Pipeline: Thesis Streaming 중 Antithesis 준비
    
    Returns:
        결과 + 타이밍 정보
    """
    t_start = time.perf_counter()

    # Prevent accidental double-execution in the same process (best-effort)
    if task and getattr(task, "task_id", None):
        tid = str(task.task_id)
        if tid in _ACTIVE_TASKS:
            append_ledger({
                "event": "wave_guard_blocked",
                "task_id": tid,
                "note": "duplicate invocation prevented"
            })
            return {
                "task_id": tid,
                "summary": "[wave] duplicate invocation prevented by guard",
                "citations": [],
                "notes": "wave_pipeline_guard",
                "timing": {"thesis": 0.0, "antithesis": 0.0, "synthesis": 0.0, "total": 0.0},
            }
        _ACTIVE_TASKS[tid] = t_start

    # Amygdala → mPFC → RhythmController 통합
    try:
        # 1) 편도체: 두려움 신호 감지
        fear_level = estimate_fear_level(window=1000)
        fear_ctx = get_fear_context(fear_level)
        
        # 2) mPFC: 두려움 조절 및 행동 게이트 결정
        context = {
            "is_critical": getattr(task, "priority", "normal") == "high",
            "has_backup": True,  # 현재는 항상 백업 가능 가정
            "recent_success_rate": 0.7,  # TODO: 실제 통계에서 계산
        }
        prefrontal_decision = regulate_fear_response(fear_level, context)
        
        # 3) RhythmController: 신호 추정 및 fear 통합
        signals = estimate_signals()
        rhythm_params, hint = map_to_params(signals, fear_level=prefrontal_decision.modulated_fear)
        
        # 4) 행동 게이트 체크
        action_gate = prefrontal_decision.action_gate
        
        if action_gate == "pause":
            append_ledger({
                "event": "wave_pipeline_paused",
                "task_id": getattr(task, "task_id", None),
                "fear_level": fear_level,
                "modulated_fear": prefrontal_decision.modulated_fear,
                "reasoning": prefrontal_decision.reasoning,
                "level": "warning"
            })
            # 일시 정지 후 재개 (안전한 방식)
            pause_duration = prefrontal_decision.behavioral_adjustments.get("pause_duration", 3.0)
            time.sleep(pause_duration)
            
        elif action_gate == "safe_mode":
            append_ledger({
                "event": "wave_pipeline_safe_mode",
                "task_id": getattr(task, "task_id", None),
                "fear_level": fear_level,
                "reasoning": prefrontal_decision.reasoning,
                "level": "error"
            })
            # 안전 모드: 최소 동작만 수행
            if task and getattr(task, "task_id", None):
                _ACTIVE_TASKS.pop(str(task.task_id), None)
            return {
                "task_id": getattr(task, "task_id", None),
                "summary": f"[safe_mode] {prefrontal_decision.reasoning}",
                "citations": [],
                "notes": "safe_mode_activated",
                "timing": {"thesis": 0.0, "antithesis": 0.0, "synthesis": 0.0, "total": 0.0},
            }
        
        # 5) ToolRegistry에 최적화 힌트 적용
        if hasattr(tools, "set_optimization_hint"):
            try:
                # 행동 조정 사항 병합
                merged_hint = {**hint, **prefrontal_decision.behavioral_adjustments}
                tools.set_optimization_hint(merged_hint)
            except Exception:
                pass
        
        # 6) Ledger에 기록
        append_ledger({
            "event": "amygdala_mpfc_rhythm",
            "task_id": getattr(task, "task_id", None),
            "fear_level": fear_level,
            "fear_state": fear_ctx["state"],
            "modulated_fear": prefrontal_decision.modulated_fear,
            "action_gate": action_gate,
            "reasoning": prefrontal_decision.reasoning,
            "rhythm_params": rhythm_params,
            "signals": signals,
            "hint": {k: hint[k] for k in ("preferred_channels","should_throttle_offpeak","batch_compression_level","theta_overlap") if k in hint},
        })
    except Exception as e:
        # 실패 시 기본 동작
        append_ledger({
            "event": "amygdala_mpfc_fallback",
            "task_id": getattr(task, "task_id", None),
            "error": str(e),
            "level": "warning"
        })
        # 기본값으로 진행
        signals = {"D": 0.5, "S": 0.5, "O": 0.5}
        rhythm_params, hint = map_to_params(signals, fear_level=0.35)
        append_ledger({
            "event": "rhythm_params_error",
            "task_id": getattr(task, "task_id", None),
            "error": f"{type(e).__name__}: {e}"
        })
    
    # 1. Thesis 시작 (Streaming)
    append_ledger({"event": "wave_thesis_start", "task_id": task.task_id})
    buffer = StreamingBuffer()
    
    t0 = time.perf_counter()
    out_thesis = run_streaming_thesis_with_callback(task, plan, tools, buffer, conversation_context)
    t1 = time.perf_counter()
    
    append_ledger({
        "event": "wave_thesis_end",
        "task_id": task.task_id,
        "duration_sec": float(t1 - t0)
    })
    
    # 2. Antithesis (Thesis 완료 후 즉시)
    append_ledger({"event": "wave_antithesis_start", "task_id": task.task_id})
    t2 = time.perf_counter()
    out_anti = run_antithesis(task, out_thesis, tools, conversation_context)
    t3 = time.perf_counter()
    
    append_ledger({
        "event": "wave_antithesis_end",
        "task_id": task.task_id,
        "duration_sec": float(t3 - t2)
    })
    
    # 3. Synthesis
    append_ledger({"event": "wave_synthesis_start", "task_id": task.task_id})
    t4 = time.perf_counter()
    out_synth = run_synthesis(task, [out_thesis, out_anti], tools, conversation_context)
    t5 = time.perf_counter()
    
    append_ledger({
        "event": "wave_synthesis_end",
        "task_id": task.task_id,
        "duration_sec": float(t5 - t4)
    })
    
    t_end = time.perf_counter()
    
    # 타이밍 정보
    timing = {
        "thesis": t1 - t0,
        "antithesis": t3 - t2,
        "synthesis": t5 - t4,
        "total": t_end - t_start
    }
    
    result = {
        "task_id": task.task_id,
        "summary": out_synth.summary,
        "citations": out_synth.citations,
        "notes": "wave_pipeline",
        "timing": timing
    }
    
    append_ledger({
        "event": "wave_pipeline_complete",
        "task_id": task.task_id,
        "timing": timing
    })
    
    # Clear re-entrancy guard
    try:
        if task and getattr(task, "task_id", None):
            _ACTIVE_TASKS.pop(str(task.task_id), None)
    except Exception:
        pass

    return result


# TODO Phase 2: 실제 Streaming 중 Antithesis를 "준비"하는 버전
# - Thesis가 50% 진행 시 Antithesis용 RAG 미리 조회
# - Thesis 완료 즉시 Antithesis LLM 호출
# - 예상 개선: 30-40% (오버랩으로 0.5-1s 절약)
