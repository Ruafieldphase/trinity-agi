from __future__ import annotations

from typing import Dict, Any, List, Tuple
import os
import time

from .contracts import EvalReport, RUNEReport, TaskSpec, PersonaOutput
from .memory_bus import append_ledger
from .evidence_cache import get_evidence_cache

try:
    # Normal package import
    from fdo_agi_repo.tools.rag.config_loader import get_rag_config
except ModuleNotFoundError:  # script-run from fdo_agi_repo
    try:
        from tools.rag.config_loader import get_rag_config  # type: ignore
    except ModuleNotFoundError:
        from ..tools.rag.config_loader import get_rag_config  # type: ignore

from .config import get_evaluation_config


def rune_from_eval(eval_report: EvalReport) -> RUNEReport:
    """
    간단한 규칙 기반 RUNE: 증거 없거나 품질이 임계값 미만이면 재계획(replan)
    """
    eval_cfg = get_evaluation_config()
    min_q = float(eval_cfg.get("min_quality", 0.6))
    replan = (not eval_report.evidence_ok) or (eval_report.quality < min_q)
    recs = ["강한 근거 추가", "모호한 문장 줄이기"] if replan else ["다음 단계 진행"]
    return RUNEReport(
        task_id=eval_report.task_id,
        impact=max(0.1, eval_report.quality),
        transparency=0.7,
        confidence=0.5,
        risks=eval_report.risks,
        recommendations=recs,
        replan=replan,
    )


def is_evidence_force_enabled(task: TaskSpec) -> bool:
    """
    Dev/Test 전용 강제 게이트: task.goal에 "__force_evidence__"가 포함되고,
    환경변수 EVIDENCE_GATE_FORCE=1 또는 outputs/allow_force_evidence.flag 파일이 존재할 때 활성화
    """
    try:
        from pathlib import Path
        force_marker = "__force_evidence__"
        has_marker = isinstance(getattr(task, "goal", ""), str) and (force_marker in task.goal)
        repo_root = Path(__file__).parent.parent
        sentinel = repo_root / "outputs" / "allow_force_evidence.flag"
        force_enabled = (os.getenv("EVIDENCE_GATE_FORCE", "0") == "1") or sentinel.exists()
        return bool(has_marker and force_enabled)
    except Exception:
        return False


def evidence_gate_correction(task: TaskSpec, outs: List[PersonaOutput], registry) -> Dict[str, Any]:
    """
    Evidence Gate (경량 보정): 증거/인용이 없으면 RAG를 통해 인용을 주입한다.
    Phase 2: RAG 결과를 캐시하여 지연을 줄인다.

    Returns: {
      "updated": bool,            # 인용 추가 여부
      "added": int,               # 추가된 인용 수
      "initial_quality": float,   # 보정 전 품질
      "initial_replan": bool      # 보정 전 RUNE.replan
    }
    """
    try:
        cache = get_evidence_cache(ttl_seconds=300, max_entries=1000)

        synth = next((o for o in outs if o.persona == "synthesis"), None)
        if synth is None:
            return {"updated": False, "added": 0, "initial_quality": 0.0, "initial_replan": False}

        # 초기 상태 기록 (델타 계산용)
        from .pipeline import EVAL  # 순환 참조 방지 위해 내부 import
        initial_eval = EVAL(outs)
        initial_rune = rune_from_eval(initial_eval)
        initial_quality = float(initial_eval.quality)
        initial_replan = bool(initial_rune.replan)

        forced = is_evidence_force_enabled(task)
        if (synth.citations and len(synth.citations) > 0) and not forced:
            return {"updated": False, "added": 0, "initial_quality": initial_quality, "initial_replan": initial_replan}

        # Evidence-gate 설정
        rcfg = get_rag_config().get("evidence_gate", {})
        top_k = int(rcfg.get("top_k", 5))
        min_rel = float(rcfg.get("min_relevance", 0.4))
        include_types = rcfg.get("include_types")  # None or list/str

        def _collect_from_rag(rag_result: Dict[str, Any], min_rel_val: float) -> Tuple[int, int, List[Dict[str, Any]], List[Dict[str, Any]]]:
            hits_local = rag_result.get("hits", []) if rag_result.get("ok") else []
            cites_local: List[Dict[str, Any]] = []
            for h in hits_local or []:
                try:
                    src = str(h.get("source", "local"))
                except Exception:
                    src = "local"
                try:
                    ptr = str(h.get("id", ""))
                except Exception:
                    ptr = ""
                snip = str(h.get("snippet", ""))[:200]
                try:
                    rel_val = float(h.get("relevance", 0.0))
                except Exception:
                    rel_val = 0.0
                cites_local.append({
                    "source": src,
                    "pointer": ptr,
                    "snippet": snip,
                    "relevance": rel_val,
                })
            qual_local = [c for c in cites_local if float(c.get("relevance", 0) or 0.0) >= float(min_rel_val)]
            return len(hits_local or []), len(qual_local), cites_local, qual_local

        # Pass 1: 캐시 확인 후, include_types를 사용하는 타깃 검색
        cache_key = task.goal if isinstance(task.goal, str) else str(task.goal)
        cached_rag1 = cache.get(cache_key)
        cache_hit = cached_rag1 is not None
        if cache_hit:
            rag1 = cached_rag1
            rag1_latency_ms = 0.0
        else:
            rag1_start = time.time()
            rag1 = registry.call("rag", {"query": task.goal, "top_k": top_k, "include_types": include_types})
            rag1_latency_ms = (time.time() - rag1_start) * 1000.0
            cache.put(cache_key, rag1, latency_ms=rag1_latency_ms)

        hits1, qual1, cites1, qualc1 = _collect_from_rag(rag1, min_rel)

        # Pass 2: 타깃에서 충분치 않으면 넓게 검색 (include_types 제거)
        used_pass = "targeted"
        rag2_latency_ms = 0.0
        added_cites: List[Dict[str, Any]] = []
        if qual1 == 0:
            used_pass = "broaden"
            cache_key2 = f"broaden::{cache_key}"
            cached_rag2 = cache.get(cache_key2)
            if cached_rag2 is not None:
                rag2 = cached_rag2
            else:
                rag2_start = time.time()
                rag2 = registry.call("rag", {"query": task.goal, "top_k": top_k})
                rag2_latency_ms = (time.time() - rag2_start) * 1000.0
                cache.put(cache_key2, rag2, latency_ms=rag2_latency_ms)
            hits2, qual2, cites2, qualc2 = _collect_from_rag(rag2, min_rel)
            if qual2 > 0:
                added_cites = qualc2[: min(3, len(qualc2))]
            elif hits1 > 0 or (rag1.get("ok") and cites1):
                # fallback: 관련도 기준 미달이라도 상위 1-2개만라도 추가
                added_cites = cites1[: min(2, len(cites1))]
        else:
            added_cites = qualc1[: min(3, len(qualc1))]

        # Pass 3: 여전히 없으면 synthetic placeholder (관측용)
        used_synthetic = False
        if not added_cites:
            used_pass = "synthetic"
            used_synthetic = True
            added_cites = [{
                "source": "synthetic",
                "pointer": "",
                "snippet": "No external evidence found; placeholder citation added.",
                "relevance": 0.0,
            }]

        # 인용 주입
        before_cnt = len(synth.citations or [])
        synth.citations = (synth.citations or []) + added_cites
        after_cnt = len(synth.citations)
        added = max(0, after_cnt - before_cnt)

        # 로깅 (캐시 통계 포함)
        try:
            cache_stats = cache.get_stats()
        except Exception:
            cache_stats = {}

        append_ledger({
            "event": "evidence_correction",
            "task_id": task.task_id,
            "pass": used_pass,
            "cache_hit": bool(cache_hit),
            "rag_latency_ms": float(rag1_latency_ms),
            "rag2_latency_ms": float(rag2_latency_ms),
            "added": int(added),
            "total_citations": int(after_cnt),
            "min_relevance": float(min_rel),
            "top_k": int(top_k),
            "used_synthetic": bool(used_synthetic),
            "cache": cache_stats,
        })

        return {"updated": added > 0, "added": added, "initial_quality": initial_quality, "initial_replan": initial_replan}

    except Exception as e:
        # 실패 시에도 파이프라인이 계속 돌도록 보수적으로 동작
        append_ledger({
            "event": "evidence_correction_error",
            "task_id": getattr(task, "task_id", "unknown"),
            "error": str(e),
        })
        return {"updated": False, "added": 0, "initial_quality": 0.0, "initial_replan": False}
