#!/usr/bin/env python3
"""
Production 통합 테스트 스위트

P2.2 dotenv 수정 후 시스템 전체 안정성 검증
- 다양한 시나리오 테스트 (20개)
- Replan 발생 여부 확인
- Corrections_enabled 설정 검증
- Evidence gate 정상 작동 확인
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any

# Repo root 경로 추가
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from orchestrator.pipeline import run_task


# 테스트 시나리오 정의
TEST_SCENARIOS = [
    # 카테고리 1: 일반 작업 (5개)
    {
        "id": "general_001",
        "title": "최근 AGI 개선사항 요약",
        "goal": "AGI 시스템의 최근 1주일간 개선사항을 요약하고 성과를 분석해주세요",
        "expected": "quality >= 0.6, evidence_ok=True, replan=False"
    },
    {
        "id": "general_002",
        "title": "Replan 문제 분석",
        "goal": "Replan이 발생하는 원인과 해결 방법을 설명해주세요",
        "expected": "quality >= 0.6, evidence_ok=True, replan=False"
    },
    {
        "id": "general_003",
        "title": "Evidence gate 동작 설명",
        "goal": "Evidence gate가 어떻게 작동하는지 설명해주세요",
        "expected": "quality >= 0.6, evidence_ok=True, replan=False"
    },
    {
        "id": "general_004",
        "title": "Config 설정 가이드",
        "goal": "AGI 시스템의 config 설정 방법을 설명해주세요",
        "expected": "quality >= 0.6, evidence_ok=True, replan=False"
    },
    {
        "id": "general_005",
        "title": "dotenv 사용법",
        "goal": "Python에서 dotenv를 사용하는 방법과 장점을 설명해주세요",
        "expected": "quality >= 0.6, evidence_ok=True, replan=False"
    },

    # 카테고리 2: 복잡한 작업 (5개)
    {
        "id": "complex_001",
        "title": "AGI 아키텍처 분석",
        "goal": "AGI 시스템의 전체 아키텍처를 분석하고, Thesis-Antithesis-Synthesis 패턴의 장단점을 평가해주세요",
        "expected": "quality >= 0.6, evidence_ok=True, replan=False"
    },
    {
        "id": "complex_002",
        "title": "성능 최적화 전략",
        "goal": "Local LLM, Second Pass, Replan 최적화 작업의 전체적인 전략과 시너지 효과를 분석해주세요",
        "expected": "quality >= 0.6, evidence_ok=True, replan=False"
    },
    {
        "id": "complex_003",
        "title": "시스템 통합 분석",
        "goal": "Core Gateway, Phase 5 오케스트레이션, AGI 시스템이 어떻게 통합되어 작동하는지 분석해주세요",
        "expected": "quality >= 0.6, evidence_ok=True, replan=False"
    },
    {
        "id": "complex_004",
        "title": "모니터링 시스템 설계",
        "goal": "AGI 시스템의 모니터링 전략을 설계하고, 핵심 지표와 알람 기준을 제안해주세요",
        "expected": "quality >= 0.6, evidence_ok=True, replan=False"
    },
    {
        "id": "complex_005",
        "title": "배포 전략 수립",
        "goal": "AGI 시스템의 Production 배포 전략을 수립하고, 리스크와 대응 방안을 분석해주세요",
        "expected": "quality >= 0.6, evidence_ok=True, replan=False"
    },

    # 카테고리 3: 기술적 질문 (5개)
    {
        "id": "technical_001",
        "title": "Meta-Cognition 구현",
        "goal": "Meta-Cognition 시스템의 구현 원리와 confidence 계산 방법을 설명해주세요",
        "expected": "quality >= 0.6, evidence_ok=True, replan=False"
    },
    {
        "id": "technical_002",
        "title": "RAG 통합",
        "goal": "RAG가 AGI 시스템에 어떻게 통합되어 있고, evidence gate에서 어떻게 활용되는지 설명해주세요",
        "expected": "quality >= 0.6, evidence_ok=True, replan=False"
    },
    {
        "id": "technical_003",
        "title": "LRU Cache 관리",
        "goal": "@lru_cache를 사용한 config 캐싱의 장단점과 주의사항을 설명해주세요",
        "expected": "quality >= 0.6, evidence_ok=True, replan=False"
    },
    {
        "id": "technical_004",
        "title": "환경변수 우선순위",
        "goal": "Python에서 환경변수의 우선순위 (.env, export, config file)와 best practice를 설명해주세요",
        "expected": "quality >= 0.6, evidence_ok=True, replan=False"
    },
    {
        "id": "technical_005",
        "title": "Pydantic 검증",
        "goal": "TaskSpec에서 Pydantic을 사용한 검증의 장점과 활용 방법을 설명해주세요",
        "expected": "quality >= 0.6, evidence_ok=True, replan=False"
    },

    # 카테고리 4: 비교/분석 (5개)
    {
        "id": "comparison_001",
        "title": "P2.1 vs P2.2 비교",
        "goal": "P2.1 (프롬프트 개선)과 P2.2 (Evidence gate)의 차이점과 시너지 효과를 비교 분석해주세요",
        "expected": "quality >= 0.6, evidence_ok=True, replan=False"
    },
    {
        "id": "comparison_002",
        "title": "Before vs After",
        "goal": "dotenv 수정 전후의 시스템 동작 차이를 비교하고, 개선 효과를 분석해주세요",
        "expected": "quality >= 0.6, evidence_ok=True, replan=False"
    },
    {
        "id": "comparison_003",
        "title": "Local vs Cloud LLM",
        "goal": "Local LLM (Gemini 2.0 Flash)과 Cloud API 사용의 장단점을 비교해주세요",
        "expected": "quality >= 0.6, evidence_ok=True, replan=False"
    },
    {
        "id": "comparison_004",
        "title": "Thesis vs Synthesis",
        "goal": "Thesis와 Synthesis 페르소나의 역할 차이와 각각의 중요성을 비교해주세요",
        "expected": "quality >= 0.6, evidence_ok=True, replan=False"
    },
    {
        "id": "comparison_005",
        "title": "테스트 vs Production",
        "goal": "테스트 환경과 Production 환경에서의 차이점과 검증 전략을 비교해주세요",
        "expected": "quality >= 0.6, evidence_ok=True, replan=False"
    }
]


def run_test_scenario(scenario: Dict[str, Any], tool_cfg: Dict[str, Any]) -> Dict[str, Any]:
    """단일 테스트 시나리오 실행"""
    test_id = scenario["id"]
    print(f"\n{'='*60}")
    print(f"Test: {test_id} - {scenario['title']}")
    print(f"{'='*60}")
    print(f"Goal: {scenario['goal']}")
    print(f"Expected: {scenario['expected']}")

    # TaskSpec 생성
    spec = {
        "task_id": f"prod_test_{test_id}_{int(time.time())}",
        "title": scenario["title"],
        "goal": scenario["goal"]
    }

    # 실행
    start_time = time.perf_counter()
    try:
        result = run_task(tool_cfg, spec)
        duration = time.perf_counter() - start_time

        # 결과 수집
        task_id = result.get("task_id")
        citations = result.get("citations", [])

        # 레저에서 평가 정보 추출
        eval_info = extract_eval_from_ledger(task_id)

        test_result = {
            "test_id": test_id,
            "title": scenario["title"],
            "task_id": task_id,
            "status": "success",
            "duration_sec": duration,
            "citations_count": len(citations),
            **eval_info
        }

        # 결과 출력
        print(f"\nResult:")
        print(f"  Status: SUCCESS")
        print(f"  Duration: {duration:.2f}s")
        print(f"  Corrections enabled: {test_result.get('corrections_enabled')}")
        print(f"  Quality: {test_result.get('quality')}")
        print(f"  Evidence OK: {test_result.get('evidence_ok')}")
        print(f"  Replan: {test_result.get('replan')}")
        print(f"  Citations: {len(citations)}")
        print(f"  Evidence correction: {test_result.get('evidence_correction_attempted')}")

        return test_result

    except Exception as e:
        duration = time.perf_counter() - start_time
        print(f"\nResult: FAILED - {type(e).__name__}: {e}")
        return {
            "test_id": test_id,
            "title": scenario["title"],
            "status": "failed",
            "error": f"{type(e).__name__}: {e}",
            "duration_sec": duration
        }


def extract_eval_from_ledger(task_id: str) -> Dict[str, Any]:
    """레저에서 task의 평가 정보 추출"""
    ledger_path = repo_root / "memory" / "resonance_ledger.jsonl"

    eval_info = {
        "corrections_enabled": None,
        "quality": None,
        "evidence_ok": None,
        "replan": None,
        "evidence_correction_attempted": False,
        "evidence_correction_added": 0
    }

    try:
        with open(ledger_path, 'r', encoding='utf-8') as f:
            for line in f:
                evt = json.loads(line.strip())
                if evt.get("task_id") == task_id:
                    event_type = evt.get("event")

                    if event_type == "run_config":
                        eval_info["corrections_enabled"] = evt.get("corrections", {}).get("enabled")

                    elif event_type == "eval":
                        # 첫 번째 eval만 사용 (initial evaluation)
                        if eval_info["quality"] is None:
                            eval_info["quality"] = evt.get("quality")
                            eval_info["evidence_ok"] = evt.get("evidence_ok")

                    elif event_type == "rune":
                        # 첫 번째 rune만 사용
                        if eval_info["replan"] is None:
                            rune = evt.get("rune", {})
                            eval_info["replan"] = rune.get("replan")

                    elif event_type == "evidence_correction":
                        eval_info["evidence_correction_attempted"] = evt.get("attempted", False)
                        eval_info["evidence_correction_added"] = evt.get("added", 0)

    except Exception as e:
        print(f"Warning: Failed to extract eval info from ledger: {e}")

    return eval_info


def analyze_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """테스트 결과 분석"""
    total = len(results)
    successful = sum(1 for r in results if r["status"] == "success")
    failed = total - successful

    # 성공한 테스트만 분석
    success_results = [r for r in results if r["status"] == "success"]

    if not success_results:
        return {
            "total_tests": total,
            "successful": 0,
            "failed": total,
            "success_rate": 0.0
        }

    # 핵심 지표
    corrections_enabled_count = sum(1 for r in success_results if r.get("corrections_enabled") is True)
    high_quality_count = sum(1 for r in success_results if r.get("quality", 0) >= 0.6)
    evidence_ok_count = sum(1 for r in success_results if r.get("evidence_ok") is True)
    replan_count = sum(1 for r in success_results if r.get("replan") is True)
    evidence_correction_count = sum(1 for r in success_results if r.get("evidence_correction_attempted") is True)

    # 평균값
    avg_quality = sum(r.get("quality", 0) for r in success_results) / len(success_results)
    avg_duration = sum(r.get("duration_sec", 0) for r in success_results) / len(success_results)
    avg_citations = sum(r.get("citations_count", 0) for r in success_results) / len(success_results)

    analysis = {
        "total_tests": total,
        "successful": successful,
        "failed": failed,
        "success_rate": successful / total,

        # P2.2 검증 핵심 지표
        "corrections_enabled_rate": corrections_enabled_count / len(success_results),
        "high_quality_rate": high_quality_count / len(success_results),
        "evidence_ok_rate": evidence_ok_count / len(success_results),
        "replan_rate": replan_count / len(success_results),
        "evidence_correction_rate": evidence_correction_count / len(success_results),

        # 평균값
        "avg_quality": avg_quality,
        "avg_duration_sec": avg_duration,
        "avg_citations": avg_citations,

        # 절대값
        "replan_count": replan_count,
        "evidence_correction_count": evidence_correction_count,
        "corrections_enabled_count": corrections_enabled_count
    }

    return analysis


def print_summary(analysis: Dict[str, Any], results: List[Dict[str, Any]]):
    """결과 요약 출력"""
    print("\n" + "="*60)
    print("PRODUCTION TEST SUMMARY")
    print("="*60)

    print(f"\n📊 Overall Results:")
    print(f"  Total tests: {analysis['total_tests']}")
    print(f"  Successful: {analysis['successful']} ({analysis['success_rate']*100:.1f}%)")
    print(f"  Failed: {analysis['failed']}")

    print(f"\n🎯 P2.2 Validation (핵심 지표):")
    print(f"  Corrections enabled: {analysis['corrections_enabled_count']}/{analysis['successful']} ({analysis['corrections_enabled_rate']*100:.1f}%)")
    print(f"  High quality (>=0.6): {analysis['successful'] if analysis.get('high_quality_rate') else 0}/{analysis['successful']} ({analysis.get('high_quality_rate', 0)*100:.1f}%)")
    print(f"  Evidence OK: {analysis['successful'] if analysis.get('evidence_ok_rate') else 0}/{analysis['successful']} ({analysis.get('evidence_ok_rate', 0)*100:.1f}%)")
    print(f"  Replan count: {analysis['replan_count']} ({analysis['replan_rate']*100:.1f}%)")
    print(f"  Evidence correction: {analysis['evidence_correction_count']} ({analysis['evidence_correction_rate']*100:.1f}%)")

    print(f"\n📈 Performance:")
    print(f"  Avg quality: {analysis['avg_quality']:.3f}")
    print(f"  Avg duration: {analysis['avg_duration_sec']:.2f}s")
    print(f"  Avg citations: {analysis['avg_citations']:.1f}")

    # P2.2 검증 결과
    print(f"\n✅ P2.2 Validation Result:")
    if analysis['corrections_enabled_rate'] >= 0.95 and analysis['replan_rate'] <= 0.10:
        print(f"  🟢 PASS - dotenv 수정 정상 작동!")
        print(f"    - Corrections enabled: {analysis['corrections_enabled_rate']*100:.1f}% (>= 95%)")
        print(f"    - Replan rate: {analysis['replan_rate']*100:.1f}% (<= 10%)")
    else:
        print(f"  🔴 FAIL - 추가 조사 필요")
        if analysis['corrections_enabled_rate'] < 0.95:
            print(f"    ❌ Corrections enabled: {analysis['corrections_enabled_rate']*100:.1f}% (target >= 95%)")
        if analysis['replan_rate'] > 0.10:
            print(f"    ❌ Replan rate: {analysis['replan_rate']*100:.1f}% (target <= 10%)")

    # 실패한 테스트 표시
    if analysis['failed'] > 0:
        print(f"\n❌ Failed Tests:")
        for r in results:
            if r["status"] == "failed":
                print(f"  - {r['test_id']}: {r.get('error', 'Unknown error')}")

    # Replan 발생 케이스 표시
    if analysis['replan_count'] > 0:
        print(f"\n⚠️ Replan Cases:")
        for r in results:
            if r["status"] == "success" and r.get("replan") is True:
                print(f"  - {r['test_id']}: quality={r.get('quality')}, evidence_ok={r.get('evidence_ok')}")


def main():
    """메인 실행"""
    print("="*60)
    print("PRODUCTION INTEGRATION TEST SUITE")
    print("="*60)
    print(f"Start time: {datetime.now(timezone.utc).isoformat()}")
    print(f"Total scenarios: {len(TEST_SCENARIOS)}")
    print(f"Target: Validate P2.2 dotenv fix")
    print("="*60)

    tool_cfg = {}
    results = []

    # 테스트 실행
    for i, scenario in enumerate(TEST_SCENARIOS, 1):
        print(f"\n\n[{i}/{len(TEST_SCENARIOS)}] Running test...")
        result = run_test_scenario(scenario, tool_cfg)
        results.append(result)

        # 짧은 휴식 (LLM API rate limit 고려)
        if i < len(TEST_SCENARIOS):
            time.sleep(2)

    # 결과 분석
    analysis = analyze_results(results)

    # 요약 출력
    print_summary(analysis, results)

    # 결과 저장
    output_dir = repo_root / "outputs"
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"production_test_results_{timestamp}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "analysis": analysis,
            "results": results
        }, f, indent=2, ensure_ascii=False)

    print(f"\n📁 Results saved to: {output_file}")

    # 최종 판정
    if analysis['corrections_enabled_rate'] >= 0.95 and analysis['replan_rate'] <= 0.10:
        print(f"\n🎉 P2.2 VALIDATION: PASS")
        return 0
    else:
        print(f"\n⚠️ P2.2 VALIDATION: NEEDS INVESTIGATION")
        return 1


if __name__ == "__main__":
    sys.exit(main())
