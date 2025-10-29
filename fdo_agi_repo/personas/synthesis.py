from __future__ import annotations
from typing import Dict, Any, List
import os
try:
    from fdo_agi_repo.orchestrator.contracts import TaskSpec, PersonaOutput, Action
    from fdo_agi_repo.orchestrator.memory_bus import append_ledger
except ModuleNotFoundError:
    from orchestrator.contracts import TaskSpec, PersonaOutput, Action  # type: ignore
    from orchestrator.memory_bus import append_ledger  # type: ignore
import time
import google.generativeai as genai

# Configure Google AI Studio API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyDTCQiXRrOMWqmq2REy2Zh8HQ8VvYJEbdQ")
genai.configure(api_key=GEMINI_API_KEY)

# Placeholder fallback function
def _compose_markdown(task: TaskSpec, thesis: str, anti: str, cites: list[dict]) -> str:
    lines = []
    lines.append(f"# 결과 요약: {task.title}")
    lines.append("")
    lines.append("## 목표")
    lines.append(f"- {task.goal}")
    lines.append("")
    lines.append("## 제안 (Thesis)")
    lines.append(thesis)
    lines.append("")
    lines.append("## 검증 (Antithesis)")
    lines.append(anti)
    lines.append("")
    lines.append("## 참고 (Local)")
    if cites:
        for c in cites:
            lines.append(f"- {c.get('source','local')}: {c.get('pointer','')}")
    else:
        lines.append("- (없음)")
    lines.append("")
    lines.append("## 다음 단계")
    lines.append("1. 참고 소스에서 핵심 근거 2개 발췌해 본문 보강")
    lines.append("2. 산출물 구조(서론-본론-결론)로 확장")
    lines.append("3. 품질 점검(간결성/근거성/완결성) 후 제출")
    return "\n".join(lines)

def run_synthesis(task: TaskSpec, outs: List[PersonaOutput], tools, conversation_context: str = "") -> PersonaOutput:
    # 1. 입력 데이터 준비
    cites: list[dict] = []
    for o in outs:
        cites.extend(o.citations)
    
    thesis_txt = next((o.summary for o in outs if o.persona == "thesis"), "(없음)")
    anti_txt   = next((o.summary for o in outs if o.persona == "antithesis"), "(없음)")

    # 2. 프롬프트 구성
    system_prompt = (
        "당신은 통합 편집자입니다. 상반되는 '제안(Thesis)'과 '비판(Antithesis)'을 모두 수용하여, "
        "하나의 완성도 높고 구조화된 결과 문서를 작성하세요. 최종 문서는 제안의 창의성과 비판의 날카로움을 모두 반영해야 합니다.\n\n"
        "⚠️ **필수 요구사항**:\n"
        "1. 최종 문서의 모든 주장은 **구체적인 근거(예: RAG 검색 결과, 논리적 추론 과정, 수치/통계)**로 뒷받침되어야 합니다.\n"
        "2. 각 핵심 주장 뒤에 근거 출처를 명시하거나 '[참고: ...]' 형태로 즉시 인용하세요.\n"
        "3. 근거 없는 일반적인 서술은 피하세요.\n"
        "4. 가능하면 2~3개 이상의 인용/근거를 포함하여 주장을 강화하세요."
    )
    
    # 대화 맥락 주입 (Phase 2: Persona Context Propagation)
    if conversation_context:
        system_prompt += f"\n\n{conversation_context}"
        system_prompt += "\n⚠️ **맥락 연계 필수**: 위 이전 대화에서 논의된 내용과 연관성이 있다면, 그 맥락을 최종 문서에 반영하고 일관성을 유지하십시오."

    # Prompt compaction
    def _compact(text: str, max_chars: int, head: int = 600, tail: int = 600) -> str:
        if max_chars <= 0 or len(text) <= max_chars:
            return text
        head = max(0, min(head, max_chars))
        tail = max(0, min(tail, max_chars - head))
        if head + tail >= max_chars:
            tail = max_chars - head
        return text[:head] + "\n... [중략/요약] ...\n" + text[-tail:]

    try:
        section_max = int(os.environ.get("SYNTHESIS_SECTION_MAX_CHARS", "900"))
    except Exception:
        section_max = 900
    
    thesis_comp = _compact(thesis_txt, section_max)
    anti_comp = _compact(anti_txt, section_max)

    user_prompt = (
        f"제안(Thesis):\n---\n{thesis_comp}\n---\n\n"
        f"비판(Antithesis):\n---\n{anti_comp}\n---\n\n"
        "지시사항: 위의 제안과 비판을 종합하여, '결과 요약, 목표, 제안, 검증, 참고(Local), 다음 단계' 섹션을 포함하는 최종 Markdown 문서를 생성하세요.\n"
        "⚠️ 작성 시 각 주장에 구체적인 근거(출처/데이터)를 인라인 형태로 반드시 포함하세요."
    )

    # 3. Gemini LLM 호출 (Google AI Studio API)
    doc: str
    err_text = None
    t_llm0 = time.perf_counter()
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(f"{system_prompt}\n\n{user_prompt}")
        doc = response.text
    except Exception as e:
        err_text = f"{type(e).__name__}: {e}"
        # LLM 호출 실패 시, 기존 placeholder 로직으로 폴백
        doc = _compose_markdown(task, thesis_txt, anti_txt, cites)

    t_llm1 = time.perf_counter()
    append_ledger({
        "event": "persona_llm_run",
        "task_id": task.task_id,
        "persona": "synthesis",
        "provider": "google-ai-studio",
        "model": "gemini-2.0-flash",
        "duration_sec": float(t_llm1 - t_llm0),
        "ok": bool(bool(doc) and not err_text),
        "error": err_text,
        "prompt_chars": len(system_prompt) + len(user_prompt)
    })

    # 4. 결과물 파일로 저장 및 PersonaOutput 반환
    tools.call("fileio", {"op":"write", "path":"sandbox/docs/result.md", "text": doc})

    summary = "[SYNTHESIS] 초안이 sandbox/docs/result.md에 저장되었습니다. '다음 단계'를 따라 증거를 보강하세요."
    action = Action(type="TOOL_CALL", tool="fileio", args={"op":"write","path":"sandbox/docs/result.md"})
    
    return PersonaOutput(
        task_id=task.task_id,
        persona="synthesis",
        summary=summary,
        citations=cites,
        actions=[action]
    )
