from __future__ import annotations
from typing import Dict, Any
import os
try:
    from fdo_agi_repo.orchestrator.contracts import TaskSpec, PersonaOutput
    from fdo_agi_repo.orchestrator.memory_bus import append_ledger
except ModuleNotFoundError:  # script-run fallback
    from orchestrator.contracts import TaskSpec, PersonaOutput  # type: ignore
    from orchestrator.memory_bus import append_ledger  # type: ignore
import time
import google.generativeai as genai

# Configure Google AI Studio API (no hardcoded default key)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)  # type: ignore[attr-defined]

# Placeholder fallback function
def _draft_thesis(goal: str, cites_count: int, cite_paths: list[str]) -> str:
    lines = []
    lines.append(f"[THESIS] 목표: {goal}")
    lines.append("- 접근: 3단계 실행 계획 수립 (요구 분석 → 근거 확보 → 산출물 작성)")
    lines.append(f"- 근거: 로컬 참조 {cites_count}개 활용 ({', '.join(cite_paths) if cite_paths else 'N/A'})")
    lines.append("- 출력: sandbox/docs/result.md에 초안 저장 및 증거 보강 계획 포함")
    return "\n".join(lines)

def run_thesis(task: TaskSpec, plan: Dict[str, Any], tools, conversation_context: str = "") -> PersonaOutput:
    # 1. 로컬 RAG 참조 확보
    cites = []
    rag_results_text = ""
    try:
        res = tools.call("rag", {"query": task.goal, "top_k": 3})
        rag_hits = res.get("hits", [])
        for it in rag_hits[:3]:
            cites.append({"source": it.get("source", "local"), "pointer": it.get("id", "")})
        rag_results_text = "\n".join([f"- {hit.get('id', '')}: {hit.get('text', '')[:150]}..." for hit in rag_hits])
    except Exception as e:
        append_ledger({"event": "rag_call_failed", "task_id": task.task_id, "persona": "thesis", "error": str(e)})

    # 2. 학습 컨텍스트(Few-shot) 확인
    learning_context = plan.get("learning_context", "")

    # 3. 프롬프트 구성 - 증거 기반 출력 강화
    prompt_parts = [
        "당신은 창의적 발산형 페르소나(Thesis)입니다. 분석가로서, 주어진 목표를 달성하기 위한 3단계 실행 계획을 제안하고, 로컬 근거 활용을 우선합니다.",
        "\n\n⚠️ **필수 요구사항 (CRITICAL)**: ",
        "\n1. **모든 주장에는 구체적인 근거 필수**: RAG 검색 결과, 참고 문헌, 데이터 포인트를 반드시 인용",
        "\n2. **근거 없는 일반론 금지**: \"일반적으로\", \"보통\" 같은 추상적 표현 대신 구체적 출처 명시",
        "\n3. **인용 형식**: [출처: {파일/문서명}] 또는 \"<참고: {검색결과ID}>\" 형태로 명시적 표기",
        "\n4. **증거 부족 시**: RAG 결과가 없다면 명시적으로 \"추가 조사 필요\" 또는 \"웹 검색 권장\" 표기"
    ]
    
    # 대화 맥락 주입 (Phase 2: Persona Context Propagation)
    if conversation_context:
        prompt_parts.append(f"\n\n{conversation_context}")
        prompt_parts.append("\n⚠️ **맥락 활용 필수**: 위 이전 대화 내용과 관련 있다면 반드시 언급하고, 일관성 있는 계획을 수립하십시오.")
    
    # RAG 검색 결과 평가
    rag_quality_msg = ""
    if rag_results_text:
        rag_quality_msg = f"\n✅ **검색 결과 {len(rag_hits)}건 확보됨** - 이를 반드시 활용하여 근거 기반 계획 수립"
    else:
        rag_quality_msg = "\n⚠️ **검색 결과 없음** - 일반적 지식만으로 작업 시 낮은 품질 예상. 웹 검색 또는 외부 참조 필요성 명시 권장"
    prompt_parts.append(rag_quality_msg)
    
    if learning_context:
        prompt_parts.append(f"\n\n--- 과거 학습된 성공 사례 ---\n{learning_context}")
    
    prompt_parts.append(f"\n\n--- 현재 작업 ---\n목표: {task.goal}")
    prompt_parts.append(f"\n\n--- 참고 가능한 RAG 검색 결과 ---\n{rag_results_text if rag_results_text else '(검색 결과 없음 - 외부 조사 필요)'}")
    prompt_parts.append(
        "\n\n=== ⚠️ CRITICAL: 증거 기반 계획 필수 요구사항 ===\n"
        "다음 4단계를 **반드시** 순서대로 수행하십시오:\n\n"
        
        "**1단계: RAG 검색 결과 검토**\n"
        "   - 제공된 RAG 검색 결과를 먼저 읽고 평가\n"
        "   - 각 검색 결과의 관련성과 신뢰도 판단\n"
        "   - 검색 결과가 충분하지 않으면 \"추가 웹 검색 필요: [구체적 키워드]\" 명시\n\n"
        
        "**2단계: 핵심 근거 선택 (최소 3개)**\n"
        "   - RAG 결과에서 가장 관련성 높은 3개 이상의 구체적 증거 선택\n"
        "   - 각 증거에 대해 출처를 명확히 기록 (파일명, 함수명, 줄 번호 등)\n"
        "   - 예시: [출처: pipeline.py의 EvidenceStage 클래스], [참고: 검색결과 #2의 설정 예시]\n\n"
        
        "**3단계: 증거 기반 실행 계획 작성**\n"
        "   - 각 작업 단계마다 **반드시** 1개 이상의 출처/근거를 명시\n"
        "   - 근거 없는 추측이나 일반론은 \"[가정: 추가 검증 필요]\"로 표시\n"
        "   - 계획의 모든 핵심 주장에 인용 포함\n\n"
        
        "**4단계: 품질 자가 검증**\n"
        "   - 작성한 계획에 3개 이상의 구체적 출처가 포함되었는지 확인\n"
        "   - 각 출처가 실제 제공된 RAG 결과에서 나왔는지 검증\n"
        "   - 부족하면 2단계로 돌아가 근거 추가\n\n"
        
        "📋 **출력 포맷 예시**:\n"
        "```\n"
        "## 작업 계획\n\n"
        "### 1. [작업명]\n"
        "[출처: config.md Line 15-20] 설정 파일에 따르면...\n"
        "[참고: 검색결과 #3] 유사 사례에서는...\n\n"
        "### 2. [작업명]\n"
        "[출처: pipeline.py의 run() 메서드] 파이프라인 구조상...\n"
        "```\n\n"
        
        "⚠️ **경고**: 출처 없는 계획은 자동으로 품질 0.4 이하로 평가되어 재작업 요구됩니다.\n"
        "           반드시 위 4단계 프로세스를 따라 **증거 기반 계획**을 작성하십시오."
    )
    
    prompt = "".join(prompt_parts)

    # 4. Gemini LLM 호출 (Google AI Studio API)
    summary = ""
    err_text = None
    t_llm0 = time.perf_counter()
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")  # type: ignore[attr-defined]
        response = model.generate_content(prompt)
        summary = response.text
    except Exception as e:
        err_text = f"{type(e).__name__}: {e}"
        # LLM 호출 실패 시, 기존 placeholder 로직으로 폴백
        summary = _draft_thesis(task.goal, len(cites), [c.get("pointer", "") for c in cites])
    
    t_llm1 = time.perf_counter()
    append_ledger({
        "event": "persona_llm_run",
        "task_id": task.task_id,
        "persona": "thesis",
        "provider": "google-ai-studio",
        "model": "gemini-2.0-flash",
        "duration_sec": float(t_llm1 - t_llm0),
        "ok": bool(bool(summary) and not err_text),
        "error": err_text,
        "prompt_chars": len(prompt)
    })

    # 5. PersonaOutput 반환
    return PersonaOutput(
        task_id=task.task_id,
        persona="thesis",
        summary=summary,
        citations=cites,
        actions=[]
    )