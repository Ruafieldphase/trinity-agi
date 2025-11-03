import json
from pathlib import Path


def load_rag_config():
    repo_root = Path(__file__).resolve().parents[1]
    cfg_path = repo_root / "config" / "rag_config.json"
    assert cfg_path.exists(), f"rag_config.json not found at {cfg_path}"
    with cfg_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_rag_config_keys_and_types():
    cfg = load_rag_config()

    # evidence_gate
    assert "evidence_gate" in cfg and isinstance(cfg["evidence_gate"], dict), "Missing evidence_gate section"
    eg = cfg["evidence_gate"]

    assert "top_k" in eg and isinstance(eg["top_k"], int), "evidence_gate.top_k must be int"
    assert 1 <= eg["top_k"] <= 50, "evidence_gate.top_k out of reasonable range"

    assert "min_relevance" in eg and isinstance(eg["min_relevance"], (int, float)), "min_relevance must be number"
    assert 0.0 <= float(eg["min_relevance"]) <= 1.0, "min_relevance must be within [0,1]"

    # guard that retry_broaden key exists and is boolean (prevents silent formatter removals)
    assert "retry_broaden" in eg and isinstance(eg["retry_broaden"], bool), "retry_broaden must exist and be boolean"

    # pass2_top_k should exist and be >= top_k (ensures 2nd pass scope is not narrower by accident)
    assert "pass2_top_k" in eg and isinstance(eg["pass2_top_k"], int), "pass2_top_k must be int"
    assert eg["pass2_top_k"] >= eg["top_k"], "pass2_top_k expected to be >= top_k"

    # include_types presence and basic shape
    assert "include_types" in eg and isinstance(eg["include_types"], list), "include_types must be list"
    assert all(isinstance(x, str) for x in eg["include_types"]), "include_types must be list[str]"
    assert len(eg["include_types"]) > 0, "include_types should not be empty"

    # bm25 section
    assert "bm25" in cfg and isinstance(cfg["bm25"], dict), "Missing bm25 section"
    bm = cfg["bm25"]
    assert "k1" in bm and isinstance(bm["k1"], (int, float)), "bm25.k1 must be number"
    assert "b" in bm and isinstance(bm["b"], (int, float)), "bm25.b must be number"

    # weights section (existence only; detailed schema may evolve)
    assert "weights" in cfg and isinstance(cfg["weights"], dict), "Missing weights section"

    # recency, mmr, hybrid sections minimal structure
    assert "recency" in cfg and isinstance(cfg["recency"], dict), "Missing recency section"
    assert "enabled" in cfg["recency"], "recency.enabled missing"

    assert "mmr" in cfg and isinstance(cfg["mmr"], dict), "Missing mmr section"
    assert "enabled" in cfg["mmr"], "mmr.enabled missing"

    assert "hybrid" in cfg and isinstance(cfg["hybrid"], dict), "Missing hybrid section"
    hyb = cfg["hybrid"]
    assert "enabled" in hyb, "hybrid.enabled missing"
    assert "vector_store_path" in hyb and isinstance(hyb["vector_store_path"], str), "hybrid.vector_store_path must be string"
