# -*- coding: utf-8 -*-
"""
Lightweight tests for ChatOps intent resolver.
Runs a set of utterances and asserts expected tokens.
Exit code 0 on success; non-zero on failure.
"""
from __future__ import annotations
import sys
from typing import Tuple

# Ensure relative import works when invoked as a script
import os
sys.path.insert(0, os.path.dirname(__file__))

import chatops_intent as I  # type: ignore

CASES: Tuple[Tuple[str, str], ...] = (
    ('Core 관문을 열자', 'core_open'),
    ('Core 게이트 열어', 'core_open'),
    ('Core health check', 'core_open'),
    ('Core 상태 확인', 'core_open'),
    ('Core 대시보드', 'core_dashboard'),
    ('Core dashboard', 'core_dashboard'),
    ('open Core dashboard', 'core_dashboard'),
    ('preflight check', 'preflight'),
    ('oauth flow', 'preflight_interactive'),
    ('AGI health status', 'agi_health'),
    ('AGI dashboard overview', 'agi_dashboard'),
    ('AGI summary report', 'agi_summary'),
    ('start the stream', 'start_stream'),
    ('go live', 'start_stream'),
    ('stop the stream', 'stop_stream'),
    ('go offline', 'stop_stream'),
    ('switch to ai dev', 'switch_scene:ai dev'),
    ('switch scene to ai dev', 'switch_scene:ai dev'),
    ('start the bot', 'bot_start'),
    ('run the bot', 'bot_start'),
    ('stop the bot', 'bot_stop'),
    ('bot dry run', 'bot_dryrun'),
    ('conversation summary', 'conversation_summary'),
    ('session start', 'session_start'),
    ('start session', 'session_start'),
    ('session add task', 'session_add_task'),
    ('session end', 'session_end'),
    ('session recent', 'session_recent'),
    ('search sessions for bqi', 'session_search:bqi'),
    ('session active', 'session_active'),
    ('session stats', 'session_stats'),
    ('session details', 'session_details'),
    ('save chat logs', 'save_conversations'),
    ('wrap up the day', 'end_session'),
    ('resume context', 'resume_context'),
)


def main() -> int:
    failed = []
    for utter, expect in CASES:
        got = I.resolve_rules(utter)
        if got != expect:
            failed.append((utter, expect, got))
    if failed:
        print("FAIL: intent mismatches")
        for u, e, g in failed:
            print(f"  utter={u!r} expect={e} got={g}")
        return 1
    print("OK: all intent cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
