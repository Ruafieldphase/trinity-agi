#!/usr/bin/env python3
"""Debug: Test RAG call through registry"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from orchestrator.tool_registry import ToolRegistry
from orchestrator.config import get_app_config

# Check RAG_DISABLE env
print(f"RAG_DISABLE env: {os.environ.get('RAG_DISABLE', 'not set')}")

# Load config and create registry
cfg = get_app_config()
registry = ToolRegistry(cfg)

# Test direct call
print("\n=== Test 1: Direct registry.call('rag') ===")
try:
    result = registry.call("rag", {
        "query": "AGI 자기교정 루프 설명 3문장",
        "top_k": 5,
        "include_types": ["rune_validation", "eval", "rune", "task_start", "routing"]
    })
    print(f"OK: {result.get('ok')}")
    print(f"Hits: {len(result.get('hits', []))}")
    print(f"Total found: {result.get('total_found')}")
    print(f"Used fallback: {result.get('used_fallback')}")
    if result.get('hits'):
        print(f"First hit: {result['hits'][0]}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Test with evidence_gate config
print("\n=== Test 2: With evidence_gate config ===")
from tools.rag.config_loader import get_rag_config
rcfg = get_rag_config().get("evidence_gate", {})
print(f"evidence_gate config: {rcfg}")

try:
    result = registry.call("rag", {
        "query": "force replan (no citations)",
        "top_k": rcfg.get("top_k", 5),
        "include_types": rcfg.get("include_types")
    })
    print(f"OK: {result.get('ok')}")
    print(f"Hits: {len(result.get('hits', []))}")
    if not result.get('ok'):
        print(f"Error: {result.get('error')}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
