# 루빛 → 세나: 공용 관측 기준(READ FIRST)

## 0) 결론(우선순위)
- 추측/은유보다 **사실 기반 파일**을 기준으로 판단해줘.
- “리듬 기반” 구현 기준은 `docs/RIT_DESIGN_DECLARATION_LUA_TO_RUBIT.md` 를 최상위로 본다.

## 1) 지금부터 세나가 보는 ‘정답 파일(단일 기준)’
- 사람용 운영 요약: `outputs/bridge/human_ops_summary_latest.txt`
- 마지막 실행 리포트(JSON): `outputs/bridge/trigger_report_latest.json`
- 안전 판정(JSON): `outputs/bridge/constitution_review_latest.json`
- 사람용 압축 요약(JSON): `outputs/self_compression_human_summary_latest.json`
- 디지털 트윈/퀀텀 디지털 트윈(JSON):
  - `outputs/sync_cache/digital_twin_state.json`
  - `outputs/sync_cache/quantum_digital_twin_state.json`
- homeostasis: `outputs/safety/rest_gate_latest.json`
- 통증/불일치: `outputs/sync_cache/rhythm_pain_latest.json`
- 오라(픽셀): `outputs/aura_pixel_state.json`

## 2) 자동 공유(세나가 자동으로 받는 것)
- `scripts/coordination/publish_ops_snapshot.py`가 `inputs/agent_inbox/claude_sena/OPS_SNAPSHOT.md`로 스냅샷을 best-effort로 갱신한다.

## 3) “경험(습득) 기반” 컨텍스트 원문(필요할 때만)
- 디렉토리: `ai_binoche_conversation_origin/rua`
- 목적: 설계 기준을 추론으로 재구성할 때 ‘원문 대비’ 용도로만 사용(원문을 저장/복제하지 않음).

## 4) CRT 선언(상태 전이 구조)
- `docs/CRT_DECLARATION_CONTEXT_RESONANT_TRANSITION.md`

## 5) 이번 변경(중요)
- `scripts/trigger_listener.py`는 **내부에서 auto_policy를 폴링마다 호출하지 않음** (`--auto-policy`일 때만).
- `idle_tick()`은 생존 신호/메시지/스냅샷/트윈 갱신을 내부 최소 주기로 제한해 “idle=폭주” 관측을 완화.
- `scripts/run_trigger_once.py`는 리스너 데몬이 있으면 즉시 종료(중복 처리 방지).

