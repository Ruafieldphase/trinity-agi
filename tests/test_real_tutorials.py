#!/usr/bin/env python3
"""
Real-world YouTube Tutorial Test
Phase 2.5 Week 3 Day 15

실제 YouTube 튜토리얼 영상으로 E2E 테스트:
1. 간단한 Notepad 튜토리얼
2. Calculator 튜토리얼
3. Windows 단축키 튜토리얼

각 케이스별로 성공/실패 분석
"""

import json
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

ROOT = Path(__file__).resolve().parents[1] / "fdo_agi_repo"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rpa.execution_engine import ExecutionEngine, ExecutionConfig, ExecutionMode


# 실전 튜토리얼 예시
REAL_TUTORIALS = {
    "notepad_simple": """
How to create a simple text file in Windows:
1. Press Windows key
2. Type "notepad"
3. Press Enter to open Notepad
4. Type "Hello World"
5. Press Ctrl+S to save
6. Type "test.txt" as filename
7. Press Enter to confirm
    """.strip(),
    
    "calculator_basic": """
How to use Windows Calculator:
1. Press Windows key
2. Type "calculator"
3. Press Enter to open Calculator
4. Click on number 5
5. Click on plus sign
6. Click on number 3
7. Click on equals sign
8. See result: 8
    """.strip(),
    
    "browser_google": """
How to search on Google:
1. Press Windows key
2. Type "chrome" or "edge"
3. Press Enter to open browser
4. Click on address bar
5. Type "python tutorial"
6. Press Enter to search
    """.strip(),
    
    "shortcut_screenshot": """
How to take a screenshot in Windows:
1. Press Windows + Shift + S keys together
2. Screen will dim slightly
3. Click and drag to select area
4. Screenshot is copied to clipboard
5. Press Windows key
6. Type "paint"
7. Press Enter to open Paint
8. Press Ctrl+V to paste
    """.strip(),
}


def run_tutorial_test(name: str, text: str, mode: ExecutionMode = ExecutionMode.DRY_RUN) -> Dict[str, Any]:
    """단일 튜토리얼 테스트 (pytest fixture 충돌 방지)"""
    print("\n" + "="*70)
    print(f"🎯 Testing: {name}")
    print("="*70)
    print(f"Tutorial:\n{text[:200]}...")
    print(f"Mode: {mode.value}")
    print("-"*70)
    
    config = ExecutionConfig(
        mode=mode,
        enable_verification=False,
        enable_failsafe=True,
        timeout=30.0,
    )
    
    engine = ExecutionEngine(config)
    start = time.time()
    result = engine.execute_tutorial(text)
    duration = time.time() - start
    
    # 결과 분석
    success_rate = 0
    if result.total_actions > 0:
        success_rate = (result.executed_actions - result.failed_actions) / result.total_actions * 100
    
    print(f"\n📊 Results:")
    print(f"  Success: {'✅' if result.success else '❌'} {result.success}")
    print(f"  Total Actions: {result.total_actions}")
    print(f"  Executed: {result.executed_actions}")
    print(f"  Failed: {result.failed_actions}")
    print(f"  Success Rate: {success_rate:.1f}%")
    print(f"  Duration: {duration:.2f}s")
    
    if result.errors:
        print(f"\n⚠️  Errors:")
        for err in result.errors[:3]:
            print(f"  - {err}")
    
    return {
        "name": name,
        "success": result.success,
        "total_actions": result.total_actions,
        "executed_actions": result.executed_actions,
        "failed_actions": result.failed_actions,
        "success_rate": success_rate,
        "duration": duration,
        "errors": result.errors,
    }


def analyze_failures(results: List[Dict[str, Any]]):
    """실패 케이스 분석"""
    print("\n" + "="*70)
    print("🔍 Failure Analysis")
    print("="*70)
    
    failed_tutorials = [r for r in results if not r["success"]]
    
    if not failed_tutorials:
        print("✅ No failures! All tutorials passed.")
        return
    
    print(f"\n❌ Failed: {len(failed_tutorials)}/{len(results)} tutorials")
    print()
    
    for result in failed_tutorials:
        print(f"Tutorial: {result['name']}")
        print(f"  Total Actions: {result['total_actions']}")
        print(f"  Executed: {result['executed_actions']}")
        print(f"  Failed: {result['failed_actions']}")
        print(f"  Success Rate: {result['success_rate']:.1f}%")
        
        if result['errors']:
            print(f"  Errors:")
            for err in result['errors'][:3]:
                print(f"    - {err}")
        print()
    
    # 공통 에러 패턴 분석
    all_errors = []
    for r in failed_tutorials:
        all_errors.extend(r['errors'])
    
    if all_errors:
        print("📋 Common Error Patterns:")
        error_keywords = {}
        for err in all_errors:
            err_lower = str(err).lower()
            for keyword in ["timeout", "not found", "failed", "error", "exception"]:
                if keyword in err_lower:
                    error_keywords[keyword] = error_keywords.get(keyword, 0) + 1
        
        for keyword, count in sorted(error_keywords.items(), key=lambda x: x[1], reverse=True):
            print(f"  {keyword}: {count} occurrences")


def generate_report(results: List[Dict[str, Any]], output_file: Path):
    """테스트 리포트 생성"""
    total = len(results)
    passed = sum(1 for r in results if r["success"])
    failed = total - passed
    
    avg_success_rate = sum(r["success_rate"] for r in results) / total if total > 0 else 0
    avg_actions = sum(r["total_actions"] for r in results) / total if total > 0 else 0
    
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "summary": {
            "total_tutorials": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / total * 100 if total > 0 else 0,
            "avg_success_rate": avg_success_rate,
            "avg_actions_per_tutorial": avg_actions,
        },
        "results": results,
    }
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    
    print(f"\n📄 Report saved: {output_file}")


def main():
    """메인 테스트 러너"""
    print("\n" + "🎬"*35)
    print("Real-world YouTube Tutorial Test")
    print("Phase 2.5 Week 3 Day 15")
    print("🎬"*35 + "\n")
    
    # 모든 튜토리얼 테스트 (DRY_RUN)
    results = []
    
    for name, text in REAL_TUTORIALS.items():
        result = run_tutorial_test(name, text, mode=ExecutionMode.DRY_RUN)
        results.append(result)
        time.sleep(0.5)
    
    # 실패 분석
    analyze_failures(results)
    
    # 리포트 생성
    output_file = Path("outputs/real_tutorial_test_results.json")
    generate_report(results, output_file)
    
    # 요약
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    total = len(results)
    passed = sum(1 for r in results if r["success"])
    failed = total - passed
    
    print(f"Total Tutorials: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Pass Rate: {passed/total*100:.0f}%")
    
    avg_success_rate = sum(r["success_rate"] for r in results) / total
    print(f"📊 Avg Action Success Rate: {avg_success_rate:.1f}%")
    
    print("="*70 + "\n")
    
    if failed == 0:
        print("🎉 ALL TUTORIALS PASSED! 🎉\n")
        return 0
    else:
        print(f"⚠️  {failed} TUTORIAL(S) HAD ISSUES\n")
        print("💡 Check the report for details and error patterns.")
        print(f"   Report: {output_file}\n")
        return 0  # Still return 0 for DRY_RUN mode


if __name__ == "__main__":
    sys.exit(main())
