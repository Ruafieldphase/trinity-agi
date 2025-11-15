"""
Hippocampus + Everything 통합 테스트
Phase 2 & 3 기능 검증
"""

import sys
from pathlib import Path

# Add repo to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "fdo_agi_repo"))

from copilot.hippocampus import CopilotHippocampus


def test_everything_integration():
    """Everything 검색 통합 테스트"""
    print("🧠 Testing Hippocampus + Everything Integration\n")
    
    # Hippocampus 초기화 (workspace_root 전달)
    workspace = Path(__file__).parent.parent
    hip = CopilotHippocampus(workspace_root=workspace)
    
    # 테스트 1: Python 파일 검색
    print("=" * 60)
    print("📝 Test 1: Search Python files with 'hippocampus'")
    print("=" * 60)
    
    results = hip.search_files(
        query="hippocampus",
        extension="py",
        max_results=10
    )
    
    print(f"\n✅ Found {len(results)} Python files:")
    for i, r in enumerate(results[:5], 1):
        size_kb = r.get('size', 0) / 1024
        print(f"  {i}. {r['name']}")
        print(f"     Path: {r['full_path']}")
        print(f"     Size: {size_kb:.1f} KB")
        print(f"     Modified: {r.get('modified', 'N/A')}")
        print()
    
    # 테스트 2: Memory 폴더 내 검색
    print("\n" + "=" * 60)
    print("📁 Test 2: Search in memory folder")
    print("=" * 60)
    
    results = hip.search_files(
        query="goal",
        path_filter="memory",
        max_results=10
    )
    
    print(f"\n✅ Found {len(results)} files in memory/:")
    for i, r in enumerate(results[:5], 1):
        print(f"  {i}. {r['name']} - {r.get('size', 0)} bytes")
    
    # 테스트 3: Markdown 문서 검색
    print("\n" + "=" * 60)
    print("📄 Test 3: Search Markdown docs")
    print("=" * 60)
    
    results = hip.search_files(
        query="complete",
        extension="md",
        max_results=10
    )
    
    print(f"\n✅ Found {len(results)} Markdown files:")
    for i, r in enumerate(results[:5], 1):
        print(f"  {i}. {r['name']}")
    
    # 테스트 4: JSON 설정 파일 검색
    print("\n" + "=" * 60)
    print("⚙️ Test 4: Search JSON config files")
    print("=" * 60)
    
    results = hip.search_files(
        query="",
        extension="json",
        path_filter="fdo_agi_repo",
        max_results=10
    )
    
    print(f"\n✅ Found {len(results)} JSON files:")
    for i, r in enumerate(results[:5], 1):
        print(f"  {i}. {r['name']} - {r['directory']}")
    
    # 테스트 5: 성능 테스트
    print("\n" + "=" * 60)
    print("⚡ Test 5: Performance check")
    print("=" * 60)
    
    import time
    
    start = time.time()
    results = hip.search_files(
        query="test",
        max_results=100
    )
    elapsed = time.time() - start
    
    print(f"\n✅ Searched {len(results)} files in {elapsed*1000:.1f}ms")
    print(f"   Average: {(elapsed/max(len(results), 1))*1000:.2f}ms per file")
    
    # Everything 사용 여부 확인
    print("\n" + "=" * 60)
    print("🔍 System Status")
    print("=" * 60)
    
    if hip.everything:
        print("✅ Everything search: ACTIVE")
        print("   Ultra-fast file indexing enabled!")
    else:
        print("⚠️ Everything search: FALLBACK mode")
        print("   Using glob-based search (slower)")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_everything_integration()
