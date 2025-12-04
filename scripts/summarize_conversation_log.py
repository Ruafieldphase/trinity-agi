#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Summarize a conversation JSONL log into Markdown and JSON metrics.

Usage:
  python scripts/summarize_conversation_log.py \
    --input D:\\nas_backup\\ai_binoche_conversation_origin\\cladeCLI-sena\\d--nas-backup\\da6b26b2-fa3a-4bba-b35c-12bf2db986f7.jsonl \
    --out-md outputs/conversation_summary.md \
    --out-json outputs/conversation_timeline.json \
    --max-timeline 50

This script is schema-tolerant: it attempts to infer roles, timestamps, tool calls, and errors
from a variety of common fields.
"""

from __future__ import annotations
import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

ISO_DT_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)$")

# Minimal bilingual stopword set (extend as needed without external deps)
STOPWORDS = set(
    [
        # English common
        "the","a","an","and","or","to","of","in","on","for","with","by","is","are","was","were","be","as","at","it","this","that","from","into","out","about","over","after","before","then","than","so","but","if","not","no","yes","do","does","did","you","we","they","i","he","she","them","his","her","our","your","their","my",
        # Korean common particles and helpers (rough list)
        "은","는","이","가","을","를","의","에","에서","으로","와","과","도","만","처럼","부터","까지","하다","했다","합니다","합니다.","그리고","하지만","또","또한","즉","예:","예", 
    ]
)

HANGUL_WORD_RE = re.compile(r"[\uAC00-\uD7A3]+|")
LATIN_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_\-]+")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Summarize conversation JSONL log")
    p.add_argument("--input", required=True, help="Path to JSONL log file")
    p.add_argument("--out-md", required=True, help="Path to write Markdown summary")
    p.add_argument("--out-json", required=True, help="Path to write JSON metrics/timeline")
    p.add_argument("--max-timeline", type=int, default=40, help="Max timeline entries in outputs")
    return p.parse_args()


def try_parse_dt(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        # treat as unix epoch seconds if plausible
        try:
            if value > 1e12:  # ms
                return datetime.fromtimestamp(value / 1000.0, tz=timezone.utc)
            return datetime.fromtimestamp(value, tz=timezone.utc)
        except Exception:
            return None
    if isinstance(value, str):
        s = value.strip()
        # Try ISO8601
        try:
            if ISO_DT_RE.match(s):
                # datetime.fromisoformat cannot parse 'Z' directly before 3.11; handle 'Z'
                if s.endswith("Z"):
                    s = s[:-1] + "+00:00"
                return datetime.fromisoformat(s)
        except Exception:
            pass
        # Try common formats
        for fmt in [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y/%m/%d %H:%M:%S",
            "%Y/%m/%d %H:%M:%S.%f",
        ]:
            try:
                return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
            except Exception:
                continue
    return None


ROLE_KEYS = ["role","sender","author","source","type"]
CONTENT_KEYS = ["content","text","message","body","args","prompt","input"]
TOOL_KEYS = ["tool","action","function","function_call","recipient","tool_name","plugin"]
RESULT_KEYS = ["result","response","output","tool_result","data","status"]
ERROR_KEYS = ["error","exception","traceback","stderr"]
TS_KEYS = ["ts","timestamp","time","created_at","@timestamp","datetime"]
NAME_KEYS = ["name","id","label","title"]


def get_first(obj: Dict[str, Any], keys: List[str]) -> Any:
    for k in keys:
        if k in obj:
            return obj[k]
    return None


def to_role(obj: Dict[str, Any]) -> str:
    v = get_first(obj, ROLE_KEYS)
    if isinstance(v, str):
        vs = v.lower()
        # map common aliases
        if vs in {"assistant","ai","bot"}:
            return "assistant"
        if vs in {"user","human","client"}:
            return "user"
        if vs in {"system"}:
            return "system"
        if vs in {"tool","function","plugin"}:
            return "tool"
        return vs
    # heuristics based on presence of fields
    if any(k in obj for k in TOOL_KEYS):
        return "tool"
    return "unknown"


def to_text(obj: Dict[str, Any]) -> str:
    v = get_first(obj, CONTENT_KEYS)
    # Common nested cases
    if isinstance(v, dict):
        # OpenAI-like messages with {"type":"text","text":"..."}
        if "text" in v and isinstance(v["text"], str):
            return v["text"]
        try:
            return json.dumps(v, ensure_ascii=False)
        except Exception:
            return str(v)
    if isinstance(v, list):
        try:
            return json.dumps(v, ensure_ascii=False)
        except Exception:
            return str(v)
    if isinstance(v, str):
        return v
    # Fallback to any name or id
    n = get_first(obj, NAME_KEYS)
    if isinstance(n, str):
        return n
    return ""


def detect_tool(obj: Dict[str, Any]) -> Optional[str]:
    for k in TOOL_KEYS:
        if k in obj:
            val = obj[k]
            if isinstance(val, dict):
                # function_call: {"name": ..., "arguments": ...}
                name = val.get("name") or val.get("tool") or val.get("function")
                if isinstance(name, str):
                    return name
            if isinstance(val, str):
                return val
    return None


def detect_result_status(obj: Dict[str, Any]) -> Tuple[Optional[str], Optional[bool]]:
    # returns (status_label, is_error)
    # Check explicit error fields first
    for k in ERROR_KEYS:
        if k in obj and obj[k]:
            return ("error", True)
    # Then status fields
    status = obj.get("status")
    if isinstance(status, (str, int)):
        s = str(status).lower()
        if any(x in s for x in ["fail","error","exception","timeout","abort","cancel"]):
            return (s, True)
        if any(x in s for x in ["ok","success","succeed","done","200","0"]):
            return (s, False)
        return (s, None)
    # If we see result keys but no error hint, assume success unknown
    if any(k in obj for k in RESULT_KEYS):
        return ("result", None)
    return (None, None)


def extract_timestamp(obj: Dict[str, Any], idx: int) -> Tuple[Optional[datetime], str]:
    for k in TS_KEYS:
        if k in obj:
            dt = try_parse_dt(obj[k])
            if dt:
                return dt, k
    return None, ""


def tokenize(text: str) -> List[str]:
    tokens: List[str] = []
    # Hangul words
    for m in re.finditer(r"[\uAC00-\uD7A3]{2,}", text):
        tokens.append(m.group(0))
    # Latin words (keep hyphen/underscore)
    for m in re.finditer(r"[A-Za-z][A-Za-z0-9_\-]{2,}", text):
        tokens.append(m.group(0).lower())
    return [t for t in tokens if t not in STOPWORDS]


def shorten(text: str, limit: int = 160) -> str:
    t = text.strip().replace("\n", " ")
    return t if len(t) <= limit else t[: limit - 1] + "…"


def main() -> int:
    args = parse_args()
    in_path = args.input
    out_md = args.out_md
    out_json = args.out_json
    max_timeline = args.max_timeline

    if not os.path.exists(in_path):
        print(f"Input file not found: {in_path}", file=sys.stderr)
        return 2

    messages: List[Dict[str, Any]] = []
    total_lines = 0
    bad_lines = 0

    with open(in_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            total_lines += 1
            s = line.strip()
            if not s:
                continue
            try:
                obj = json.loads(s)
                messages.append(obj)
            except Exception:
                bad_lines += 1
                continue

    # Aggregations
    role_counter = Counter()
    tool_counter = Counter()
    tool_success = 0
    tool_error = 0
    tool_unknown = 0

    timeline: List[Dict[str, Any]] = []
    all_tokens = Counter()

    start_dt: Optional[datetime] = None
    end_dt: Optional[datetime] = None

    for idx, obj in enumerate(messages):
        role = to_role(obj)
        text = to_text(obj)
        tool = detect_tool(obj)
        status, is_err = detect_result_status(obj)
        ts, ts_key = extract_timestamp(obj, idx)

        role_counter[role] += 1
        if tool:
            tool_counter[tool] += 1
            if is_err is True:
                tool_error += 1
            elif is_err is False:
                tool_success += 1
            else:
                tool_unknown += 1

        toks = tokenize(text)
        all_tokens.update(toks)

        if ts:
            start_dt = ts if (start_dt is None or ts < start_dt) else start_dt
            end_dt = ts if (end_dt is None or ts > end_dt) else end_dt

        timeline.append(
            {
                "idx": idx,
                "ts": ts.isoformat() if ts else None,
                "ts_key": ts_key,
                "role": role,
                "tool": tool,
                "status": status,
                "is_error": is_err,
                "text": shorten(text, 200),
            }
        )

    # Select timeline subset
    # Priority: preserve order, include all errors, cap at max_timeline
    error_idxs = {e["idx"] for e in timeline if e["is_error"] is True}
    selected: List[Dict[str, Any]] = []
    for item in timeline:
        if len(selected) >= max_timeline:
            break
        selected.append(item)
    # Ensure errors are included; if some missing and we have room, append them
    remaining_errors = [e for e in timeline if e["idx"] not in {x["idx"] for x in selected} and e["is_error"] is True]
    for e in remaining_errors:
        if len(selected) >= max_timeline:
            break
        selected.append(e)
    # Keep chronological order by idx
    selected.sort(key=lambda x: x["idx"]) 

    duration_sec = None
    if start_dt and end_dt:
        duration_sec = int((end_dt - start_dt).total_seconds())

    # Top tokens as topics
    top_topics = [w for w, c in all_tokens.most_common(15)]

    metrics = {
        "total_lines": total_lines,
        "parsed_messages": len(messages),
        "bad_lines": bad_lines,
        "roles": role_counter,
        "tools": tool_counter,
        "tool_success": tool_success,
        "tool_error": tool_error,
        "tool_unknown": tool_unknown,
        "start_ts": start_dt.isoformat() if start_dt else None,
        "end_ts": end_dt.isoformat() if end_dt else None,
        "duration_sec": duration_sec,
        "top_topics": top_topics,
        "timeline_sample": selected,
    }

    # Prepare Markdown summary
    def fmt_role_counts() -> str:
        if not role_counter:
            return "(없음)"
        parts = [f"{k}: {v}" for k, v in role_counter.items()]
        return ", ".join(parts)

    def fmt_tool_counts() -> str:
        if not tool_counter:
            return "(없음)"
        parts = [f"{k}: {v}" for k, v in tool_counter.most_common(12)]
        return ", ".join(parts)

    md_lines = []
    md_lines.append("# 대화 로그 요약")
    md_lines.append("")
    md_lines.append("## 개요")
    md_lines.append("")
    md_lines.append(f"- 총 메시지(파싱): {len(messages)} / 원시 라인: {total_lines} (파싱 실패 {bad_lines})")
    if start_dt and end_dt:
        md_lines.append(f"- 기간: {start_dt.isoformat()} → {end_dt.isoformat()} (약 {duration_sec}s)")
    md_lines.append(f"- 역할 분포: {fmt_role_counts()}")
    md_lines.append(f"- 도구 호출 상위: {fmt_tool_counts()}")
    md_lines.append(f"- 도구 결과: 성공 {tool_success}, 오류 {tool_error}, 불명 {tool_unknown}")
    if top_topics:
        md_lines.append(f"- 주요 토픽(키워드): {', '.join(top_topics[:12])}")
    md_lines.append("")

    md_lines.append("## 타임라인 (샘플)")
    md_lines.append("")
    if selected:
        md_lines.append("| # | 시각 | 역할 | 도구 | 상태 | 내용 |")
        md_lines.append("|---:|:---|:---|:---|:---|:---|")
        for e in selected:
            md_lines.append(
                f"| {e['idx']} | {e['ts'] or ''} | {e['role']} | {e['tool'] or ''} | {e['status'] or ''} | {e['text'].replace('|','\\|')} |"
            )
    else:
        md_lines.append("(타임라인 데이터 없음)")
    md_lines.append("")

    md_lines.append("## 리스크 · 개선안")
    md_lines.append("")
    md_lines.append("- 스키마 다양성: 키 이름 불일치 시 일부 항목이 누락될 수 있음 → 스키마 매핑 파일을 제공하면 정밀도 향상")
    md_lines.append("- 타임스탬프 없음: 순서만으로 정렬 → 로그 수집 시각 필드 보강 권장")
    md_lines.append("- 대용량 로그: 현재는 전 파일 단일 패스 처리 → 추후 스트리밍/샘플링 옵션 추가 가능")
    md_lines.append("- 민감정보: 본문 요약 시 민감키가 포함될 수 있음 → 마스킹 규칙 옵션화 필요")
    md_lines.append("")

    # Ensure output dirs
    os.makedirs(os.path.dirname(out_md) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(out_json) or ".", exist_ok=True)

    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    # Convert Counters to plain dicts for JSON
    json_metrics = dict(metrics)
    json_metrics["roles"] = dict(role_counter)
    json_metrics["tools"] = dict(tool_counter)

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(json_metrics, f, ensure_ascii=False, indent=2)

    print(f"Wrote: {out_md}")
    print(f"Wrote: {out_json}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        sys.exit(130)
