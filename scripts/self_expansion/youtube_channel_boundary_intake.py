#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube Channel Boundary Intake v1

목표
- 사용자가 언급한 '경계 학습에 좋은 채널'을, 브라우저를 띄우지 않고도
  (자막/메타 기반)으로 "경계 후보"를 습득 가능한 탐색 세션으로 고정한다.

핵심 철학(리듬/경계)
- 영상 전체를 '학습(주입)'하지 않는다.
- 짧은 요약/느낌/경계 규칙만 남긴다.
- 안전/휴식 게이트가 걸리면 아무것도 하지 않는 것이 정상이다(Idle=생존).

입력
- scripts/youtube_channels.json : 채널명 → channel_id 매핑(일부는 placeholder)
- outputs/bridge/constitution_review_latest.json (optional)
- outputs/safety/rest_gate_latest.json (optional)

출력
- outputs/youtube_channel_boundary_intake_latest.json
- outputs/youtube_channel_boundary_intake_history.jsonl
- inputs/intake/exploration/sessions/auto_experience_<ts>_youtube_channel.json
"""

from __future__ import annotations

import json
import time
import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import sys
import argparse


WORKSPACE = Path(__file__).resolve().parents[2]
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))
OUTPUTS = WORKSPACE / "outputs"
BRIDGE = OUTPUTS / "bridge"
SAFETY = OUTPUTS / "safety"
SIGNALS = WORKSPACE / "signals"
SESSIONS = WORKSPACE / "inputs" / "intake" / "exploration" / "sessions"

CHANNELS_FILE = WORKSPACE / "scripts" / "youtube_channels.json"
STATE = OUTPUTS / "sync_cache" / "youtube_channel_boundary_state.json"
OUT_LATEST = OUTPUTS / "youtube_channel_boundary_intake_latest.json"
OUT_HISTORY = OUTPUTS / "youtube_channel_boundary_intake_history.jsonl"

CONSTITUTION = BRIDGE / "constitution_review_latest.json"
REST_GATE = SAFETY / "rest_gate_latest.json"


def _utc_iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        if not path.exists():
            return None
        obj = json.loads(path.read_text(encoding="utf-8-sig"))
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def _atomic_write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _append_jsonl(path: Path, obj: dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _sha256_head(s: str) -> str:
    return hashlib.sha256((s or "").encode("utf-8", errors="ignore")).hexdigest()[:16]


def _safety_status() -> str:
    c = _load_json(CONSTITUTION) or {}
    st = str((c.get("status") or "")).upper().strip()
    return st or "UNKNOWN"


def _rest_status(now: float) -> str:
    rg = _load_json(REST_GATE) or {}
    st = str((rg.get("status") or "")).upper().strip()
    if st == "REST":
        until = rg.get("rest_until_epoch")
        if until is None:
            return "REST"
        try:
            if float(now) < float(until):
                return "REST"
        except Exception:
            return "REST"
    return "OK"


def _load_state() -> dict[str, Any]:
    return _load_json(STATE) or {}


def _save_state(st: dict[str, Any]) -> None:
    _atomic_write_json(STATE, st)


def _load_channels() -> dict[str, str]:
    if CHANNELS_FILE.exists():
        try:
            obj = json.loads(CHANNELS_FILE.read_text(encoding="utf-8-sig"))
            if isinstance(obj, dict):
                return {str(k): str(v) for k, v in obj.items()}
        except Exception:
            pass
    return {}


def _save_channels(ch: dict[str, str]) -> None:
    CHANNELS_FILE.parent.mkdir(parents=True, exist_ok=True)
    CHANNELS_FILE.write_text(json.dumps(ch, ensure_ascii=False, indent=2), encoding="utf-8")


def _resolve_channel_id_best_effort(name: str) -> Optional[str]:
    """
    Placeholder 채널 ID를 "질문 없이" best-effort로 채운다.
    - 정확 100% 보장 불가. (그래도 실행/습득을 멈추지 않는 것이 목적)
    """
    try:
        import yt_dlp  # type: ignore

        q = f"ytsearch5:{name} 강의"
        ydl_opts: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "skip_download": True,
            # Prevent long hangs on flaky network/extractors.
            "socket_timeout": 10,
            "retries": 1,
            "fragment_retries": 1,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore
            info = ydl.extract_info(q, download=False)
        entries = info.get("entries") if isinstance(info, dict) else None
        if not isinstance(entries, list):
            return None

        # Prefer entries where uploader/channel name contains query tokens.
        tokens = [t for t in str(name).split() if t]
        best = None
        best_score = -1
        for e in entries:
            if not isinstance(e, dict):
                continue
            cid = e.get("channel_id") or e.get("uploader_id") or ""
            cid = str(cid)
            if cid.startswith("UC") and len(cid) >= 10:
                pass
            else:
                continue
            uploader = str(e.get("uploader") or e.get("channel") or "")
            score = 0
            for t in tokens:
                if t and t in uploader:
                    score += 1
            if score > best_score:
                best_score = score
                best = cid
        return best
    except Exception:
        return None


def _looks_child_related_title(title: str) -> bool:
    t = (title or "").strip()
    if not t:
        return False
    try:
        import re

        # Strong / obvious child-minor cues (avoid wasting cycles & avoid safety flips)
        child_re = r"(청소년|미성년|아동|어린이|키즈|초등|중학생|고등학생|학생\s*\d+|학생\b|캠프\b)"
        return bool(re.search(child_re, t, re.IGNORECASE))
    except Exception:
        return False


def _name_tokens(name: str) -> list[str]:
    raw = (name or "").strip()
    if not raw:
        return []
    drop = {"교수", "박사", "선생님", "TV", "tv", "채널"}
    parts = [p.strip() for p in raw.replace("/", " ").split() if p.strip()]
    toks = [p for p in parts if p not in drop]
    # Also keep the raw without honorifics (Korean)
    compact = raw.replace("교수", "").replace("박사", "").replace("선생님", "").strip()
    if compact and compact not in toks:
        toks.append(compact)
    return [t for t in toks if len(t) >= 2]


def _feed_matches_name(feed_title: str, channel_name: str) -> bool:
    ft = (feed_title or "").strip()
    if not ft:
        return False
    toks = _name_tokens(channel_name)
    if not toks:
        return True  # nothing to validate against
    return any(t in ft for t in toks)


def _list_recent_video_candidates(channel_id: str, limit: int = 12) -> tuple[list[dict[str, str]], str]:
    """
    Returns (candidates, feed_title).
    candidate: {"video_id":..., "url":..., "title":...}
    """
    # 1) RSS (fast, stable, no cookies)
    try:
        import urllib.request
        import xml.etree.ElementTree as ET

        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        with urllib.request.urlopen(rss_url, timeout=8) as r:
            data = r.read(260_000)
        root = ET.fromstring(data)

        # Atom feed title
        feed_title = ""
        for el in list(root):
            if isinstance(el.tag, str) and el.tag.endswith("title") and el.text:
                feed_title = el.text.strip()
                break

        out: list[dict[str, str]] = []
        # Entries: use title + yt:videoId
        for entry in root.iter():
            if not (isinstance(entry.tag, str) and entry.tag.endswith("entry")):
                continue
            vid = ""
            etitle = ""
            for child in list(entry):
                if not isinstance(child.tag, str):
                    continue
                if child.tag.endswith("videoId") and child.text:
                    vid = child.text.strip()
                elif child.tag.endswith("title") and child.text:
                    etitle = child.text.strip()
            if not vid:
                continue
            out.append({"video_id": vid, "url": f"https://youtube.com/watch?v={vid}", "title": etitle})
            if len(out) >= int(limit):
                break
        if out:
            return out, feed_title
    except Exception:
        pass

    # 2) Fallback: yt-dlp (best-effort)
    try:
        import yt_dlp  # type: ignore

        ydl_opts: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "skip_download": True,
            "playlistend": int(limit),
            # Prevent long hangs on flaky network/extractors.
            "socket_timeout": 10,
            "retries": 1,
            "fragment_retries": 1,
        }
        url = f"https://www.youtube.com/channel/{channel_id}/videos"
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore
            info = ydl.extract_info(url, download=False)
        entries = info.get("entries") if isinstance(info, dict) else None
        out2: list[dict[str, str]] = []
        if isinstance(entries, list):
            for e in entries:
                if not isinstance(e, dict):
                    continue
                vid = e.get("id")
                if not isinstance(vid, str) or not vid:
                    continue
                out2.append(
                    {
                        "video_id": vid,
                        "url": f"https://youtube.com/watch?v={vid}",
                        "title": str(e.get("title") or ""),
                    }
                )
        return out2, ""
    except Exception:
        return [], ""


def _extract_video_id(url: str) -> str:
    u = (url or "").strip()
    if "watch?v=" in u:
        return u.split("watch?v=", 1)[1].split("&", 1)[0]
    if "youtu.be/" in u:
        return u.split("youtu.be/", 1)[1].split("?", 1)[0]
    return _sha256_head(u)


def _cap_text(s: str, n: int = 240) -> str:
    s = (s or "").strip()
    if len(s) <= n:
        return s
    return s[:n].rstrip() + "…"


def _classify_content_form(*, title: str, duration_sec: float) -> dict[str, str]:
    """
    사용자 관측: "대중강연(압축)" vs "긴 설명(전개)".
    저장은 메타만(원문/자막 저장 금지).
    """
    t = (title or "").strip()
    d = float(duration_sec or 0.0)

    talk_re = r"(강연|특강|토크|대담|세미나|인터뷰|콘서트|Q&A|질문)"
    explain_re = r"(설명|해설|강의|수업|레슨|전체|풀버전|장시간|라이브|live)"

    presentation_form = "UNKNOWN"
    try:
        import re

        if re.search(talk_re, t, re.IGNORECASE):
            presentation_form = "TALK"
        elif re.search(explain_re, t, re.IGNORECASE):
            presentation_form = "EXPLAIN"
    except Exception:
        pass

    # Compression mode: conservative thresholds
    if d <= 0:
        compression_mode = "UNKNOWN"
    elif d < 20 * 60:
        compression_mode = "COMPRESSED"
    elif d >= 60 * 60:
        compression_mode = "EXPANDED"
    else:
        compression_mode = "MIXED"

    return {
        "compression_mode": compression_mode,
        "presentation_form": presentation_form,
    }


def _infer_culture_lens(*, channel_name: str, title: str) -> dict[str, str]:
    """
    사용자 관점: 대한민국(우리↔개인 확장/수축 + 비빔밥식 mix 문화) 렌즈.
    - 강요하지 않고, 습득 세션의 "관점 태그"로만 남긴다.
    - 원문/자막 저장 금지(메타만).
    """
    s = f"{channel_name} {title}".strip()
    try:
        import re

        has_hangul = bool(re.search(r"[가-힣]", s))
    except Exception:
        has_hangul = False

    if not has_hangul:
        return {"culture": "UNKNOWN", "lens": "NONE"}

    # 기본 렌즈: KR mix + expand/contract
    return {"culture": "KR", "lens": "KR_MIX_EXPAND_CONTRACT"}


def _generate_boundaries_with_llm(
    *,
    title: str,
    tone: str,
    core: str,
    themes: list[str],
    compression_mode: str,
    presentation_form: str,
) -> list[dict[str, Any]]:
    """
    사람에게 선택을 묻지 않고, '경계 규칙' 3~6개만 생성.
    - URL/고유명/계정/개인정보 금지.
    """
    prompt = f"""
너는 '경계 학습'을 위한 규칙 생성기다.
아래 입력은 유튜브 영상 분석 요약이다. 여기서 인간/AGI 모두에게 유효한 '경계 규칙'만 뽑아라.

메타:
- compression_mode: {compression_mode}   # COMPRESSED/MIXED/EXPANDED
- presentation_form: {presentation_form} # TALK/EXPLAIN/UNKNOWN
- lens_hint: 대한민국 문화 관점(우리↔개인 확장/수축 + mix)처럼 "경계가 섞이고 다시 분리되는" 패턴을 경계 규칙으로 표현해도 된다(단, 일반적/비개인/비지시).

제약:
- 개인정보/계정/비밀번호/토큰/링크/URL/채널ID/실명 등 고유식별 정보는 절대 쓰지 마라.
- 실행 지시(클릭/로그인/구매 등)도 금지.
- 규칙은 짧고 일반적이어야 한다(한 줄).

입력:
- title: {title}
- emotional_tone: {tone}
- core_message: {core}
- themes: {', '.join(themes[:8])}

출력은 반드시 JSON 하나:
{{
  "boundaries": [
    {{"polarity":"deny|allow|caution","text":"..."}}
  ]
}}
"""
    try:
        from services.model_selector import ModelSelector  # type: ignore

        ms = ModelSelector()
        resp, _model = ms.try_generate_content(prompt, intent="boundary_rules", text_length=len(prompt), urgency=False)
        if not resp:
            raise RuntimeError("no_response")
        txt = getattr(resp, "text", "") or ""
        raw = txt.strip()
        if "```" in raw:
            raw = raw.split("```", 1)[-1]
            if "```" in raw:
                raw = raw.split("```", 1)[0]
        obj = json.loads(raw)
        bs = obj.get("boundaries") if isinstance(obj, dict) else None
        if not isinstance(bs, list):
            raise ValueError("missing_boundaries")
        out: list[dict[str, Any]] = []
        for b in bs[:8]:
            if not isinstance(b, dict):
                continue
            pol = str(b.get("polarity") or "").strip().lower()
            if pol not in ("deny", "allow", "caution"):
                pol = "caution"
            text = _cap_text(str(b.get("text") or ""))
            if not text:
                continue
            if "http://" in text or "https://" in text or "@" in text:
                continue
            out.append({"polarity": pol, "text": text})
        if out:
            return out
    except Exception:
        pass

    # Fallback: always safe, generic boundaries
    return [
        {"polarity": "deny", "text": "개인정보/계정/비밀번호/토큰/키 추출·저장 금지"},
        {"polarity": "deny", "text": "대용량 원문 저장 금지(메타/요약만)"},
        {"polarity": "allow", "text": "느낌(저비용)으로 스캔하고 경계에서만 고비용 연산"},
        {"polarity": "caution", "text": "경계 패턴이 반복될 때만 개념을 추가(과잉 일반화 금지)"},
        {"polarity": "allow", "text": "Idle/쉼/여백은 정상 생존"},
    ]


def _write_session(*, now: float, channel_name: str, channel_id: str, video_id: str, summary: dict[str, Any]) -> Path:
    SESSIONS.mkdir(parents=True, exist_ok=True)
    path = SESSIONS / f"auto_experience_{int(now)}_youtube_channel.json"

    title = str(summary.get("title") or "") or f"YouTube {video_id}"
    tone = str(summary.get("emotional_tone") or "중립적")
    core = str(summary.get("core_message") or "")[:240]
    duration_sec = float(summary.get("duration_sec") or 0.0)
    themes = summary.get("resonance_themes") if isinstance(summary.get("resonance_themes"), list) else []
    themes = [str(x) for x in themes[:8]]

    form = _classify_content_form(title=title, duration_sec=duration_sec)
    lens = _infer_culture_lens(channel_name=channel_name, title=title)
    boundaries = _generate_boundaries_with_llm(
        title=title,
        tone=tone,
        core=core,
        themes=themes,
        compression_mode=str(form.get("compression_mode") or "UNKNOWN"),
        presentation_form=str(form.get("presentation_form") or "UNKNOWN"),
    )

    payload: dict[str, Any] = {
        "source": "youtube_channel",
        "title": f"{channel_name} - boundary intake",
        "tags": [
            "youtube",
            "boundary",
            "channel_learning",
            form.get("compression_mode", "UNKNOWN").lower(),
            str(lens.get("culture") or "unknown").lower(),
            str(lens.get("lens") or "none").lower(),
        ],
        "notes": _cap_text(
            f"{title} | tone={tone} | duration={int(duration_sec)}s | {form.get('compression_mode')} | {core}",
            420,
        ),
        "timestamp": float(now),
        "where": {"platform": "windows", "layer": "youtube_channel_boundary_intake"},
        "who": {"role": "agi", "mode": "unconscious"},
        "boundaries": boundaries,
        "comparisons": [],
        "meta": {
            "channel_name": channel_name,
            "channel_id": channel_id,
            "video_id": video_id,
            "duration_sec": duration_sec,
            "compression_mode": form.get("compression_mode"),
            "presentation_form": form.get("presentation_form"),
            "culture": lens.get("culture"),
            "lens": lens.get("lens"),
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def run_youtube_channel_boundary_intake(
    workspace_root: Path,
    *,
    cooldown_sec: int = 6 * 60 * 60,
    max_videos_per_run: int = 1,
) -> dict[str, Any]:
    now = time.time()
    safety = _safety_status()
    rest = _rest_status(now)

    if safety in ("BLOCK", "REVIEW"):
        res = {"ok": True, "skipped": True, "reason": f"safety={safety}", "timestamp_utc": _utc_iso(now)}
        _atomic_write_json(OUT_LATEST, res)
        _append_jsonl(OUT_HISTORY, res)
        return res
    if rest == "REST":
        res = {"ok": True, "skipped": True, "reason": "rest_gate=REST", "timestamp_utc": _utc_iso(now)}
        _atomic_write_json(OUT_LATEST, res)
        _append_jsonl(OUT_HISTORY, res)
        return res

    st = _load_state()
    last_run = float(st.get("last_run_epoch") or 0.0)
    if float(cooldown_sec) > 0 and (now - last_run) < float(cooldown_sec):
        res = {"ok": True, "skipped": True, "reason": "cooldown", "timestamp_utc": _utc_iso(now)}
        _atomic_write_json(OUT_LATEST, res)
        _append_jsonl(OUT_HISTORY, res)
        return res

    channels = _load_channels()
    if not channels:
        res = {"ok": True, "skipped": True, "reason": "no_channels_config", "timestamp_utc": _utc_iso(now)}
        _atomic_write_json(OUT_LATEST, res)
        _append_jsonl(OUT_HISTORY, res)
        return res

    # Fill placeholders best-effort (no questions).
    updated = False
    for name, cid in list(channels.items()):
        if str(cid).strip() == "CHANNEL_ID_HERE":
            resolved = _resolve_channel_id_best_effort(name)
            if resolved:
                channels[name] = resolved
                updated = True
    if updated:
        _save_channels(channels)

    learned = st.get("learned_videos") if isinstance(st.get("learned_videos"), list) else []
    learned_set = {str(x) for x in learned if isinstance(x, str)}

    # Round-robin pointer
    names = [k for k in channels.keys()]
    if not names:
        res = {"ok": True, "skipped": True, "reason": "no_channels", "timestamp_utc": _utc_iso(now)}
        _atomic_write_json(OUT_LATEST, res)
        _append_jsonl(OUT_HISTORY, res)
        return res

    ptr = int(st.get("rr_ptr") or 0) % max(1, len(names))
    processed: list[dict[str, Any]] = []

    try:
        from scripts.youtube_feeling_learner import YouTubeFeelingLearner  # type: ignore

        learner = YouTubeFeelingLearner()
    except Exception as e:
        res = {
            "ok": False,
            "error": f"learner_init_failed: {type(e).__name__}: {e}",
            "timestamp_utc": _utc_iso(now),
        }
        _atomic_write_json(OUT_LATEST, res)
        _append_jsonl(OUT_HISTORY, res)
        return res

    for _ in range(len(names)):
        if len(processed) >= int(max_videos_per_run):
            break
        name = names[ptr]
        ptr = (ptr + 1) % len(names)
        cid = str(channels.get(name) or "").strip()
        if not cid or cid == "CHANNEL_ID_HERE":
            continue

        candidates, feed_title = _list_recent_video_candidates(cid, limit=10)
        if (not candidates) or (feed_title and not _feed_matches_name(feed_title, name)):
            # best-effort auto-fix when channel_id seems wrong/outdated
            resolved = _resolve_channel_id_best_effort(name)
            if resolved and resolved != cid:
                channels[name] = resolved
                _save_channels(channels)
                cid = resolved
                candidates, feed_title = _list_recent_video_candidates(cid, limit=10)

        # If feed title still mismatches, do NOT proceed with this channel.
        # This prevents "wrong channel mapping" accidents (e.g., youth/minor content) from contaminating sessions.
        if feed_title and not _feed_matches_name(feed_title, name):
            continue

        if not candidates:
            continue

        target = None
        target_vid = None
        for c in candidates:
            if not isinstance(c, dict):
                continue
            u = str(c.get("url") or "")
            vid = str(c.get("video_id") or _extract_video_id(u))
            title_hint = str(c.get("title") or "")
            if vid in learned_set:
                continue
            if _looks_child_related_title(title_hint):
                # Mark as learned so we don't re-hit obvious child/minor content.
                learned_set.add(vid)
                continue
            target = u
            target_vid = vid
            break
        if not target:
            continue

        vid = str(target_vid or _extract_video_id(target))
        try:
            analysis = learner.analyze_feeling(video_url=target, context=f"boundary_intake:{name}", analyzed_by="youtube_channel_boundary_intake")
            # learner.analyze_feeling is async; handle both sync/async compatibility
            if hasattr(analysis, "__await__"):
                import asyncio

                analysis = asyncio.run(analysis)  # type: ignore
            # asdict-like payload
            summary = {
                "video_id": getattr(analysis, "video_id", vid),
                "title": getattr(analysis, "title", ""),
                "duration_sec": float(getattr(analysis, "duration", 0.0) or 0.0),
                "emotional_tone": getattr(analysis, "emotional_tone", ""),
                "core_message": getattr(analysis, "core_message", ""),
                "resonance_themes": getattr(analysis, "resonance_themes", []),
                "timestamp": getattr(analysis, "timestamp", _utc_iso(now)),
            }

            # Skip if analysis reveals child/minor content (safety-first, no session write).
            if _looks_child_related_title(str(summary.get("title") or "")):
                learned_set.add(vid)
                continue
            form = _classify_content_form(title=str(summary.get("title") or ""), duration_sec=float(summary.get("duration_sec") or 0.0))

            session_path = _write_session(
                now=now,
                channel_name=name,
                channel_id=cid,
                video_id=str(summary.get("video_id") or vid),
                summary=summary,
            )

            processed.append(
                {
                    "channel_name": name,
                    "channel_id": cid,
                    "video_id": str(summary.get("video_id") or vid),
                    "video_sig": _sha256_head(target),
                    "session_file": str(session_path),
                    "tone": _cap_text(str(summary.get("emotional_tone") or ""), 60),
                    "duration_sec": float(summary.get("duration_sec") or 0.0),
                    "compression_mode": form.get("compression_mode"),
                    "presentation_form": form.get("presentation_form"),
                    "themes": [str(x) for x in (summary.get("resonance_themes") or [])[:8]],
                }
            )
            learned_set.add(vid)
        except Exception:
            continue

    st_out = {
        "last_run_epoch": float(now),
        "rr_ptr": int(ptr),
        "learned_videos": sorted(list(learned_set))[-2000:],  # bounded
    }
    _save_state(st_out)

    res = {
        "ok": True,
        "timestamp_utc": _utc_iso(now),
        "safety": safety,
        "rest_gate": rest,
        "processed_count": len(processed),
        "processed": processed,
        "note": "1 run = 0~N videos, session written when processed",
    }
    _atomic_write_json(OUT_LATEST, res)
    _append_jsonl(OUT_HISTORY, res)
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", type=str, default=str(WORKSPACE))
    ap.add_argument("--force", action="store_true", help="Ignore cooldown (manual verification).")
    ap.add_argument("--cooldown-sec", type=int, default=6 * 60 * 60)
    ap.add_argument("--max-videos", type=int, default=1)
    args = ap.parse_args()

    import os

    cooldown = 0 if bool(args.force) else int(args.cooldown_sec)
    if str(os.environ.get("AGI_YT_CHANNEL_FORCE") or "").strip() in ("1", "true", "TRUE", "yes", "YES"):
        cooldown = 0

    run_youtube_channel_boundary_intake(
        Path(args.workspace).resolve(),
        cooldown_sec=int(cooldown),
        max_videos_per_run=int(args.max_videos),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
