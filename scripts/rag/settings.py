from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class RagSettings:
    index: Path
    top_k: int = 3
    min_score: Optional[float] = None


def load_rag_settings(config_path: Path) -> RagSettings:
    data = json.loads(config_path.read_bytes().decode("utf-8-sig"))
    rag_section = data.get("rag")
    if not rag_section:
        raise ValueError("Configuration file is missing 'rag' section.")

    index_value = rag_section.get("index")
    if not index_value:
        raise ValueError("RAG configuration requires an 'index' path.")

    index_path_raw = Path(index_value)
    if index_path_raw.is_absolute():
        index_path = index_path_raw
    else:
        base_candidates = [config_path.parent, config_path.parent.parent]
        for base in base_candidates:
            candidate = (base / index_path_raw).resolve()
            if candidate.exists():
                index_path = candidate
                break
        else:
            index_path = (config_path.parent / index_path_raw).resolve()

    top_k = int(rag_section.get("top_k", 3))
    min_score_value = rag_section.get("min_score")
    min_score = float(min_score_value) if min_score_value is not None else None

    return RagSettings(index=index_path, top_k=top_k, min_score=min_score)
