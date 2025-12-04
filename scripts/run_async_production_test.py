"""
Async Thesis 활성화 후 연속 테스트 실행
Production 환경에서 5개 태스크를 연속 실행하여 효과 측정
"""
import sys
import time
import uuid
from pathlib import Path


def run_single_task(task_num: int) -> dict:
    """단일 태스크 실행"""
    here = Path(__file__).resolve()
    root = here.parents[1]
    
    # Path setup
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    fdo = root / "fdo_agi_repo"
    if str(fdo) not in sys.path:
        sys.path.insert(0, str(fdo))
    
    from fdo_agi_repo.orchestrator import pipeline
    
    task_id = f"async-prod-{int(time.time())}-{uuid.uuid4().hex[:6]}"
    spec = {
        "task_id": task_id,
        "title": f"Async Thesis Production Test #{task_num}",
        "goal": f"Lightweight task to measure async thesis performance in production (test {task_num}/5).",
        "constraints": [],
        "inputs": {},
        "scope": "analysis",
        "permissions": ["READ"],
        "evidence_required": False,
    }
    
    start = time.time()
    print(f"\n[{task_num}/5] Starting: {task_id}")
    
    try:
        result = pipeline.run_task({}, spec)
        duration = time.time() - start
        status = result.get("status", "unknown")
        
        print(f"[{task_num}/5] Completed: {status} in {duration:.2f}s")
        
        return {
            "task_id": task_id,
            "status": status,
            "duration": duration,
            "success": True,
        }
    except Exception as e:
        duration = time.time() - start
        print(f"[{task_num}/5] Failed: {e}")
        
        return {
            "task_id": task_id,
            "status": "error",
            "duration": duration,
            "success": False,
            "error": str(e),
        }


def main(argv: list) -> int:
    print("=" * 70)
    print("  Async Thesis Production Test (5 Tasks)")
    print("=" * 70)
    print()
    
    results = []
    
    for i in range(1, 6):
        result = run_single_task(i)
        results.append(result)
        
        # 태스크 간 짧은 대기 (시스템 안정화)
        if i < 5:
            time.sleep(2)
    
    # 결과 요약
    print("\n" + "=" * 70)
    print("  Summary")
    print("=" * 70)
    
    successes = [r for r in results if r["success"]]
    failures = [r for r in results if not r["success"]]
    
    print(f"\nSuccess: {len(successes)}/5")
    print(f"Failure: {len(failures)}/5")
    
    if successes:
        durations = [r["duration"] for r in successes]
        print(f"\nDuration: min={min(durations):.2f}s, max={max(durations):.2f}s, avg={sum(durations)/len(durations):.2f}s")
    
    print("\nTask IDs:")
    for r in results:
        status_icon = "✓" if r["success"] else "✗"
        print(f"  {status_icon} {r['task_id']} ({r['duration']:.2f}s)")
    
    print("\n" + "=" * 70)
    print(f"Run analyze_ledger_async_comparison.py to see full analysis")
    print("=" * 70)
    
    return 0 if len(failures) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
