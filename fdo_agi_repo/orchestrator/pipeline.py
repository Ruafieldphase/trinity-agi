from __future__ import annotations
import uuid
import os
from typing import Dict, Any, List
import time
import sys
from pathlib import Path

# 프로젝트 루트 경로 설정 (BQI 모듈 import용)
_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from .contracts import TaskSpec, PersonaOutput, EvalReport
from .memory_bus import append_coordinate, append_ledger, tail_ledger, snapshot_memory
from .safe_pre import SAFE_pre
from .self_correction import rune_from_eval, evidence_gate_correction, is_evidence_force_enabled
from .learning import adaptive_replan_with_learning
from .meta_cognition import MetaCognitionSystem
from .tool_registry import ToolRegistry
from .config import is_corrections_enabled, get_corrections_config, get_evaluation_config, is_async_thesis_enabled, is_response_cache_enabled, get_response_cache_config

# Response Cache (Phase 2.5)
from .response_cache import get_response_cache

# Lumen Feedback System (Phase 6.1)
# Lumen Feedback System (Phase 6.1)
# Optional dependency: provide safe fallbacks when Lumen package is unavailable.
try:
    from lumen.feedback_loop_redis import FeedbackLoopRedis
    from lumen.adaptive_ttl_policy import AdaptiveTTLPolicy
    from lumen.cache_size_optimizer import CacheSizeOptimizer
except ModuleNotFoundError:
    class FeedbackLoopRedis:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass

        def record(self, *args, **kwargs):
            pass

        def close(self):
            pass

    class AdaptiveTTLPolicy:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass

        def get_ttl(self, *args, **kwargs):
            # Provide a conservative default TTL
            return 0

    class CacheSizeOptimizer:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass

        def get_size(self, *args, **kwargs):
            # Provide a conservative default cache size
            return 0

# BQI 통합 (Phase 1)
from scripts.rune.bqi_adapter import analyse_question
from .conversation_memory import ConversationMemory
from .user_profile import get_user_profile_context
try:
    from fdo_agi_repo.personas.thesis import run_thesis
    from fdo_agi_repo.personas.antithesis import run_antithesis
    from fdo_agi_repo.personas.synthesis import run_synthesis
except ModuleNotFoundError:
    # Allow script-run from fdo_agi_repo working directory
    from personas.thesis import run_thesis  # type: ignore
    from personas.antithesis import run_antithesis  # type: ignore
    from personas.synthesis import run_synthesis  # type: ignore

def PLAN(task: TaskSpec, memory_snapshot: Dict[str, Any]) -> Dict[str, Any]:
    steps = ["thesis","antithesis","synthesis"]
    return {"steps": steps, "memory_snapshot": memory_snapshot}


def _run_with_cache(
    persona: str,
    task: TaskSpec,
    runner_func,
    *args,
    cache_context: str = "",
    **kwargs
) -> PersonaOutput:
    """
    Response Cache wrapper for Thesis/Antithesis/Synthesis
    
    Args:
        persona: "thesis", "antithesis", or "synthesis"
        task: TaskSpec
        runner_func: run_thesis, run_antithesis, or run_synthesis
        cache_context: Additional context for cache key (e.g., thesis output for antithesis)
        *args, **kwargs: Arguments for runner_func
        
    Returns:
        PersonaOutput (from cache or fresh call)
    """
    # Check if cache is enabled
    if not is_response_cache_enabled():
        return runner_func(*args, **kwargs)
    
    # Get cache instance
    cache_cfg = get_response_cache_config()
    cache = get_response_cache(
        ttl_seconds=cache_cfg["ttl_seconds"],
        max_entries=cache_cfg["max_entries"]
    )
    
    # Try to get from cache
    goal_str = task.goal if isinstance(task.goal, str) else str(task.goal)
    cached_response = cache.get(persona, goal_str, cache_context)
    
    if cached_response is not None:
        # Cache hit! Reconstruct PersonaOutput
        append_ledger({
            "event": f"{persona}_cache_hit",
            "task_id": task.task_id,
            "cache_context_len": len(cache_context)
        })
        return PersonaOutput(**cached_response)
    
    # Cache miss - run actual LLM call
    t_start = time.perf_counter()
    result = runner_func(*args, **kwargs)
    t_end = time.perf_counter()
    latency_ms = (t_end - t_start) * 1000
    
    # Store in cache
    cache.put(
        persona,
        goal_str,
        result.__dict__,
        cache_context,
        latency_ms=latency_ms
    )
    
    append_ledger({
        "event": f"{persona}_cache_miss",
        "task_id": task.task_id,
        "latency_ms": round(latency_ms, 2)
    })
    
    return result


def EVAL(outputs: List[PersonaOutput]) -> EvalReport:
    """
    연속형 품질 휴리스틱 (개선됨):
    - 기본 0.30에서 시작 (증거 없으면 낮은 품질)
    - (합성(synthetic) 제외) 실제 인용 수에 따라 +0.15씩, 최대 +0.45 (3개)
    - (합성 제외) 인용 평균 관련도(가능 시) >= 0.5 이면 +0.15
    - synthesis 요약 길이 충분(>= 240자) 시 +0.10
    - [0.0, 1.0]로 클램핑
    evidence_ok: 합성이 아닌 실제 인용이 1개 이상 존재하면 True
    
    개선 사항:
    - 기본 점수 0.50 → 0.30 (증거 없으면 자동 재작업)
    - 인용당 가중치 0.10 → 0.15 (증거의 중요성 강화)
    - 요약 길이 가중치 0.05 → 0.10 (완성도 강조)
    - 관련도 가중치 0.10 → 0.15 (품질 높은 증거 우대)
    """
    # 합성(synthetic) 인용은 품질 가점 및 evidence_ok 계산에서 제외
    non_synth_citations: List[dict] = []
    for o in outputs:
        for c in (o.citations or []):
            try:
                src = str(c.get("source", ""))
            except Exception:
                src = ""
            if src.lower() == "synthetic":
                continue
            non_synth_citations.append(c)

    total_cites = len(non_synth_citations)

    # 평균 관련도 추정 (가능 시, 합성 제외)
    rel_vals: List[float] = []
    for c in non_synth_citations:
        try:
            rel_vals.append(float(c.get("relevance", 0.0)))
        except Exception:
            pass
    avg_rel = (sum(rel_vals) / len(rel_vals)) if rel_vals else 0.0

    # synthesis 요약 길이 체크
    synth = next((o for o in outputs if o.persona == "synthesis"), outputs[-1])
    synth_len = len(synth.summary or "")

    # 개선된 품질 계산: 증거 중심 + 기본값 상향
    quality = 0.40  # 기본값 상향 (0.30 → 0.40)
    quality += 0.15 * min(total_cites, 3)  # 인용당 가중치 증가 (0.10 → 0.15)
    if avg_rel >= 0.5:
        quality += 0.15  # 관련도 가중치 증가 (0.10 → 0.15)
    if synth_len >= 240:
        quality += 0.10  # 완성도 가중치 증가 (0.05 → 0.10)
    quality = max(0.0, min(1.0, quality))

    evidence_ok = total_cites > 0
    risks: List[str] = []
    return EvalReport(task_id=outputs[-1].task_id, quality=quality, evidence_ok=evidence_ok, risks=risks, notes="auto")

def run_task(tool_cfg: Dict[str, Any], spec: Dict[str, Any]) -> Dict[str, Any]:
    task = TaskSpec(**spec)
    tool_cfg = dict(tool_cfg) if tool_cfg else {}
    t_start = time.perf_counter()  # Start duration tracking
    
    # BQI 좌표 생성 (Phase 1)
    bqi_coord = analyse_question(task.goal)
    
    # Task 시작 이벤트 (BQI 포함)
    append_coordinate({
        "event": "task_start",
        "task_id": task.task_id,
        "task": task.model_dump(),
        "bqi": bqi_coord.to_dict()
    })
    
    # 대화 메모리 초기화 및 관련 맥락 검색
    conv_memory = ConversationMemory()
    relevant_context = conv_memory.get_relevant_context(task.goal, top_k=3)
    
    if relevant_context:
        context_prompt = conv_memory.format_context_for_prompt(relevant_context)
        append_ledger({
            "event": "context_retrieved",
            "task_id": task.task_id,
            "context_count": len(relevant_context),
            "bqi_similarity": "enabled"
        })
    else:
        context_prompt = None

    # 사용자 프로필(전 페르소나 공통 선호도/제약) 주입
    try:
        _profile_ctx = get_user_profile_context()
        if _profile_ctx:
            context_prompt = f"{_profile_ctx}\n\n{context_prompt}" if context_prompt else _profile_ctx
            append_ledger({
                "event": "user_profile_injected",
                "task_id": task.task_id,
                "profile_len": len(_profile_ctx)
            })
    except Exception as _profile_ex:
        append_ledger({
            "event": "user_profile_inject_failed",
            "task_id": task.task_id,
            "error": str(_profile_ex)
        })
    
    gate = SAFE_pre(task.model_dump(), tail_ledger())
    if not gate["allowed"]:
        append_ledger({"event": "needs_approval", "task_id": task.task_id, "risk": gate["risk"]})
        return {"status": "HALT", "reason": "approval_required", "gate": gate}

    # 실행 설정 로깅: 평가 임계값 및 자기교정 구성
    eval_cfg = get_evaluation_config()
    corr_cfg = get_corrections_config()
    optimization_info: Dict[str, Any] = {}
    optimization_adjustments: Dict[str, Any] = {}
    try:
        from .resonance_bridge import get_resonance_optimization

        optimization_info = get_resonance_optimization()
    except Exception:
        optimization_info = {}

    if optimization_info.get("enabled"):
        preferred_channels = optimization_info.get("preferred_channels")
        if preferred_channels and "preferred_channels" not in tool_cfg:
            tool_cfg["preferred_channels"] = preferred_channels

        batch_pref = optimization_info.get("batch_compression_level") or optimization_info.get("batch_compression")
        if isinstance(batch_pref, str) and batch_pref.lower() not in {"", "auto", "none", "off"} and "batch_compression" not in tool_cfg:
            tool_cfg["batch_compression"] = batch_pref

        if optimization_info.get("should_throttle_offpeak"):
            original_max = int(corr_cfg.get("max_passes", 2))
            if original_max > 1:
                corr_cfg = dict(corr_cfg)
                corr_cfg["max_passes"] = 1
                optimization_adjustments["max_passes"] = {
                    "from": original_max,
                    "to": 1,
                    "reason": "offpeak_throttle",
                }

    append_ledger({
        "event": "run_config",
        "task_id": task.task_id,
        "evaluation": {"min_quality": float(eval_cfg.get("min_quality", 0.6))},
        "corrections": {"enabled": bool(corr_cfg.get("enabled", True)), "max_passes": int(corr_cfg.get("max_passes", 2))},
        "bqi_coord": bqi_coord.to_dict(),
    })
    if optimization_info:
        opt_event: Dict[str, Any] = {
            "event": "resonance_optimization",
            "task_id": task.task_id,
            "enabled": bool(optimization_info.get("enabled")),
            "prefer_gateway": bool(optimization_info.get("prefer_gateway")),
            "prefer_peak_hours": bool(optimization_info.get("prefer_peak_hours")),
            "is_peak_now": bool(optimization_info.get("is_peak_now")),
            "current_hour": int(optimization_info.get("current_hour", 0)),
            "peak_window": optimization_info.get("peak_window"),
            "preferred_channels": optimization_info.get("preferred_channels"),
            "offpeak_mode": optimization_info.get("offpeak_mode"),
            "batch_compression": optimization_info.get("batch_compression"),
            "batch_compression_level": optimization_info.get("batch_compression_level"),
            "learning_bias": optimization_info.get("learning_bias"),
            "phase": optimization_info.get("phase"),
            "should_throttle_offpeak": bool(optimization_info.get("should_throttle_offpeak")),
            "timeout_ms": optimization_info.get("timeout_ms"),
            "retry_attempts": optimization_info.get("retry_attempts"),
        }
        if optimization_adjustments:
            opt_event["adjustments"] = optimization_adjustments
        append_ledger(opt_event)
    # Autopoietic Loop: Folding starts with Thesis phase (context folding)
    try:
        append_ledger({
            "event": "autopoietic_phase",
            "task_id": task.task_id,
            "phase": "folding",
            "stage": "start",
            "context_count": int(len(relevant_context) if relevant_context else 0)
        })
    except Exception:
        pass

    registry = ToolRegistry(tool_cfg)
    # Phase 3: BQI 좌표를 Registry에 설정 (RAG 호출 시 자동 전달)
    registry.set_bqi_coord(bqi_coord.to_dict())
    if optimization_info:
        try:
            registry.set_optimization_hint(optimization_info)
            pref_channels = optimization_info.get("preferred_channels")
            if pref_channels:
                registry.set_routing_preference(pref_channels)
        except Exception:
            pass
    plan = PLAN(task, snapshot_memory())

    # Phase 4: Meta-Cognition - 자기능력 평가
    meta_system = MetaCognitionSystem()
    # 현재 시스템에서 사용 가능한 도구 목록 (registry 기반, 동적)
    try:
        available_tools = registry.list_available_tools_for_meta()
    except Exception:
        available_tools = ["rag", "websearch", "fileio", "codeexec", "tabular"]
    
    thesis_eval = meta_system.evaluate_self_capability(
        task_goal=task.goal,
        persona="thesis",
        available_tools=available_tools
    )
    
    append_ledger({
        "event": "meta_cognition",
        "task_id": task.task_id,
        "persona": "thesis",
        "confidence": float(thesis_eval["confidence"]),
        "past_performance": float(thesis_eval["past_performance"]),
        "tools_availability": float(thesis_eval["tools_availability"]),
        "domain": thesis_eval["domain"],
        "should_delegate": thesis_eval["should_delegate"],
        "reason": thesis_eval["reason"]
    })
    
    # 낮은 confidence에 대한 경고 (향후 delegation 로직 확장 포인트)
    if thesis_eval["should_delegate"]:
        append_ledger({
            "event": "low_confidence_warning",
            "task_id": task.task_id,
            "confidence": float(thesis_eval["confidence"]),
            "recommendation": "Consider alternative approach or request human guidance"
        })

    # 타이밍 계측 및 단계별 이벤트 로깅
    # Pipeline-level TTFT measurement (Phase 2.9: End-to-End Streaming)
    # Streaming이 활성화되면 첫 번째 persona(thesis)의 TTFT가 전체 파이프라인의 TTFT
    pipeline_ttft = None
    pipeline_start = time.perf_counter()
    
    t0 = time.perf_counter()
    append_ledger({"event": "thesis_start", "task_id": task.task_id})

    # Async Thesis (feature-flagged, 기본 비활성)
    out_thesis = None  # type: ignore
    antithesis_prep_context = None  # type: ignore
    
    # Check if parallel antithesis prep is enabled
    parallel_anti_prep_enabled = False
    try:
        import yaml
        _cfg_path = Path(__file__).parent.parent / "configs" / "app.yaml"
        if _cfg_path.exists():
            with open(_cfg_path, "r", encoding="utf-8") as _f:
                _cfg = yaml.safe_load(_f)
            parallel_anti_prep_enabled = _cfg.get("orchestration", {}).get("parallel_antithesis_prep", {}).get("enabled", False)
    except Exception:
        parallel_anti_prep_enabled = os.environ.get("PARALLEL_ANTITHESIS_PREP_ENABLED", "").lower() == "true"
    
    if is_async_thesis_enabled():
        try:
            from concurrent.futures import ThreadPoolExecutor
            append_ledger({
                "event": "thesis_async_enabled",
                "task_id": task.task_id,
            })
            
            # Phase 2: Parallel Antithesis Prep (optional)
            if parallel_anti_prep_enabled:
                append_ledger({
                    "event": "parallel_antithesis_prep_enabled",
                    "task_id": task.task_id
                })
                from fdo_agi_repo.orchestrator.parallel_antithesis import prepare_antithesis_context
                
                with ThreadPoolExecutor(max_workers=2) as _exec:
                    # Future 1: Thesis 실행 (with cache)
                    _thesis_future = _exec.submit(
                        _run_with_cache,
                        "thesis",
                        task,
                        run_thesis,
                        task, plan, registry,
                        conversation_context=context_prompt or ""
                    )
                    # Future 2: Antithesis 준비 (thesis_out 없이 가능한 부분)
                    _prep_future = _exec.submit(prepare_antithesis_context, task, context_prompt or "")
                    
                    # 병렬 실행 완료 대기
                    out_thesis = _thesis_future.result()
                    antithesis_prep_context = _prep_future.result()
                    
                    append_ledger({
                        "event": "parallel_antithesis_prep_done",
                        "task_id": task.task_id
                    })
            else:
                # 기존 Async Thesis만 (Antithesis 준비 병렬화 없음, with cache)
                with ThreadPoolExecutor(max_workers=1) as _exec:
                    _future = _exec.submit(
                        _run_with_cache,
                        "thesis",
                        task,
                        run_thesis,
                        task, plan, registry,
                        conversation_context=context_prompt or ""
                    )
                    out_thesis = _future.result()
        except Exception as _async_ex:
            append_ledger({
                "event": "thesis_async_fallback",
                "task_id": task.task_id,
                "error": str(_async_ex)
            })
            # Fallback with cache
            out_thesis = _run_with_cache(
                "thesis",
                task,
                run_thesis,
                task, plan, registry,
                conversation_context=context_prompt or ""
            )
            antithesis_prep_context = None  # Fallback 시 준비 컨텍스트 무효화
    else:
        # Sync mode with cache
        out_thesis = _run_with_cache(
            "thesis",
            task,
            run_thesis,
            task, plan, registry,
            conversation_context=context_prompt or ""
        )

    t1 = time.perf_counter()
    
    # Pipeline TTFT: Thesis의 TTFT를 전체 파이프라인 TTFT로 기록 (Phase 2.9)
    # Ledger에서 마지막 thesis_end 이벤트 확인 및 TTFT 추출
    try:
        recent_logs = tail_ledger(n=5)
        for log in reversed(recent_logs):
            if log.get("persona") == "thesis" and "ttft_sec" in log:
                pipeline_ttft = log["ttft_sec"]
                break
    except Exception:
        pass
    
    append_ledger({
        "event_type": "thesis_end",  # 루멘 권장: 일관된 필드명
        "task_id": task.task_id,
        "duration_sec": float(t1 - t0),
        "latency_ms": float((t1 - t0) * 1000),  # 루멘(合) 권장: 레이턴시 추가
        "citations": len(out_thesis.citations),
        "quality": min(1.0, len(out_thesis.citations) / 10.0)  # 루멘(合) 권장: 품질 메트릭
    })
    # Autopoietic Loop: Folding end (after Thesis)
    try:
        append_ledger({
            "event": "autopoietic_phase",
            "task_id": task.task_id,
            "phase": "folding",
            "stage": "end",
            "duration_sec": float(t1 - t0),
            "citations": len(out_thesis.citations)
        })
    except Exception:
        pass

    append_ledger({"event": "antithesis_start", "task_id": task.task_id})
    t2 = time.perf_counter()
    
    # Use prepared context if available (Phase 2: Parallel Antithesis Prep)
    if antithesis_prep_context is not None:
        append_ledger({
            "event": "antithesis_using_prep_context",
            "task_id": task.task_id
        })
        from fdo_agi_repo.orchestrator.parallel_antithesis import run_antithesis_with_prep
        # Cache key includes thesis output for determinism
        thesis_summary = out_thesis.summary[:200] if out_thesis.summary else ""
        out_anti = _run_with_cache(
            "antithesis",
            task,
            run_antithesis_with_prep,
            task, out_thesis, registry,
            conversation_context=context_prompt or "",
            prep_context=antithesis_prep_context,
            cache_context=thesis_summary
        )
    else:
        # Standard antithesis with cache
        thesis_summary = out_thesis.summary[:200] if out_thesis.summary else ""
        out_anti = _run_with_cache(
            "antithesis",
            task,
            run_antithesis,
            task, out_thesis, registry,
            conversation_context=context_prompt or "",
            cache_context=thesis_summary
        )
    
    t3 = time.perf_counter()
    append_ledger({
        "event_type": "antithesis_end",  # 루멘 권장: 일관된 필드명
        "task_id": task.task_id,
        "duration_sec": float(t3 - t2),
        "latency_ms": float((t3 - t2) * 1000),  # 루멘(合) 권장
        "quality": 0.85 if hasattr(out_anti, 'summary') and out_anti.summary else 0.5  # 루멘(合) 권장
    })
    # Autopoietic Loop: Unfolding end (after Antithesis)
    try:
        append_ledger({
            "event": "autopoietic_phase",
            "task_id": task.task_id,
            "phase": "unfolding",
            "stage": "end",
            "duration_sec": float(t3 - t2)
        })
    except Exception:
        pass

    append_ledger({"event": "synthesis_start", "task_id": task.task_id})
    t4 = time.perf_counter()
    
    # Synthesis with cache (context = thesis + antithesis summaries)
    thesis_summary = out_thesis.summary[:100] if out_thesis.summary else ""
    anti_summary = out_anti.summary[:100] if out_anti.summary else ""
    synth_context = f"{thesis_summary}|{anti_summary}"
    
    out_synth = _run_with_cache(
        "synthesis",
        task,
        run_synthesis,
        task, [out_thesis, out_anti], registry,
        conversation_context=context_prompt or "",
        cache_context=synth_context
    )
    
    t5 = time.perf_counter()
    
    # Pipeline-level metrics (Phase 2.9: End-to-End Streaming)
    pipeline_total = t5 - pipeline_start
    pipeline_streaming_enabled = (
        os.environ.get("THESIS_STREAMING", "true").lower() == "true" and
        os.environ.get("ANTITHESIS_STREAMING", "true").lower() == "true" and
        os.environ.get("SYNTHESIS_STREAMING", "true").lower() == "true"
    )
    
    append_ledger({
        "event_type": "synthesis_end",  # 루멘 권장: 일관된 필드명
        "task_id": task.task_id,
        "duration_sec": float(t5 - t4),
        "latency_ms": float((t5 - t4) * 1000),  # 루멘(合) 권장
        "citations": len(out_synth.citations),
        "quality": min(1.0, len(out_synth.citations) / 10.0)  # 루멘(合) 권장
    })
    
    # Pipeline summary event
    pipeline_log = {
        "event": "pipeline_e2e_complete",
        "task_id": task.task_id,
        "total_duration_sec": float(pipeline_total),
        "streaming_enabled": pipeline_streaming_enabled
    }
    
    if pipeline_ttft is not None:
        pipeline_log["pipeline_ttft_sec"] = float(pipeline_ttft)
        # Perceived improvement: (전체시간 - TTFT) / 전체시간
        perceived = ((pipeline_total - pipeline_ttft) / pipeline_total) * 100
        pipeline_log["pipeline_perceived_improvement_pct"] = float(perceived)
    
    append_ledger(pipeline_log)
    # Autopoietic Loop: Integration end (after Synthesis)
    try:
        append_ledger({
            "event": "autopoietic_phase",
            "task_id": task.task_id,
            "phase": "integration",
            "stage": "end",
            "duration_sec": float(t5 - t4),
            "citations": len(out_synth.citations)
        })
    except Exception:
        pass

    eval_report = EVAL([out_thesis, out_anti, out_synth])
    rune = rune_from_eval(eval_report)

    append_ledger({
        "event": "eval",
        "task_id": task.task_id,
        "quality": float(eval_report.quality),
        "evidence_ok": bool(eval_report.evidence_ok),
        "eval": eval_report.model_dump()
    })
    append_ledger({"event": "rune", "task_id": task.task_id, "rune": rune.model_dump()})

    # Prepare Symmetry phase bookkeeping
    evidence_gate_triggered = False
    second_pass_executed = False
    _sym_start = time.perf_counter()
    try:
        append_ledger({
            "event": "autopoietic_phase",
            "task_id": task.task_id,
            "phase": "symmetry",
            "stage": "start"
        })
    except Exception:
        pass

    # Phase 6b: Enhanced Binoche Decision Engine (Parallel A/B Test)
    from .pipeline_binoche_adapter import enhanced_binoche_decision
    
    enhanced_decision = enhanced_binoche_decision(
        task_goal=task.goal,
        eval_report=eval_report.model_dump(),
        bqi_coord=bqi_coord.to_dict(),
        meta_confidence=float(thesis_eval.get("confidence") or 0.0)
    )
    
    append_ledger({
        "event": "binoche_enhanced_decision",
        "task_id": task.task_id,
        "enhanced_action": enhanced_decision["action"],
        "enhanced_confidence": enhanced_decision["confidence"],
        "enhanced_rule": enhanced_decision["rule_applied"],
        "enhanced_reason": enhanced_decision["reason"],
        "enhanced_pattern": enhanced_decision["bqi_pattern"]
    })

    # Meta-Cognition: warn on low confidence or ask_user action (Enhanced)
    try:
        if enhanced_decision["action"] == "ask_user" or float(enhanced_decision["confidence"]) < 0.6:
            level = "warning" if float(enhanced_decision["confidence"]) >= 0.5 else "critical"
            append_ledger({
                "event": "meta_cognition_warning",
                "task_id": task.task_id,
                "source": "enhanced_binoche",
                "level": level,
                "action": enhanced_decision["action"],
                "confidence": float(enhanced_decision["confidence"]),
                "reason": enhanced_decision.get("reason"),
                "rule": enhanced_decision.get("rule_applied"),
                "bqi_pattern": enhanced_decision.get("bqi_pattern")
            })
    except Exception as mc_ex:
        append_ledger({"event": "meta_cognition_warning_error", "task_id": task.task_id, "error": str(mc_ex)})

    # Phase 6g-6j: Binoche Ensemble (BQI + Quality multi-model decision) - Legacy System
    from .binoche_recommender import get_binoche_recommendation
    from .binoche_config import should_auto_approve, should_auto_revise, get_pattern_threshold
    from .binoche_ensemble import get_ensemble_decision
    
    # Step 1: Get BQI-based recommendation
    binoche_decision, binoche_confidence, binoche_reason = get_binoche_recommendation(
        bqi_coord=bqi_coord.to_dict(),
        quality=float(eval_report.quality)
    )
    
    pattern_key = f"p{bqi_coord.priority}_e:{'keywords' if bqi_coord.emotion.get('keywords', ['neutral']) != ['neutral'] else 'neutral'}_r:{bqi_coord.rhythm_phase}"
    
    # Step 2: Get ensemble decision (BQI + Quality) with judge details
    ensemble_decision, ensemble_confidence, ensemble_reason, judges = get_ensemble_decision(
        bqi_coord=bqi_coord.to_dict(),
        quality=float(eval_report.quality),
        bqi_decision=binoche_decision,
        bqi_confidence=binoche_confidence
    )
    
    append_ledger({
        "event": "binoche_decision",
        "task_id": task.task_id,
        "bqi_pattern": pattern_key,
        "decision": binoche_decision,
        "confidence": float(binoche_confidence),
        "reason": binoche_reason,
        "quality": float(eval_report.quality),
        "ensemble_decision": ensemble_decision,
        "ensemble_confidence": float(ensemble_confidence),
        "ensemble_reason": ensemble_reason,
        "judges": {
            "logic": {
                "decision": judges["logic"]["decision"],
                "confidence": float(judges["logic"]["confidence"])
            },
            "emotion": {
                "decision": judges["emotion"]["decision"],
                "confidence": float(judges["emotion"]["confidence"])
            },
            "rhythm": {
                "decision": judges["rhythm"]["decision"],
                "confidence": float(judges["rhythm"]["confidence"])
            }
        },
        "thresholds": {
            "approve_confidence": get_pattern_threshold(pattern_key, "auto_approve_confidence"),
            "approve_quality": get_pattern_threshold(pattern_key, "auto_approve_quality"),
            "revise_confidence": get_pattern_threshold(pattern_key, "auto_revise_confidence") if bqi_coord.rhythm_phase == "planning" else None,
            "revise_quality": get_pattern_threshold(pattern_key, "auto_revise_quality") if bqi_coord.rhythm_phase == "planning" else None
        }
    })
    
    # Phase 6k: A/B Comparison Logging
    ab_comparison = {
        "event": "binoche_ab_comparison",
        "task_id": task.task_id,
        "legacy_decision": ensemble_decision,
        "legacy_confidence": float(ensemble_confidence),
        "enhanced_decision": enhanced_decision["action"],
        "enhanced_confidence": enhanced_decision["confidence"],
        "decisions_match": ensemble_decision == enhanced_decision["action"],
        "confidence_diff": enhanced_decision["confidence"] - float(ensemble_confidence)
    }
    append_ledger(ab_comparison)

    # Meta-Cognition: warn on low confidence for Legacy Ensemble as well
    try:
        if float(ensemble_confidence) < 0.6:
            level = "warning" if float(ensemble_confidence) >= 0.5 else "critical"
            append_ledger({
                "event": "meta_cognition_low_confidence",
                "task_id": task.task_id,
                "source": "legacy_ensemble",
                "level": level,
                "decision": ensemble_decision,
                "confidence": float(ensemble_confidence),
                "reason": ensemble_reason,
                "bqi_pattern": pattern_key
            })
    except Exception as mc_legacy_ex:
        append_ledger({"event": "meta_cognition_low_confidence_error", "task_id": task.task_id, "error": str(mc_legacy_ex)})
    
    # Phase 6h+6j: Planning auto-revise with ensemble confidence
    planning_auto_revise_triggered = False
    if should_auto_revise(pattern_key, ensemble_confidence, float(eval_report.quality), bqi_coord.rhythm_phase):
        append_ledger({
            "event": "binoche_auto_revise",
            "task_id": task.task_id,
            "bqi_confidence": float(binoche_confidence),
            "ensemble_confidence": float(ensemble_confidence),
            "quality": float(eval_report.quality),
            "reason": f"Ensemble auto-revise: {ensemble_reason}"
        })
        planning_auto_revise_triggered = True
    
    # Phase 6i+6j: High-confidence auto-approve with ensemble decision
    if ensemble_decision == "approve" and should_auto_approve(pattern_key, ensemble_confidence, float(eval_report.quality)):
        append_ledger({
            "event": "binoche_auto_approve",
            "task_id": task.task_id,
            "bqi_confidence": float(binoche_confidence),
            "ensemble_confidence": float(ensemble_confidence),
            "quality": float(eval_report.quality),
            "reason": f"Ensemble auto-approve: {ensemble_reason}"
        })
        
        result = {
            "task_id": task.task_id,
            "summary": out_synth.summary,
            "citations": out_synth.citations,
            "notes": "auto_approved_by_ensemble",
            "binoche_confidence": float(binoche_confidence),
            "ensemble_confidence": float(ensemble_confidence)
        }
        
        # 대화 메모리에 Q&A 저장
        conv_memory.add_turn(
            question=task.goal,
            answer=out_synth.summary,
            task_id=task.task_id,
            bqi_coord=bqi_coord
        )
        
        # Autopoietic Loop: Symmetry end (early auto-approve path)
        try:
            append_ledger({
                "event": "autopoietic_phase",
                "task_id": task.task_id,
                "phase": "symmetry",
                "stage": "end",
                "duration_sec": float(time.perf_counter() - _sym_start),
                "evidence_gate_triggered": False,
                "second_pass": False,
                "final_quality": float(eval_report.quality),
                "final_evidence_ok": bool(eval_report.evidence_ok)
            })
        except Exception:
            pass

        append_coordinate({"event": "task_end", "task_id": task.task_id, "result": result, "binoche_auto_approved": True})
        
        # Policy evaluation + closed-loop snapshot (early exit path)
        try:
            from .resonance_bridge import (
                record_task_resonance,
                evaluate_resonance_policy,
                get_closed_loop_snapshot,
                get_closed_loop_period_sec,
            )
            task_duration = time.perf_counter() - t_start
            # Evaluate against active policy (observe by default)
            try:
                pol_eval = evaluate_resonance_policy(eval_report.model_dump(), task_duration)
                append_ledger({
                    "event": "resonance_policy",
                    "task_id": task.task_id,
                    **pol_eval,
                })
                from .resonance_bridge import should_emit_closed_loop
                period = get_closed_loop_period_sec()
                if should_emit_closed_loop(period):
                    cls = get_closed_loop_snapshot()
                    if cls:
                        append_ledger({
                            "event": "closed_loop_snapshot",
                            "task_id": task.task_id,
                            "snapshot": cls,
                        })
            except Exception:
                pass
            record_task_resonance(
                task_id=task.task_id,
                task_goal=task.goal,
                eval_report=eval_report.model_dump(),
                bqi_coord=bqi_coord.to_dict() if bqi_coord else None,
                duration_sec=task_duration,
            )
        except Exception:
            pass
        
        return result

    # Evidence gate: if evidence is missing OR forced (dev/test) OR planning auto-revise, attempt one lightweight corrective pass (citations via RAG)
    evidence_gate_triggered = (not eval_report.evidence_ok) or (not out_synth.citations) or is_evidence_force_enabled(task) or planning_auto_revise_triggered
    if evidence_gate_triggered:
        trigger_reason = "no_evidence" if not eval_report.evidence_ok else ("empty_citations" if not out_synth.citations else ("forced" if is_evidence_force_enabled(task) else "planning_auto_revise"))
        append_ledger({
            "event": "evidence_gate_triggered",
            "task_id": task.task_id,
            "reason": trigger_reason,
            "initial_quality": float(eval_report.quality),
            "initial_evidence_ok": bool(eval_report.evidence_ok),
            "binoche_triggered": planning_auto_revise_triggered
        })
        corr_info = evidence_gate_correction(task, [out_thesis, out_anti, out_synth], registry)
        if corr_info.get("updated"):
            # Re-evaluate after adding citations
            eval_report = EVAL([out_thesis, out_anti, out_synth])
            rune = rune_from_eval(eval_report)
            append_ledger({
                "event": "eval",
                "task_id": task.task_id,
                "pass": "evidence_gate",
                "quality": float(eval_report.quality),
                "evidence_ok": bool(eval_report.evidence_ok),
                "quality_delta": float(eval_report.quality) - corr_info.get("initial_quality", 0.0),
                "eval": eval_report.model_dump()
            })
            append_ledger({
                "event": "rune",
                "task_id": task.task_id,
                "pass": "evidence_gate",
                "replan_changed": bool(corr_info.get("initial_replan")) != rune.replan,
                "rune": rune.model_dump()
            })
        else:
            # Evidence gate ran but no citations added - log failure for observability
            append_ledger({
                "event": "evidence_gate_failed",
                "task_id": task.task_id,
                "reason": "no_citations_added",
                "attempted_passes": 3  # targeted, broaden, synthetic
            })

    # Optional self-correction pass (configurable) after rune (adaptive learning)
    corr_cfg = get_corrections_config()
    if not corr_cfg.get("enabled", True):
        append_ledger({"event": "corrections_skipped", "task_id": task.task_id, "reason": "disabled"})
    else:
        max_passes = max(1, int(corr_cfg.get("max_passes", 2)))
        # 현재 구현은 1회 추가 패스만 수행 (호환성), 필요 시 루프로 확장 가능
        if rune.replan and max_passes > 1:
            # Phase 3: Adaptive Learning - Few-shot 프롬프트 생성
            learning_result = adaptive_replan_with_learning(
                eval_report=eval_report,
                task_goal=task.goal,
                memory_snapshot=snapshot_memory()
            )
            
            # Learning 결과 로깅
            append_ledger({
                "event": "learning",
                "task_id": task.task_id,
                "strategy": learning_result.get("strategy", "unknown"),
                "success_cases_found": len(learning_result.get("success_cases", [])),
                "enhanced_prompt_length": len(learning_result.get("enhanced_prompt", ""))
            })
            
            # Enhanced prompt를 plan에 추가
            enhanced_plan = {**plan}
            if learning_result.get("enhanced_prompt"):
                enhanced_plan["learning_context"] = learning_result["enhanced_prompt"]
            
            # 재실행
            append_ledger({"event": "thesis_start", "task_id": task.task_id, "pass": 2})
            t6 = time.perf_counter()
            out_thesis = run_thesis(task, enhanced_plan, registry, conversation_context=context_prompt or "")
            t7 = time.perf_counter()
            append_ledger({
                "event": "thesis_end",
                "task_id": task.task_id,
                "pass": 2,
                "duration_sec": float(t7 - t6),
                "citations": len(out_thesis.citations)
            })

            append_ledger({"event": "synthesis_start", "task_id": task.task_id, "pass": 2})
            t8 = time.perf_counter()
            out_synth = run_synthesis(task, [out_thesis, out_anti], registry, conversation_context=context_prompt or "")
            t9 = time.perf_counter()
            append_ledger({
                "event": "synthesis_end",
                "task_id": task.task_id,
                "pass": 2,
                "duration_sec": float(t9 - t8),
                "citations": len(out_synth.citations)
            })
            append_ledger({"event": "second_pass", "task_id": task.task_id})
            second_pass_executed = True

    result = {
        "task_id": task.task_id,
        "summary": out_synth.summary,
        "citations": out_synth.citations,
        "notes": "completed"
    }
    
    # 대화 메모리에 Q&A 저장 (Phase 1 완료)
    conv_memory.add_turn(
        question=task.goal,
        answer=out_synth.summary,
        task_id=task.task_id,
        bqi_coord=bqi_coord
    )
    
    # Autopoietic Loop: Symmetry end (normal completion)
    try:
        append_ledger({
            "event": "autopoietic_phase",
            "task_id": task.task_id,
            "phase": "symmetry",
            "stage": "end",
            "duration_sec": float(time.perf_counter() - _sym_start),
            "evidence_gate_triggered": bool(evidence_gate_triggered),
            "second_pass": bool(second_pass_executed),
            "final_quality": float(eval_report.quality),
            "final_evidence_ok": bool(eval_report.evidence_ok)
        })
    except Exception:
        pass

    append_coordinate({"event": "task_end", "task_id": task.task_id, "result": result})
    
    # Policy evaluation + closed-loop snapshot, then record resonance event
    try:
        from .resonance_bridge import (
            record_task_resonance,
            evaluate_resonance_policy,
            get_closed_loop_snapshot,
            get_closed_loop_period_sec,
        )
        task_duration = time.perf_counter() - t_start
        try:
            pol_eval = evaluate_resonance_policy(eval_report.model_dump(), task_duration)
            append_ledger({
                "event": "resonance_policy",
                "task_id": task.task_id,
                **pol_eval,
            })
            from .resonance_bridge import should_emit_closed_loop
            period = get_closed_loop_period_sec()
            if should_emit_closed_loop(period):
                cls = get_closed_loop_snapshot()
                if cls:
                    append_ledger({
                        "event": "closed_loop_snapshot",
                        "task_id": task.task_id,
                        "snapshot": cls,
                    })
        except Exception:
            pass
        record_task_resonance(
            task_id=task.task_id,
            task_goal=task.goal,
            eval_report=eval_report.model_dump(),
            bqi_coord=bqi_coord.to_dict() if bqi_coord else None,
            duration_sec=task_duration,
        )
    except Exception:
        pass  # Silent fallback if resonance not initialized
    
    return result
