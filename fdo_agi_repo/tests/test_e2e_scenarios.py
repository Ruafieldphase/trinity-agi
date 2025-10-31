"""
Phase 2.5 실전 테스트 시나리오
간단한 YouTube 튜토리얼로 E2E 파이프라인 검증
"""

import asyncio
import logging
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

# UTF-8 강제 설정 (Windows 폰트 깨짐 방지)
from rpa.utf8_utils import force_utf8
force_utf8()

from rpa.e2e_pipeline import E2EPipeline, E2EConfig


# 테스트 시나리오
TEST_SCENARIOS = [
    {
        "name": "Python 기초 튜토리얼",
        "url": "https://www.youtube.com/watch?v=kqtD5dpn9C8",  # Python in 100 Seconds
        "description": "짧은 Python 소개 영상",
        "expected_keywords": ["python", "programming", "code"]
    },
    {
        "name": "VSCode 단축키",
        "url": "https://www.youtube.com/watch?v=ifTF3ags0XI",  # VSCode shortcuts
        "description": "VSCode 단축키 튜토리얼",
        "expected_keywords": ["vscode", "shortcut", "editor"]
    }
]


async def run_scenario(pipeline: E2EPipeline, scenario: dict):
    """시나리오 실행"""
    print(f"\n{'='*70}")
    print(f"🎬 Scenario: {scenario['name']}")
    print(f"🔗 URL: {scenario['url']}")
    print(f"📝 Description: {scenario['description']}")
    print(f"{'='*70}\n")
    
    try:
        # E2E 파이프라인 실행
        task = await pipeline.run_learning_task(scenario['url'])
        
        # 결과 분석
        print(f"\n✅ Task Completed: {task.task_id}")
        print(f"   Status: {task.status}")
        
        if task.video_analysis:
            print(f"\n📊 Video Analysis:")
            print(f"   Title: {task.video_analysis.title}")
            print(f"   Duration: {task.video_analysis.duration}s")
            print(f"   Subtitles: {len(task.video_analysis.subtitles)} entries")
            print(f"   Keywords: {task.video_analysis.keywords[:10]}")
            
            # 예상 키워드 검증
            found_keywords = [k for k in scenario['expected_keywords'] 
                            if any(k.lower() in keyword.lower() 
                                   for keyword in task.video_analysis.keywords)]
            
            print(f"\n🔍 Keyword Validation:")
            for expected in scenario['expected_keywords']:
                found = expected in [k.lower() for k in task.video_analysis.keywords]
                status = "✅" if found else "❌"
                print(f"   {status} {expected}")
        
        if task.execution_steps:
            print(f"\n🎯 Extracted Steps: {len(task.execution_steps)}")
            for i, step in enumerate(task.execution_steps[:5], 1):
                print(f"   {i}. {step['action']}: {step['description'][:50]}...")
        
        return {
            "scenario": scenario['name'],
            "success": task.status == "completed",
            "task_id": task.task_id
        }
    
    except Exception as e:
        print(f"\n❌ Scenario Failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "scenario": scenario['name'],
            "success": False,
            "error": str(e)
        }


async def main():
    """실전 테스트 메인"""
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*70)
    print("🚀 Phase 2.5 실전 테스트 - E2E Pipeline")
    print("="*70)
    
    # 설정
    config = E2EConfig(
        enable_auto_execution=False,  # 안전을 위해 자동 실행 비활성화
        max_steps=10
    )
    
    pipeline = E2EPipeline(config)
    
    print(f"\n⚙️ Configuration:")
    print(f"   Auto-execution: {config.enable_auto_execution}")
    print(f"   Max steps: {config.max_steps}")
    print(f"   Output dir: {config.output_dir}")
    
    # 시나리오 실행
    results = []
    
    # 첫 번째 시나리오만 테스트 (빠른 검증)
    scenario = TEST_SCENARIOS[0]
    result = await run_scenario(pipeline, scenario)
    results.append(result)
    
    # 결과 요약
    print("\n" + "="*70)
    print("📋 Test Summary")
    print("="*70)
    
    success_count = sum(1 for r in results if r['success'])
    total_count = len(results)
    
    for result in results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{status} - {result['scenario']}")
        if 'task_id' in result:
            print(f"         Task ID: {result['task_id']}")
        if 'error' in result:
            print(f"         Error: {result['error']}")
    
    print(f"\n🎯 Result: {success_count}/{total_count} scenarios passed")
    
    if success_count == total_count:
        print("✅ ALL SCENARIOS PASSED")
        return 0
    else:
        print("⚠️ SOME SCENARIOS FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
