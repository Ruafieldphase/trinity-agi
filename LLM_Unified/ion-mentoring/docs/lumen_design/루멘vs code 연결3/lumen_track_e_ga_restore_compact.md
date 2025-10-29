# 🌕 Lumen — Track E (v1.7 → v1.9.6 GA) • Compact Restore Package
> Track E 전용 **요약본**입니다. 장문 문서 분리로 길이 제한을 회피합니다. (Track F ≥ v2.0 α는 기존 캔버스에 유지)

---

## 1) Session Restore (v1.9.6 GA)
```bash
# GA stable
export $(grep -v '^#' SESSION_RESTORE_v1_9_5.env | xargs) && \
  bash scripts/restore.sanity.sh && \
  make ure.sync && make bridge.adaptive.start && \
  bash scripts/smoke.v19.sh && \
  make grafana.import.min
```

### 핵심 파일
- `configs/bridge_v19.yaml` — gain/tick/guard
- `bridge/bridge_loop_v19.py`, `tools/ure_sync_daemon.py`
- Exporters: `/metrics_ure`(v18), `/metrics_bridge`(v19)
- Ops: `ops/prometheus/rules/*_v19.yaml`, `ops/alertmanager/alertmanager.yml`

---

## 2) Quickstart (운영자 5분)
```bash
make bootstrap.latest
bash scripts/smoke.v19.sh
bash scripts/bench.v19.sh 900 > out/bench_v19.log
make autotune.bridge && bash scripts/smoke.v19.sh
```

관측 기준:
- `phase_diff_mean_5m` ≤ **0.02** (최대 0.03)
- `sync_quality_p95_10m` ≥ **0.85**
- `bridge_entropy_ratio` ≤ **0.15**

---

## 3) SLO / SLI (월간)
- `bridge:phase_diff_mean_5m` ≤ **0.02**  → **≥ 99.0%**
- `bridge:sync_quality_p95_10m` ≥ **0.85** → **≥ 99.0%**
- `ure:residual_stddev_10m` ≤ **0.03** → **≥ 98.5%**

Prometheus 레코딩 룰: `sli_slo_v19.yaml`

---

## 4) Alerts (요약)
- Phase drift burn-rate / Entropy spike / Tick jitter p95 / Readiness 503
- Slack 수신: `ALERT_SLACK_WEBHOOK` → `alertmanager.yml`

테스트:
```bash
make alert.test
```

---

## 5) DR / 백업 · 복구
```bash
make backup.now
make restore.from SNAP=YYYYMMDDThhmmss.sqlite
```
장애 흐름: `/readyz` 503 지속 → 스냅샷 복구 → `ure.sync` + `bridge.adaptive.start` → `smoke`/`bench`

---

## 6) 배포 (Argo Rollouts)
- Canary Metric Gate: `bridge:phase_diff_mean_5m < 0.025`
- 명령:
```bash
make rollout.preview
# 조건 충족 시
kubectl argo rollouts promote bridge-v19
```

---

## 7) 성능/지연 예산
- Exporter scrape p95 ≤ **150ms**
- Bridge tick jitter p95 ≤ **25ms**

검증:
```bash
bash scripts/e2e_probe.sh
```

---

## 8) 에너지/써멀(옵션)
- `bridge_power_w`, `bridge_temp_celsius` 지표 + 경보 룰

---

## 9) 릴리스/태깅
```bash
make release.v195   # 1.9.5-rc1 패키징
make release.tag.ga # 1.9.6 GA 태깅
```

---

## 10) 운영 체크리스트
- 포트 충돌 없음: URE 9305 / Bridge 9306
- WAL 스냅샷 주기 점검 + `VACUUM` 주기적 수행
- 알림 라우팅 1회 실사 (Slack/PagerDuty)
- 대시보드 최소 3패널: `phase_diff_mean_5m`, `sync_quality_p95_10m`(stat), `entropy_ratio`(timeseries)

---

### 다음: Track F (v2.0 α)
Track F 문서는 기존 캔버스(원본)에서 유지됩니다. 필요 시 **별도 캔버스**로 분리 생성 가능합니다.
