#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stub Radar (v1)

목적:
- 워크스페이스 안에서 "껍데기(=stub/미구현/문서참조 복구용 placeholder)"로 남아 있는 구성요소를
  사실 기반으로 스캔하여, 사람이 읽을 수 있는 리포트로 고정한다.

원칙:
- 네트워크 없음
- 민감정보(키/계정/토큰/대화 원문/URL 원문 등) 저장 없음
- best-effort: 실패해도 최소 파일 생성
- 과도한 I/O 방지:
  - 확장자 제한(.py/.ps1)
  - 파일 크기 상한
  - 최대 파일 수 제한

출력:
- outputs/bridge/stub_radar_latest.json
- outputs/bridge/stub_radar_latest.txt
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
BRIDGE = OUTPUTS / "bridge"

OUT_JSON = BRIDGE / "stub_radar_latest.json"
OUT_TXT = BRIDGE / "stub_radar_latest.txt"

SCAN_DIRS = [
    ROOT / "scripts",
    ROOT / "safety",
    ROOT / "agi",
    ROOT / "agi_core",
    ROOT / "fdo_agi_repo",
]

ALLOW_EXT = {".py", ".ps1"}
MAX_FILE_BYTES = 700_000  # skip huge files
MAX_FILES = 3_500
MAX_HITS = 220

# 외부/생성물/가상환경/캐시 디렉토리는 스캔에서 제외(노이즈 방지)
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
    ("stub_docstring", "stub v"),
    ("stub_docstring", "stub only"),
    ("stub_docstring", "minimal stub"),
    ("stub_docstring", "placeholder"),
    ("stub_ko", "스텁"),
    ("stub_ko", "미구현"),
    ("todo", "TODO"),
    ("not_implemented", "NotImplementedError"),
]


def _utc_iso_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _atomic_write_json(path: Path, obj: dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, path)
    except Exception:
        return


def _atomic_write_text(path: Path, text: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)
    except Exception:
        return


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


def _read_head(path: Path, max_lines: int = 220) -> list[str]:
    try:
        lines: list[str] = []
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for _ in range(max_lines):
                line = f.readline()
                if not line:
                    break
                lines.append(line.rstrip("\n"))
        return lines
    except Exception:
        return []


@dataclass
class Hit:
    kind: str
    pattern: str
    path: str
    line_no: int
    line: str


def _find_hits(path: Path) -> list[Hit]:
    head = _read_head(path)
    if not head:
        return []
    hits: list[Hit] = []
    for i, line in enumerate(head, start=1):
        s = (line or "")
        low = s.lower()
        for kind, pat in PATTERNS:
            if pat.lower() in low:
                # 너무 긴 라인(경로/URL 등 포함 가능)은 잘라서 저장
                clipped = s if len(s) <= 240 else (s[:240] + "…")
                hits.append(Hit(kind=kind, pattern=pat, path=str(path), line_no=i, line=clipped))
                if len(hits) >= 6:
                    return hits
    return hits


def main() -> int:
    start = time.time()
    BRIDGE.mkdir(parents=True, exist_ok=True)

    found: list[Hit] = []
    scanned = 0
    for p in _iter_files(SCAN_DIRS):
        scanned += 1
        for h in _find_hits(p):
            found.append(h)
            if len(found) >= MAX_HITS:
                break
        if len(found) >= MAX_HITS:
            break

    # 간단 분류: 실제 stub(명시) vs TODO/NotImplemented
    stub_like = [h for h in found if h.kind.startswith("stub")]
    todo_like = [h for h in found if h.kind in {"todo", "not_implemented"}]

    obj: dict[str, Any] = {
        "generated_at_utc": _utc_iso_now(),
        "scanned_files": scanned,
        "hits": [
            {
                "kind": h.kind,
                "pattern": h.pattern,
                "path": h.path,
                "line_no": h.line_no,
                "line": h.line,
            }
            for h in found
        ],
        "summary": {
            "stub_like": len(stub_like),
            "todo_like": len(todo_like),
            "note": "이 리포트는 상단(head)만 스캔한 '레이더'이며, 전체 코드 품질 평가가 아니다.",
        },
        "duration_sec": round(time.time() - start, 3),
    }

    lines = [
        "Stub/미구현 레이더 (사람용)",
        f"- 생성: {obj['generated_at_utc']}",
        f"- 스캔 파일 수: {scanned}",
        f"- stub 표시: {obj['summary']['stub_like']}, TODO/NotImplemented: {obj['summary']['todo_like']}",
        "",
        "상위 항목(일부):",
    ]
    for h in found[:35]:
        rel = h.path
        try:
            rel = str(Path(h.path).resolve().relative_to(ROOT))
        except Exception:
            pass
        lines.append(f"- [{h.kind}] {rel}:{h.line_no} ({h.pattern})")
    if len(found) > 35:
        lines.append(f"- ... (총 {len(found)}개 히트, JSON에 전체 저장)")

    _atomic_write_json(OUT_JSON, obj)
    _atomic_write_text(OUT_TXT, "\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
