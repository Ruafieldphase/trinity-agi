# -*- coding: utf-8 -*-
"""
ChatOps Intent Resolver
- Input: --say "<utterance>"
- Output: one ASCII token in stdout:
  preflight | preflight_interactive | start_stream | stop_stream | quick_status | obs_status |
  switch_scene:<name> | bot_start | bot_stop | bot_dryrun | onboarding | install_secret | unknown

Reason: Avoid Unicode regex issues on Windows PowerShell 5.1 by delegating NLP to Python.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone


def resolve_rules(utter: str) -> str:
    if not utter:
        return "unknown"
    u = utter.strip().lower()

    # Preflight / OAuth
    if re.search(r"^(프리플라이트|점검|체크)", u):
        return "preflight"
    if re.search(r"(oauth|오쓰|동의|인증)", u):
        return "preflight_interactive"

    # AGI Operations
    if re.search(r"(agi|에이지아이).*(상태|헬스|건강)", u) or re.search(r"에이지아이.*체크", u):
        return "agi_health"
    if re.search(r"(agi|에이지아이).*(대시보드|현황)", u):
        return "agi_dashboard"
    if re.search(r"(agi|에이지아이).*(요약|분석)", u):
        return "agi_summary"
    if re.search(r"(ledger|레저|원장).*(요약|분석)", u):
        return "agi_summary"
    
    # BQI Operations
    if re.search(r"(bqi|페르소나|persona|phase\s*6|페이즈\s*6).*(학습|실행|run)", u):
        return "bqi_phase6"
    if re.search(r"(비노쉬|binoche).*(학습|persona)", u):
        return "bqi_phase6"
    
    # Canary Operations
    if re.search(r"(카나리|canary).*(상태|status)", u):
        return "canary_status"
    if re.search(r"(카나리|canary).*(\d+).*(%|퍼센트|프로)", u):
        # Extract percentage: "카나리 10% 올려" -> 10
        m = re.search(r"(\d+)", u)
        if m:
            pct = m.group(1)
            return f"canary_deploy:{pct}"
    if re.search(r"(카나리|canary).*(롤백|되돌려|원복)", u):
        return "canary_rollback"
    
    # Unified Ops Dashboard
    if re.search(r"(통합|전체).*(상태|대시보드|현황)", u):
        return "ops_dashboard"
    if re.search(r"(운영|시스템).*(상태|대시보드)", u):
        return "ops_dashboard"

    # Start/Stop stream
    if re.search(r"(방송|스트림).*시작", u) or re.search(r"시작.*(방송|스트림)", u):
        return "start_stream"
    if re.search(r"(방송|스트림).*(멈춰|정지|중지)", u):
        return "stop_stream"

    # Quick/OBS status
    if re.search(r"퀵\s*상태|quick\s*status", u):
        return "quick_status"
    if re.search(r"obs\s*상태|obs\s*status", u):
        return "obs_status"
    if re.search(r"상태.*보여|\bstatus\b|\bstate\b|\bhealth\b", u) or u == "상태":
        return "ops_dashboard"  # Default to unified dashboard

    # Scene switch (extract scene name after '씬' or 'scene')
    m = re.search(r"(?:씬|scene)\s*([\w\-\s\.]+)", u)
    if m:
        scene = m.group(1)
        # Trim trailing Korean postpositions like '로', '으로', and following words
        scene = re.sub(r"\s*(로|으로).*$", "", scene).strip()
        if scene:
            return f"switch_scene:{scene}"

    # Bot controls
    if re.search(r"봇.*(켜|시작)", u) or re.search(r"(자동응답).*(켜|시작)", u):
        return "bot_start"
    if re.search(r"봇.*(꺼|중지|정지)", u) or re.search(r"(자동응답).*(꺼|중지|정지)", u):
        return "bot_stop"
    if re.search(r"드라이런|dry", u):
        return "bot_dryrun"

    # Onboarding helpers
    if re.search(r"온보딩|onboarding", u):
        return "onboarding"
    if re.search(r"시크릿.*등록|secret.*install|client.*secret", u):
        return "install_secret"
    # OBS deps installation
    # Support both English and Korean variants, e.g.,
    #  - "install obs deps", "obs deps setup"
    #  - "OBS 의존성 설치", "OBS 라이브러리 설치", "오비스 의존성"
    if re.search(r"\bobs\b.*(install|setup|deps|설치|의존성)|오비스.*(설치|의존성)|obs\s*라이브러리\s*설치", u):
        return "install_obs_deps"

    # Conversation summary
    if re.search(r"(대화|로그).*(요약|보고서|리포트)", u) or re.search(r"\b요약\b", u):
        return "conversation_summary"

    return "unknown"


def _log_event(utter: str, intent: str, resolved_by: str) -> None:
    """Append a JSONL log line for intent resolution when LLM mode is enabled.

    Fields: ts, utter, intent, by
    """
    try:
        out_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.abspath(os.path.join(out_dir, "llm_intent_log.jsonl"))
        rec = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "utter": utter,
            "intent": intent,
            "by": resolved_by,
        }
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        # Never break routing due to logging failures
        pass


def resolve(utter: str, use_llm: bool = False) -> str:
    token = resolve_rules(utter)
    if token != "unknown":
        if use_llm:
            _log_event(utter, token, resolved_by="rules")
        return token
    if not use_llm:
        return token
    # LLM fallback (safe by design)
    try:
        from llm_client import classify_intent as llm_classify  # type: ignore

        intent = llm_classify(utter or "")
        if isinstance(intent, str) and intent:
            _log_event(utter, intent, resolved_by="llm")
            return intent
        _log_event(utter, token, resolved_by="llm-fail")
        return token
    except Exception:
        _log_event(utter, token, resolved_by="llm-error")
        return token


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--say", dest="say", default="")
    ap.add_argument("--use-llm", dest="use_llm", action="store_true")
    ns, _ = ap.parse_known_args(argv)
    try:
        use_llm = ns.use_llm or os.getenv("CHATOPS_USE_LLM", "0").strip() in {"1", "true", "yes"}
        token = resolve(ns.say or "", use_llm=use_llm)
        sys.stdout.write(token)
        return 0
    except Exception:
        sys.stdout.write("unknown")
        return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
