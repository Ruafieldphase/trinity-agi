# Execution‑Unit SLI Collector v1.1
**(Per‑Run Counters + Multi‑Window Burn Rate + Alert Templates)**

목적: CI 실행 단위(하루 파이프라인 1회)를 정확히 계수해 **정석 SLI/SLO**를 운영하고, **멀티 윈도우 버닝레이트** 알림과 **Slack/이메일 템플릿**을 제공한다. (Status Dashboard v1.0 상위 확장)

---

## 0) 왜 실행 단위 SLI인가?
- 이전 v1.0은 “상태 플래그”를 시계열처럼 샘플링했지만, **성공/실패 실행 수** 기반의 SLI가 더 정확하다. (SRE 권고)
- 이번 버전은 실행이 끝날 때마다 **성공/실패 카운터**를 1회 밀어주며, 기간별 성공률을 정밀 추적한다.

---

## 1) 메트릭 모델(정의)
- `lumen_runs_total{pipeline="daily"}` — 실행 총합
- `lumen_runs_success_total{pipeline="daily"}` — 성공 실행 합
- `lumen_runs_failed_total{pipeline="daily"}` — 실패 실행 합 (선택: = runs_total - success_total)
- `lumen_stage_success_total{pipeline,stage}` — 스테이지 단위 성공 합
- `lumen_stage_failed_total{pipeline,stage}` — 스테이지 단위 실패 합
- 라벨: `pipeline`(daily/verify), `run_id`(YYYYMMDD‑HHMMSS‑sha), `version`(파이프라인 버전)

집계 SLI:
```
lumen_sli_success_ratio = increase(lumen_runs_success_total[7d]) / increase(lumen_runs_total[7d])
```

---

## 2) Pushgateway 기반 수집기 (CI 친화)
> CI(Job) → Pushgateway → Prometheus pull. 에페메럴 잡에 적합.

### 2.1 스크립트 `scripts/sli_push.py`
```python
#!/usr/bin/env python3
import os, time, json, requests
from datetime import datetime, timezone, timedelta

PGW = os.environ.get('PUSHGATEWAY_URL','http://localhost:9091')
PIPE = os.environ.get('LUMEN_PIPELINE','daily')
RUN_ID = os.environ.get('LUMEN_RUN_ID') or datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
VER = os.environ.get('LUMEN_PIPELINE_VERSION','v1')
JOB = f"lumen_{PIPE}"

# stage=build|pdf|freeze|upload|verify|distribute

def push_counter(metric: str, labels: dict, value: int=1):
    # text format payload
    lbl = ",".join([f'{k}="{v}"' for k,v in labels.items()])
    body = f"{metric}{{{lbl}}} {value}\n"
    url = f"{PGW}/metrics/job/{JOB}/run_id/{RUN_ID}"
    r = requests.post(url, data=body.encode('utf-8'), timeout=10)
    r.raise_for_status()

if __name__=='__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--ok', action='store_true', help='mark whole run success')
    ap.add_argument('--fail', action='store_true', help='mark whole run failed')
    ap.add_argument('--stage', type=str, help='stage name')
    ap.add_argument('--stage_ok', action='store_true')
    ap.add_argument('--stage_fail', action='store_true')
    args = ap.parse_args()

    if args.ok:
        push_counter('lumen_runs_total', { 'pipeline': PIPE, 'version': VER })
        push_counter('lumen_runs_success_total', { 'pipeline': PIPE, 'version': VER })
    if args.fail:
        push_counter('lumen_runs_total', { 'pipeline': PIPE, 'version': VER })
        push_counter('lumen_runs_failed_total', { 'pipeline': PIPE, 'version': VER })
    if args.stage and args.stage_ok:
        push_counter('lumen_stage_success_total', { 'pipeline': PIPE, 'stage': args.stage, 'version': VER })
    if args.stage and args.stage_fail:
        push_counter('lumen_stage_failed_total', { 'pipeline': PIPE, 'stage': args.stage, 'version': VER })
```

### 2.2 GitHub Actions 연동 (발췌)
`lumen_daily.yml` 각 스테이지 직후:
```yaml
- name: Stage build ok
  if: success()
  run: |
    python scripts/sli_push.py --stage build --stage_ok

- name: Stage build fail
  if: failure()
  run: |
    python scripts/sli_push.py --stage build --stage_fail
```
마지막에 실행 단위 합계 기록:
```yaml
- name: Mark run success
  if: success()
  run: python scripts/sli_push.py --ok

- name: Mark run failed
  if: failure()
  run: python scripts/sli_push.py --fail
```
워크플로 전체에 환경변수 추가:
```yaml
env:
  PUSHGATEWAY_URL: ${{ secrets.PUSHGATEWAY_URL }}
  LUMEN_PIPELINE: daily
  LUMEN_PIPELINE_VERSION: v1.1
```

---

## 3) 녹화 룰 & 버닝레이트 (정석)
`prometheus/rules/lumen_sli.rules.yml`
```yaml
groups:
- name: lumen_sli
  interval: 1m
  rules:
  - record: lumen:sli7d
    expr: increase(lumen_runs_success_total[7d]) / clamp_min(increase(lumen_runs_total[7d]), 1)
  - record: lumen:sli30d
    expr: increase(lumen_runs_success_total[30d]) / clamp_min(increase(lumen_runs_total[30d]), 1)

  # 에러율 = 1 - 성공률 (창구 단위)
  - record: lumen:error_rate_5m
    expr: 1 - (increase(lumen_runs_success_total[5m]) / clamp_min(increase(lumen_runs_total[5m]),1))
  - record: lumen:error_rate_1h
    expr: 1 - (increase(lumen_runs_success_total[1h]) / clamp_min(increase(lumen_runs_total[1h]),1))
```

멀티 윈도우 버닝레이트(Alert 추천):
- 목표 SLO = 99%/30일 → 에러버짓 = 1%
- 빠른 창(5m)과 느린 창(1h) 동시 초과 시 페이지

`prometheus/rules/lumen_burn.rules.yml`
```yaml
groups:
- name: lumen_burn
  rules:
  - alert: LumenSLOBurnMultiWindow
    expr: (lumen:error_rate_5m > 0.14) and (lumen:error_rate_1h > 0.02)
    for: 10m
    labels: { severity: page }
    annotations:
      summary: "SLO 버닝 감지 (5m & 1h)"
      description: "5m 에러율={{ $value | humanizePercentage }} / 1h 임계=2%"
      runbook_url: https://runbook.local/lumen#slo-burn
```
> 기준치는 서비스 빈도에 맞게 튜닝(예: 하루 1회 실행이면 창을 1d/7d로 조정)하세요.

---

## 4) 무결성 알림(정교화)
`prometheus/rules/lumen_integrity.rules.yml`
```yaml
groups:
- name: lumen_integrity
  rules:
  - alert: LumenIntegrityMismatch
    expr: increase(lumen_runs_total[1d]) > 0 and lumen_remote_integrity_ok == 0
    for: 5m
    labels: { severity: page }
    annotations:
      summary: 원격 무결성 해시 불일치 (최근 실행)
      runbook_url: https://runbook.local/lumen#integrity
```

---

## 5) Alertmanager 템플릿 (Slack/이메일)
`alertmanager/templates/lumen.tmpl`
```gotemplate
{{ define "lumen.title" }}[Lumen] {{ .CommonLabels.alertname }} ({{ .Status }}){{ end }}
{{ define "lumen.body" }}
*Alert:* {{ .CommonLabels.alertname }}  
*Severity:* {{ .CommonLabels.severity }}  
*Pipeline:* {{ index .CommonLabels "pipeline" | default "daily" }}  
*Starts:* {{ .Alerts.Firing | len }} firing, {{ .Alerts.Resolved | len }} resolved  

{{ range .Alerts }}
- *Labels:* {{ .Labels }}  
  *Annotations:* {{ .Annotations }}  
  *StartsAt:* {{ .StartsAt }}  
{{ end }}

Runbook: {{ (index .CommonAnnotations "runbook_url") | default "https://runbook.local/lumen" }}
{{ end }}
```
Alertmanager 설정(발췌):
```yaml
receivers:
- name: slack-oncall
  slack_configs:
  - api_url: ${SLACK_WEBHOOK}
    title: '{{ template "lumen.title" . }}'
    text: '{{ template "lumen.body" . }}'

- name: email-oncall
  email_configs:
  - to: 'oncall@example.com'
    from: 'lumen@system.local'
    smarthost: '${SMTP_HOST}:${SMTP_PORT}'
    auth_username: '${SMTP_USER}'
    auth_password: '${SMTP_PASS}'
    html: '{{ template "lumen.body" . }}'
```

---

## 6) Grafana 패널 (실행 단위 SLI)
`grafana/dashboards/lumen_sli.json` (발췌)
```json
{
  "title": "Lumen – Execution SLI",
  "panels": [
    {"type":"stat","title":"7d Success Ratio","targets":[{"expr":"lumen:sli7d"}]},
    {"type":"stat","title":"30d Success Ratio","targets":[{"expr":"lumen:sli30d"}]},
    {"type":"graph","title":"Run Volume","targets":[{"expr":"increase(lumen_runs_total[30d])"}]},
    {"type":"table","title":"Stages (success/fail)","targets":[{"expr":"sum by(stage)(increase(lumen_stage_success_total[7d]))"},{"expr":"sum by(stage)(increase(lumen_stage_failed_total[7d]))"}]}
  ]
}
```

---

## 7) 로컬 검증
- Pushgateway 기동: `docker run -p 9091:9091 prom/pushgateway`
- 수동 푸시 테스트: `PUSHGATEWAY_URL=http://localhost:9091 python scripts/sli_push.py --ok`
- Prometheus에 `scrape_configs` 추가:
```yaml
scrape_configs:
- job_name: 'pushgateway'
  static_configs: [{ targets: ['pushgateway:9091'] }]
```

---

## 8) 마이그레이션 노트 (v1.0 → v1.1)
- v1.0의 `lumen_pipeline_success`(게이지 성격)를 **보조 지표**로 유지 가능
- SLI/버닝 알림은 v1.1의 `*_total` 계수 기반으로 전환 권장
- Grafana 패널 일부는 교체: 성공률 통계(7d/30d) 중심으로 재배치

---

루멘의 판단: 이제 **실행 단위의 진짜 성공률**을 계량하고, **버닝레이트**로 건강을 판단하며, **알림 템플릿**으로 즉시 대응할 수 있다. 이 레이어를 올리면 품질 신호가 한층 또렷해진다.