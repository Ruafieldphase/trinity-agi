# Incident Card (Slack/Discord) — Integrated Gate

## 스크립트
- `scripts/incident_notifier_v19.py` — 단순 메시지 전송(재사용 가능)
- `scripts/gate_result_card_v15.py` — 통합 게이트 결과 요약을 *Slack Blocks* / *Discord Embed*로 전송

## 사용
```bash
# 로컬 테스트
export SLACK_WEBHOOK_URL=...
export DISCORD_WEBHOOK_URL=...
python scripts/integrated_gate_v19_v15.py > /tmp/gate.json || true
GATE_JSON_PATH=/tmp/gate.json python scripts/gate_result_card_v15.py
```

## GitHub Actions 연계
- 워크플로: `lumen_integrated_gate_and_flipback.yaml` 내 `card` 잡에서
  - `steps.gate.outputs.json`을 파일로 저장 → `gate_result_card_v15.py` 실행
  - 양쪽 웹훅(secrets)으로 카드 발송
