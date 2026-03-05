import os
import sys
import json
from pathlib import Path
from semantic_rag_engine import SemanticRAGEngine
from workspace_root import get_workspace_root

def deep_search():
    root = get_workspace_root()
    # Path to the actual vector store found during analysis
    vector_store_dir = root / "fdo_agi_repo" / "memory" / "vector_store"
    os.environ["AGI_VECTOR_STORE_DIR"] = str(vector_store_dir)
    
    engine = SemanticRAGEngine(root)
    
    queries = ["W1", "W2", "W3", "W4", "W1 W2 W3 W4 hierarchy", "Planes of Shion architecture"]
    
    results_map = {}
    
    print(f"🔍 Starting Deep RAG Search in {vector_store_dir}...")
    
    for q in queries:
        print(f"\nSearching for: '{q}'")
        results = engine.search(q, top_k=5)
        results_map[q] = results
        for i, r in enumerate(results, 1):
            print(f"  {i}. [{r['score']:.4f}] {r['metadata'].get('file_path', 'unknown')}")
            # Print a snippet of the content
            content = r['content'].replace('\n', ' ')[:150]
            print(f"     Content: {content}...")

    # Save findings for later reporting
    output_path = root / "scripts" / "rag_search_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results_map, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Results saved to {output_path}")

if __name__ == "__main__":
    deep_search()
