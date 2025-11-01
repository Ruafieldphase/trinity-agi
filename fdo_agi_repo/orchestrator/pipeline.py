from __future__ import annotations
import uuid
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
from .config import is_corrections_enabled, get_corrections_config, get_evaluation_config

# BQI 통합 (Phase 1)
from scripts.rune.bqi_adapter import analyse_question
from .conversation_memory import ConversationMemory
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
    
    gate = SAFE_pre(task.model_dump(), tail_ledger())
    if not gate["allowed"]:
        append_ledger({"event": "needs_approval", "task_id": task.task_id, "risk": gate["risk"]})
        return {"status": "HALT", "reason": "approval_required", "gate": gate}

    # 실행 설정 로깅: 평가 임계값 및 자기교정 구성
    eval_cfg = get_evaluation_config()
    corr_cfg = get_corrections_config()
    append_ledger({
        "event": "run_config",
        "task_id": task.task_id,
        "evaluation": {"min_quality": float(eval_cfg.get("min_quality", 0.6))},
        "corrections": {"enabled": bool(corr_cfg.get("enabled", True)), "max_passes": int(corr_cfg.get("max_passes", 2))},
        "bqi_coord": bqi_coord.to_dict(),
    })
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
    t0 = time.perf_counter()
    append_ledger({"event": "thesis_start", "task_id": task.task_id})
    out_thesis = run_thesis(task, plan, registry, conversation_context=context_prompt or "")
    t1 = time.perf_counter()
    append_ledger({
        "event": "thesis_end",
        "task_id": task.task_id,
        "duration_sec": float(t1 - t0),
        "citations": len(out_thesis.citations)
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
    out_anti   = run_antithesis(task, out_thesis, registry, conversation_context=context_prompt or "")
    t3 = time.perf_counter()
    append_ledger({"event": "antithesis_end", "task_id": task.task_id, "duration_sec": float(t3 - t2)})
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
    out_synth = run_synthesis(task, [out_thesis, out_anti], registry, conversation_context=context_prompt or "")
    t5 = time.perf_counter()
    append_ledger({
        "event": "synthesis_end",
        "task_id": task.task_id,
        "duration_sec": float(t5 - t4),
        "citations": len(out_synth.citations)
    })
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
            from .resonance_bridge import record_task_resonance, evaluate_resonance_policy, get_closed_loop_snapshot
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
                if should_emit_closed_loop():
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
        from .resonance_bridge import record_task_resonance, evaluate_resonance_policy, get_closed_loop_snapshot
        task_duration = time.perf_counter() - t_start
        try:
            pol_eval = evaluate_resonance_policy(eval_report.model_dump(), task_duration)
            append_ledger({
                "event": "resonance_policy",
                "task_id": task.task_id,
                **pol_eval,
            })
            from .resonance_bridge import should_emit_closed_loop
            if should_emit_closed_loop():
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
