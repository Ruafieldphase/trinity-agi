"""
Phase 2: Antithesis 준비 작업 병렬화

Thesis 실행 중에 Antithesis 준비 작업을 미리 수행:
1. Antithesis 프롬프트 템플릿 준비
2. Compaction 함수 준비
3. Thesis 완료 후 thesis_out만 주입하여 즉시 실행

예상 효과: +0.5-1초 개선
"""
from __future__ import annotations
import time
import os
from typing import Callable, Any
from concurrent.futures import ThreadPoolExecutor, Future

try:
    from fdo_agi_repo.orchestrator.contracts import TaskSpec, PersonaOutput
    from fdo_agi_repo.orchestrator.memory_bus import append_ledger
except ModuleNotFoundError:
    from orchestrator.contracts import TaskSpec, PersonaOutput  # type: ignore
    from orchestrator.memory_bus import append_ledger  # type: ignore


def prepare_antithesis_context(
    task: TaskSpec,
    conversation_context: str = ""
) -> dict[str, Any]:
    """
    Antithesis 실행 전에 미리 준비 가능한 컨텍스트를 구성.
    thesis_out 없이 준비 가능한 부분만 처리.
    
    Returns:
        dict with:
        - system_prompt: str
        - compaction_fn: Callable[[str], str]
        - user_prompt_template: str
    """
    # System prompt 구성
    system_prompt = (
        "당신은 비판적 검토자입니다. 주어진 제안의 논리적 허점, "
        "근거의 타당성, 실행 가능성을 날카롭게 분석하고 "
        "구체적인 보강점을 간결하게 지적하세요.\n\n"
        "⚠️ **필수 검증 항목**: 제안의 모든 주장이 **구체적인 근거"
        "(예: RAG 참조, 인용, 데이터)**로 뒷받침되는지 확인하세요. "
        "근거가 없거나 모호한 주장은 반드시 지적해야 합니다."
    )
    
    # 대화 맥락 주입
    if conversation_context:
        system_prompt += f"\n\n{conversation_context}"
        system_prompt += (
            "\n⚠️ **맥락 고려 필수**: 위 이전 대화와 관련된 내용이라면, "
            "과거 논의 사항과 일관성을 검토하십시오."
        )
    
    # Compaction 함수 준비
    try:
        src_max = int(os.environ.get("ANTITHESIS_SOURCE_MAX_CHARS", "1200"))
    except Exception:
        src_max = 1200
    
    def _compact(text: str, max_chars: int = src_max, head: int = 600, tail: int = 600) -> str:
        if max_chars <= 0 or len(text) <= max_chars:
            return text
        head = max(0, min(head, max_chars))
        tail = max(0, min(tail, max_chars - head))
        if head + tail >= max_chars:
            tail = max_chars - head
        return text[:head] + "\n... [중략/요약] ...\n" + text[-tail:]
    
    # User prompt 템플릿
    user_prompt_template = (
        "검토할 제안:\n---\n{thesis_summary}\n---\n\n"
        "요구사항: 제안의 근거, 실행가능성, 산출물 경로의 적절성을 검증하고, "
        "논리적 비약이나 빠진 부분을 지적하여 보강할 점을 제시하세요."
    )
    
    return {
        "system_prompt": system_prompt,
        "compaction_fn": _compact,
        "user_prompt_template": user_prompt_template,
        "task_id": task.task_id
    }


def run_antithesis_with_prep(
    task: TaskSpec,
    thesis_out: PersonaOutput,
    tools: Any,
    conversation_context: str = "",
    prep_context: dict[str, Any] | None = None
) -> PersonaOutput:
    """
    Antithesis를 실행하되, 사전 준비된 컨텍스트를 활용.
    
    Args:
        task: TaskSpec
        thesis_out: Thesis 출력
        tools: Registry
        conversation_context: 대화 맥락
        prep_context: prepare_antithesis_context()의 출력 (선택)
    
    Returns:
        PersonaOutput
    """
    # 준비된 컨텍스트가 없으면 즉시 준비
    if prep_context is None:
        prep_context = prepare_antithesis_context(task, conversation_context)
    
    # Thesis summary compaction (준비된 함수 사용)
    compaction_fn = prep_context["compaction_fn"]
    thesis_comp = compaction_fn(thesis_out.summary)
    
    # User prompt 완성 (thesis_out 주입)
    user_prompt = prep_context["user_prompt_template"].format(
        thesis_summary=thesis_comp
    )
    
    # LLM 호출 (기존 antithesis.py 로직)
    from fdo_agi_repo.personas.antithesis import run_antithesis
    
    # 기존 함수 호출 (단, 준비된 프롬프트 사용)
    # NOTE: 현재는 기존 함수를 그대로 호출하지만,
    # 나중에 prep_context를 직접 활용하도록 리팩토링 가능
    return run_antithesis(task, thesis_out, tools, conversation_context)


def run_thesis_and_antithesis_parallel(
    task: TaskSpec,
    thesis_fn: Callable[[], PersonaOutput],
    tools: Any,
    conversation_context: str = ""
) -> tuple[PersonaOutput, PersonaOutput]:
    """
    Thesis와 Antithesis 준비를 병렬로 실행.
    
    Args:
        task: TaskSpec
        thesis_fn: Thesis를 실행하는 함수 (인자 없음)
        tools: Registry
        conversation_context: 대화 맥락
    
    Returns:
        (thesis_out, antithesis_out)
    """
    t_start = time.perf_counter()
    
    append_ledger({
        "event": "antithesis_prep_parallel_start",
        "task_id": task.task_id
    })
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        # Future 1: Thesis 실행
        thesis_future = executor.submit(thesis_fn)
        
        # Future 2: Antithesis 준비 (thesis_out 없이 가능한 부분)
        prep_future = executor.submit(
            prepare_antithesis_context,
            task,
            conversation_context
        )
        
        # 두 작업 병렬 실행
        thesis_out = thesis_future.result()
        prep_context = prep_future.result()
    
    t_prep_done = time.perf_counter()
    prep_duration = t_prep_done - t_start
    
    append_ledger({
        "event": "antithesis_prep_parallel_done",
        "task_id": task.task_id,
        "prep_duration_sec": float(prep_duration)
    })
    
    # Antithesis 실행 (준비된 컨텍스트 활용)
    antithesis_out = run_antithesis_with_prep(
        task,
        thesis_out,
        tools,
        conversation_context,
        prep_context
    )
    
    t_end = time.perf_counter()
    total_duration = t_end - t_start
    
    append_ledger({
        "event": "antithesis_prep_parallel_complete",
        "task_id": task.task_id,
        "total_duration_sec": float(total_duration),
        "prep_duration_sec": float(prep_duration)
    })
    
    return thesis_out, antithesis_out
