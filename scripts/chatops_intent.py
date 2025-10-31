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
    if re.search(r"\bpreflight\b", u):
        return "preflight"
    if re.search(r"^(프리플라이트|점검|체크)", u):
        return "preflight"
    if re.search(r"(oauth|오쓰|동의|인증)", u):
        return "preflight_interactive"

    # AGI Operations
    if re.search(r"\bagi\b.*\b(health|status|check)\b", u) or re.search(r"\b(health|status|check)\b.*\bagi\b", u):
        return "agi_health"
    if re.search(r"\bagi\b.*\b(dashboard|overview)\b", u) or re.search(r"\b(dashboard|overview)\b.*\bagi\b", u):
        return "agi_dashboard"
    if re.search(r"\bagi\b.*\b(summary|report|analysis|digest)\b", u) or re.search(r"\b(summary|report|analysis|digest)\b.*\bagi\b", u):
        return "agi_summary"
    if re.search(r"\bledger\b.*\b(summary|report|analysis|digest)\b", u):
        return "agi_summary"
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
    
    # Lumen Gateway ("관문" == gateway)
    # Examples: "루멘 관문을 열자", "루멘 게이트 열어", "lumen gate open", "루멘 상태 확인", "lumen health check", "루멘 대시보드"
    # Dashboard intent (more specific than general health/status)
    if (
        re.search(r"(루멘|lumen).*(대시보드|dashboard|현황판)", u)
        or re.search(r"(대시보드|dashboard|현황판).*(루멘|lumen)", u)
    ):
        return "lumen_dashboard"
    # Health/open intent
    if (
        re.search(r"(루멘|lumen).*(관문|게이트|게이트웨이).*(열|open|오픈)", u)
        or re.search(r"(관문|게이트|게이트웨이).*(열|open|오픈).*(루멘|lumen)", u)
        or re.search(r"(루멘|lumen).*(상태|헬스|체크|점검|health|status|probe)", u)
        or re.search(r"(lumen).*(gate).*\b(open|probe|health|status)\b", u)
    ):
        return "lumen_open"
    
    # Unified Ops Dashboard
    if re.search(r"(통합|전체).*(상태|대시보드|현황)", u):
        return "ops_dashboard"
    if re.search(r"(운영|시스템).*(상태|대시보드)", u):
        return "ops_dashboard"

    # Start/Stop stream
    if (
        re.search(r"\b(start|begin|launch)\b.*\b(stream|streaming|broadcast)\b", u)
        or re.search(r"\b(stream|streaming|broadcast)\b.*\b(start|begin|launch)\b", u)
        or re.search(r"\bgo\s*live\b", u)
    ):
        return "start_stream"
    if (
        re.search(r"\b(stop|end|finish|shutdown|close)\b.*\b(stream|streaming|broadcast)\b", u)
        or re.search(r"\b(stream|streaming|broadcast)\b.*\b(stop|end|finish|shutdown|close)\b", u)
        or re.search(r"\bgo\s*offline\b", u)
    ):
        return "stop_stream"
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
    m = re.search(r"(?:switch|change)\s+(?:scene\s+)?to\s+([\w\-\s\.]+)", u)
    if not m:
        m = re.search(r"(?:switch|change)\s+scene\s+([\w\-\s\.]+)", u)
    if m:
        scene = m.group(1).strip()
        scene = re.sub(r"\s*(scene|layout|profile)\b.*$", "", scene).strip()
        if scene:
            return f"switch_scene:{scene}"
    m = re.search(r"(?:씬|scene)\s*([\w\-\s\.]+)", u)
    if m:
        scene = m.group(1)
        # Trim trailing Korean postpositions like '로', '으로', and following words
        scene = re.sub(r"\s*(로|으로).*$", "", scene).strip()
        if scene:
            return f"switch_scene:{scene}"

    # Bot controls
    if (
        re.search(r"\b(start|launch|resume|enable|activate)\b.*\b(bot|assistant)\b", u)
        or re.search(r"\b(bot|assistant)\b.*\b(start|launch|resume|enable|activate|turn\s*on)\b", u)
        or re.search(r"\b(?<!dry\s)run\b.*\b(bot|assistant)\b", u)
    ):
        return "bot_start"
    if (
        re.search(r"\b(stop|end|kill|shutdown|pause|terminate|disable|turn\s*off|close)\b.*\b(bot|assistant)\b", u)
        or re.search(r"\b(bot|assistant)\b.*\b(stop|end|kill|shutdown|pause|terminate|disable|turn\s*off|close)\b", u)
    ):
        return "bot_stop"
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
    if (
        re.search(r"(conversation|conversations|chat|chats).*(summary|report)", u)
        or re.search(r"(summary|report).*(conversation|conversations|chat|chats)", u)
    ):
        return "conversation_summary"
    if re.search(r"(대화|로그).*(요약|보고서|리포트)", u) or re.search(r"\b요약\b", u):
        return "conversation_summary"

    # Session Memory Operations
    if (
        re.search(r"\bstart\b.*\bsession\b", u)
        or re.search(r"\bsession\b.*\bstart\b", u)
        or re.search(r"\bopen\b.*\bsession\b", u)
        or re.search(r"\bbegin\b.*\bsession\b", u)
    ):
        return "session_start"
    # Start session: "세션 시작", "start session", "작업 시작해"
    if re.search(r"(세션|작업).*(시작|새로|만들어)", u) or re.search(r"start.*session", u):
        return "session_start"
    
    # Add task: "작업 추가", "add task", "할 일 추가"
    if (
        re.search(r"\bsession\b.*\b(add|log|record)\b.*\btask\b", u)
        or re.search(r"\btask\b.*\b(add|log|record)\b.*\bsession\b", u)
    ):
        return "session_add_task"
    if re.search(r"(작업|할\s*일|태스크).*(추가|등록)", u) or re.search(r"add.*task", u):
        return "session_add_task"
    
    # End session: "세션 종료", "end session", "작업 끝", "완료했어"
    if (
        re.search(r"\bsession\b.*\b(end|close|finish|wrap)\b", u)
        or re.search(r"\b(end|close|finish|wrap)\b.*\bsession\b", u)
        or re.search(r"\bwrap\s*up\b.*\bsession\b", u)
    ):
        return "session_end"
    if re.search(r"(세션|작업).*(종료|끝|완료|닫아)", u) or re.search(r"end.*session", u):
        return "session_end"
    
    # Recent sessions: "지난번에 뭐 했지?", "최근 작업", "recent sessions"
    if (
        re.search(r"\b(recent|latest|last)\b.*\bsessions?\b", u)
        or re.search(r"\bsessions?\b.*\b(recent|latest|last)\b", u)
    ):
        return "session_recent"
    if re.search(r"(지난번|최근|최신).*(작업|세션|뭐|무엇|했)", u) or re.search(r"recent.*sessions?", u):
        return "session_recent"
    
    # Search sessions: "BQI 작업 찾아줘", "find work", "search sessions"
    en_match = re.search(r"(?:search|find)\s+(?:sessions?|work)\s*(?:for|about|on)?\s*(.+)", u)
    if en_match:
        query = en_match.group(1).strip()
        query = re.sub(r"[.!?\s]+$", "", query)
        query = re.sub(r"\s*(?:please|pls)$", "", query).strip()
        if query:
            return f"session_search:{query}"
        return "session_search:"
    if re.search(r"(작업|세션).*(찾아|검색|search)", u) or re.search(r"find.*(work|session)", u):
        # Extract search query: word(s) before the verb
        m = re.search(r"^(.+?)\s*(?:작업|세션)", u)
        if m:
            query = m.group(1).strip()
            # Clean up Korean postpositions
            query = re.sub(r"\s*(을|를|의|이|가)$", "", query).strip()
            if query:
                return f"session_search:{query}"
        return "session_search:"
    
    # Active sessions: "활성 세션", "active sessions", "지금 작업 중"
    if (
        re.search(r"\b(current|open|active|running)\b.*\bsessions?\b", u)
        or re.search(r"\bsessions?\b.*\b(current|open|active|running)\b", u)
    ):
        return "session_active"
    if re.search(r"(활성|진행중|작업중).*(세션|작업)", u) or re.search(r"active.*sessions?", u):
        return "session_active"
    
    # Session stats: "세션 통계", "작업 통계", "session stats"
    if (
        re.search(r"(stats|statistics|metrics)\b.*\bsessions?\b", u)
        or re.search(r"\bsessions?\b.*\b(stats|statistics|metrics)\b", u)
    ):
        return "session_stats"
    if re.search(r"(세션|작업).*(통계|stats)", u) or re.search(r"session.*stats", u):
        return "session_stats"
    
    # Session details: "세션 상세", "세션 정보", "session details"
    if (
        re.search(r"(details|info|information|overview)\b.*\bsessions?\b", u)
        or re.search(r"\bsessions?\b.*\b(details|info|information|overview)\b", u)
    ):
        return "session_details"
    if re.search(r"(세션|작업).*(상세|정보|details)", u) or re.search(r"session.*details", u):
        return "session_details"
    
    # Save daily conversations: "대화 저장", "오늘 작업 저장", "save conversations"
    if (
        re.search(r"\bsave\b.*\b(conversation|conversations|chat|chats|log|logs)\b", u)
        or re.search(r"(conversation|conversations|chat|chats|log|logs)\b.*\b(save|archive|store)\b", u)
    ):
        return "save_conversations"
    if re.search(r"(대화|작업|세션).*(저장|기록)", u) or re.search(r"save.*conversations?", u):
        return "save_conversations"
    
    # End daily session: "오늘 여기까지", "하루 마무리", "end day", "close session"
    if (
        re.search(r"\b(end|wrap|close|finish)\b.*\b(day|today)\b", u)
        or re.search(r"\b(day|today)\b.*\b(end|wrap|close|finish)\b", u)
        or re.search(r"\bwrap\s*up\b.*\b(day|today)\b", u)
    ):
        return "end_session"
    if re.search(r"(오늘|하루).*(여기까지|끝|마무리|종료)", u) or re.search(r"end.*(day|daily)", u):
        return "end_session"
    if re.search(r"(close|finish).*(session|day)", u):
        return "end_session"
    if re.search(r"(대화|내용).*(저장|세이브)", u) or re.search(r"save.*(chat|conversation)", u):
        return "end_session"  # "대화 내용 저장해줘" → end_session
    
    # Resume from saved context: "저장된 대화", "작업 이어가", "resume work"
    if re.search(r"(저장된|이전).*(대화|작업|컨텍스트|맥락)", u):
        return "resume_context"
    if re.search(r"(작업|대화).*(이어가|계속|continue)", u) or re.search(r"resume.*(work|context)", u):
        return "resume_context"
    if re.search(r"(맥락|컨텍스트).*(복원|이어)", u):
        return "resume_context"

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
