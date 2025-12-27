import sys
from pathlib import Path
import json
import time

# Set paths
WORKSPACE_ROOT = Path(__file__).parent.parent
sys.path.append(str(WORKSPACE_ROOT))

from fdo_agi_repo.copilot.hippocampus import CopilotHippocampus

def verify_rag():
    print("Starting RAG integration verification...")
    
    # 1. Initialize Hippocampus
    hp = CopilotHippocampus(WORKSPACE_ROOT)
    print("OK: Hippocampus initialized.")
    if hp.rag_engine:
        print("OK: Semantic RAG engine is active.")
    else:
        print("FAIL: Semantic RAG engine is not active.")
        return

    # 2. Store a unique memory in working memory
    unique_content = "시안은 2025년 크리스마스 이브에 LangChain 기반의 벡터 RAG 시스템으로 업그레이드되었습니다."
    hp.add_to_working_memory({
        "type": "event",
        "content": unique_content,
        "quality": 1.0,
        "importance": 1.0,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
    })
    print(f"OK: Stored working memory: {unique_content[:30]}...")

    # 3. Consolidate to Long-Term (and Vector Index)
    print("Consolidating memories...")
    hp.consolidate(force=True)
    print("OK: Consolidation complete.")

    # 4. Search with a semantic query (not identical words)
    # Search for "시안의 업그레이드 내용" (What was Shion's upgrade?)
    search_query = "시안이의 시스템 업데이트 내용에 대해 알려줘"
    print(f"Searching for: '{search_query}'")
    
    results = hp.recall(search_query, top_k=5)
    resonance = results[0] if results else {}
    vector_result = next((item for item in results if item.get("is_vector")), None)
    
    print("\n--- Search Results ---")
    print(f"Content: {resonance.get('data') or resonance.get('content')}")
    print(f"Type: {resonance.get('type')}")
    print(f"Vector Match: {resonance.get('is_vector', False)}")
    
    if vector_result:
        print("SUCCESS: Vector RAG returned a semantically related memory.")
    else:
        print("FAILURE: No vector-based result was returned.")

if __name__ == "__main__":
    verify_rag()
