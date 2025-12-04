#!/usr/bin/env python3
"""
Convert Task Queue Server results (/api/results) into a BQI-friendly feedback dataset (JSONL).

Inputs:
  - HTTP GET {server}/api/results  (default server: http://127.0.0.1:8091)

Outputs:
  - fdo_agi_repo/outputs/rpa_feedback_bqi.jsonl

Schema (aligned with youtube_feedback_to_bqi v1):
{
  "ts": ISO8601,
  "source": "rpa",
  "task_id": str,
  "bqi_coord": {"priority": int, "emotion": [str], "rhythm": str},
  "quality": float,       # 0.0..1.0 heuristic from success + content signal
  "confidence": float,    # 0.0..1.0 heuristic from success + metadata presence
  "meta": {
    "action": str|None,
    "message": str|None,
    "engine": str|None,
    "chars": int|None,
    "count": int|None,
    "path": str|None,
    "width": int|None,
    "height": int|None,
    "submitted_at": str|None
  },
  "summary": str|None,
  "video_url": null
}

Heuristics (v1):
  - content_signal = 1 if OCR(char/count) or screenshot(path/width/height) present, else 0
  - quality = clamp01(0.2 + 0.6*(success?1:0) + 0.2*content_signal)
  - confidence = clamp01(0.4 + 0.4*(success?1:0) + 0.2*(submitted_at present?1:0))
  - bqi_coord:
      * priority = 3 if failed else 2
      * emotion = ["focus"] if action exists else ["curious"]
      * rhythm = "act" if action exists else "observe"
"""
from __future__ import annotations
import json
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]  # .../fdo_agi_repo
OUT_JSONL = ROOT / "outputs" / "rpa_feedback_bqi.jsonl"


def clamp01(x: float) -> float:
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def fetch_results(server: str, timeout: int = 10) -> List[Dict[str, Any]]:
    url = server.rstrip('/') + '/api/results'
    req = Request(url, headers={"User-Agent": "rpa-feedback/1.0"})
    with urlopen(req, timeout=timeout) as resp:
        data = json.load(resp)
    return data.get("results", []) if isinstance(data, dict) else []


def to_int(x: Any) -> int | None:
    try:
        if x is None:
            return None
        return int(x)
    except Exception:
        return None


def build_bqi_coord(action: str | None, success: bool) -> Dict[str, Any]:
    if action and isinstance(action, str) and action.strip():
        emo = ["focus"]
        rhythm = "act"
    else:
        emo = ["curious"]
        rhythm = "observe"
    priority = 2 if success else 3
    return {"priority": priority, "emotion": emo, "rhythm": rhythm}


def compute_quality_confidence(success: bool, submitted_at: str | None, data: Dict[str, Any]) -> tuple[float, float, int]:
    content_signal = 0
    if isinstance(data, dict):
        if data.get("engine") and (to_int(data.get("chars")) or to_int(data.get("count"))):
            content_signal = 1
        elif data.get("path") and (to_int(data.get("width")) and to_int(data.get("height"))):
            content_signal = 1
    q = clamp01(0.2 + 0.6 * (1.0 if success else 0.0) + 0.2 * content_signal)
    c = clamp01(0.4 + 0.4 * (1.0 if success else 0.0) + 0.2 * (1.0 if (submitted_at and str(submitted_at).strip()) else 0.0))
    return q, c, content_signal


def pick_summary(data: Dict[str, Any]) -> str | None:
    if not isinstance(data, dict):
        return None
    if data.get("message"):
        return str(data.get("message"))
    if data.get("action"):
        return f"action={data.get('action')}"
    if data.get("engine") and (data.get("chars") or data.get("count")):
        return f"ocr {data.get('engine')} chars={data.get('chars') or data.get('count')}"
    if data.get("path") and (data.get("width") and data.get("height")):
        return f"screenshot {data.get('width')}x{data.get('height')}"
    return None


def normalize_item(it: Dict[str, Any]) -> Dict[str, Any]:
    # Ensure expected fields exist and types are simple
    data = it.get("data") or {}
    meta = {
        "action": data.get("action"),
        "message": data.get("message"),
        "engine": data.get("engine"),
        "chars": to_int(data.get("chars")),
        "count": to_int(data.get("count")),
        "path": data.get("path"),
        "width": to_int(data.get("width")),
        "height": to_int(data.get("height")),
        "submitted_at": it.get("submitted_at"),
    }
    return meta


def main(argv: List[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", default="http://127.0.0.1:8091")
    ap.add_argument("--count", type=int, default=50)
    ap.add_argument("--out", default=str(OUT_JSONL))
    args = ap.parse_args(argv)

    try:
        results = fetch_results(args.server)
    except (URLError, HTTPError) as e:
        print(f"[RPA→BQI] Failed to fetch {args.server}/api/results: {e}")
        return 1

    # Sort by submitted_at desc, fallback stable by task_id
    def sort_key(x: Dict[str, Any]):
        return (x.get("submitted_at") or "", x.get("task_id") or "")

    results_sorted = sorted(results, key=sort_key, reverse=True)[: max(args.count, 1)]

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    with out_path.open("w", encoding="utf-8") as out:
        for it in results_sorted:
            task_id = it.get("task_id") or "rpa-unknown"
            success = bool(it.get("success"))
            submitted_at = it.get("submitted_at")
            data = it.get("data") or {}
            meta = normalize_item(it)

            quality, confidence, _ = compute_quality_confidence(success, submitted_at, data)
            bqi_coord = build_bqi_coord(meta.get("action"), success)

            rec = {
                "ts": (submitted_at or datetime.now(timezone.utc).isoformat()),
                "source": "rpa",
                "task_id": str(task_id),
                "bqi_coord": bqi_coord,
                "quality": round(quality, 4),
                "confidence": round(confidence, 4),
                "meta": meta,
                "summary": pick_summary(data),
                "video_url": None
            }
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            written += 1

    print(f"[RPA→BQI] Wrote {written} records → {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
