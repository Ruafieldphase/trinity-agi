#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rua Conversation Intake (Hippocampus-friendly index)

목표:
- `ai_binoche_conversation_origin/rua`의 대화/사유 기록을
  무거운 분석 없이 "인덱스(메타 + 짧은 발췌 + 경계 후보)"로 고정한다.
- 이 인덱스는 full_cycle 리포트와 해마(episodic) 전사의 입력이 된다.

입력:
- <workspace>/ai_binoche_conversation_origin/rua/*.md (주로)
- (옵션) origin/conversations.json (있으면 존재만 기록)

출력:
- <workspace>/outputs/rua_conversation_intake_latest.json
- <workspace>/outputs/rua_conversation_intake_history.jsonl (append)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def utc_iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _safe_read_text(path: Path, max_bytes: int = 220_000) -> str:
    try:
        data = path.read_bytes()
        if len(data) > max_bytes:
            data = data[:max_bytes]
        # utf-8-sig도 허용 (BOM)
        try:
            return data.decode("utf-8-sig", errors="replace")
        except Exception:
            return data.decode("utf-8", errors="replace")
    except Exception:
        return ""


def _hash_head(text: str, max_len: int = 12_000) -> str:
    h = hashlib.sha256()
    h.update((text[:max_len]).encode("utf-8", errors="replace"))
    return h.hexdigest()


def _extract_keywords(text: str) -> Dict[str, int]:
    """
    아주 가벼운 키워드 카운트(한국어/혼합).
    - 목적: '무엇을 미분/압축/연결'하는지의 방향성만 잡는다.
    """
    vocab = [
        "리듬", "공명", "의식", "무의식", "배경자아", "정반합", "프랙탈", "동역학",
        "경계", "수축", "확장", "통합", "압축", "미분", "연결", "정책", "허용", "금지", "주의",
        "해마", "기억", "에피소드", "경험", "관측", "실행", "대시보드", "트리거", "브리지", "sync",
        "구글어스", "로드뷰", "여행", "도시", "자연", "소리", "파동", "입자",
        "암흑뉴런", "DarkNeuron", "Dark Neuron", "드림", "꿈", "낮", "밤", "명상", "여백", "의미화",
        "관계", "거리", "상태", "제약", "4대 힘", "중력", "전자기", "강력", "약력",
        # 관점/사회/문화(경계 확장·수축 렌즈)
        "우리", "개인", "공동체", "사회", "주체", "자기",
        "혼합", "믹스", "비빔밥", "대한민국", "한국",
        # 위상적 표현(확장/수축의 다른 말)
        "펼침", "접힘", "열림", "닫힘",
    ]
    counts: Dict[str, int] = {}
    for w in vocab:
        c = text.count(w)
        if c:
            counts[w] = int(c)
    return counts


def _extract_boundaries(text: str, max_rules: int = 40) -> List[Dict[str, Any]]:
    deny_markers = ("하면 안", "하지 말", "금지", "불가", "하지마", "위험", "주의", "조심")
    allow_markers = ("해도 됨", "가능", "허용", "괜찮", "된다", "OK")
    rules: List[Dict[str, Any]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        # Never store potential identifiers / links / local paths as "boundary" text.
        if "http://" in line or "https://" in line or "@" in line:
            continue
        if re.search(r"\b[A-Za-z]:\\", line):
            continue
        polarity = None
        if any(m in line for m in deny_markers):
            polarity = "deny"
        elif any(m in line for m in allow_markers):
            polarity = "allow"
        elif "주의" in line or "조심" in line:
            polarity = "caution"
        if polarity:
            rules.append({"polarity": polarity, "text": line})
        if len(rules) >= max_rules:
            break
    return rules


def _excerpt(text: str, max_chars: int = 600) -> str:
    s = re.sub(r"\s+", " ", (text or "").strip())
    # Best-effort redaction (avoid leaking PII/links/paths into outputs).
    try:
        s = re.sub(r"https?://[^\s)\]]+", "[REDACTED_URL]", s)
        s = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]", s)
        s = re.sub(r"\b[A-Za-z]:\\[^\s]+", "[REDACTED_PATH]", s)
    except Exception:
        pass
    if len(s) <= max_chars:
        return s
    return s[: max_chars - 1] + "…"


def _compute_boundary_dynamics(keyword_counts: Dict[str, int]) -> Dict[str, Any]:
    """
    대화를 '경계' 관점에서 볼 때의 확장/수축/혼합 신호를 아주 가볍게 요약.
    - 목적: "관점이 어떻게 변했는지"를 파일 메타로 관측 가능하게.
    """
    def c(k: str) -> int:
        v = keyword_counts.get(k, 0)
        return int(v) if isinstance(v, int) else 0

    expansion = c("확장") + c("펼침") + c("열림")
    contraction = c("수축") + c("압축") + c("접힘") + c("닫힘")
    mix = c("혼합") + c("믹스") + c("비빔밥") + c("정반합") + c("통합")
    boundary = c("경계") + c("제약") + c("금지") + c("허용")
    collective = c("우리") + c("공동체") + c("사회")
    individual = c("개인") + c("주체") + c("자기")

    if mix >= max(expansion, contraction) and mix >= 3:
        dominant = "mix"
    elif (expansion - contraction) >= 3:
        dominant = "expand"
    elif (contraction - expansion) >= 3:
        dominant = "contract"
    else:
        dominant = "balanced"

    ratio = float(expansion + 1) / float(contraction + 1)

    return {
        "expansion_markers": expansion,
        "contraction_markers": contraction,
        "mix_markers": mix,
        "boundary_markers": boundary,
        "collective_markers": collective,
        "individual_markers": individual,
        "expand_vs_contract_ratio": round(ratio, 3),
        "dominant_mode": dominant,
    }


@dataclass
class RuaDoc:
    relpath: str
    path: str
    size: int
    mtime: float
    mtime_iso: str
    sha256_head: str
    title: str
    excerpt: str
    keyword_counts: Dict[str, int]
    boundary_dynamics: Dict[str, Any]
    boundaries: List[Dict[str, Any]]


def _load_prev_latest(workspace_root: Path) -> Dict[str, Any]:
    p = workspace_root / "outputs" / "rua_conversation_intake_latest.json"
    if not p.exists():
        return {}
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def run_rua_conversation_intake(workspace_root: Path, max_docs: int = 120) -> Dict[str, Any]:
    workspace_root = workspace_root.resolve()
    base = workspace_root / "ai_binoche_conversation_origin" / "rua"
    export_file = base / "origin" / "conversations.json"

    prev = _load_prev_latest(workspace_root)
    prev_seen = set()
    try:
        for d in prev.get("docs", []):
            rp = d.get("relpath")
            h = d.get("sha256_head")
            if isinstance(rp, str) and isinstance(h, str):
                prev_seen.add((rp, h))
    except Exception:
        prev_seen = set()

    docs: List[RuaDoc] = []
    if base.exists():
        for p in base.glob("*.md"):
            try:
                st = p.stat()
            except Exception:
                continue
            text = _safe_read_text(p)
            sha = _hash_head(text)
            rel = str(p.relative_to(workspace_root))
            title = (text.splitlines()[0].strip() if text.splitlines() else p.stem)
            kw = _extract_keywords(text)
            docs.append(
                RuaDoc(
                    relpath=rel,
                    path=str(p),
                    size=int(st.st_size),
                    mtime=float(st.st_mtime),
                    mtime_iso=utc_iso(float(st.st_mtime)),
                    sha256_head=sha,
                    title=title if title else p.stem,
                    excerpt=_excerpt(text),
                    keyword_counts=kw,
                    boundary_dynamics=_compute_boundary_dynamics(kw),
                    boundaries=_extract_boundaries(text),
                )
            )

    docs.sort(key=lambda d: d.mtime, reverse=True)
    new_docs = [d.relpath for d in docs if (d.relpath, d.sha256_head) not in prev_seen]

    newest = asdict(docs[0]) if docs else None
    now = time.time()
    return {
        "ok": True,
        "scanned_at": utc_iso(now),
        "base_dir": str(base),
        "export_file": {"path": str(export_file), "exists": export_file.exists()},
        "total_docs": len(docs),
        "new_docs_count": len(new_docs),
        "new_docs": new_docs[:50],
        "newest": newest,
        "docs": [asdict(d) for d in docs[:max_docs]],
        "note": f"docs에는 최근 {max_docs}개만 포함(요약). 원본은 ai_binoche_conversation_origin/rua에 존재.",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", type=str, default=str(Path(__file__).resolve().parents[2]))
    ap.add_argument("--out", type=str, default=str(Path("outputs") / "rua_conversation_intake_latest.json"))
    ap.add_argument("--history", type=str, default=str(Path("outputs") / "rua_conversation_intake_history.jsonl"))
    ap.add_argument("--max-docs", type=int, default=120)
    args = ap.parse_args()

    ws = Path(args.workspace).resolve()
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = (ws / out_path).resolve()
    hist_path = Path(args.history)
    if not hist_path.is_absolute():
        hist_path = (ws / hist_path).resolve()

    result = run_rua_conversation_intake(ws, max_docs=int(args.max_docs))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        with hist_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
    except Exception:
        pass
    print(json.dumps({"ok": True, "out": str(out_path), "total_docs": result.get("total_docs")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
