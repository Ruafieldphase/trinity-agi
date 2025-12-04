import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

# Use absolute base path to avoid drive-relative quirks like 'd:nas_backup\\...'
BASE = r"C:\workspace\agi"
LEDGER_PATH = os.path.join(BASE, "fdo_agi_repo", "memory", "resonance_ledger.jsonl")
# Primary Sena consolidated log
SENA_JSONL = os.path.join(BASE, "outputs", "sena", "sena_conversations_flat.jsonl")
# Additional Sena raw logs (recursive)
SENA_RAW_DIR = os.path.join(BASE, "ai_binoche_conversation_origin", "cladeCLI-sena")
OUT_JSON = os.path.join(BASE, "outputs", "sena_correlation_latest.json")
OUT_MD = os.path.join(BASE, "outputs", "sena_correlation_latest.md")

# Default +/- window (minutes). Can override with env SENA_CORR_WINDOW_MIN or argv --window-minutes
WINDOW_SECONDS = 10 * 60  # +/- 10 minutes


def parse_epoch(ts: Any) -> Optional[float]:
    # Ledger uses float epoch seconds. Sena uses ISO8601.
    if ts is None:
        return None
    if isinstance(ts, (int, float)):
        return float(ts)
    if isinstance(ts, str):
        s = ts.strip()
        # try float string
        try:
            return float(s)
        except Exception:
            pass
        # try ISO8601
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            return dt.timestamp()
        except Exception:
            return None
    return None


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    if not os.path.exists(path):
        return items
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                items.append(obj)
            except Exception:
                # skip malformed
                continue
    return items


def load_sena_sources() -> List[Dict[str, Any]]:
    # Merge primary consolidated Sena file and any raw jsonl files under SENA_RAW_DIR
    merged: List[Dict[str, Any]] = []
    seen: set = set()  # dedupe by (create_time, author_role, hash(content[:200]))

    # 1) Primary consolidated file
    primary = load_jsonl(SENA_JSONL)
    for it in primary:
        key = (
            str(it.get("create_time") or it.get("update_time") or ""),
            str(it.get("author_role") or ""),
            hash((it.get("content") or "")[:200]),
        )
        if key in seen:
            continue
        seen.add(key)
        merged.append(it)

    # 2) Raw jsonl files discovered recursively
    if os.path.isdir(SENA_RAW_DIR):
        for root, _, files in os.walk(SENA_RAW_DIR):
            for fn in files:
                if not fn.lower().endswith(".jsonl"):
                    continue
                path = os.path.join(root, fn)
                try:
                    docs = load_jsonl(path)
                except Exception:
                    docs = []
                for it in docs:
                    key = (
                        str(it.get("create_time") or it.get("update_time") or ""),
                        str(it.get("author_role") or ""),
                        hash((it.get("content") or "")[:200]),
                    )
                    if key in seen:
                        continue
                    seen.add(key)
                    merged.append(it)

    return merged


def summarize_cache(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    cache_hits = 0
    cache_misses = 0
    cache_evictions = 0
    total_time_saved_ms = 0.0
    cache_hit_events = 0
    cache_miss_events = 0

    # latency distributions by cache hit
    lat_cache: List[float] = []
    lat_nocache: List[float] = []

    for e in entries:
        if e.get("event") != "evidence_correction":
            continue
        cache_hit = bool(e.get("cache_hit", False))
        rag_latency = float(e.get("rag_latency_ms", 0.0) or 0.0)
        cache = e.get("cache") or {}
        # Aggregate per-event cache stats if present
        try:
            cache_hits += int(cache.get("hits", 0) or 0)
            cache_misses += int(cache.get("misses", 0) or 0)
            cache_evictions += int(cache.get("evictions", 0) or 0)
            total_time_saved_ms += float(cache.get("total_time_saved_ms", 0.0) or 0.0)
        except Exception:
            pass

        if cache_hit:
            cache_hit_events += 1
            lat_cache.append(rag_latency)
        else:
            cache_miss_events += 1
            lat_nocache.append(rag_latency)

    total_ops = cache_hits + cache_misses
    hit_rate_percent = (cache_hits / total_ops * 100.0) if total_ops > 0 else 0.0

    def pct(n: int, d: int) -> float:
        return (n / d * 100.0) if d > 0 else 0.0

    def safe_median(x: List[float]) -> Optional[float]:
        if not x:
            return None
        s = sorted(x)
        mid = len(s) // 2
        if len(s) % 2 == 1:
            return s[mid]
        return (s[mid - 1] + s[mid]) / 2.0

    return {
        "events": {
            "cache_hit_events": cache_hit_events,
            "cache_miss_events": cache_miss_events,
            "cache_hit_event_rate_percent": pct(cache_hit_events, cache_hit_events + cache_miss_events),
            "median_latency_ms_when_cache_hit": safe_median(lat_cache),
            "median_latency_ms_when_cache_miss": safe_median(lat_nocache),
        },
        "counters": {
            "hits": cache_hits,
            "misses": cache_misses,
            "hit_rate_percent": round(hit_rate_percent, 2),
            "evictions": cache_evictions,
            "total_time_saved_ms": round(total_time_saved_ms, 2),
        },
    }


def build_sena_index(sena_items: List[Dict[str, Any]]) -> List[Tuple[float, Dict[str, Any]]]:
    indexed: List[Tuple[float, Dict[str, Any]]] = []
    for it in sena_items:
        ts = parse_epoch(it.get("create_time")) or parse_epoch(it.get("update_time"))
        if ts is None:
            continue
        indexed.append((ts, it))
    indexed.sort(key=lambda x: x[0])
    return indexed


def correlate(ledger_items: List[Dict[str, Any]], sena_index: List[Tuple[float, Dict[str, Any]]]) -> Dict[str, Any]:
    # Find ledger anomalies and correlate with nearby sena messages
    anomalies: List[Dict[str, Any]] = []
    zero_hit_events = 0
    error_events = 0

    for e in ledger_items:
        if e.get("event") != "evidence_correction":
            continue
        ts = parse_epoch(e.get("ts"))
        if ts is None:
            continue
        has_error = bool(e.get("error"))
        hits = int(e.get("hits", 0) or 0)
        if has_error:
            error_events += 1
        if hits == 0:
            zero_hit_events += 1

        if has_error or hits == 0:
            # find sena messages within window
            near: List[Dict[str, Any]] = []
            # two-pointer/linear scan since both are moderate sized
            # naive approach: binary search could be added if needed
            for ts_sena, sena_rec in sena_index:
                if abs(ts_sena - ts) <= WINDOW_SECONDS:
                    near.append({
                        "create_time": sena_rec.get("create_time"),
                        "conversation_title": sena_rec.get("conversation_title"),
                        "author_role": sena_rec.get("author_role"),
                        "content_preview": (sena_rec.get("content") or "")[:120],
                    })
            anomalies.append({
                "ts": ts,
                "ts_iso": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(),
                "error": e.get("error"),
                "hits": hits,
                "added": int(e.get("added", 0) or 0),
                "forced": e.get("forced"),
                "pass": e.get("pass"),
                "nearby_sena_messages": near[:10],  # cap to 10 examples
            })

    return {
        "window_seconds": WINDOW_SECONDS,
        "summary": {
            "ledger_evidence_events": sum(1 for e in ledger_items if e.get("event") == "evidence_correction"),
            "zero_hit_events": zero_hit_events,
            "error_events": error_events,
        },
        "anomalies": anomalies[:200],  # safety cap
    }


def main() -> int:
    global WINDOW_SECONDS

    # Allow override of window via env or argv
    try:
        env_min = os.getenv("SENA_CORR_WINDOW_MIN")
        if env_min:
            WINDOW_SECONDS = int(float(env_min) * 60)
    except Exception:
        pass
    # argv: --window-minutes N
    try:
        if "--window-minutes" in sys.argv:
            idx = sys.argv.index("--window-minutes")
            val = sys.argv[idx + 1]
            WINDOW_SECONDS = int(float(val) * 60)
    except Exception:
        pass

    ledger_items = load_jsonl(LEDGER_PATH)
    sena_items = load_sena_sources()

    cache_summary = summarize_cache(ledger_items)
    sena_index = build_sena_index(sena_items)
    correlation = correlate(ledger_items, sena_index)

    out = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "ledger_path": LEDGER_PATH,
            "sena_primary": SENA_JSONL,
            "sena_raw_dir": SENA_RAW_DIR,
            "window_minutes": WINDOW_SECONDS // 60,
        },
        "cache": cache_summary,
        "correlation": correlation,
    }

    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    # Markdown summary
    lines: List[str] = []
    lines.append("# Sena Correlation and Cache Summary")
    lines.append("")
    lines.append(f"Generated: {out['generated']}")
    lines.append("")
    lines.append("## Cache Summary")
    lines.append("")
    c = out["cache"]
    lines.append("- Hits: {} | Misses: {} | Hit Rate: {}% | Evictions: {}".format(
        c["counters"]["hits"], c["counters"]["misses"], c["counters"]["hit_rate_percent"], c["counters"]["evictions"],
    ))
    lines.append("- Total Time Saved (ms): {}".format(c["counters"]["total_time_saved_ms"]))
    lines.append("- Median RAG Latency (cache hit): {} ms".format(c["events"]["median_latency_ms_when_cache_hit"]))
    lines.append("- Median RAG Latency (cache miss): {} ms".format(c["events"]["median_latency_ms_when_cache_miss"]))
    lines.append("- Cache-hit events: {} ({}%)".format(
        c["events"]["cache_hit_events"], round(c["events"]["cache_hit_event_rate_percent"], 2)
    ))
    lines.append("")

    lines.append("## Correlation with Sena")
    lines.append("")
    corr = out["correlation"]
    lines.append("- Window: +/- {} minutes".format(WINDOW_SECONDS // 60))
    lines.append("- Evidence corrections: {}".format(corr["summary"]["ledger_evidence_events"]))
    lines.append("- Zero-hit events: {}".format(corr["summary"]["zero_hit_events"]))
    lines.append("- Error events: {}".format(corr["summary"]["error_events"]))
    lines.append("")
    lines.append("### Sample anomalies (up to 10)")
    for a in corr["anomalies"][:10]:
        lines.append("-")
        lines.append("  - When: {}".format(a["ts_iso"]))
        lines.append("  - Error: {} | Hits: {} | Added: {} | Pass: {} | Forced: {}".format(
            a.get("error"), a.get("hits"), a.get("added"), a.get("pass"), a.get("forced")
        ))
        near = a.get("nearby_sena_messages", [])
        if near:
            for m in near[:3]:
                lines.append("    - Sena: {} | {} | {}".format(
                    m.get("create_time"), m.get("author_role"), (m.get("content_preview") or "").replace("\n", " ")
                ))
        else:
            lines.append("    - Sena: (no messages in window)")

    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Wrote {OUT_JSON} and {OUT_MD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
