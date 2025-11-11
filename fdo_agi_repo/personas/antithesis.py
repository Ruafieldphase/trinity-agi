from __future__ import annotations
from typing import Dict, Any, List
import os
try:
    from fdo_agi_repo.orchestrator.contracts import TaskSpec, PersonaOutput
    from fdo_agi_repo.orchestrator.memory_bus import append_ledger
except ModuleNotFoundError:
    from orchestrator.contracts import TaskSpec, PersonaOutput  # type: ignore
    from orchestrator.memory_bus import append_ledger  # type: ignore
import time
import google.generativeai as genai

# Configure Google AI Studio API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyDTCQiXRrOMWqmq2REy2Zh8HQ8VvYJEbdQ")
genai.configure(api_key=GEMINI_API_KEY)

# Placeholder fallback function
def _heuristic_critique(thesis_out: PersonaOutput) -> str:
    issues = []
    recs = []

    if len(thesis_out.citations) < 1:
        issues.append("근거 부족")
        recs.append("로컬 히트 최소 1개 이상 확보 필요 (memory/*.jsonl)")

    if "result.md" not in thesis_out.summary:
        issues.append("산출물 경로 미기재")
        recs.append("sandbox/docs/result.md를 산출물 경로로 명시")

    if "3단계" not in thesis_out.summary:
        issues.append("실행 단계 불명확")
        recs.append("요구 분석 → 근거 확보 → 산출물 작성 3단계를 명확히 기술")

    status = ", ".join(issues) if issues else "기본 OK"
    detail = ("; ".join(recs)) if recs else "추가 검증 항목 없음"
    return f"[ANTITHESIS] 검증: {status}\n- 권고: {detail}"

def run_antithesis(task: TaskSpec, thesis_out: PersonaOutput, tools, conversation_context: str = "") -> PersonaOutput:
    # 1. 프롬프트 구성
    system_prompt = "당신은 비판적 검토자입니다. 주어진 제안의 논리적 허점, 근거의 타당성, 실행 가능성을 날카롭게 분석하고 구체적인 보강점을 간결하게 지적하세요.\n\n⚠️ **필수 검증 항목**: 제안의 모든 주장이 **구체적인 근거(예: RAG 참조, 인용, 데이터)**로 뒷받침되는지 확인하세요. 근거가 없거나 모호한 주장은 반드시 지적해야 합니다."
    
    # 대화 맥락 주입 (Phase 2: Persona Context Propagation)
    if conversation_context:
        system_prompt += f"\n\n{conversation_context}"
        system_prompt += "\n⚠️ **맥락 고려 필수**: 위 이전 대화와 관련된 내용이라면, 과거 논의 사항과 일관성을 검토하십시오."

    # Optimization hint
    channel_hint = None
    throttled = False
    batch_pref = None
    try:
        opt_hint = getattr(tools, "get_optimization_hint", lambda: None)()
    except Exception:
        opt_hint = None
    if isinstance(opt_hint, dict):
        pref = opt_hint.get("preferred_channels")
        if isinstance(pref, list) and pref:
            channel_hint = str(pref[0]).lower()
        elif isinstance(pref, str) and pref:
            channel_hint = pref.lower()
        throttled = bool(opt_hint.get("should_throttle_offpeak", False))
        batch_level = opt_hint.get("batch_compression_level")
        if isinstance(batch_level, str) and batch_level:
            batch_pref = batch_level
        else:
            batch_flag = opt_hint.get("batch_compression")
            if batch_flag is True:
                batch_pref = "high"
    try:
        append_ledger({
            "event": "persona_channel_hint",
            "task_id": task.task_id,
            "persona": "antithesis",
            "channel_hint": channel_hint,
            "throttle": bool(throttled),
            "batch_compression": batch_pref or "auto"
        })
    except Exception:
        pass

    # Prompt compaction for long thesis summary
    def _compact(text: str, max_chars: int, head: int = 600, tail: int = 600) -> str:
        if max_chars <= 0 or len(text) <= max_chars:
            return text
        head = max(0, min(head, max_chars))
        tail = max(0, min(tail, max_chars - head))
        if head + tail >= max_chars:
            tail = max_chars - head
        return text[:head] + "\n... [중략/요약] ...\n" + text[-tail:]

    try:
        src_max = int(os.environ.get("ANTITHESIS_SOURCE_MAX_CHARS", "1200"))
    except Exception:
        src_max = 1200
    thesis_comp = _compact(thesis_out.summary, src_max)

    user_prompt = f"검토할 제안:\n---\n{thesis_comp}\n---\n\n요구사항: 제안의 근거, 실행가능성, 산출물 경로의 적절성을 검증하고, 논리적 비약이나 빠진 부분을 지적하여 보강할 점을 제시하세요."
    if isinstance(batch_pref, str) and batch_pref.lower() in {"high", "max"}:
        user_prompt += "\n\n⚙️ **Batch Compression**: 핵심 문제만 간결히 지적하고, 불필요한 서술을 줄이세요."

    prefer_local = (channel_hint == "local_llm")
    if prefer_local or throttled:
        summary = _heuristic_critique(thesis_out)
        try:
            append_ledger({
                "event": "persona_local_fallback",
                "task_id": task.task_id,
                "persona": "antithesis",
                "reason": "throttle_offpeak" if throttled and not prefer_local else "preferred_local"
            })
        except Exception:
            pass
        return PersonaOutput(
            task_id=task.task_id,
            persona="antithesis",
            summary=summary,
            citations=thesis_out.citations,
            actions=[]
        )

    # 2. Gemini LLM 호출 (Google AI Studio API)
    # Streaming 옵션 (환경변수로 제어)
    use_streaming = os.environ.get("ANTITHESIS_STREAMING", "true").lower() == "true"
    if channel_hint == "cloud_ai":
        use_streaming = False
    elif channel_hint == "gateway":
        use_streaming = True
    model_name = os.environ.get("ANTITHESIS_MODEL", "gemini-2.0-flash")
    if channel_hint == "cloud_ai":
        model_name = os.environ.get("ANTITHESIS_MODEL_CLOUD", model_name)
    elif channel_hint == "gateway":
        model_name = os.environ.get("ANTITHESIS_MODEL_GATEWAY", model_name)
    
    summary = ""
    err_text = None
    ttft = None  # Time To First Token
    t_llm0 = time.perf_counter()
    
    try:
        model = genai.GenerativeModel(model_name)
        prompt = f"{system_prompt}\n\n{user_prompt}"
        
        if use_streaming:
            # Streaming: 첫 토큰 빠른 반환
            chunks = []
            response = model.generate_content(prompt, stream=True)
            for chunk in response:
                if ttft is None:
                    ttft = time.perf_counter() - t_llm0
                if hasattr(chunk, 'text'):
                    chunks.append(chunk.text)
            summary = f"[ANTITHESIS] 비판 결과\n{''.join(chunks)}"
        else:
            # Baseline: 전통적 방식
            response = model.generate_content(prompt)
            summary = f"[ANTITHESIS] 비판 결과\n{response.text}"
            
    except Exception as e:
        err_text = f"{type(e).__name__}: {e}"
        # LLM 호출 실패 시, 기존 placeholder 로직으로 폴백
        summary = _heuristic_critique(thesis_out)

    t_llm1 = time.perf_counter()
    
    # Ledger 기록
    log_entry = {
        "event": "persona_llm_run",
        "task_id": task.task_id,
        "persona": "antithesis",
        "provider": "google-ai-studio",
        "model": model_name,
        "duration_sec": float(t_llm1 - t_llm0),
        "ok": bool(bool(summary) and not err_text),
        "error": err_text,
        "prompt_chars": len(system_prompt) + len(user_prompt),
        "streaming": use_streaming
    }
    
    # TTFT 메트릭 추가 (streaming 시에만)
    if use_streaming and ttft is not None:
        log_entry["ttft_sec"] = float(ttft)
        perceived_improvement = ((t_llm1 - t_llm0 - ttft) / (t_llm1 - t_llm0)) * 100
        log_entry["perceived_improvement_pct"] = float(perceived_improvement)
    if channel_hint:
        log_entry["channel_hint"] = channel_hint
    if throttled:
        log_entry["throttle_applied"] = True
    
    append_ledger(log_entry)

    # 3. PersonaOutput 반환
    return PersonaOutput(
        task_id=task.task_id,
        persona="antithesis",
        summary=summary,
        citations=thesis_out.citations,
        actions=[]
    )
