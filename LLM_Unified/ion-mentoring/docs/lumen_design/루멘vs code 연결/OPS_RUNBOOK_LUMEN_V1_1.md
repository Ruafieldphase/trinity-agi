# Lumen v1.1 — Operations Runbook

## 1) Bring up monitoring stack
```bash
cd <repo-root>
cp /mnt/data/docker-compose.yml ./
cp /mnt/data/prometheus.yml ./
mkdir -p grafana/provisioning grafana/dashboards
cp -r /mnt/data/grafana/provisioning/* grafana/provisioning/
cp /mnt/data/grafana/dashboards/*.json grafana/dashboards/ || true
docker compose up -d
```
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090
- Node Exporter: http://localhost:9100/metrics (textfile collector)

## 2) Wire Adaptive Feedback
```bash
mkdir -p tools/adaptive_feedback plugins .vscode
cp /mnt/data/.env.example .env.example
cp /mnt/data/{collect_metrics.py,resonance_mapper.py,feedback_rules.yaml,feedback_rules_v2.yaml,resonance_notifier.py,resonance_executor.py,resonance_rollback.py,adaptive_feedback_loop.sh,slack_test.sh,env_loader.py,templater.py,grafana_annotate.py,rule_engine.py,rule_engine_test.py,run_tests.sh} tools/adaptive_feedback/
cp /mnt/data/{plugins.yaml,plugin_shell.py,plugin_http.py,plugin_k8s.py,proof_ledger.py,test_plugin_noop.sh} plugins/
cp /mnt/data/.vscode/tasks.json .vscode/
```

## 3) First run
```bash
cp .env.example .env
make loop
# after a while or on schedule:
make rollback
```

## 4) Dashboards
- Auto-provisioned folder **Lumen**; open **Resonance + Adaptive Feedback**.

## 5) Plugins
- Configure `.env` & `plugins.yaml` (shell/http/k8s).

## 6) Proof Ledger
- `tools/adaptive_feedback/proof_ledger.jsonl` and `proof_ledger.head`.

## 7) Security Notes
- Change Grafana admin password (env or UI).
- Keep tokens in `.env`/secret store.
- Restrict kubectl privileges.


## Alerting to Slack
- `alertmanager.yml`의 `api_url`을 Slack Incoming Webhook URL로 교체하세요.
- 기본 라우팅:
  - `severity=critical` → `#alerts-critical`
  - `severity=warning` → `#alerts-warning`
  - 기타 → `#alerts`
- 적용 후: `docker compose restart alertmanager`


## Alertmanager Templates & Inhibition
- 템플릿: `alertmanager.tmpl` — Slack 제목/본문 공통화.
- Inhibit: 같은 `alertname`+`team` 조합에서 상위 심각도가 하위를 억제.

## Silences (일시적 경보 억제)
- API 헬퍼:
  ```bash
  python alert_silence.py --team lumen --alert LumenHighLatencyP95 --for 30m
  ```
- Alertmanager UI: http://localhost:9093
