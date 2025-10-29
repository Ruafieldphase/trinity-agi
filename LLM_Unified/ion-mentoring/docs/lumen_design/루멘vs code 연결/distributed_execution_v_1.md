# Distributed Execution v1.0  
**(Multi‑Region + Failure Taxonomy + Smart Reruns)**

목적: 파이프라인을 여러 리전/러너로 분산 실행하고, 실패를 **원인별(분류) 계수**, **중복 없이 집계**, **선별 재시도(Smart Rerun)**까지 자동화합니다. (SLI v1.1 상위 확장)

---

## 0) 설계 개요
- **분산 실행**: GitHub Actions matrix `region`/`runner`로 병렬 수행 → 동일 날짜에 *여러 결과* 중 **최종 성공**만 1회로 집계
- **실패 분류**: `error_class` 라벨(네트워크, 토큰만료, 외부API, 빌드, 의존성, 환경, 알수없음)
- **스마트 재시도**: 재현 가능성이 낮은 일시 오류만 자동 재실행(백오프/상한), 영구 오류는 바로 티켓 전송
- **집계 원칙**: `run_id`를 **(pipeline, date, region)**로 생성 → 최종 승자(성공)만 일일 SLI 집계에 반영

---

## 1) 실행 ID & 라벨 스키마
`run_id = YYYYMMDD-<region>-<shortsha>`  
라벨: `{pipeline, region, runner, version, error_class?, stage?}`

카운터(확장):
- `lumen_runs_total{...}` / `lumen_runs_success_total{...}` / `lumen_runs_failed_total{error_class=...}`
- `lumen_stage_(success|failed)_total{stage=..., error_class?}`

---

## 2) GitHub Actions 분산 실행 (발췌)
`.github/workflows/lumen_daily.yml`
```yaml
strategy:
  matrix:
    region: [ap-northeast-2, us-west-2]
    include:
      - region: ap-northeast-2
        runner: ubuntu-latest
      - region: us-west-2
        runner: ubuntu-latest
runs-on: ${{ matrix.runner }}

env:
  LUMEN_REGION: ${{ matrix.region }}
  LUMEN_PIPELINE: daily
  LUMEN_PIPELINE_VERSION: v1.2
  PUSHGATEWAY_URL: ${{ secrets.PUSHGATEWAY_URL }}

steps:
  - name: Generate run id
    run: echo "LUMEN_RUN_ID=$(date -u +%Y%m%d)-${{ matrix.region }}-${GITHUB_SHA::8}" >> $GITHUB_ENV

  # ... (기존 단계들)

  - name: Mark run success
    if: success()
    run: python scripts/sli_push_ext.py --ok

  - name: Mark run failed
    if: failure()
    run: |
      err=$(python scripts/classify_failure.py --from-gh)
      python scripts/sli_push_ext.py --fail --error_class "$err"
```

> 동일 날짜를 여러 리전에서 수행해 **하나라도 성공하면** 그 날짜는 성공으로 취급.

---

## 3) 실패 분류기 — `scripts/classify_failure.py`
```python
#!/usr/bin/env python3
import os, sys, re, json

PATTERNS = [
  (r"Connection( timed out| reset)|ECONNREFUSED|TLS handshake", "network"),
  (r"401|403|expired|invalid (token|credentials)", "token_expired"),
  (r"5\d{2} (Internal|Bad Gateway|Service Unavailable)", "external_api"),
  (r"ModuleNotFoundError|ImportError|No module named", "dependency"),
  (r"SyntaxError|TypeError|NameError", "build"),
  (r"No space left on device|ENOSPC|Permission denied", "environment"),
]

DEFAULT = "unknown"

if __name__ == "__main__":
  # GH Actions 예: 직전 스텝 로그 혹은 env에서 메시지 전달받는 방식(단순화)
  text = os.environ.get('LUMEN_LAST_ERROR', '') + ' ' + ' '.join(sys.argv[1:])
  text = text.lower()
  for pat, label in PATTERNS:
    if re.search(pat.lower(), text):
      print(label)
      sys.exit(0)
  print(DEFAULT)
```

---

## 4) 확장 Push 스크립트 — `scripts/sli_push_ext.py`
```python
#!/usr/bin/env python3
import os, requests
from datetime import datetime, timezone

PGW = os.environ.get('PUSHGATEWAY_URL','http://localhost:9091')
PIPE = os.environ.get('LUMEN_PIPELINE','daily')
RUN_ID = os.environ['LUMEN_RUN_ID']
VER = os.environ.get('LUMEN_PIPELINE_VERSION','v1')
REG = os.environ.get('LUMEN_REGION','ap-northeast-2')
RUNNER = os.environ.get('RUNNER_NAME','gha')
JOB = f"lumen_{PIPE}"

# POST helper

def push(metric: str, labels: dict, value: int=1):
    lbl = ",".join([f'{k}="{v}"' for k,v in labels.items()])
    body = f"{metric}{{{lbl}}} {value}\n"
    url = f"{PGW}/metrics/job/{JOB}/run_id/{RUN_ID}"
    r = requests.post(url, data=body.encode('utf-8'), timeout=10)
    r.raise_for_status()

if __name__=='__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--ok', action='store_true')
    ap.add_argument('--fail', action='store_true')
    ap.add_argument('--error_class', type=str, default='unknown')
    ap.add_argument('--stage', type=str)
    ap.add_argument('--stage_ok', action='store_true')
    ap.add_argument('--stage_fail', action='store_true')
    a = ap.parse_args()

    base = { 'pipeline': PIPE, 'version': VER, 'region': REG, 'runner': RUNNER }

    if a.ok:
        push('lumen_runs_total', base)
        push('lumen_runs_success_total', base)
    if a.fail:
        push('lumen_runs_total', base)
        push('lumen_runs_failed_total', {**base, 'error_class': a.error_class})
    if a.stage and a.stage_ok:
        push('lumen_stage_success_total', {**base, 'stage': a.stage})
    if a.stage and a.stage_fail:
        push('lumen_stage_failed_total', {**base, 'stage': a.stage, 'error_class': a.error_class})
```

---

## 5) 중복 제거·승자 선출 — Prometheus 룰
하루 단위로 **리전별 실행** 중 성공이 1개라도 있으면 그 날짜는 성공으로 계산.

`prometheus/rules/lumen_aggregate.rules.yml`
```yaml
groups:
- name: lumen_aggregate
  interval: 1m
  rules:
  - record: lumen:daily_runs_success
    expr: sum by(day) (max_over_time(increase(lumen_runs_success_total[1d]) > 0)[1d:1m])
  - record: lumen:daily_runs_total
    expr: sum by(day) (max_over_time(increase(lumen_runs_total[1d]) > 0)[1d:1m])
  - record: lumen:sli1d
    expr: lumen:daily_runs_success / clamp_min(lumen:daily_runs_total, 1)

  # 리전별 실패 분포(원인)
  - record: lumen:failures_by_class:1d
    expr: sum by(region, error_class)(increase(lumen_runs_failed_total[1d]))
```
> 운영 환경에 맞게 `day` 라벨을 메트릭에 주입하거나 `timestamp()` 기반으로 변환할 수 있습니다(간단화를 위해 생략).

---

## 6) 스마트 재시도 정책
- **자동 재시도 허용(error_class)**: `network`, `external_api` → 최대 2회, 백오프 5s/30s
- **보류 & 티켓(error_class)**: `token_expired`, `dependency`, `build`, `environment` → 즉시 티켓/알림, 수동 개입

`.github/workflows/lumen_daily.yml` (발췌)
```yaml
- name: Smart Rerun gate
  if: failure()
  run: |
    err=$(python scripts/classify_failure.py --from-gh)
    echo "ERR_CLASS=$err" >> $GITHUB_ENV

- name: Smart Rerun (transient only)
  if: failure() && contains('network,external_api', env.ERR_CLASS)
  run: |
    python scripts/retry.py 2 5 -- bash -lc "python scripts/upload_archive.py $(date -u +%Y-%m-%d) && python scripts/verify_remote.py $(date -u +%Y-%m-%d)"
```

---

## 7) 알림 강화 (요약)
- Slack/이메일 템플릿에 `region`, `error_class`, `run_id` 노출
- **단일 리전 연속 실패** 경보:
```yaml
- alert: LumenRegionConsecutiveFailures
  expr: increase(lumen_runs_failed_total{region="us-west-2"}[6h]) >= 2
  for: 0m
  labels: { severity: ticket }
  annotations:
    summary: us-west-2 리전에서 2회 연속 실패
```

---

## 8) 대시보드 패널(발췌)
- **Map/Stat**: 지역별 성공률 `sum by(region)(increase(lumen_runs_success_total[7d])) / sum by(region)(increase(lumen_runs_total[7d]))`
- **Bar**: `increase(lumen_runs_failed_total[7d]) by (error_class)`
- **Table**: 최근 10회 실행 `run_id, region, result, error_class`

---

## 9) Runbook 보강
- `token_expired`: 토큰 재발급 후 재실행(수동) → CI 변수 회전 스텝 문서화
- `dependency`: `pip freeze`/캐시 무효화 → `pip install --no-cache-dir`
- `environment`: 러너 디스크/권한 점검, 아티팩트 정리

---

## 10) 적용 순서
1) `sli_push_ext.py`, `classify_failure.py` 추가 → 워크플로 훅 연결
2) matrix `region` 확정 → `LUMEN_REGION` 주입
3) Prometheus 룰 로드/검증 → Grafana 패널 추가
4) Alert 강화 룰 배치 → 티켓/온콜 라우팅 확인

루멘의 판단: 이제 파이프라인은 **다중 리전에서 스스로 균형**을 잡고, 실패는 **원인별로 투명**해졌으며, **일시 오류만 현명하게 다시 시도**합니다. 다음 박자에서는 **아티팩트 지문(merkle) + 전 구간 추적(trace id)**로 감사가능성을 높일 수 있어요.