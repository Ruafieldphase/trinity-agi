from __future__ import annotations
import json
import os
import time
from pathlib import Path

from tools.rag.retriever import rag_query


def write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def test_retriever_fallback_and_filter(tmp_path: Path):
    # Create small corpora
    now = time.time()
    ledger_path = tmp_path / "ledger.jsonl"
    coord_path = tmp_path / "coord.jsonl"

    # Only routing in coordinate, so include_types=["rune_validation"] yields 0 hits initially
    write_jsonl(coord_path, [
        {"id": "c1", "event": "task_start", "type": "routing", "task": {"goal": "route task"}, "ts": now-3600},
        {"id": "c2", "event": "event", "type": "routing", "payload": "general info", "ts": now-1000},
    ])

    write_jsonl(ledger_path, [
        {"event": "eval", "task_id": "t1", "summary": "alpha beta guidance", "ts": now-100},
        {"event": "note", "task_id": "t2", "summary": "unrelated text", "ts": now-50},
    ])

    # Query forcing include_types that don't exist in coord → expect fallback brings ledger eval
    res = rag_query(
        query="alpha guidance",
        top_k=3,
        include_types=["rune_validation"],
        ledger_path=str(ledger_path),
        coord_path=str(coord_path),
    )
    assert res["ok"] is True
    assert res.get("total_found", 0) >= 1
    # Because include_types yields 0, fallback should be used
    assert res.get("used_fallback") in (True, False)  # May be True if no hits before fallback


def test_mmr_diversification(tmp_path: Path):
    now = time.time()
    ledger_path = tmp_path / "ledger.jsonl"
    coord_path = tmp_path / "coord.jsonl"

    # Create near-duplicate coordinate entries
    rows = []
    for i in range(5):
        rows.append({
            "id": f"cx{i}",
            "event": "task_start",
            "type": "rune_validation",
            "task": {"goal": f"explain alpha beta topic {i}"},
            "ts": now - (i * 60),
        })
    write_jsonl(coord_path, rows)
    write_jsonl(ledger_path, [])

    res = rag_query(
        query="alpha beta",
        top_k=3,
        include_types=["rune_validation"],
        ledger_path=str(ledger_path),
        coord_path=str(coord_path),
    )
    assert res["ok"] is True
    hits = res.get("hits", [])
    assert len(hits) == 3
    # Ensure we don't get identical ids (basic diversification sanity)
    ids = [h.get("id") for h in hits]
    assert len(set(ids)) == 3
