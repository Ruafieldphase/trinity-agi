"""
StallGuard: Information-theoretic stall/loop detector

Checks recent activity across files and optional HTTP endpoints to decide if the
system is making progress or stuck in a low-information loop. Outputs a JSON
summary and returns non-zero on detected stall.

Signals used
- Recency: file modification time within window
- Novelty: Shannon entropy of the last window of bytes
- Compressibility: gzip compression ratio of the last window

Exit codes
- 0: healthy
- 1: stall suspected (actionable)

Usage example
python stall_guard.py --paths outputs/results_log.jsonl fdo_agi_repo/memory/resonance_ledger.jsonl \
    --urls http://127.0.0.1:8091/api/health \
    --window-seconds 300 --min-entropy 2.5 --min-compression-ratio 1.05 \
    --out-json outputs/stall_guard_report.json
"""
from __future__ import annotations

import argparse
import gzip
import io
import json
import math
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Dict, Any

try:
    import urllib.request as urlreq
except Exception:  # pragma: no cover - fallback not critical
    urlreq = None


def shannon_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    # Byte frequency
    counts = [0] * 256
    for b in data:
        counts[b] += 1
    total = float(len(data))
    ent = 0.0
    for c in counts:
        if c:
            p = c / total
            ent -= p * math.log2(p)
    return ent  # bits per byte (0..8)


def gzip_ratio(data: bytes) -> float:
    if not data:
        return 1.0
    bio = io.BytesIO()
    with gzip.GzipFile(fileobj=bio, mode="wb") as gz:
        gz.write(data)
    comp = bio.tell()
    if comp == 0:
        return 1.0
    return max(1.0, len(data) / comp)


def tail_bytes(p: Path, max_bytes: int = 4096) -> bytes:
    try:
        size = p.stat().st_size
        with p.open("rb", errors="ignore") as f:  # type: ignore[arg-type]
            if size <= max_bytes:
                return f.read()
            f.seek(size - max_bytes)
            return f.read()
    except FileNotFoundError:
        return b""
    except Exception:
        return b""


def http_ok(url: str, timeout: float = 2.0) -> bool:
    if urlreq is None:
        return False
    try:
        with urlreq.urlopen(url, timeout=timeout) as r:  # nosec B310
            return 200 <= getattr(r, "status", 0) < 300
    except Exception:
        return False


@dataclass
class FileSignal:
    path: str
    exists: bool
    modified_secs: Optional[float]
    entropy_bits_per_byte: float
    compression_ratio: float
    sample_len: int


@dataclass
class UrlSignal:
    url: str
    ok: bool


@dataclass
class StallReport:
    status: str  # "healthy" | "stall"
    window_seconds: int
    min_entropy: float
    min_compression_ratio: float
    max_modified_age: int
    now_epoch: int
    files: List[FileSignal]
    urls: List[UrlSignal]
    notes: List[str]

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


def evaluate(
    files: List[Path],
    urls: List[str],
    window_seconds: int,
    min_entropy: float,
    min_compression_ratio: float,
) -> StallReport:
    now = time.time()
    file_signals: List[FileSignal] = []
    url_signals: List[UrlSignal] = []
    notes: List[str] = []

    # File-based signals
    for p in files:
        exists = p.exists()
        m_age = None
        if exists:
            try:
                m_age = max(0.0, now - p.stat().st_mtime)
            except Exception:
                m_age = None
        tail = tail_bytes(p)
        ent = shannon_entropy(tail)
        ratio = gzip_ratio(tail)
        file_signals.append(
            FileSignal(
                path=str(p),
                exists=exists,
                modified_secs=(m_age if m_age is not None else None),
                entropy_bits_per_byte=ent,
                compression_ratio=ratio,
                sample_len=len(tail),
            )
        )

    # URL-based signals
    for u in urls:
        ok = http_ok(u)
        url_signals.append(UrlSignal(url=u, ok=ok))

    # Decision: consider stall if ANY critical channel is stale AND low-information
    stale_flags = []
    low_info_flags = []
    for s in file_signals:
        if not s.exists:
            continue
        if s.modified_secs is None:
            continue
        stale_flags.append(s.modified_secs > window_seconds)
        # Only evaluate low-info if we have enough data in the tail
        if s.sample_len >= 64:
            low_info_flags.append(
                (s.entropy_bits_per_byte < min_entropy)
                or (s.compression_ratio < min_compression_ratio)
            )
        else:
            low_info_flags.append(False)

    url_down = any(not u.ok for u in url_signals) if url_signals else False

    stall = False
    # Heuristic: stall if (stale AND low-info) on any file OR critical URL down
    if file_signals:
        for stale, low in zip(stale_flags, low_info_flags):
            if stale and low:
                stall = True
                notes.append("stale+lowinfo detected on a monitored file")
                break
        # If all files are stale (no activity), that's also a stall
        if not stall and all(stale_flags) and file_signals:
            stall = True
            notes.append("all monitored files stale within window")
    if url_down:
        stall = True
        notes.append("one or more critical URLs unhealthy")

    return StallReport(
        status=("stall" if stall else "healthy"),
        window_seconds=window_seconds,
        min_entropy=min_entropy,
        min_compression_ratio=min_compression_ratio,
        max_modified_age=window_seconds,
        now_epoch=int(now),
        files=file_signals,
        urls=url_signals,
        notes=notes,
    )


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Stall/loop detector")
    ap.add_argument("--paths", nargs="*", default=[], help="Files to monitor")
    ap.add_argument("--urls", nargs="*", default=[], help="Health URLs to check")
    ap.add_argument("--window-seconds", type=int, default=300)
    ap.add_argument("--min-entropy", type=float, default=2.5)
    ap.add_argument("--min-compression-ratio", type=float, default=1.05)
    ap.add_argument("--out-json", type=str, default="")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    files = [Path(p) for p in args.paths]
    rep = evaluate(
        files=files,
        urls=list(args.urls),
        window_seconds=args.window_seconds,
        min_entropy=args.min_entropy,
        min_compression_ratio=args.min_compression_ratio,
    )
    out = rep.to_json()
    sys.stdout.write(out + "\n")
    if args.out_json:
        try:
            Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
            Path(args.out_json).write_text(out, encoding="utf-8")
        except Exception:
            # Non-fatal
            pass
    return 1 if rep.status == "stall" else 0


if __name__ == "__main__":
    raise SystemExit(main())
