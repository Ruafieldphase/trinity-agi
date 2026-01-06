#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
System Gaps Report (v1)

목적:
- 워크스페이스에서 '껍데기/미구현/미연결' 요소를 사실 기반으로 요약해
  비프로그래머도 바로 읽을 수 있는 리포트를 생성한다.

포함 범위(사실 기반):
- 명시적 stub(파일 헤더/주석에 stub/placeholder/미구현 표기)
- TODO / NotImplementedError 같은 구현 공백 신호
- *.disabled(의도적으로 꺼둔 기능)
- 운영 루프에 "연결은 됐지만 출력이 오래된" 관측 파일(미연결 의심)

원칙:
- 네트워크 없음
- 민감정보 원문 저장 없음(라인은 짧게 clip)
- best-effort: 실패해도 최소 출력 생성

출력:
- outputs/bridge/system_gaps_report_latest.txt
- outputs/bridge/system_gaps_report_latest.json
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from workspace_root import get_workspace_root


ROOT = get_workspace_root()
OUTPUTS = ROOT / "outputs"
BRIDGE = OUTPUTS / "bridge"
SYNC_CACHE = OUTPUTS / "sync_cache"

OUT_TXT = BRIDGE / "system_gaps_report_latest.txt"
OUT_JSON = BRIDGE / "system_gaps_report_latest.json"

# Reuse stub_radar outputs if present (cheap). Fall back to a local scan.
STUB_RADAR_JSON = BRIDGE / "stub_radar_latest.json"

SCAN_DIRS = [
    ROOT / "scripts",
    ROOT / "safety",
    ROOT / "agi",
    ROOT / "agi_core",
    ROOT / "fdo_agi_repo",
]

ALLOW_EXT = {".py", ".ps1", ".md"}
MAX_FILE_BYTES = 800_000
MAX_FILES = 6_000
MAX_HITS = 600

# 외부/생성물/가상환경/캐시 디렉토리는 스캔/리포트에서 제외(노이즈 방지)
EXCLUDE_PARTS = {
    ".git",
    ".venv",
    ".venv_local",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".pytest_tmp",
    ".next",
    "dist",
    "build",
    "site-packages",
}

PATTERNS = [
    ("stub", "stub v"),
    ("stub", "stub only"),
    ("stub", "minimal stub"),
    ("stub", "placeholder"),
    ("stub", "스텁"),
    ("stub", "미구현"),
    ("todo", "TODO"),
    ("not_implemented", "NotImplementedError"),
]

OBS_STALENESS = [
    # (label, path, stale_seconds)
    ("glymphatic_metrics_latest", OUTPUTS / "glymphatic_metrics_latest.json", 6 * 60 * 60),
    ("deep_sleep_consolidation_latest", OUTPUTS / "deep_sleep_consolidation_latest.json", 24 * 60 * 60),
    ("digital_twin_state", SYNC_CACHE / "digital_twin_state.json", 60 * 60),
    ("quantum_digital_twin_state", SYNC_CACHE / "quantum_digital_twin_state.json", 60 * 60),
    ("rhythm_pain_latest", SYNC_CACHE / "rhythm_pain_latest.json", 10 * 60),
]


def _utc_iso_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _atomic_write_text(path: Path, text: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)
    except Exception:
        return


def _atomic_write_json(path: Path, obj: dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, path)
    except Exception:
        return


def _file_age_s(path: Path) -> float | None:
    try:
        if not path.exists():
            return None
        return max(0.0, time.time() - path.stat().st_mtime)
    except Exception:
        return None


def _fmt_age(age_s: float | None) -> str:
    if age_s is None:
        return "없음"
    if age_s < 60:
        return f"{int(age_s)}초"
    if age_s < 3600:
        return f"{int(age_s // 60)}분"
    return f"{int(age_s // 3600)}시간"


def _iter_files(dirs: Iterable[Path]) -> Iterable[Path]:
    count = 0
    for base in dirs:
        if not base.exists():
            continue
        try:
            for p in base.rglob("*"):
                if count >= MAX_FILES:
                    return
                if not p.is_file():
                    continue
                try:
                    if any(part in EXCLUDE_PARTS for part in p.parts):
                        continue
                except Exception:
                    pass
                if p.suffix.lower() not in ALLOW_EXT:
                    continue
                try:
                    if p.stat().st_size > MAX_FILE_BYTES:
                        continue
                except Exception:
                    continue
                count += 1
                yield p
        except Exception:
            continue


def _read_head(path: Path, max_lines: int = 260) -> list[str]:
    try:
        out: list[str] = []
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for _ in range(max_lines):
                line = f.readline()
                if not line:
                    break
                out.append(line.rstrip("\n"))
        return out
    except Exception:
        return []


@dataclass
class Hit:
    kind: str
    pattern: str
    path: str
    line_no: int
    line: str


def _scan_hits_fallback() -> tuple[int, list[Hit]]:
    scanned = 0
    hits: list[Hit] = []
    for p in _iter_files(SCAN_DIRS):
        scanned += 1
        head = _read_head(p)
        if not head:
            continue
        for i, line in enumerate(head, start=1):
            low = (line or "").lower()
            for kind, pat in PATTERNS:
                if pat.lower() in low:
                    clipped = line if len(line) <= 240 else (line[:240] + "…")
                    hits.append(Hit(kind=kind, pattern=pat, path=str(p), line_no=i, line=clipped))
                    if len(hits) >= MAX_HITS:
                        return scanned, hits
        # also detect disabled files via filename
        if p.name.endswith(".disabled") or p.suffix.lower() == ".disabled":
            hits.append(Hit(kind="disabled", pattern="*.disabled", path=str(p), line_no=1, line="(disabled file)"))
            if len(hits) >= MAX_HITS:
                return scanned, hits
    return scanned, hits


def _load_stub_radar() -> tuple[int, list[Hit]]:
    try:
        if not STUB_RADAR_JSON.exists():
            return 0, []
        obj = json.loads(STUB_RADAR_JSON.read_text(encoding="utf-8-sig"))
        if not isinstance(obj, dict):
            return 0, []
        scanned = int(obj.get("scanned_files") or 0)
        raw = obj.get("hits") if isinstance(obj.get("hits"), list) else []
        hits: list[Hit] = []
        for r in raw:
            if not isinstance(r, dict):
                continue
            p = str(r.get("path") or "")
            try:
                if any(part in EXCLUDE_PARTS for part in Path(p).parts):
                    continue
            except Exception:
                pass
            hits.append(
                Hit(
                    kind=str(r.get("kind") or ""),
                    pattern=str(r.get("pattern") or ""),
                    path=p,
                    line_no=int(r.get("line_no") or 0),
                    line=str(r.get("line") or ""),
                )
            )
        return scanned, hits
    except Exception:
        return 0, []


def _prioritize(h: Hit) -> tuple[int, str]:
    p = h.path.replace("\\", "/").lower()
    if "/safety/" in p or p.endswith("/safety/red_line_monitor.py") or p.endswith("/safety/kill_switch.py"):
        return 0, p
    if "/scripts/trigger_listener.py" in p or "/scripts/self_expansion/" in p:
        return 1, p
    if "/scripts/windows/" in p or "/body/" in p:
        return 2, p
    if "/scripts/tools/" in p:
        return 3, p
    if "/scripts/planning/" in p or "/scripts/metacognition/" in p:
        return 4, p
    return 7, p


def main() -> int:
    start = time.time()
    BRIDGE.mkdir(parents=True, exist_ok=True)

    scanned, hits = _load_stub_radar()
    source = "stub_radar_latest.json"
    if not hits:
        scanned, hits = _scan_hits_fallback()
        source = "fallback_head_scan"

    # also collect disabled files (fast filename scan)
    disabled: list[str] = []
    try:
        for p in (ROOT / "scripts").rglob("*.disabled"):
            if p.is_file():
                disabled.append(str(p))
    except Exception:
        pass

    # Observability gaps: stale outputs
    stales: list[dict[str, Any]] = []
    for label, path, stale_s in OBS_STALENESS:
        age = _file_age_s(path)
        stales.append(
            {
                "label": label,
                "path": str(path),
                "age_s": age,
                "stale_threshold_s": stale_s,
                "is_stale": (age is None) or (age > float(stale_s)),
            }
        )

    # Sort hits for report (priority + path)
    hits_sorted = sorted(hits, key=_prioritize)

    # Count categories
    counts: dict[str, int] = {}
    for h in hits:
        k = str(h.kind or "unknown")
        counts[k] = counts.get(k, 0) + 1

    obj: dict[str, Any] = {
        "generated_at_utc": _utc_iso_now(),
        "source": source,
        "scanned_files": scanned,
        "counts": counts,
        "disabled_files_count": len(disabled),
        "stale_observables": stales,
        "top_hits": [
            {
                "kind": h.kind,
                "pattern": h.pattern,
                "path": h.path,
                "line_no": h.line_no,
                "line": h.line,
            }
            for h in hits_sorted[:120]
        ],
        "duration_sec": round(time.time() - start, 3),
        "note": "이 리포트는 사실 기반(표기/스키마/갱신시간)이다. stub=나쁨이 아니라 '미구현/미연결' 신호일 수 있다.",
    }

    # Human-readable
    lines: list[str] = []
    lines.append("시스템 갭/껍데기 리포트 (사람용)")
    lines.append(f"- 생성: {obj['generated_at_utc']}")
    lines.append(f"- 소스: {source}")
    lines.append(f"- 스캔 파일 수(참조): {scanned}")
    lines.append("")
    lines.append("1) 껍데기/미구현 신호(카운트)")
    for k in sorted(counts.keys()):
        lines.append(f"- {k}: {counts[k]}")
    lines.append(f"- *.disabled 파일: {len(disabled)}")
    lines.append("")
    lines.append("2) 관측 파일 stale(미연결 의심)")
    for s in stales:
        label = str(s.get("label"))
        age_s = s.get("age_s")
        is_stale = bool(s.get("is_stale"))
        lines.append(f"- {label}: {_fmt_age(age_s)} ({'stale' if is_stale else 'ok'})")
    lines.append("")
    lines.append("3) 우선순위 상위 히트(일부)")
    for h in hits_sorted[:35]:
        rel = h.path
        try:
            rel = str(Path(h.path).resolve().relative_to(ROOT))
        except Exception:
            pass
        lines.append(f"- [{h.kind}] {rel}:{h.line_no} ({h.pattern})")
    if len(hits_sorted) > 35:
        lines.append(f"- ... (상위 120개는 JSON에 포함, 총 히트 {len(hits_sorted)}개)")

    _atomic_write_json(OUT_JSON, obj)
    _atomic_write_text(OUT_TXT, "\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
