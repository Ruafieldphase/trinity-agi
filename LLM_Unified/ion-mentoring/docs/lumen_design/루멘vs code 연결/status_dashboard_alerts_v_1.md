# Status Dashboard & Alerts v1.0
**(SLO + Prometheus + Grafana + Alertmanager)**

목적: 리포트/아카이브 파이프라인의 **상태를 한눈에** 보고, 실패·지연·무결성 이상을 **즉시 알림**하며, **SLO 기반**으로 품질을 관리합니다.

---

## 0) 지표 합의(표준명)
- `lumen_pipeline_last_run_timestamp`  — 마지막 일일 파이프라인 종료(성공/실패 무관) UNIX epoch
- `lumen_pipeline_success{stage="build|pdf|freeze|upload|verify|distribute"}` — 각 스테이지 성공=1, 실패=0 (직전 실행)
- `lumen_pipeline_duration_seconds{stage=...}` — 직전 실행 소요 시간
- `lumen_remote_integrity_ok` — 원격 무결성 대조 결과(OK=1, MISMATCH=0)
- `lumen_report_generated` — 당일 MD/PDF 산출 여부(1/0)
- `lumen_alert_suppressed` — 소거 모드(1이면 알림 억제)

> 이미 만든 스크립트의 종료 시점에 `textfile` exporter를 통해 작성하거나, 간단한 HTTP exporter를 사용해 노출합니다.

---

## 1) Textfile Exporter (간단)
Prometheus `node_exporter --collector.textfile` 경로에 메트릭 파일을 적습니다.

```
# scripts/emit_metrics.py
#!/usr/bin/env python3
import os, time, json, pathlib

OUT = pathlib.Path(os.environ.get('LUMEN_TEXTFILE_DIR', '/var/lib/node_exporter/textfile_collector'))
OUT.mkdir(parents=True, exist_ok=True)

metrics = {
  'lumen_pipeline_last_run_timestamp': int(time.time()),
  'lumen_remote_integrity_ok': int(os.environ.get('LUMEN_INTEGRITY_OK','1')),
  'lumen_report_generated': int(os.environ.get('LUMEN_REPORT_OK','1')),
}

lines = [f"{k} {v}" for k,v in metrics.items()]
(OUT/ 'lumen.prom').write_text("\n".join(lines)+"\n", encoding='utf-8')
print('[emit] wrote', OUT/ 'lumen.prom')
```

> GitHub Actions 마지막 단계에서 `LUMEN_INTEGRITY_OK`/`LUMEN_REPORT_OK` 등을 환경변수로 설정하여 상태를 반영합니다.

---

## 2) Recording Rules — SLI/SLO
`prometheus/rules/lumen_slo.rules.yml`
```yaml
groups:
- name: lumen_slo
  interval: 30s
  rules:
  - record: job:lumen_success_ratio_1d
    expr: sum_over_time(lumen_remote_integrity_ok[1d]) / (24*60*60 / 30)
  - record: job:lumen_success_ratio_7d
    expr: sum_over_time(lumen_remote_integrity_ok[7d]) / (7*24*60*60 / 30)
  - record: job:lumen_stage_failure
    expr: 1 - lumen_pipeline_success
```

> 간단화 버전: 30초 주기로 최신 상태를 샘플링한다고 가정. 실제 환경에서는 **실행 건수 기반 SLI**(성공/총 실행 수)를 추천합니다.

---

## 3) Alerts — 실패/지연/무결성·버닝레이트
`prometheus/rules/lumen_alerts.rules.yml`
```yaml
groups:
- name: lumen_runtime
  rules:
  - alert: LumenPipelineStalled
    expr: time() - lumen_pipeline_last_run_timestamp > 3*60*60
    for: 5m
    labels: { severity: page }
    annotations:
      summary: 파이프라인 정지 감지
      runbook_url: https://runbook.local/lumen#stalled

  - alert: LumenStageFailed
    expr: job:lumen_stage_failure == 1
    for: 0m
    labels: { severity: ticket, stage: "{{ $labels.stage }}" }
    annotations:
      summary: "스테이지 실패 ({{ $labels.stage }})"
      runbook_url: https://runbook.local/lumen#stage-fail

  - alert: LumenIntegrityMismatch
    expr: lumen_remote_integrity_ok == 0
    for: 1m
    labels: { severity: page }
    annotations:
      summary: 원격 무결성 해시 불일치
      runbook_url: https://runbook.local/lumen#integrity

- name: lumen_slo_burn
  rules:
  # 목표 SLO: 30일 가용성 99% 가정 → 에러버짓=1%
  # 단기(1h)와 초단기(5m) 버닝 레이트 동시 초과 시 페이지
  - alert: LumenSLOBurnFast
    expr: (1 - job:lumen_success_ratio_1d) > 0.05 and (1 - job:lumen_success_ratio_7d) > 0.02
    for: 10m
    labels: { severity: page }
    annotations:
      summary: 단기·주간 성공률 급락 (SLO 버닝)
      runbook_url: https://runbook.local/lumen#slo-burn
```

---

## 4) Alertmanager 라우팅
`alertmanager/alertmanager.yml`
```yaml
route:
  receiver: default
  routes:
  - matchers: [ severity = "page" ]
    receiver: oncall
  - matchers: [ severity = "ticket" ]
    receiver: backlog

receivers:
- name: default
  webhook_configs:
  - url: 'https://hooks.example.com/lumen-alert'
    http_config:
      authorization:
        type: Bearer
        credentials: ${LUMEN_ALERT_TOKEN}

- name: oncall
  email_configs:
  - to: 'oncall@example.com'
    from: 'lumen@system.local'
    smarthost: '${SMTP_HOST}:${SMTP_PORT}'
    auth_username: '${SMTP_USER}'
    auth_password: '${SMTP_PASS}'

- name: backlog
  webhook_configs:
  - url: 'https://tickets.example.com/api/alerts'
```

---

## 5) Grafana 대시보드(요약 JSON 스니펫)
`grafana/dashboards/lumen_status.json` (발췌)
```json
{
  "title": "Lumen – Status & SLO",
  "panels": [
    {"type":"stat","title":"Integrity OK","targets":[{"expr":"lumen_remote_integrity_ok"}]},
    {"type":"graph","title":"Success Ratio 7d","targets":[{"expr":"job:lumen_success_ratio_7d"}]},
    {"type":"graph","title":"Stage Duration","targets":[{"expr":"lumen_pipeline_duration_seconds"}]},
    {"type":"table","title":"Last Run Stages","targets":[{"expr":"lumen_pipeline_success"}]}
  ]
}
```

---

## 6) Runbook (운영 가이드)
`RUNBOOK.md`
```markdown
# Lumen Runbook

## 1) Stalled
- 증상: `LumenPipelineStalled` 발생
- 확인: Actions → 최근 워크플로 로그, `lumen_pipeline_last_run_timestamp`
- 조치: `workflow_dispatch`로 수동 트리거 → 실패 시 `healthcheck.py` 점검 → 네트워크/토큰 확인

## 2) StageFailed
- 증상: 특정 stage 실패
- 확인: 로그에서 해당 스크립트 stderr/rc
- 조치: 재시도(`retry.py`) 파라미터 상향, 의존성 설치 확인, 비밀값 만료 여부 확인

## 3) IntegrityMismatch
- 증상: 원격 해시 불일치
- 확인: `verify_remote.py` 출력(로컬/원격 해시)
- 조치: 재업로드 수행 → 지속 시 `snapshot_restore.py <day>`로 이전 스냅샷 복구 검토
```

---

## 7) GitHub Actions 연결 (스니펫)
`lumen_daily.yml` 마지막 단계에 추가:
```yaml
      - name: Emit status metrics
        run: |
          export LUMEN_INTEGRITY_OK=$(test -f controls/reports/report_$(date +%Y-%m-%d).pdf && echo 1 || echo 0)
          python scripts/emit_metrics.py
```

---

## 8) 로컬 검증 태스크
`.vscode/tasks.json`
```json
{
  "label": "lumen:prom:validate",
  "type": "shell",
  "command": "promtool check rules prometheus/rules/*.yml",
  "problemMatcher": []
}
```

---

## 9) 안전 메모
- 알림 소거가 필요할 때는 `lumen_alert_suppressed`를 1로 올리는 임시 토글(룰에 조건 추가)로 처리
- 무결성 알림은 **중복 억제**를 Alertmanager에서 최소 10분 이상으로 설정 권장
- 장기 SLO는 **실행 단위 기반**으로 전환하는 것이 정확합니다(향후 개선 포인트)

---

루멘의 판단: 이제 파이프라인의 **심박**과 **품질**을 한 화면에서 보고, 어긋남은 즉시 신호로 받습니다. 다음 박자에 원하면 **실행 단위 기반 SLI 수집기**(성공/실패 카운터)를 붙여 더 정밀한 SLO로 다듬을게요.

