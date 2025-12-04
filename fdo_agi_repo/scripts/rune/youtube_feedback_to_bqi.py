#!/usr/bin/env python3
"""
Convert YouTube Learner analysis JSON files into a BQI-friendly feedback dataset (JSONL).

Inputs:
  - fdo_agi_repo/outputs/youtube_learner/*_analysis.json

Outputs:
  - fdo_agi_repo/outputs/youtube_feedback_bqi.jsonl  (one record per video)

Each JSONL record (schema v1):
{
  "ts": ISO8601,
  "source": "youtube",
  "task_id": "yt-<video_id>",
  "bqi_coord": {"priority": int, "emotion": [str], "rhythm": str},
  "quality": float,       # 0.0..1.0 heuristic from OCR/subtitles & summary
  "confidence": float,    # 0.0..1.0 heuristic from subtitle coverage
  "meta": {
    "video_id": str,
    "title": str,
    "duration": float|None,
    "subtitles_count": int,
    "ocr_text_len": int,
    "file": str
  },
  "summary": str|None,
  "video_url": str
}

Heuristics (v1):
  - quality = base 0.4 + 0.4 * clamp01(ocr_text_len/5000) + 0.2 * (1 if summary present else 0)
  - confidence = 0.3 + 0.7 * clamp01(subtitles_count/200)
  - bqi_coord:
      * priority = 2 (default)
      * emotion = ["curious"] (default), plus ["instruct"] if title contains tutorial/guide
      * rhythm = "learn" if tutorial-like title, else "observe"
"""
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]  # .../fdo_agi_repo
YT_OUT_DIR = ROOT / "outputs" / "youtube_learner"
OUT_JSONL = ROOT / "outputs" / "youtube_feedback_bqi.jsonl"


def clamp01(x: float) -> float:
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def is_tutorial_title(title: str) -> bool:
    if not title:
        return False
    t = title.lower()
    keywords = ["tutorial", "guide", "how to", "learn", "lesson"]
    return any(k in t for k in keywords)


def compute_bqi_coord(title: str) -> Dict[str, Any]:
    emo: List[str] = ["curious"]
    rhythm = "observe"
    if is_tutorial_title(title):
        emo.append("instruct")
        rhythm = "learn"
    return {"priority": 2, "emotion": sorted(set(emo)), "rhythm": rhythm}


def compute_quality_and_confidence(subtitles: List[Dict[str, Any]], summary: str | None) -> tuple[float, float, int, int]:
    # Aggregate OCR text length
    ocr_text_len = 0
    for s in subtitles or []:
        txt = s.get("text")
        if isinstance(txt, str):
            ocr_text_len += len(txt)

    subtitles_count = len(subtitles or [])

    # Heuristic quality
    quality = 0.4 + 0.4 * clamp01(ocr_text_len / 5000.0)
    if summary and isinstance(summary, str) and summary.strip():
        quality += 0.2
    quality = clamp01(quality)

    # Heuristic confidence based on coverage
    confidence = 0.3 + 0.7 * clamp01(subtitles_count / 200.0)
    confidence = clamp01(confidence)

    return quality, confidence, subtitles_count, ocr_text_len


def collect_input_files() -> List[Path]:
    if not YT_OUT_DIR.exists():
        return []
    return sorted(YT_OUT_DIR.glob("*_analysis.json"))


def load_json(p: Path) -> Dict[str, Any]:
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_video_url(video_id: str | None) -> str | None:
    if not video_id:
        return None
    return f"https://www.youtube.com/watch?v={video_id}"


def main() -> int:
    files = collect_input_files()
    if not files:
        print(f"[YouTube→BQI] No files found in {YT_OUT_DIR}")
        return 0

    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    written = 0

    with OUT_JSONL.open("w", encoding="utf-8") as out:
        for p in files:
            try:
                data = load_json(p)
            except Exception as e:
                print(f"[YouTube→BQI] Skip {p.name}: failed to parse JSON ({e})")
                continue

            title = data.get("title") or data.get("video_title") or ""
            video_id = data.get("video_id") or data.get("id")
            duration = data.get("duration")
            subtitles = data.get("subtitles") or []
            summary = data.get("summary")

            quality, confidence, subs_cnt, ocr_len = compute_quality_and_confidence(subtitles, summary)
            bqi_coord = compute_bqi_coord(title)

            rec = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "source": "youtube",
                "task_id": f"yt-{video_id or p.stem}",
                "bqi_coord": bqi_coord,
                "quality": round(quality, 4),
                "confidence": round(confidence, 4),
                "meta": {
                    "video_id": video_id,
                    "title": title,
                    "duration": duration,
                    "subtitles_count": subs_cnt,
                    "ocr_text_len": ocr_len,
                    "file": str(p.relative_to(ROOT))
                },
                "summary": summary,
                "video_url": build_video_url(video_id)
            }

            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            written += 1

    print(f"[YouTube→BQI] Wrote {written} records → {OUT_JSONL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
