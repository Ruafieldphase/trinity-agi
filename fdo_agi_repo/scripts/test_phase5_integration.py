"""
Phase 5: End-to-End Integration Test
모든 AGI 컴포넌트가 함께 작동하는지 종합 검증

테스트 시나리오:
1. Learning + Meta-cognition 동시 작동
2. Low quality → Learning → Improvement 전체 흐름
3. Low confidence → Warning + Delegation readiness
4. Performance metrics 수집
"""

import sys
import os
import json
import time
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from orchestrator.pipeline import run_task
from orchestrator.memory_bus import tail_ledger
from orchestrator.meta_cognition import MetaCognitionSystem
from orchestrator.tool_registry import ToolRegistry

REPO_ROOT = Path(__file__).resolve().parent.parent
MEMORY_DIR = REPO_ROOT / "memory"


def _memory_path(filename: str) -> Path:
    """Helper to resolve memory artifacts regardless of current working dir."""
    return MEMORY_DIR / filename

def test_end_to_end_integration():
    """End-to-end 통합 테스트 - 모든 AGI 기능 동시 작동"""
    
    print("=" * 80)
    print("🧪 AGI Phase 5: End-to-End Integration Test")
    print("=" * 80)
    print()
    
    # Test scenario 1: Complex task that triggers all systems
    print("📌 Scenario 1: Complex Python task (triggers meta-cognition + learning)")
    print("-" * 80)
    
    task_spec = {
        "task_id": f"integration_test_{int(time.time())}",
        "title": "Python 고급 기법",
        "goal": "Python 데코레이터와 제너레이터의 차이를 5문장으로 설명하고, 각각의 실제 사용 예시 코드를 제공해주세요",
        "scope": "doc"
    }
    
    tool_cfg = {"enabled": True}
    
    print(f"Task: {task_spec['goal']}")
    print()
    
    start_time = time.time()
    
    try:
        # Phase 1-4 통합 실행
        result = run_task(tool_cfg, task_spec)
        
        elapsed = time.time() - start_time
        
        print(f"✅ Task completed in {elapsed:.2f}s")
        print(f"   Task ID: {result['task_id']}")
        print(f"   Summary: {result['summary'][:100]}...")
        print(f"   Citations: {len(result['citations'])} sources")
        print()
        
        # Ledger에서 이벤트 분석
        print("📊 Analyzing Ledger events...")
        print("-" * 80)
        
        ledger_path = _memory_path("resonance_ledger.jsonl")
        coordinate_path = _memory_path("coordinate.jsonl")
        
        if not ledger_path.exists():
            print("⚠️  Ledger file not found!")
            return False
        
        # 최근 이벤트 분석 (Ledger + Coordinate)
        events = []
        
        # Resonance Ledger
        with open(ledger_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    events.append(json.loads(line))
                except:
                    pass
        
        # Coordinate (task_start, task_end)
        if coordinate_path.exists():
            with open(coordinate_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            events.append(json.loads(line))
                        except:
                            pass
        
        # 현재 task 관련 이벤트만 필터링
        task_events = [e for e in events if e.get('task_id') == task_spec['task_id']]
        
        if not task_events:
            print("⚠️  No events found for this task!")
            return False
        
        # 이벤트 타입별 카운트
        event_types = {}
        for e in task_events:
            event_type = e.get('event', 'unknown')
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        print(f"Total events for task: {len(task_events)}")
        for event_type, count in sorted(event_types.items()):
            print(f"   - {event_type}: {count}")
        print()
        
        # Phase별 검증
        phases_validated = {
              "phase1_execution": "task_end" in event_types,  # task_end만 있어도 실행 완료 확인
            "phase2_llm": "eval" in event_types,
            "phase3_learning": "learning" in event_types,
            "phase4_meta_cognition": "meta_cognition" in event_types
        }
        
        print("🔍 Phase Validation:")
        print("-" * 80)
        for phase, validated in phases_validated.items():
            status = "✅" if validated else "❌"
            print(f"{status} {phase}: {'PASS' if validated else 'FAIL'}")
        print()
        
        # Meta-cognition 상세 분석
        meta_events = [e for e in task_events if e.get('event') == 'meta_cognition']
        if meta_events:
            print("🧠 Meta-Cognition Analysis:")
            print("-" * 80)
            for meta in meta_events:
                print(f"   Persona: {meta.get('persona')}")
                print(f"   Confidence: {meta.get('confidence', 0):.3f}")
                print(f"   Past performance: {meta.get('past_performance', 0):.3f}")
                print(f"   Tools availability: {meta.get('tools_availability', 0):.3f}")
                print(f"   Domain: {meta.get('domain')}")
                print(f"   Should delegate: {meta.get('should_delegate')}")
                print(f"   Reason: {meta.get('reason')}")
            print()
        
        # Learning 상세 분석
        learning_events = [e for e in task_events if e.get('event') == 'learning']
        if learning_events:
            print("📚 Learning Analysis:")
            print("-" * 80)
            for learn in learning_events:
                print(f"   Strategy: {learn.get('strategy')}")
                print(f"   Success cases found: {learn.get('success_cases_found')}")
                print(f"   Enhanced prompt length: {learn.get('enhanced_prompt_length')}")
            print()
        
        # Second pass 발생 여부
        second_pass = "second_pass" in event_types
        if second_pass:
            print("🔄 Second Pass Detection:")
            print("-" * 80)
            print("   ✅ Second pass occurred (system triggered self-correction)")
            print()
        
        # 종합 평가
        all_phases_pass = all(phases_validated.values())
        
        print("=" * 80)
        print("🎯 Integration Test Result:")
        print("=" * 80)
        
        if all_phases_pass:
            print("✅ ALL PHASES INTEGRATED SUCCESSFULLY!")
            print()
            print("AGI System Status:")
            print("   - Phase 1 (Execution): ✅ Working")
            print("   - Phase 2 (LLM Backend): ✅ Working")
            print("   - Phase 3 (Learning): ✅ Working")
            print("   - Phase 4 (Meta-Cognition): ✅ Working")
            print()
            print(f"Total execution time: {elapsed:.2f}s")
            print(f"Total events logged: {len(task_events)}")
            
            if second_pass:
                print("   - Self-correction: ✅ Triggered")
            
            return True
        else:
            print("⚠️  Some phases not validated:")
            for phase, validated in phases_validated.items():
                if not validated:
                    print(f"   - {phase}: MISSING")
            return False
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_low_confidence_scenario():
    """Low confidence 시나리오 테스트 - delegation warning 확인"""
    
    print("\n")
    print("=" * 80)
    print("📌 Scenario 2: Low confidence task (missing critical tools)")
    print("=" * 80)
    print()
    
    # 도구가 부족한 작업 (웹 검색 필요하지만 RAG만 사용 가능)
    task_spec = {
        "task_id": f"low_confidence_test_{int(time.time())}",
        "title": "최신 뉴스 요약",
        "goal": "2025년 10월 최신 AI 기술 뉴스를 웹에서 검색하여 요약해주세요",
        "scope": "doc"
    }
    
    tool_cfg = {"enabled": True, "websearch_enabled": False, "rag_enabled": False}
    
    print(f"Task: {task_spec['goal']}")
    print("Expected: Meta-cognition should detect need for websearch")
    print()
    
    try:
        previous_flag = os.environ.get("WEBSEARCH_DISABLE")
        os.environ["WEBSEARCH_DISABLE"] = "1"
        registry_preview = ToolRegistry(tool_cfg)
        preview_tools = registry_preview.list_available_tools_for_meta()
        print("Preview Meta-Cognition (before run_task):")
        print(f"   tools: {preview_tools}")
        preview_eval = MetaCognitionSystem().evaluate_self_capability(
            task_goal=task_spec["goal"],
            persona="thesis",
            available_tools=preview_tools
        )
        print(f"   confidence: {preview_eval['confidence']:.3f}")
        print(f"   tools_availability: {preview_eval['tools_availability']:.3f}")
        print(f"   should_delegate: {preview_eval['should_delegate']}")
        print()
        try:
            result = run_task(tool_cfg, task_spec)
        finally:
            if previous_flag is None:
                os.environ.pop("WEBSEARCH_DISABLE", None)
            else:
                os.environ["WEBSEARCH_DISABLE"] = previous_flag
        
        # Ledger 확인
        ledger_path = _memory_path("resonance_ledger.jsonl")
        with open(ledger_path, 'r', encoding='utf-8') as f:
            events = [json.loads(line) for line in f if line.strip()]
        
        task_events = [e for e in events if e.get('task_id') == task_spec['task_id']]
        
        # Low confidence warning 확인
        warnings = [e for e in task_events if e.get('event') == 'low_confidence_warning']
        
        if warnings:
            print("\u2705 Low confidence warning detected:")
            for w in warnings:
                print(f"   Confidence: {w.get('confidence', 0):.3f}")
                print(f"   Recommendation: {w.get('recommendation')}")
            return True

        print("\u26a0\ufe0f  No low confidence warning (expected when websearch is disabled)")
        meta_events = [e for e in task_events if e.get('event') == 'meta_cognition']
        if meta_events:
            latest_meta = meta_events[-1]
            print(f"   Run confidence: {latest_meta.get('confidence', 0):.3f}")
            print(f"   Tools availability: {latest_meta.get('tools_availability', 0):.3f}")
            print(f"   Should delegate: {latest_meta.get('should_delegate')}")
        else:
            print("   Meta-cognition event missing for task run")
        return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def measure_performance_metrics():
    """성능 메트릭 측정"""
    
    print("\n")
    print("=" * 80)
    print("📊 Performance Metrics")
    print("=" * 80)
    print()
    
    ledger_path = _memory_path("resonance_ledger.jsonl")
    if not ledger_path.exists():
        print("⚠️  No ledger file found")
        return
    
    with open(ledger_path, 'r', encoding='utf-8') as f:
        events = [json.loads(line) for line in f if line.strip()]
    
    # 메트릭 계산
    total_tasks = len([e for e in events if e.get('event') == 'task_start'])
    completed_tasks = len([e for e in events if e.get('event') == 'task_end'])
    
    meta_cognition_count = len([e for e in events if e.get('event') == 'meta_cognition'])
    learning_count = len([e for e in events if e.get('event') == 'learning'])
    second_pass_count = len([e for e in events if e.get('event') == 'second_pass'])
    
    # 평균 confidence 계산
    meta_events = [e for e in events if e.get('event') == 'meta_cognition']
    if meta_events:
        avg_confidence = sum(e.get('confidence', 0) for e in meta_events) / len(meta_events)
    else:
        avg_confidence = 0
    
    # 평균 quality 계산
    eval_events = [e for e in events if e.get('event') == 'eval']
    if eval_events:
        avg_quality = sum(e.get('eval', {}).get('quality', 0) for e in eval_events) / len(eval_events)
    else:
        avg_quality = 0
    
    print(f"Total tasks started: {total_tasks}")
    print(f"Total tasks completed: {completed_tasks}")
    print(f"Completion rate: {(completed_tasks/total_tasks*100 if total_tasks > 0 else 0):.1f}%")
    print()
    print(f"Meta-cognition evaluations: {meta_cognition_count}")
    print(f"Learning events: {learning_count}")
    print(f"Second passes: {second_pass_count}")
    print()
    print(f"Average confidence: {avg_confidence:.3f}")
    print(f"Average quality: {avg_quality:.3f}")
    print()
    
    # AGI 자율성 지표
    if total_tasks > 0:
        learning_rate = (learning_count / total_tasks) * 100
        self_correction_rate = (second_pass_count / total_tasks) * 100
        
        print("🤖 AGI Autonomy Indicators:")
        print(f"   - Learning rate: {learning_rate:.1f}% (tasks that triggered learning)")
        print(f"   - Self-correction rate: {self_correction_rate:.1f}% (tasks with second pass)")
        print(f"   - Avg confidence: {avg_confidence:.3f} (self-awareness)")
        print(f"   - Avg quality: {avg_quality:.3f} (output quality)")

if __name__ == "__main__":
    print("\n")
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                 AGI Phase 5: Integration Test Suite                         ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    # Test 1: End-to-end integration
    test1_pass = test_end_to_end_integration()
    
    # Test 2: Low confidence scenario
    test2_pass = test_low_confidence_scenario()
    
    # Performance metrics
    measure_performance_metrics()
    
    # Final summary
    print("\n")
    print("=" * 80)
    print("🎉 FINAL SUMMARY")
    print("=" * 80)
    
    if test1_pass and test2_pass:
        print("✅ ALL INTEGRATION TESTS PASSED!")
        print()
        print("AGI System is fully operational with:")
        print("   ✅ Phase 1: Execution")
        print("   ✅ Phase 2: LLM Backend")
        print("   ✅ Phase 3: Autonomous Learning")
        print("   ✅ Phase 4: Meta-Cognition")
        print("   ✅ Phase 5: Integration verified")
        print()
        print("🚀 System ready for production use!")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed or incomplete")
        print("Please review the logs above for details")
        sys.exit(1)
