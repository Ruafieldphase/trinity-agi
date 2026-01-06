import json
from pathlib import Path
import csv
from datetime import datetime, timezone

OUT_DIR = Path("outputs/youtube_learner")
INDEX = OUT_DIR / "INDEX.md"
INDEX_CSV = OUT_DIR / "INDEX.csv"

def load_entries():
    entries = []
    if not OUT_DIR.exists():
        return entries
    for p in sorted(OUT_DIR.glob("*_analysis.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            ts = data.get("analyzed_at") or ""
            dt = None
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "")) if ts else None
            except Exception:
                dt = None
            entries.append({
                "path": p,
                "video_id": data.get("video_id", ""),
                "title": data.get("title", "")[:120],
                "duration": data.get("duration", 0),
                "subs": data.get("subtitles_count", 0),
                "frames": data.get("frames_count", 0),
                "keywords": ", ".join(data.get("keywords", [])[:5]),
                "analyzed_at": ts,
                "dt": dt or datetime.fromtimestamp(p.stat().st_mtime),
            })
        except Exception:
            continue
    # 최신순 정렬
    entries.sort(key=lambda x: x["dt"], reverse=True)
    return entries

def write_index(entries):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    lines = []
    lines.append("# YouTube Learner Index\n")
    now_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    lines.append(f"Updated: {now_utc}\n")
    lines.append("\n")
    if not entries:
        lines.append("No analysis files found in outputs/youtube_learner.\n")
        INDEX.write_text("".join(lines), encoding="utf-8")
        return
    # 표 헤더
    lines.append("| Video ID | Title | Dur(s) | Subs | Frames | Keywords | Analyzed At |\n")
    lines.append("|---|---|---:|---:|---:|---|---|\n")
    for e in entries:
        vid = e["video_id"]
        title = e["title"].replace("|", " ")
        dur = int(e["duration"] or 0)
        subs = e["subs"]
        frames = e["frames"]
        kw = e["keywords"].replace("|", ",")
        ts = (e["analyzed_at"] or "").replace("T", " ")[:19]
        rel_json = e["path"].as_posix()
        md_path = e["path"].with_suffix(".md")
        rel_link = md_path.as_posix() if md_path.exists() else rel_json
        lines.append(f"| {vid} | [{title}]({rel_link}) | {dur} | {subs} | {frames} | {kw} | {ts} |\n")
    INDEX.write_text("".join(lines), encoding="utf-8")
    # Also write CSV for analysis
    with INDEX_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["video_id","title","duration","subtitles","frames","keywords","analyzed_at","path"])
        for e in entries:
            writer.writerow([
                e["video_id"],
                e["title"],
                int(e["duration"] or 0),
                e["subs"],
                e["frames"],
                e["keywords"],
                e["analyzed_at"],
                e["path"].as_posix(),
            ])

def main():
    entries = load_entries()
    write_index(entries)

if __name__ == "__main__":
    main()
