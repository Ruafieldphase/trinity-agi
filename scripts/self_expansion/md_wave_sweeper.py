#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MD Wave Sweeper (v1) — 파동 학습 기반 문서 역추적

목표
- 워크스페이스에 존재하는 방대한 .md 문서에서 "미연결 포인트"를 자동으로 추출한다.
- 여기서 말하는 미연결 포인트:
  1) TODO/NEXT/GAP/미완/누락/연결/통합 등의 표식
  2) 문서가 언급하는 코드/스크립트/산출물 경로가 실제로 존재하는지(끊긴 연결)
- 외부 모델 호출 없이 파일 기반으로만 수행한다.
- 전체 스캔은 무겁기 때문에, 기본은 "증분 스캔"으로 동작한다.

출력
- outputs/md_wave_sweep_latest.json
- outputs/md_wave_sweep_latest.md
- outputs/md_wave_sweep_history.jsonl (append-only)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


def utc_iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _safe_load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else None
    except Exception:
        try:
            obj = json.loads(path.read_text(encoding="utf-8-sig"))
            return obj if isinstance(obj, dict) else None
        except Exception:
            return None


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def _atomic_write_json(path: Path, obj: Dict[str, Any]) -> None:
    _atomic_write_text(path, json.dumps(obj, ensure_ascii=False, indent=2))


ISSUE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("todo", re.compile(r"\bTODO\b", re.IGNORECASE)),
    ("next", re.compile(r"\bNEXT\b", re.IGNORECASE)),
    ("gap", re.compile(r"\bGAP\b", re.IGNORECASE)),
    ("pending", re.compile(r"\bpending\b", re.IGNORECASE)),
    ("blocked", re.compile(r"\bblock(?:ed|er)?\b", re.IGNORECASE)),
    ("korean_markers", re.compile(r"(미완|누락|연결|통합|필요|해야|미구현|보완)")),
]

# 경로/파일 레퍼런스(과도하게 잡지 않도록 확장자 기반)
REF_RE = re.compile(
    r"(?P<ref>(?:[A-Za-z]:\\\\[^\s`\"']+|[A-Za-z0-9_./\\-]+?\.(?:py|ps1|jsonl?|md|html|yml|yaml|sh)))"
)


@dataclass
class MdIssue:
    kind: str
    line_no: int
    line: str


@dataclass
class MdRef:
    ref: str
    normalized: str
    exists: bool
    ref_class: str  # local_ok / local_missing / remote_ref / loose_ref


@dataclass
class MdDocSummary:
    relpath: str
    mtime: float
    size: int
    title: str
    issues: List[MdIssue]
    missing_refs: List[MdRef]


def _extract_title(lines: List[str]) -> str:
    for ln in lines[:60]:
        s = ln.strip()
        if s.startswith("#"):
            return s.lstrip("#").strip()[:120]
    return ""


def _read_text_head(path: Path, max_bytes: int = 200_000) -> str:
    # 대용량 파일에서 멈추는 것을 피하기 위해 head만 읽는다.
    try:
        data = path.read_bytes()[:max_bytes]
        return data.decode("utf-8", errors="replace")
    except Exception:
        try:
            return path.read_text(encoding="utf-8", errors="replace")[:max_bytes]
        except Exception:
            return ""


def _normalize_ref(ws: Path, raw: str) -> Tuple[str, Path | None]:
    r = raw.strip().strip("`\"'()[]{}")
    # URL은 제외
    if "://" in r:
        return r, None
    # Linux absolute/tilde는 로컬 존재성 판단 대상이 아님(원격 참조)
    if r.startswith("/home/") or r.startswith("~/") or r.startswith("/etc/") or r.startswith("/run/"):
        return r, None
    # 문서에서 `/scripts/...`처럼 "레포 루트 기준"으로 표기하는 케이스 지원
    if r.startswith("/") and not r.startswith(("/home/", "/etc/", "/run/")):
        r = r.lstrip("/")
    # Windows 절대경로
    if re.match(r"^[A-Za-z]:\\", r):
        try:
            return r, Path(r)
        except Exception:
            return r, None
    # 슬래시/역슬래시 혼용 정규화
    r2 = r.replace("\\", "/")
    # 문서에서 레포 루트를 `agi/`로 한 단계 감싸서 표기하는 케이스(예: agi/scripts/...)를 워크스페이스 기준으로 정규화
    if r2.startswith("agi/"):
        r2 = r2[len("agi/") :]
    if r2.startswith("./"):
        r2 = r2[2:]
    # 루트 상대 경로로 취급
    p = (ws / r2).resolve()
    return r2, p


def _classify_ref(norm: str, p: Path | None) -> str:
    """
    ref_class:
    - remote_ref: /home/... 등 원격/리눅스 절대경로
    - local_ok:   워크스페이스에서 존재 확인됨
    - local_missing: 경로/프리픽스가 명확한데 존재하지 않음(액션 가능)
    - loose_ref:  파일명만 있는 느슨한 언급(노이즈가 많아 missing으로 취급하지 않음)
    """
    if norm.startswith("/home/") or norm.startswith("~/") or norm.startswith("/etc/") or norm.startswith("/run/"):
        return "remote_ref"
    # Windows 절대경로는 환경 의존성이 커서 "로컬 미연결"로 보지 않는다.
    # (예: 특정 venv/python.exe, 로컬 머신별 경로 차이)
    if re.match(r"^[A-Za-z]:\\", norm):
        return "external_ref"
    # NAS/외부 경로는 로컬 결함으로 취급하지 않는다(환경 의존)
    if norm.startswith(("/nas_backup/", "nas_backup/")):
        return "remote_ref"
    if norm.startswith("../"):
        return "external_ref"
    # 문서용 플레이스홀더
    if norm.startswith("path/to/"):
        return "external_ref"
    # 문서에 등장하는 예시 경로(환경 의존)
    if norm.startswith("workspace/"):
        return "external_ref"
    # 별도 통합 레포를 가정한 경로(현 워크스페이스 밖)
    if norm.startswith("fdo_agi_integrated/"):
        return "external_ref"
    # 데이터킷/실험 산출물 폴더(현 환경에 없을 수 있음)
    if norm.startswith("pii_toolkit_"):
        return "external_ref"
    if p is not None and p.exists():
        return "local_ok"

    # outputs/signals는 생성/소비되는 "상태 파일"이라, 부재가 곧 미연결을 의미하지 않는다.
    if norm.startswith(("outputs/", "signals/")):
        return "transient_ref"
    # fdo_agi_repo/outputs도 산출물 영역(상태/리포트)이라, 부재를 결함으로 보지 않는다.
    if norm.startswith("fdo_agi_repo/outputs/"):
        return "transient_ref"
    # logs는 산출물/아카이브 영역(시점 의존)
    if norm.startswith("logs/"):
        return "transient_ref"

    # 워크스페이스 내 경로처럼 보이는 케이스만 missing으로 분류
    if norm.startswith(("scripts/", "services/", "memory/", "docs/", "config/", "fdo_agi_repo/", "integrations/")):
        return "local_missing"
    if "/" in norm or "\\" in norm:
        return "local_missing"

    # tasks.json 같은 단독 파일명 언급은 문맥상 '설명용'이 많아 loose로 둔다.
    return "loose_ref"


def _scan_one_doc(ws: Path, path: Path, max_issues: int = 30, max_missing_refs: int = 30) -> MdDocSummary:
    st = path.stat()
    rel = path.resolve().relative_to(ws.resolve()).as_posix()
    text = _read_text_head(path)
    lines = text.splitlines()
    title = _extract_title(lines)

    issues: List[MdIssue] = []
    for i, ln in enumerate(lines, start=1):
        if not ln.strip():
            continue
        for kind, pat in ISSUE_PATTERNS:
            if pat.search(ln):
                issues.append(MdIssue(kind=kind, line_no=i, line=ln.strip()[:240]))
                break
        if len(issues) >= max_issues:
            break

    # references
    missing_refs: List[MdRef] = []
    seen_norm: set[str] = set()
    for i, ln in enumerate(lines, start=1):
        for m in REF_RE.finditer(ln):
            raw = m.group("ref")
            norm, p = _normalize_ref(ws, raw)
            if not norm or norm in seen_norm:
                continue
            seen_norm.add(norm)
            ref_class = _classify_ref(norm, p)
            exists = bool(p and p.exists())
            # actionable missing만 리스트에 포함 (remote/loose/transient는 노이즈가 커서 제외)
            if ref_class == "local_missing":
                missing_refs.append(MdRef(ref=raw, normalized=norm, exists=exists, ref_class=ref_class))
                if len(missing_refs) >= max_missing_refs:
                    break
        if len(missing_refs) >= max_missing_refs:
            break

    return MdDocSummary(
        relpath=rel,
        mtime=float(st.st_mtime),
        size=int(st.st_size),
        title=title,
        issues=issues,
        missing_refs=missing_refs,
    )


def iter_target_md_files(ws: Path) -> Iterable[Path]:
    """
    전체 6k+ md를 매번 읽지 않도록, '연결 가능성이 높은 구간'을 우선 타겟으로 한다.
    필요 시 차후 확장.
    """
    roots = [
        ws / "docs",
        ws / "scripts",
        ws / "services",
        ws / "inputs" / "agent_inbox",
        ws,  # repo root의 *.md
    ]
    seen: set[Path] = set()
    for r in roots:
        if not r.exists():
            continue
        if r.is_file() and r.suffix.lower() == ".md":
            p = r.resolve()
            if p not in seen:
                seen.add(p)
                yield p
            continue
        if r == ws:
            for p in ws.glob("*.md"):
                pp = p.resolve()
                if pp not in seen:
                    seen.add(pp)
                    yield pp
            continue
        for p in r.rglob("*.md"):
            pp = p.resolve()
            if pp not in seen:
                seen.add(pp)
                yield pp


def build_md_wave_sweep(ws: Path, incremental: bool = True) -> Dict[str, Any]:
    ws = ws.resolve()
    state_path = ws / "outputs" / "sync_cache" / "md_wave_sweep_state.json"
    state = _safe_load_json(state_path) or {}
    prev_index = state.get("files") if isinstance(state.get("files"), dict) else {}

    docs: List[MdDocSummary] = []
    changed = 0
    total = 0
    for p in iter_target_md_files(ws):
        total += 1
        try:
            st = p.stat()
            key = p.resolve().as_posix()
            prev = prev_index.get(key) if isinstance(prev_index.get(key), dict) else {}
            prev_m = float(prev.get("mtime") or 0.0)
            prev_s = int(prev.get("size") or 0)
            if incremental and prev and float(st.st_mtime) == prev_m and int(st.st_size) == prev_s:
                continue
            changed += 1
            docs.append(_scan_one_doc(ws, p))
        except Exception:
            continue

    # 업데이트된 docs만 나오면 "전체 요약"이 부족할 수 있어, state에 누적 요약 인덱스를 유지한다.
    # - docs는 최신 변경 파일만 담고, out에는 index 통계(issues/missing)를 전체 기준으로 유지한다.
    index_all = dict(prev_index) if isinstance(prev_index, dict) else {}
    for d in docs:
        abs_key = str((ws / d.relpath).resolve().as_posix())
        index_all[abs_key] = {"mtime": d.mtime, "size": d.size}

    # 통계
    issues_total = sum(len(d.issues) for d in docs)
    missing_total = sum(len(d.missing_refs) for d in docs)
    top_missing = []
    for d in docs:
        for r in d.missing_refs:
            top_missing.append({"doc": d.relpath, **asdict(r)})
    top_missing = top_missing[:80]

    now = time.time()
    out: Dict[str, Any] = {
        "ok": True,
        "version": "md_wave_sweep_v1",
        "generated_at": utc_iso(now),
        "scope": {
            "incremental": bool(incremental),
            "roots": ["docs/", "scripts/", "services/", "inputs/agent_inbox/", "*.md(root)"],
            "max_bytes_per_file": 200_000,
        },
        "stats": {
            "target_md_files_seen": total,
            "changed_files_scanned": changed,
            "changed_docs_included": len(docs),
            "issues_found_in_changed": issues_total,
            "missing_refs_found_in_changed": missing_total,
        },
        "changed_docs": [asdict(d) for d in docs[:120]],
        "missing_references_sample": top_missing,
        "note": "missing_references_sample은 local_missing(액션 가능)만 포함한다. changed_docs는 증분 스캔 결과(최근 변경 위주)이며, 전체 전수 스캔은 저빈도로 별도 수행하는 것이 안전하다.",
    }

    # state 업데이트
    try:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write_json(state_path, {"last_run_ts": now, "files": index_all})
    except Exception:
        pass

    return out


def render_markdown(report: Dict[str, Any]) -> str:
    stats = report.get("stats") if isinstance(report.get("stats"), dict) else {}
    docs = report.get("changed_docs") if isinstance(report.get("changed_docs"), list) else []
    miss = report.get("missing_references_sample") if isinstance(report.get("missing_references_sample"), list) else []

    lines: List[str] = []
    lines.append("# MD Wave Sweep v1")
    lines.append("")
    lines.append(f"- generated_at: `{report.get('generated_at')}`")
    lines.append(f"- incremental: `{(report.get('scope') or {}).get('incremental')}`")
    lines.append("")
    lines.append("## Stats")
    for k in ("target_md_files_seen", "changed_files_scanned", "issues_found_in_changed", "missing_refs_found_in_changed"):
        lines.append(f"- `{k}`: `{stats.get(k)}`")
    lines.append("")

    if docs:
        lines.append("## Changed Docs (sample)")
        for d in docs[:25]:
            if not isinstance(d, dict):
                continue
            issues = d.get("issues") if isinstance(d.get("issues"), list) else []
            missing = d.get("missing_refs") if isinstance(d.get("missing_refs"), list) else []
            lines.append(f"- `{d.get('relpath')}` — issues={len(issues)} missing_refs={len(missing)}")
    else:
        lines.append("## Changed Docs")
        lines.append("- (no changes detected)")

    lines.append("")
    if miss:
        lines.append("## Missing References (sample)")
        for m in miss[:30]:
            if not isinstance(m, dict):
                continue
            lines.append(f"- `{m.get('doc')}` → `{m.get('normalized')}`")
    else:
        lines.append("## Missing References (sample)")
        lines.append("- (none in changed docs)")
    lines.append("")
    lines.append("> note: 이 리포트는 ‘연결 고리’ 점검용이며, 문서 내용을 재작성하지 않는다.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", type=str, default=str(Path(__file__).resolve().parents[2]))
    ap.add_argument("--full", action="store_true", help="증분 스캔 대신 전체 대상 파일을 강제 스캔(무거움)")
    ap.add_argument("--out-json", type=str, default=str(Path("outputs") / "md_wave_sweep_latest.json"))
    ap.add_argument("--out-md", type=str, default=str(Path("outputs") / "md_wave_sweep_latest.md"))
    ap.add_argument("--history", type=str, default=str(Path("outputs") / "md_wave_sweep_history.jsonl"))
    args = ap.parse_args()

    ws = Path(args.workspace).resolve()
    out_json = Path(args.out_json)
    if not out_json.is_absolute():
        out_json = (ws / out_json).resolve()
    out_md = Path(args.out_md)
    if not out_md.is_absolute():
        out_md = (ws / out_md).resolve()
    hist = Path(args.history)
    if not hist.is_absolute():
        hist = (ws / hist).resolve()

    report = build_md_wave_sweep(ws, incremental=not args.full)
    _atomic_write_json(out_json, report)
    _atomic_write_text(out_md, render_markdown(report))
    try:
        hist.parent.mkdir(parents=True, exist_ok=True)
        with hist.open("a", encoding="utf-8") as f:
            f.write(json.dumps(report, ensure_ascii=False) + "\n")
    except Exception:
        pass

    print(json.dumps({"ok": True, "out": str(out_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
