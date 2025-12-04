"""
메모리 검색 및 Few-shot Learning 모듈
과거 성공 사례를 찾아 프롬프트에 주입
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
import json
import os

def search_memory_for_success_cases(
    task_id: str,
    min_quality: float = 0.8,
    top_k: int = 3,
    ledger_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Resonance Ledger에서 고품질(quality >= min_quality) 과거 실행 사례를 검색
    """
    if ledger_path is None:
        ledger_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "memory",
            "resonance_ledger.jsonl"
        )
    
    if not os.path.exists(ledger_path):
        return []
    
    success_cases = []
    
    try:
        with open(ledger_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    entry = json.loads(line)
                    if entry.get("event") == "eval":
                        eval_data = entry.get("eval", {})
                        quality = float(eval_data.get("quality", 0.0))
                        
                        if quality >= min_quality:
                            success_cases.append({
                                "task_id": eval_data.get("task_id", "unknown"),
                                "quality": quality,
                                "evidence_ok": eval_data.get("evidence_ok", False),
                                "notes": eval_data.get("notes", "")
                            })
                except json.JSONDecodeError:
                    continue
    except Exception:
        return []
    
    success_cases.sort(key=lambda x: x["quality"], reverse=True)
    return success_cases[:top_k]

def build_few_shot_prompt(
    success_cases: List[Dict[str, Any]],
    current_task_goal: str,
    current_problem: str
) -> str:
    """
    과거 성공 사례와 현재 문제점을 바탕으로 메타-학습 프롬프트 생성
    """
    if not success_cases:
        # 과거 성공 사례가 없으면, 간단한 재시도 지시
        return (
            f"이전 시도에서 다음 문제를 발견했습니다: {current_problem}. "
            "다른 접근 방식으로 목표를 다시 시도하세요."
        )

    prompt_parts = [
        "당신은 스스로의 결과물을 개선하는 메타-학습 AI입니다.",
        "이전 시도에서 다음 문제를 발견했습니다:",
        f"- 문제점: {current_problem}",
        "\n참고할 만한 과거의 성공적인 작업 패턴은 다음과 같습니다:"
    ]

    for i, case in enumerate(success_cases, 1):
        prompt_parts.append(f"\n[성공 사례 #{i}] (품질: {case['quality']:.2f}) - 특징: {case.get('notes', 'N/A')}")

    prompt_parts.extend([
        "\n[새로운 지시사항]",
        f"현재 목표: {current_task_goal}",
        "위의 문제점을 해결하고, 과거 성공 사례의 패턴을 적용하여 완전히 새로운, 개선된 결과물을 생성하세요."
    ])

    return "\n".join(prompt_parts)

def adaptive_replan_with_learning(
    eval_report: Any,
    task_goal: str,
    memory_snapshot: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    평가 결과를 기반으로 재계획 여부 결정 + Few-shot Learning 적용
    """
    from .config import get_evaluation_config
    
    eval_cfg = get_evaluation_config()
    min_quality_threshold = float(eval_cfg.get("min_quality", 0.6))
    
    should_replan = (
        eval_report.quality < min_quality_threshold or
        not eval_report.evidence_ok
    )
    
    if not should_replan:
        return {
            "replan": False,
            "enhanced_prompt": "",
            "strategy": "no_replan_needed",
            "success_cases": []
        }
    
    # 1. 과거 성공 사례 검색
    success_cases = search_memory_for_success_cases(
        task_id=eval_report.task_id,
        min_quality=0.8,  # 고품질 사례만
        top_k=3
    )
    
    # 2. 개선된 Few-shot 프롬프트 생성
    enhanced_prompt = build_few_shot_prompt(
        success_cases=success_cases,
        current_task_goal=task_goal,
        current_problem=eval_report.notes or "품질 미달"
    )
    
    return {
        "replan": True,
        "enhanced_prompt": enhanced_prompt,
        "strategy": "few_shot_learning" if success_cases else "simple_retry",
        "success_cases": success_cases
    }