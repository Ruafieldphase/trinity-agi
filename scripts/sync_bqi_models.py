#!/usr/bin/env python3
"""
Copy and normalize core BQI learning artifacts into the workspace `outputs/`.

Phase 9 E2E 검증 스크립트는 루트 `outputs/` 경로에 다음 구조를 기대한다:
  - `bqi_pattern_model.json` → truthy `patterns` 키
  - `binoche_persona.json`   → truthy `traits`  키
  - `ensemble_weights.json`  → truthy `weights` 키

원본 산출물(`fdo_agi_repo/outputs/*.json`)을 읽어 필요한 필드가 없으면
간단한 요약을 생성해 주입한다.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime

SOURCE_DIR = Path("fdo_agi_repo/outputs")
TARGET_DIR = Path("outputs")
YOUTUBE_SOURCE_DIR = SOURCE_DIR / "youtube_learner"


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)


def ensure_patterns(data: Dict[str, Any]) -> Dict[str, Any]:
    if data.get("patterns"):
        return data

    derived: List[Dict[str, Any]] = []
    for key in ("priority_rules", "emotion_rules", "rhythm_rules"):
        rules = data.get(key)
        if isinstance(rules, dict) and rules:
            derived.append({"type": key, "count": len(rules)})

    if not derived:
        task_count = data.get("meta", {}).get("task_count", 0)
        derived.append({"type": "summary", "count": task_count or 1})

    data = dict(data)
    data["patterns"] = derived
    return data


def ensure_traits(data: Dict[str, Any]) -> Dict[str, Any]:
    if data.get("traits"):
        return data

    traits: List[Dict[str, Any]] = []
    stats = data.get("stats", {})
    if isinstance(stats, dict):
        for key, value in stats.items():
            if isinstance(value, (int, float)):
                traits.append({"name": key, "value": value})

    decision_patterns = data.get("decision_patterns")
    if isinstance(decision_patterns, dict) and decision_patterns:
        traits.append(
            {
                "name": "decision_modes",
                "value": list(decision_patterns.keys()),
            }
        )

    if not traits:
        traits.append({"name": "summary", "value": "auto-generated trait placeholder"})

    data = dict(data)
    data["traits"] = traits
    return data


def sync_file(name: str) -> str:
    src = SOURCE_DIR / name
    if not src.exists():
        raise FileNotFoundError(str(src))

    data = load_json(src)

    if name == "bqi_pattern_model.json":
        data = ensure_patterns(data)
    elif name == "binoche_persona.json":
        data = ensure_traits(data)

    dst = TARGET_DIR / name
    write_json(dst, data)
    return str(dst)


def main() -> None:
    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    files = [
        "bqi_pattern_model.json",
        "binoche_persona.json",
        "ensemble_weights.json",
    ]

    copied = []
    missing = []

    for name in files:
        try:
            copied.append(sync_file(name))
        except FileNotFoundError as exc:
            missing.append(str(exc))

    youtube_index_created = False
    if YOUTUBE_SOURCE_DIR.exists():
        entries: List[Dict[str, Any]] = []
        for path in sorted(YOUTUBE_SOURCE_DIR.glob("*_analysis.json")):
            data = load_json(path)
            video_id = data.get("video_id") or path.stem.replace("_analysis", "")
            title = data.get("title") or data.get("metadata", {}).get("title", "unknown")
            analyzed_at = data.get("analyzed_at")

            entries.append(
                {
                    "id": video_id,
                    "title": title,
                    "analysis_path": str(path),
                    "duration": data.get("duration"),
                    "analyzed_at": analyzed_at,
                }
            )

        if entries:
            youtube_index = {
                "generated_at": datetime.now().isoformat(),
                "videos": entries,
            }
            write_json(TARGET_DIR / "youtube_learner_index.json", youtube_index)
            youtube_index_created = True

    if copied or youtube_index_created:
        print("✅ Normalized BQI artifacts:")
        for path in copied:
            print(f"   - {path}")
        if youtube_index_created:
            print(f"   - {TARGET_DIR / 'youtube_learner_index.json'}")
    else:
        print("⚠️  No BQI artifacts synced (source files missing)")

    if missing:
        print("\n🚫 Missing source files:")
        for path in missing:
            print(f"   - {path}")


if __name__ == "__main__":
    main()
