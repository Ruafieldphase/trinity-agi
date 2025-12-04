#!/usr/bin/env python3
"""
빠른 검증 스크립트 (5개 대표 시나리오)

P2.2 dotenv 수정 후 즉시 검증용
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime, timezone

# Repo root 경로 추가
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from orchestrator.pipeline import run_task


# 대표 시나리오 (카테고리별 1개씩)
QUICK_SCENARIOS = [
    {
        "id": "general_001",
        "title": "최근 AGI 개선사항 요약",
        "goal": "AGI 시스템의 최근 1주일간 개선사항을 요약하고 성과를 분석해주세요"
    },
    {
        "id": "complex_001",
        "title": "AGI 아키텍처 분석",
        "goal": "AGI 시스템의 전체 아키텍처를 분석하고, Thesis-Antithesis-Synthesis 패턴의 장단점을 평가해주세요"
    },
    {
        "id": "technical_002",
        "title": "RAG 통합",
        "goal": "RAG가 AGI 시스템에 어떻게 통합되어 있고, evidence gate에서 어떻게 활용되는지 설명해주세요"
    },
    {
        "id": "comparison_001",
        "title": "P2.1 vs P2.2 비교",
        "goal": "P2.1 (프롬프트 개선)과 P2.2 (Evidence gate)의 차이점과 시너지 효과를 비교 분석해주세요"
    },
    {
        "id": "comparison_002",
        "title": "Before vs After",
        "goal": "dotenv 수정 전후의 시스템 동작 차이를 비교하고, 개선 효과를 분석해주세요"
    }
]


def extract_eval_from_ledger(task_id: str) -> dict:
    """레저에서 task의 평가 정보 추출"""
    ledger_path = repo_root / "memory" / "resonance_ledger.jsonl"

    eval_info = {
        "corrections_enabled": None,
        "quality": None,
        "evidence_ok": None,
        "replan": None,
        "evidence_correction_attempted": False
    }

    try:
        with open(ledger_path, 'r', encoding='utf-8') as f:
            for line in f:
                evt = json.loads(line.strip())
                if evt.get("task_id") == task_id:
                    event_type = evt.get("event")

                    if event_type == "run_config":
                        eval_info["corrections_enabled"] = evt.get("corrections", {}).get("enabled")
                    elif event_type == "eval" and eval_info["quality"] is None:
                        eval_info["quality"] = evt.get("quality")
                        eval_info["evidence_ok"] = evt.get("evidence_ok")
                    elif event_type == "rune" and eval_info["replan"] is None:
                        eval_info["replan"] = evt.get("rune", {}).get("replan")
                    elif event_type == "evidence_correction":
                        eval_info["evidence_correction_attempted"] = evt.get("attempted", False)

    except Exception as e:
        print(f"Warning: {e}")

    return eval_info


def main():
    print("="*60)
    print("QUICK VALIDATION (5 scenarios)")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Purpose: Validate P2.2 dotenv fix\n")

    tool_cfg = {}
    results = []

    for i, scenario in enumerate(QUICK_SCENARIOS, 1):
        print(f"\n[{i}/5] {scenario['title']}")
        print(f"Goal: {scenario['goal'][:60]}...")

        spec = {
            "task_id": f"quick_val_{scenario['id']}_{int(time.time())}",
            "title": scenario["title"],
            "goal": scenario["goal"]
        }

        start = time.perf_counter()
        try:
            result = run_task(tool_cfg, spec)
            duration = time.perf_counter() - start

            task_id = result.get("task_id")
            citations = len(result.get("citations", []))
            eval_info = extract_eval_from_ledger(task_id)

            print(f"  Duration: {duration:.1f}s")
            print(f"  Corrections: {eval_info['corrections_enabled']}")
            print(f"  Quality: {eval_info['quality']}")
            print(f"  Evidence OK: {eval_info['evidence_ok']}")
            print(f"  Replan: {eval_info['replan']}")
            print(f"  Citations: {citations}")

            results.append({
                "test_id": scenario["id"],
                "status": "success",
                **eval_info,
                "duration": duration,
                "citations": citations
            })

        except Exception as e:
            print(f"  FAILED: {e}")
            results.append({
                "test_id": scenario["id"],
                "status": "failed",
                "error": str(e)
            })

        if i < 5:
            time.sleep(2)

    # 분석
    success = [r for r in results if r["status"] == "success"]
    corrections_ok = sum(1 for r in success if r.get("corrections_enabled") is True)
    no_replan = sum(1 for r in success if r.get("replan") is False)

    print(f"\n{'='*60}")
    print("RESULTS")
    print(f"{'='*60}")
    print(f"Total: {len(results)}")
    print(f"Success: {len(success)}/5")
    print(f"Corrections enabled: {corrections_ok}/{len(success)}")
    print(f"No replan: {no_replan}/{len(success)}")

    if len(success) == 5 and corrections_ok == 5 and no_replan == 5:
        print(f"\n✅ PASS - P2.2 dotenv fix working!")
        return 0
    else:
        print(f"\n⚠️ NEEDS INVESTIGATION")
        if corrections_ok < len(success):
            print(f"  - Corrections not fully enabled")
        if no_replan < len(success):
            print(f"  - Replan still occurring")
        return 1


if __name__ == "__main__":
    sys.exit(main())
