from __future__ import annotations
from typing import Any, Dict
import json
import os


_DEFAULT_CONFIG: Dict[str, Any] = {
    "evidence_gate": {
        "top_k": 5,
        "include_types": ["rune_validation", "eval"],
        "fallback_on_empty": True,
        # If provided, try these types before fully unfiltered fallback.
        "fallback_include_types": None,
        "min_relevance": 0.3,
        # Retry strategy: if first pass yields no additions, broaden the search
        "retry_broaden": True,
        "pass2_top_k": 12,
        # As a last resort, allow a minimal synthetic citation (clearly marked)
        "allow_synthetic": True,
    },
    "bm25": {"k1": 1.2, "b": 0.75},
    "weights": {
        "ledger": {"eval": 2.0, "rune": 2.0, "default": 0.5},
        "coordinate": {"rune_validation": 2.0, "routing": 0.3, "task_start": 1.0, "default": 1.0}
    },
    "recency": {
        "enabled": True,
        "half_life_hours": 24.0  # time-decay factor; score *= 0.5 every half-life
    },
    "mmr": {
        "enabled": True,
        "lambda": 0.7  # higher = favor relevance more than diversity
    },
    "hybrid": {
        "enabled": True,  # BM25 + Dense Embedding 병합
        "rrf_k": 60,  # Reciprocal Rank Fusion 파라미터
        "vector_store_path": "memory/vector_store.json"
    }
}


def get_rag_config() -> Dict[str, Any]:
    """Load RAG config from repo config file, with safe defaults.

    Looks for fdo_agi_repo/config/rag_config.json relative to this file.
    Environment override: RAG_CONFIG_PATH can point to an absolute path.
    """
    # Env override first
    env_path = os.environ.get("RAG_CONFIG_PATH")
    if env_path and os.path.isfile(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
            return _merge_dicts(_DEFAULT_CONFIG, user_cfg)
        except Exception:
            return dict(_DEFAULT_CONFIG)

    # Default path under repo
    here = os.path.dirname(__file__)
    repo_root = os.path.abspath(os.path.join(here, "..", ".."))
    cfg_path = os.path.join(repo_root, "config", "rag_config.json")
    if os.path.isfile(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
            return _merge_dicts(_DEFAULT_CONFIG, user_cfg)
        except Exception:
            return dict(_DEFAULT_CONFIG)

    return dict(_DEFAULT_CONFIG)


def _merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Shallow+deep merge for nested dicts"""
    if not isinstance(base, dict):
        return override
    result = dict(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = _merge_dicts(result[k], v)
        else:
            result[k] = v
    return result
