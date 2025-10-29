# Lumen Resonance v1.1 — Adaptive Feedback Starter

## Files
- SESSION_RESTORE_2025-10-23.yaml — session handoff
- collect_metrics.py — Prometheus query (HTTP instant query)
- resonance_mapper.py — metrics → resonance map (coherence, phase_diff, safety, entropy)
- feedback_rules.yaml — thresholds + actions
- resonance_notifier.py — rule evaluation, console/slack output, `--emit_json`
- resonance_executor.py — applies proposals, updates Prometheus textfile metrics
- grafana_resonance_plus_feedback.json — unified dashboard skeleton
- integration_resonance_feedback_test.sh — synthetic drop test
- adaptive_feedback_loop.sh — one-shot pipeline (collect → map → propose → apply)
- slack_test.sh — webhook smoke test
- .env.example — env vars

## Quickstart
```bash
cd tools/adaptive_feedback
cp .env.example .env  # set PROM_URL, SLACK_WEBHOOK_URL if any
bash adaptive_feedback_loop.sh
```

## Metrics Export
- Textfile collector at `./metrics/lumen_metrics.prom`
- Metric: `feedback_proposals_total`

## Contract
- `resonance_mapped.json`: {coherence, phase_diff, safety, entropy}
- Ranges normalized to [0, 1]


## Plugins
- Configure `plugins.yaml` with `mode: shell|http|k8s`.
- Shell mode maps action keywords to commands.
- HTTP mode POSTs to an endpoint with `{action, step}`.
- K8s mode runs `kubectl` templates.

## Proof Ledger
- Append-only, hash-chained log: `proof_ledger.jsonl` (+ head hash in `proof_ledger.head`).
- Executor appends `apply` events; rollback appends `rollback` events.


## Env & Templates
- `.env` 값을 자동 로드하여 `${VAR:default}` 템플릿을 `plugins.yaml` 내부에서 치환합니다.
- 주요 변수: `PLUGIN_MODE`, `SERVICE`, `K8S_NAMESPACE`, `THROTTLE_PCT`, `PLUGIN_HTTP_*` 등.

## Grafana Annotation (선택)
- `.env`에 `GRAFANA_URL`, `GRAFANA_API_TOKEN`을 설정하면 적용/롤백 시 주석 이벤트를 남길 수 있습니다.
- 수동 실행 예:
  ```bash
  python grafana_annotate.py --text "Manual check" --tags lumen,test --dashboard_uid resonance-plus-feedback
  ```


## Rules v2 (Hysteresis & Cooldown)
- 파일: `feedback_rules_v2.yaml`
- 구조: `rules: [ { id, enter, exit, cooldown, actions[] } ]`
- 조건식: `"mapped.coherence < 0.55"`, `"metrics.latency_p95_ms > 400"` 등
- 상태 파일: `rules_state.json` (활성/쿨다운 저장)

### 실행 예시
```bash
python resonance_notifier.py --mode=console --metrics=metrics.json --mapper_out=resonance_mapped.json --rules=feedback_rules_v2.yaml --state_file=rules_state.json --emit_json --out=proposals.json
```


## Release Pipeline (enhanced)
- **GHCR Image**: built & pushed on workflow dispatch.
- **Cosign (keyless)**: image is signed using GitHub OIDC (requires repo permissions: `id-token: write`).
- **Grafana Snapshot (optional)**: if `GRAFANA_URL` and `GRAFANA_API_TOKEN` are set as repository secrets, a dashboard snapshot URL is appended to the Release notes.
- **Assets**: dashboard JSONs are attached to the Release.
