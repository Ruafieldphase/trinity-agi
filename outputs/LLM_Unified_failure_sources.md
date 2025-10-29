# Tier3 Failure Case Source List (LLM_Unified)

| Focus | File | Notes |
| --- | --- | --- |
| Declaration font / output failures | `hybrid_output/` logs, `sena_work_history.md` | Locate timestamps where declaration PDF regeneration is discussed. Mask any personal data. |
| Vertex API quota / auth issues | `vertex_ai_test.py`, `vertex-test-simple.py`, `system-status.json` | Extract error handling paths for inclusion in 실패 사례집. |
| Session continuity breakdowns | `session_memory_monitor.py`, `session-continuity.json` | Describe how session loss was detected and mitigated. |
| NAS / storage collisions | `system-check.py`, `today-session-highlights.md` | Reference incidents where NAS syncing failed; confirm if any sensitive paths need redaction. |
| Multi-agent orchestration stalls | `shion_collaboration_test.py`, `setup_cli_trio.py` | Capture log snippets showing recovery steps. |

각 파일에서 필요한 구간을 발췌하되, API 키·계정 정보는 `[REDACTED]` 처리 후 사례집에 포함하세요.
