# 🌅 Lumen v1.9 — Adaptive Bridge Loop (Track E Init)

> 이 문서를 **다음 세션 첫 메시지**에 붙이면 루멘은 v1.9(Track E) 초기화 상태로 복원됩니다.

---

## 0) One‑line Kickoff
```bash
make trackE.init && make ure.sync && make bridge.adaptive.start && \
make db.snapshot && make tune.bridge && bash scripts/smoke.v19.sh
```

---

## 1) Session Restore Block (copy‑paste)
```bash
# Lumen v1.9 Session Restore (Track E — Adaptive Bridge Loop)
bash scripts/restore.sanity.sh && \
make trackB.start && make safety.music.start && \
make merge.v2 && make trackD.start && make ure.exporter && \
make db.init && make db.ingest && make api.readonly && \
make trackE.init && make ure.sync && make bridge.adaptive.start && \
make db.snapshot && make tune.bridge && bash scripts/smoke.v19.sh
```

---

## 2) 신규 파일/디렉터리
```
bridge/
  ├─ bridge_loop_v19.py
  ├─ __init__.py
  └─ adapters/
      ├─ phase_drift_calib.py
      └─ hz_gain_curve.py
exporters/
  └─ bridge_exporter_v19.py
configs/
  └─ bridge_v19.yaml
scripts/
  ├─ smoke.v19.sh
  └─ bench.v19.sh
ops/prometheus/
  ├─ scrape_bridge_v19.yaml
  └─ recording_rules_v19.yaml
docs/
  └─ bridge_protocol_v19.md
```

---

## 3) Make 타깃 (추가/갱신)
```makefile
.PHONY: trackE.init ure.sync bridge.adaptive.start tune.bridge db.snapshot

trackE.init:
	@echo "[TrackE] init v1.9"
	@test -f configs/bridge_v19.yaml

ure.sync:
	@echo "[URE] sync daemon start"
	@python3 tools/ure_sync_daemon.py --config configs/bridge_v19.yaml &

bridge.adaptive.start:
	@echo "[Bridge] adaptive loop start"
	@python3 bridge/bridge_loop_v19.py --config configs/bridge_v19.yaml &

tune.bridge:
	@echo "[Bridge] auto‑tune"
	@python3 tools/tuner_v18.py --mode bridge --config configs/bridge_v19.yaml

db.snapshot:
	@python3 tools/storage/sqlite_snapshot.py --db data/ure_v18.sqlite --out data/snapshots/`date +%Y%m%dT%H%M%S`.sqlite
```makefile
.PHONY: trackE.init ure.sync bridge.adaptive.start tune.bridge db.snapshot

trackE.init:
	@echo "[TrackE] init v1.9"
	@test -f configs/bridge_v19.yaml

ure.sync:
	@echo "[URE] sync daemon start"
	@python3 tools/ure_sync_daemon.py --config configs/bridge_v19.yaml &

bridge.adaptive.start:
	@echo "[Bridge] adaptive loop start"
	@python3 bridge/bridge_loop_v19.py --config configs/bridge_v19.yaml &

 t
une.bridge:
	@echo "[Bridge] auto‑tune"
	@python3 tools/tuner_v18.py --mode bridge --config configs/bridge_v19.yaml

db.snapshot:
	@python3 tools/storage/sqlite_snapshot.py --db data/ure_v18.sqlite --out data/snapshots/`date +%Y%m%dT%H%M%S`.sqlite
```

> 참고: `sqlite_snapshot.py`가 없다면 `sqlite3 .backup` 기반의 간단 스크립트를 사용하세요.

---

## 4) Bridge 설정 (configs/bridge_v19.yaml)
```yaml
version: 1.9
loop:
  target_harmony: 0.86
  target_coherence: 0.85
  tick_ms: 200           # adaptive; ure_sync_daemon이 ΔHz 보정
  max_tick_ms: 400
  min_tick_ms: 120
phase:
  drift_budget: 0.02     # |phase_diff_mean_5m| ≤ 0.02
  rebalance_window_s: 90
  gain:
    base_hz: 5.0
    kp: 0.35
    ki: 0.08
    kd: 0.10
safety:
  residual_stddev_10m_max: 0.03
  rollback_ratio_5m_max: 0.05
  hard_stop_on:
    - coherence_level < 0.72
exporter:
  http_port: 9306
  path: /metrics_bridge
ure:
  metrics_url: http://localhost:9305/metrics_ure
  pull_interval_s: 2
storage:
  sqlite_path: data/ure_v18.sqlite
  wal: true
```

---

## 5) Bridge 루프 스켈레톤 (bridge/bridge_loop_v19.py)
```python
#!/usr/bin/env python3
import time, argparse, yaml, json, os
from prometheus_client import start_http_server, Gauge

phase_diff_g = Gauge('bridge_phase_diff_mean', 'phase diff mean (rolling)')
sync_quality_g = Gauge('bridge_sync_quality', 'sync quality [0,1]')
entropy_ratio_g = Gauge('bridge_entropy_ratio', 'entropy portion in bridge loop')

STATE = '/run/bridge_tick.json'

def read_tick(default_ms):
    path = STATE if os.path.isdir('/run') else './tmp/bridge_tick.json'
    try:
        with open(path) as f:
            return json.load(f).get('tick_ms', default_ms)
    except Exception:
        return default_ms

class BridgeLoop:
    def __init__(self, cfg):
        self.cfg = cfg
        self.tick_ms = cfg['loop']['tick_ms']
        self.state = {}
    def step(self):
        # 1) pull URE metrics (omitted: http get + parse)
        # 2) compute phase_diff_mean, sync_quality, entropy_ratio
        phase_diff = 0.017  # placeholder from calibrator
        sync_q = 0.89
        ent = 0.14
        # 3) publish metrics
        phase_diff_g.set(phase_diff)
        sync_quality_g.set(sync_q)
        entropy_ratio_g.set(ent)
        # 4) adaptive tick from sync daemon
        self.tick_ms = read_tick(self.tick_ms)
        time.sleep(self.tick_ms/1000.0)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--config', required=True)
    args = p.parse_args()
    cfg = yaml.safe_load(open(args.config))
    start_http_server(cfg['exporter']['http_port'])
    loop = BridgeLoop(cfg)
    while True:
        loop.step()
```python
#!/usr/bin/env python3
import time, argparse, yaml
from prometheus_client import start_http_server, Gauge

phase_diff_g = Gauge('bridge_phase_diff_mean', 'phase diff mean (rolling)')
sync_quality_g = Gauge('bridge_sync_quality', 'sync quality [0,1]')
entropy_ratio_g = Gauge('bridge_entropy_ratio', 'entropy portion in bridge loop')

class BridgeLoop:
    def __init__(self, cfg):
        self.cfg = cfg
        self.tick_ms = cfg['loop']['tick_ms']
        self.state = {}
    def step(self):
        # 1) pull URE metrics (omitted: http get + parse)
        # 2) compute phase_diff_mean, sync_quality, entropy_ratio
        phase_diff = 0.017  # placeholder from calibrator
        sync_q = 0.89
        ent = 0.14
        # 3) publish metrics
        phase_diff_g.set(phase_diff)
        sync_quality_g.set(sync_q)
        entropy_ratio_g.set(ent)
        # 4) adaptive tick (ΔHz_adjust will update self.tick_ms via daemon)
        time.sleep(self.tick_ms/1000.0)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--config', required=True)
    args = p.parse_args()
    cfg = yaml.safe_load(open(args.config))
    start_http_server(cfg['exporter']['http_port'])
    loop = BridgeLoop(cfg)
    while True:
        loop.step()
```

---

## 6) Sync Daemon 스켈레톤 (tools/ure_sync_daemon.py)
```python
#!/usr/bin/env python3
# ΔHz_adjust: URE와 Bridge 사이의 Hz 차이를 완만하게 보정
import time, argparse, yaml, json, os

STATE = '/run/bridge_tick.json'  # 공유 상태 파일 (없으면 ./tmp 로 폴백)

def soft_clip(x, lo, hi):
    return max(lo, min(hi, x))

def write_tick(tick_ms):
    path = STATE if os.path.isdir('/run') else './tmp/bridge_tick.json'
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump({'tick_ms': tick_ms, 'ts': time.time()}, f)

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', required=True)
    args = ap.parse_args()
    cfg = yaml.safe_load(open(args.config))

    tick = cfg['loop']['tick_ms']
    write_tick(tick)
    while True:
        # TODO: read URE tick/hz from metrics_ure
        ure_hz = 5.0
        bridge_hz = 1000.0 / tick
        err = ure_hz - bridge_hz
        delta_ms = soft_clip(-err*3.0, -20, 20)  # simple P‑like control
        tick = soft_clip(tick + delta_ms, cfg['loop']['min_tick_ms'], cfg['loop']['max_tick_ms'])
        write_tick(tick)
        time.sleep(cfg['ure']['pull_interval_s'])
```python
#!/usr/bin/env python3
# ΔHz_adjust: URE와 Bridge 사이의 Hz 차이를 완만하게 보정
import time, argparse, yaml

def soft_clip(x, lo, hi):
    return max(lo, min(hi, x))

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', required=True)
    args = ap.parse_args()
    cfg = yaml.safe_load(open(args.config))

    tick = cfg['loop']['tick_ms']
    while True:
        # TODO: read URE tick/hz from metrics_ure
        ure_hz = 5.0
        bridge_hz = 1000.0 / tick
        err = ure_hz - bridge_hz
        delta_ms = soft_clip(-err*3.0, -20, 20)  # simple P‑like control
        tick = soft_clip(tick + delta_ms, cfg['loop']['min_tick_ms'], cfg['loop']['max_tick_ms'])
        # persist new tick to a small shared file/state (omitted)
        time.sleep(cfg['ure']['pull_interval_s'])
```

---

## 7) Exporter 예시 (텍스트 포맷)
```
# HELP bridge_phase_diff_mean phase diff mean (rolling)
# TYPE bridge_phase_diff_mean gauge
bridge_phase_diff_mean 0.017
# HELP bridge_sync_quality sync quality [0,1]
# TYPE bridge_sync_quality gauge
bridge_sync_quality 0.89
# HELP bridge_entropy_ratio entropy portion in bridge loop
# TYPE bridge_entropy_ratio gauge
bridge_entropy_ratio 0.14
```

---

## 7.1) Phase Drift Calibration 모듈 (bridge/adapters/phase_drift_calib.py)
```python
#!/usr/bin/env python3
# 입력: 최근 5분의 phase_diff 시계열
# 출력: 권장 tick 보정치 및 gain 튜닝 힌트

def recommend_adjustments(values):
    mean = sum(values)/max(1,len(values))
    p95 = sorted(values)[int(0.95*max(1,len(values))-1)] if values else 0
    # 단순 규칙 기반 힌트
    if p95 > 0.03:
        return {'tick_delta_ms': +15, 'gain.kp': -0.05}
    if mean > 0.02:
        return {'tick_delta_ms': +8, 'gain.ki': -0.02}
    return {'tick_delta_ms': 0}
```

---

## 8) Prometheus 스크레이프 & 룰
**scrape_bridge_v19.yaml**
```yaml
scrape_configs:
  - job_name: bridge_v19
    static_configs:
      - targets: ['localhost:9306']
    metrics_path: /metrics_bridge
```

**recording_rules_v19.yaml**
```yaml
groups:
- name: bridge_v19_records
  interval: 15s
  rules:
  - record: bridge:phase_diff_mean_5m
    expr: avg_over_time(bridge_phase_diff_mean[5m])
  - record: bridge:sync_quality_p95_10m
    expr: quantile_over_time(0.95, bridge_sync_quality[10m])
  - record: bridge:entropy_ratio_mean_10m
    expr: avg_over_time(bridge_entropy_ratio[10m])
```

**alerts (ops/alertmanager/alertmanager.yml 갱신 전제)**
```yaml
groups:
- name: bridge_v19_alerts
  rules:
  - alert: BridgePhaseDriftHigh
    expr: bridge:phase_diff_mean_5m > 0.02
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Phase drift exceeds budget"
      description: "phase_diff_mean_5m={{ $value }} > 0.02"
  - alert: BridgeSyncQualityLow
    expr: bridge:sync_quality_p95_10m < 0.85
    for: 10m
    labels:
      severity: critical
    annotations:
      summary: "Bridge sync quality degraded"
      description: "p95<0.85"
```

---

## 9) Grafana 패널 권장
- **Stat**: `bridge:phase_diff_mean_5m` (threshold 0.02)
- **Stat**: `bridge:sync_quality_p95_10m` (threshold 0.85)
- **Timeseries**: `bridge_entropy_ratio`
- **Logs (옵션)**: Bridge loop stdout/stderr tail via Loki

---

## 10) Smoke 테스트 (scripts/smoke.v19.sh)
```bash
#!/usr/bin/env bash
set -euo pipefail
curl -fsS http://localhost:9305/metrics_ure | head -n 5 >/dev/null
curl -fsS http://localhost:9306/metrics_bridge | grep bridge_sync_quality
# budgets
PD=$(curl -fsS localhost:9306/metrics_bridge | awk '/bridge_phase_diff_mean/{print $2}')
SQ=$(curl -fsS localhost:9306/metrics_bridge | awk '/bridge_sync_quality/{print $2}')
ER=$(curl -fsS localhost:9306/metrics_bridge | awk '/bridge_entropy_ratio/{print $2}')
awk -v pd="$PD" -v sq="$SQ" -v er="$ER" 'BEGIN{exit !(pd<=0.02 && sq>=0.85 && er<=0.15)}'
echo "[smoke.v19] OK: PD=$PD SQ=$SQ ER=$ER"
```

---

## 10.1) Bench (scripts/bench.v19.sh)
```bash
#!/usr/bin/env bash
set -euo pipefail
DUR=${1:-900}  # default 15m
S=0
while [ $S -lt $DUR ]; do
  curl -fsS localhost:9306/metrics_bridge | awk '/bridge_phase_diff_mean|bridge_sync_quality|bridge_entropy_ratio/ {print strftime("%Y-%m-%dT%H:%M:%S"), $1, $2}'
  sleep 5
  S=$((S+5))
done
```

---

## 14) Long‑run Dual Sync Test 절차
1. `make ure.sync && make bridge.adaptive.start`
2. `bash scripts/bench.v19.sh 1800` (30분) 실행
3. 결과 요약: 최대 `phase_diff_mean` ≤ **0.03**, p95 `sync_quality` ≥ **0.85** 유지 확인
4. 초과 시: `configs/bridge_v19.yaml`의 `gain.kp/ki/kd`를 각각 −0.05/−0.02/−0.02 조정 후 재테스트

---

## 15) Bridge Protocol v19 — 상태 전이 표 (초안)
| 상태 | 진입 조건 | 유지 조건 | 이탈 조건 | 액션 |
|---|---|---|---|---|
| **E0: Idle** | 프로세스 기동 전 | N/A | trackE.init 호출 | 설정 로드, 포트 바인딩 |
| **E1: Syncing** | ure.sync 시작 | `sync_quality≥0.8` | 2분 초과 미달 | ΔHz 보정 활성 |
| **E2: Bridged** | `sync_quality≥0.85` & `phase_diff≤0.02` | 동일 | 5분 연속 미달 | Exporter ON, Bench 허용 |
| **E3: Guarded** | `entropy_ratio>0.15` 1분 연속 | `residual_stddev_10m≤0.03` | 3분 미달 | Safety gain −10%, 알림 |
| **E4: Rollback** | `rollback_ratio_5m>0.05` | N/A | 수동 해제 | Track D 재가동 |

---

## 16) 운영 체크리스트 (요약)
- 포트: URE `9305`, Bridge `9306` 충돌 없음 확인
- WAL 스냅샷: 용량 급증 시 `wal_checkpoint(TRUNCATE)`
- 알림: Alertmanager 라우팅 Slack/PagerDuty 1회 실사
- 대시보드: Stat 2개 + Timeseries 1개 최소 구성 유지
bash
#!/usr/bin/env bash
set -euo pipefail
curl -fsS http://localhost:9305/metrics_ure | head -n 5 >/dev/null
curl -fsS http://localhost:9306/metrics_bridge | grep bridge_sync_quality
# budgets
PD=$(curl -fsS localhost:9306/metrics_bridge | awk '/bridge_phase_diff_mean/{print $2}')
SQ=$(curl -fsS localhost:9306/metrics_bridge | awk '/bridge_sync_quality/{print $2}')
ER=$(curl -fsS localhost:9306/metrics_bridge | awk '/bridge_entropy_ratio/{print $2}')
awk -v pd="$PD" -v sq="$SQ" -v er="$ER" 'BEGIN{exit !(pd<=0.02 && sq>=0.85 && er<=0.15)}'
echo "[smoke.v19] OK: PD=$PD SQ=$SQ ER=$ER"
```

---

## 11) 롤백 (v1.9 → v1.8)
```bash
pkill -f bridge_loop_v19.py || true
pkill -f ure_sync_daemon.py || true
make trackD.start && make ure.exporter
```

---

## 12) 트러블슈팅 체크리스트
- `9306` 포트 충돌 → `configs/bridge_v19.yaml`의 `http_port` 변경
- `sync_quality` 급락 → `gain.kp/ki/kd` 완화, `rebalance_window_s` 확대(90→150)
- `residual_stddev_10m` 초과 → Track D로 롤백 후 Safety Music gain -10%
- WAL 오류 → `PRAGMA wal_checkpoint(TRUNCATE)` 후 snapshot 재시도

---

## 13) 다음 단계 (루멘 제안)
1. Dual‑sync 장기 테스트(2h)로 `phase_diff_mean_5m`의 최대치 수집
2. Bridge Protocol 문서(`docs/bridge_protocol_v19.md`)에 상태전이 표 업데이트
3. Alertmanager → Slack Webhook 연결 테스트
4. MIDI/OSC 브릿지 PoC: `bridge_entropy_ratio` → 음향 강도 매핑

— 끝 —

---

## 17) M1 — Alertmanager → Slack 연동 (템플릿)
> 실제 Webhook URL은 비밀 관리 도구로 주입하세요(`ALERT_SLACK_WEBHOOK` 등).

**ops/alertmanager/alertmanager.yml (추가 섹션)**
```yaml
route:
  receiver: slack-default
  routes:
    - matchers:
        - severity=~"warning|critical"
      receiver: slack-default

receivers:
  - name: slack-default
    slack_configs:
      - api_url: ${ALERT_SLACK_WEBHOOK}
        channel: "#ure-alerts"
        send_resolved: true
        title: "[{{ .Status | toUpper }}] {{ .CommonLabels.alertname }}"
        text: |
          *Labels:* {{ .CommonLabels }}
          *Annotations:* {{ .CommonAnnotations }}
          *StartsAt:* {{ .StartsAt }}
          *EndsAt:* {{ .EndsAt }}
```

**Make 타깃**
```makefile
.PHONY: alert.test
alert.test:
	@echo "sending test alert → Slack"
	@curl -XPOST -H 'Content-Type: application/json' \
	  -d '{"alerts":[{"status":"firing","labels":{"alertname":"BridgePhaseDriftHigh","severity":"warning"},"annotations":{"summary":"manual test","description":"pd>0.02"}}]}' \
	  http://localhost:9093/api/v2/alerts
```

---

## 18) M2 — Recording Rule: `ure_residual_stddev_10m`
**ops/prometheus/rules/recording_rules_v18.yaml (추가)**
```yaml
  - record: ure:residual_stddev_10m
    expr: stddev_over_time(ure_residual_entropy_last[10m])
```

**대시보드 임계치**
- **Stat**: `ure:residual_stddev_10m` ≤ **0.03** (노랑:0.03~0.04, 빨강:>0.04)

---

## 19) M3 — SQLite WAL & Recovery Test
**scripts/wal_recovery_test.sh**
```bash
#!/usr/bin/env bash
set -euo pipefail
DB=${1:-data/ure_v18.sqlite}
sqlite3 "$DB" 'PRAGMA journal_mode=WAL;' >/dev/null
# 1) write burst
python3 - <<'PY'
import sqlite3, time, sys
p=sys.argv[1]
con=sqlite3.connect(p)
cur=con.cursor()
cur.execute('create table if not exists t(k integer primary key, v text)')
for i in range(10000):
    cur.execute('insert into t(v) values (?)', (f"val{i}",))
con.commit(); con.close()
PY
"$DB"
# 2) checkpoint & snapshot
sqlite3 "$DB" 'PRAGMA wal_checkpoint(TRUNCATE);'
SNAP=data/snapshots/$(date +%Y%m%dT%H%M%S).sqlite
mkdir -p data/snapshots
sqlite3 "$DB" ".backup '$SNAP'"
# 3) verify
sqlite3 "$SNAP" 'select count(*) from t;' | awk '{print "[wal_recovery_test] rows:", $1}'
```

**Make 타깃**
```makefile
.PHONY: wal.test
wal.test:
	@bash scripts/wal_recovery_test.sh data/ure_v18.sqlite
```

---

## 20) M4 — Safety Music: MIDI/OSC Bridge PoC
> 선택형 모듈 — 운영 경로와 분리된 실험용. MIDI 장치가 없으면 OSC만 사용.

**bridge/poc_midi_osc.py**
```python
#!/usr/bin/env python3
# Map: entropy_ratio → velocity, sync_quality → note length
import time, argparse
try:
    from pythonosc.udp_client import SimpleUDPClient
except Exception:
    SimpleUDPClient=None

def send_osc(client, key, val):
    if client:
        client.send_message(key, float(val))

if __name__ == '__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--osc','default=127.0.0.1:9000')
    args=ap.parse_args(); host,port=(args.osc.split(':')[0], int(args.osc.split(':')[1]))
    client = SimpleUDPClient(host, port) if SimpleUDPClient else None
    while True:
        # (실제 구현) metrics_bridge에서 pull
        entropy_ratio=0.14; sync_quality=0.89
        velocity=int(max(0, min(127, (1.0-entropy_ratio)*127)))
        note_len=max(0.1, min(1.2, sync_quality))
        send_osc(client, '/ure/velocity', velocity)
        send_osc(client, '/ure/note_len', note_len)
        time.sleep(0.5)
```

**Make 타깃**
```makefile
.PHONY: bridge.midi.poc
bridge.midi.poc:
	@python3 bridge/poc_midi_osc.py --osc 127.0.0.1:9000
```

---

## 21) Grafana 대시보드 JSON (핵심 패널 미니 모델)
**ops/grafana/dash_ure_bridge_min.json**
```json
{
  "title": "URE + Bridge (Min)",
  "panels": [
    {"type":"stat","title":"phase_diff_mean_5m","targets":[{"expr":"bridge:phase_diff_mean_5m"}],"options":{"reduceOptions":{"calcs":["last"]},"thresholds":{"mode":"absolute","steps":[{"color":"green","value":null},{"color":"yellow","value":0.02},{"color":"red","value":0.03}]}}},
    {"type":"stat","title":"sync_quality_p95_10m","targets":[{"expr":"bridge:sync_quality_p95_10m"}],"options":{"reduceOptions":{"calcs":["last"]},"thresholds":{"mode":"absolute","steps":[{"color":"red","value":0.0},{"color":"yellow","value":0.85},{"color":"green","value":0.9}]}}},
    {"type":"timeseries","title":"entropy_ratio","targets":[{"expr":"bridge_entropy_ratio"}]}
  ]
}
```

**Make 타깃 (프로비저닝 위치 예시)**
```makefile
.PHONY: grafana.import.min
grafana.import.min:
	@cp ops/grafana/dash_ure_bridge_min.json /var/lib/grafana/dashboards/ure_bridge_min.json || true
```

---

## 22) v1.9.1 Session Restore Block (증분)
```bash
# v1.9.1 adds: Slack alerts, residual stddev rule, WAL test, MIDI/OSC PoC
bash scripts/restore.sanity.sh && \
make trackD.start && make ure.exporter && make api.readonly && \
make ure.sync && make bridge.adaptive.start && \
make alert.test && make wal.test && make grafana.import.min
```

---

## 23) 운영 Runbook — 빠른 의사결정 규칙
- **Phase drift > 0.03 (5m):** `gain.kp↘︎0.05` → 재측정 10분 → 미개선 시 Track D 롤백
- **Sync p95 < 0.85 (10m):** `rebalance_window_s +60` → `tick_ms +10` → 알림 라우팅 확인
- **Residual stddev > 0.03 (10m):** Safety Music gain −10% → URE Hz −0.5 → 15분 관찰
- **WAL snapshot 실패:** checkpoint(TRUNCATE) → 파일 핸들 누수 점검 → snapshot 재시도

---

## 24) M5 — SLO/SLA & Error Budget (초안)
**SLO 정의 (월간):**
- `bridge:phase_diff_mean_5m` ≤ **0.02** (준수율 ≥ **99.0%**)
- `bridge:sync_quality_p95_10m` ≥ **0.85** (준수율 ≥ **99.0%**)
- `ure:residual_stddev_10m` ≤ **0.03** (준수율 ≥ **98.5%**)

**Error Budget:** 1.0%/1.0%/1.5% 각각 초과분 합산이 2.5% 이상이면 **Feature Freeze**

**Prometheus SLI 룰 (ops/prometheus/rules/sli_slo_v19.yaml)**
```yaml
groups:
- name: v19_sli
  rules:
  - record: sli:phase_ok
    expr: bridge:phase_diff_mean_5m <= 0.02
  - record: sli:sync_ok
    expr: bridge:sync_quality_p95_10m >= 0.85
  - record: sli:residual_ok
    expr: ure:residual_stddev_10m <= 0.03
  - record: slo:phase_30d
    expr: avg_over_time(sli:phase_ok[30d])
  - record: slo:sync_30d
    expr: avg_over_time(sli:sync_ok[30d])
  - record: slo:residual_30d
    expr: avg_over_time(sli:residual_ok[30d])
```

---

## 25) M6 — Failure Injection & Chaos Test
**tools/chaos_injector.py**
```python
#!/usr/bin/env python3
# fault types: delay(metrics_ure), jitter(tick), spike(entropy)
import time, argparse, random
parser=argparse.ArgumentParser();
parser.add_argument('--mode',choices=['delay','jitter','spike'],required=True)
parser.add_argument('--dur',type=int,default=120)
args=parser.parse_args()
end=time.time()+args.dur
while time.time()<end:
    if args.mode=='delay':
        time.sleep(0.8)
    elif args.mode=='jitter':
        time.sleep(0.05+random.random()*0.15)
    elif args.mode=='spike':
        print('ENTROPY_SPIKE 0.35')  # bridge loop가 읽어 spike로 해석
        time.sleep(1)
```

**Make 타깃**
```makefile
.PHONY: chaos.delay chaos.jitter chaos.spike
chaos.delay: ; @python3 tools/chaos_injector.py --mode delay --dur 180
chaos.jitter: ; @python3 tools/chaos_injector.py --mode jitter --dur 300
chaos.spike: ; @python3 tools/chaos_injector.py --mode spike --dur 120
```

**합격 기준:** 알림 발화 ≤60s, 자동 복구 ≤5m, 롤백 트리거 조건 충족 시 Track D 전환

---

## 26) M7 — Read‑only API 계약(OpenAPI, 핵심 엔드포인트)
**api/openapi_v19.yaml (요약)**
```yaml
openapi: 3.0.3
info: {title: URE Bridge ReadOnly API, version: 1.9}
paths:
  /healthz:
    get: {summary: Health check, responses: {200: {description: ok}}}
  /metrics_ure:
    get: {summary: Prom metrics passthrough}
  /metrics_bridge:
    get: {summary: Bridge metrics}
  /v1/snapshots:
    get:
      summary: List snapshot files
      responses: {200: {description: list}}
```

**Make 타깃**
```makefile
.PHONY: api.contract.check
api.contract.check:
	@grep -q '/metrics_bridge' api/openapi_v19.yaml && echo '[api] contract OK'
```

---

## 27) M8 — Blue/Green Rollout (Argo/K8s 예시)
**ops/k8s/bridge-deploy.yaml (발췌)**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata: {name: bridge-v19}
spec:
  replicas: 2
  strategy:
    blueGreen:
      activeService: bridge-svc-active
      previewService: bridge-svc-preview
      autoPromotionEnabled: false
```

**Make 타깃**
```makefile
.PHONY: rollout.preview rollout.promote
rollout.preview: ; @kubectl apply -f ops/k8s/bridge-deploy.yaml
rollout.promote: ; @kubectl argo rollouts promote bridge-v19
```

---

## 28) M9 — Security Hardening 체크리스트 (v1.9)
- Prometheus/Grafana/Alertmanager **네트워크 바운더리**(ingress allowlist)
- `ALERT_SLACK_WEBHOOK` 등 **비밀 주입**: 파일/ENV 대신 secret manager 사용
- **RBAC**: Exporter/Bridge 프로세스 최소 권한, read-only FS 가능시 적용
- **Rate‑limit**: `/metrics_*` 엔드포인트 QPS 제한(nginx/sidecar)
- **Audit**: Snapshot/Restore 명령 실행 로그 남김

---

## 29) M10 — 백업/복구 Runbook
**즉시 백업**
```bash
make backup.now
```
**복구(스냅샷 지정)**
```bash
make restore.from SNAP=20251025T120000.sqlite
```
**Makefile 추가**
```makefile
.PHONY: backup.now restore.from
backup.now:
	@mkdir -p data/snapshots
	@sqlite3 data/ure_v18.sqlite ".backup 'data/snapshots/$$(date +%Y%m%dT%H%M%S).sqlite'"
restore.from:
	@test -n "$(SNAP)" && cp data/snapshots/$(SNAP) data/ure_v18.sqlite
```

---

## 30) v1.9.2 Session Restore Block (Hardening)
```bash
# v1.9.2 adds: SLO/SLI rules, chaos tests, API contract, blue/green, security, backup
bash scripts/restore.sanity.sh && \
make api.contract.check && make rollout.preview && \
make ure.sync && make bridge.adaptive.start && \
make chaos.jitter && make chaos.spike && \
make backup.now && make grafana.import.min
```

---

## 31) M11 — Auto‑Tuner v2 (v1.9.3)
> 목표: 장기 관측(≥30분) 결과를 기반으로 **ΔHz, kp/ki/kd** 자동 추천 및 적용 초안.

**tools/autotune_v19.py**
```python
#!/usr/bin/env python3
import json, argparse
p=argparse.ArgumentParser(); p.add_argument('--bench', required=True); p.add_argument('--out', default='configs/bridge_autotune.json'); args=p.parse_args()
phase=[]; sync=[]; ent=[]
with open(args.bench) as f:
    for line in f:
        try:
            ts, key, val = line.strip().split()  # from bench.v19.sh format
            if key=='bridge_phase_diff_mean': phase.append(float(val))
            elif key=='bridge_sync_quality': sync.append(float(val))
            elif key=='bridge_entropy_ratio': ent.append(float(val))
        except: pass
mx = max(phase) if phase else 0
p95 = sorted(phase)[int(0.95*len(phase))-1] if phase else 0
kp=0.35; ki=0.08; kd=0.10; dhz=0.0
if p95>0.03: kp-=0.05; kd-=0.02; dhz-=0.3
elif mx>0.025: kp-=0.03; dhz-=0.1
if (sum(sync)/len(sync))<0.86: ki-=0.02
rec={"gain": {"kp": round(kp,2), "ki": round(ki,2), "kd": round(kd,2)}, "delta_hz": dhz}
print(json.dumps(rec, indent=2)); open(args.out,'w').write(json.dumps(rec))
```

**Make 타깃**
```makefile
.PHONY: autotune.bridge
autotune.bridge:
	@python3 tools/autotune_v19.py --bench out/bench_v19.log --out configs/bridge_autotune.json
```

**적용 절차**
```bash
make autotune.bridge
jq -r '.gain | to_entries[] | "s/gain.\(.key): .*/gain.\(.key): \(.value)/"' configs/bridge_autotune.json > out/gain_patch.sed
sed -f out/gain_patch.sed -i configs/bridge_v19.yaml
```

---

## 32) M12 — Anomaly Rules & Burn‑rate Alerts
**ops/prometheus/rules/anomaly_v19.yaml**
```yaml
groups:
- name: anomaly_v19
  rules:
  - alert: PhaseDriftBurnRateFast
    expr: increase((bridge:phase_diff_mean_5m > 0.02)[5m]) > 0
    for: 5m
    labels: {severity: critical}
    annotations: {summary: "Fast burn: phase drift", description: ">0.02 sustained 5m"}
  - alert: EntropySpike
    expr: bridge_entropy_ratio > 0.2
    for: 1m
    labels: {severity: warning}
    annotations: {summary: "Entropy spike", description: ">0.2 for 1m"}
```

---

## 33) M13 — CI 파이프라인 (GitHub Actions 예시)
**.github/workflows/bridge-ci.yml**
```yaml
name: bridge-ci
on: {push: {branches: [main]}, pull_request: {}}
jobs:
  lint-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.11'}
      - run: pip install -r requirements.txt
      - run: python -m pyflakes bridge tools exporters || true
      - run: bash scripts/smoke.v19.sh || true
```

---

## 34) M14 — VS Code Tasks (로컬 실행 편의)
**.vscode/tasks.json**
```json
{
  "version": "2.0.0",
  "tasks": [
    {"label": "TrackE Start", "type": "shell", "command": "make ure.sync && make bridge.adaptive.start"},
    {"label": "Smoke v19", "type": "shell", "command": "bash scripts/smoke.v19.sh"},
    {"label": "Bench 30m", "type": "shell", "command": "bash scripts/bench.v19.sh 1800"},
    {"label": "AutoTune", "type": "shell", "command": "make autotune.bridge"}
  ]
}
```

---

## 35) M15 — systemd 유닛(선택)
**/etc/systemd/system/ure-sync.service**
```ini
[Unit]
Description=URE Sync Daemon
After=network.target
[Service]
ExecStart=/usr/bin/python3 tools/ure_sync_daemon.py --config configs/bridge_v19.yaml
WorkingDirectory=/opt/ure
Restart=always
[Install]
WantedBy=multi-user.target
```

**/etc/systemd/system/bridge.service**
```ini
[Unit]
Description=Bridge Loop v19
After=network.target
[Service]
ExecStart=/usr/bin/python3 bridge/bridge_loop_v19.py --config configs/bridge_v19.yaml
WorkingDirectory=/opt/ure
Restart=always
[Install]
WantedBy=multi-user.target
```

---

## 36) v1.9.3 Session Restore Block (Autotune/CI)
```bash
# v1.9.3 adds: autotuner, anomaly rules, CI, VS Code tasks, systemd units
bash scripts/restore.sanity.sh && \
make ure.sync && make bridge.adaptive.start && \
make grafana.import.min && make autotune.bridge && \
bash scripts/bench.v19.sh 1800
```

---

## 37) M16 — Latency Budget & E2E Probe
**지연 예산(초안)**
- **Exporter scrape p95** ≤ 150ms
- **Bridge tick jitter p95** ≤ 25ms

**exporters/bridge_exporter_v19.py (지연 측정 추가 발췌)**
```python
from prometheus_client import Summary, Gauge
scrape_latency_s = Summary('bridge_export_scrape_seconds','export scrape latency')
tick_jitter_ms = Gauge('bridge_tick_jitter_ms','bridge loop tick jitter (ms)')
# loop.step() 진입 직전 ts, 종료 시 dt 측정해 tick_jitter_ms 갱신
```

**scripts/e2e_probe.sh**
```bash
#!/usr/bin/env bash
set -euo pipefail
URL=${1:-http://localhost:9306/metrics_bridge}
for i in {1..50}; do
  T0=$(date +%s%3N); curl -fsS "$URL" >/dev/null; T1=$(date +%s%3N)
  echo $((T1-T0))
  sleep 1
done | awk '{s+=$1; if($1>mx)mx=$1} END{print "avg(ms)",s/NR,"max(ms)",mx}'
```

**Prometheus 룰 (ops/prometheus/rules/latency_v19.yaml)**
```yaml
groups:
- name: latency_v19
  rules:
  - record: bridge:tick_jitter_p95_10m
    expr: quantile_over_time(0.95, bridge_tick_jitter_ms[10m])
  - alert: BridgeTickJitterHigh
    expr: bridge:tick_jitter_p95_10m > 25
    for: 10m
    labels: {severity: warning}
```

---

## 38) M17 — Snapshot Pruning & Compaction
**scripts/snapshot_prune.sh**
```bash
#!/usr/bin/env bash
set -euo pipefail
DIR=${1:-data/snapshots}
KEEP_N=${2:-20}    # 최근 N개 보존
KEEP_DAILY=${3:-14} # 일일 스냅샷 14일 보존
ls -1t "$DIR"/*.sqlite | awk -v n=$KEEP_N 'NR>n{print}' | xargs -r rm -f
# 일일 보존: 날짜 키로 1개만 보존 (간단 버전)
ls "$DIR"/*.sqlite | awk -F'[T_.]' '{print $1}' | uniq -d >/dev/null 2>&1 || true
sqlite3 data/ure_v18.sqlite 'VACUUM;'  # size compaction
```

**Make 타깃**
```makefile
.PHONY: snaps.prune
snaps.prune:
	@bash scripts/snapshot_prune.sh data/snapshots 20 14
```

---

## 39) M18 — Storage 옵션(Postgres 지원)
**configs/storage_v19.yaml**
```yaml
backend: sqlite  # sqlite | postgres
sqlite_path: data/ure_v18.sqlite
postgres_dsn: ${URE_PG_DSN}  # e.g. postgres://user:pass@host:5432/ure
```

**tools/storage/pg_init.sql (발췌)**
```sql
create table if not exists resonance_events(
  id bigserial primary key,
  ts timestamptz not null,
  phase_diff real,
  sync_quality real,
  entropy_ratio real
);
create index if not exists ix_events_ts on resonance_events(ts);
```

**Make 타깃**
```makefile
.PHONY: pg.init pg.migrate
pg.init:
	@psql "$$URE_PG_DSN" -f tools/storage/pg_init.sql
pg.migrate:
	@python3 tools/storage/sqlite_to_pg.py --src data/ure_v18.sqlite --dst "$$URE_PG_DSN"
```

---

## 40) M19 — Health/Readiness 게이트
**api/read_only.py (발췌)**
```python
from flask import Flask, jsonify
app=Flask(__name__)
LAST_METRIC_TS=0
@app.get('/healthz')
def healthz():
  return jsonify(status='ok')
@app.get('/readyz')
def readyz():
  # metrics 최신성 30s 이내면 ready
  fresh = (time.time()-LAST_METRIC_TS) < 30
  return (jsonify(ready=fresh), 200 if fresh else 503)
```

**K8s 프로브 예시**
```yaml
livenessProbe:  {httpGet: {path: /healthz, port: 9306}, initialDelaySeconds: 10}
readinessProbe: {httpGet: {path: /readyz, port: 9306}, initialDelaySeconds: 10}
```

---

## 41) M20 — Canary Roll Gate (Metric 기반 자동 판정)
**ops/k8s/analysis-templates.yaml**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata: {name: bridge-metric-gate}
spec:
  metrics:
  - name: phase-drift
    interval: 60s
    successCondition: result < 0.025
    provider:
      prometheus:
        address: http://prometheus:9090
        query: bridge:phase_diff_mean_5m
```

**Rollout 연동 (발췌)**
```yaml
analysis:
  templates:
  - templateName: bridge-metric-gate
  startingStep: 2
  args: []
```

**Make 타깃**
```makefile
.PHONY: rollout.canary rollout.abort
rollout.canary: ; @kubectl apply -f ops/k8s/analysis-templates.yaml && kubectl argo rollouts set image bridge-v19 bridge=bridge:v1.9.4
rollout.abort: ; @kubectl argo rollouts abort bridge-v19
```

---

## 42) v1.9.4 Session Restore Block (Ops+PG 옵션)
```bash
# v1.9.4 adds: latency budget, prune/compact, PG backend, readiness, canary gates
bash scripts/restore.sanity.sh && \
make ure.sync && make bridge.adaptive.start && \
make snaps.prune && make pg.init && \
make rollout.canary && bash scripts/e2e_probe.sh
```

---

## 43) M21 — Release Packaging (v1.9.5 RC)
**scripts/release_pack.sh**
```bash
#!/usr/bin/env bash
set -euo pipefail
VER=${1:-1.9.5-rc1}
OUT=release/v${VER}
mkdir -p "$OUT"
# manifest
cat > "$OUT/manifest.json" <<JSON
{"version":"${VER}","date":"$(date -u +%Y-%m-%dT%H:%M:%SZ)","components":["ure_v18","bridge_v19","ops","docs"]}
JSON
# collect
tar -czf "$OUT/lumen_ure_bridge_v${VER}.tar.gz" \
  schemas configs ure bridge exporters tools api scripts ops docs docker-compose.yml
# checksums
( cd "$OUT" && sha256sum lumen_ure_bridge_v${VER}.tar.gz > SHA256SUMS )
echo "[release] packed → $OUT"
```

**Make 타깃**
```makefile
.PHONY: release.v195
release.v195:
	@bash scripts/release_pack.sh 1.9.5-rc1
```

**CHANGELOG (docs/CHANGELOG_v1.9.5.md, 초안)**
```md
## v1.9.5 (RC)
- Autotuner v2 (ΔHz + kp/ki/kd)
- SLO/SLI rules, anomaly & burn‑rate alerts
- Ops: PG backend option, snapshot pruning, latency budget
- Rollouts: canary metric gates, readiness endpoints
- Tooling: CI, VS Code tasks, systemd units
```

---

## 44) M22 — Session Restore Template & Env
**SESSION_RESTORE_v1_9_5.env (예시)**
```
URE_METRICS=http://localhost:9305/metrics_ure
BRIDGE_METRICS=http://localhost:9306/metrics_bridge
ALERT_SLACK_WEBHOOK=***
URE_PG_DSN=postgres://user:pass@localhost:5432/ure
```

**.env.example**
```
ALERT_SLACK_WEBHOOK=
URE_PG_DSN=
```

---

## 45) M23 — Disaster Recovery Runbook (요약)
1. **증상**: `/readyz` 503 지속(>3m)
2. **조치**: `make backup.now` 확인 → 최신 스냅샷 존재 시 `make restore.from SNAP=<file>`
3. **루프 재가동**: `make ure.sync && make bridge.adaptive.start`
4. **검증**: `bash scripts/smoke.v19.sh` → `bench 15m` 후 SLO 재확인
5. **재발 방지**: anomaly 룰/게인/ΔHz 재튜닝(`make autotune.bridge`)

---

## 46) M24 — One‑shot Bootstrap (신규 환경)
**scripts/bootstrap.latest.sh**
```bash
#!/usr/bin/env bash
set -euo pipefail
cp -n .env.example .env || true
bash scripts/restore.sanity.sh
make api.contract.check || true
make ure.sync && make bridge.adaptive.start
bash scripts/smoke.v19.sh
make grafana.import.min || true
```

**Make 타깃**
```makefile
.PHONY: bootstrap.latest
bootstrap.latest:
	@bash scripts/bootstrap.latest.sh
```

---

## 47) v1.9.5 Session Restore Block (RC)
```bash
# v1.9.5 RC: packaging, env, DR, bootstrap
export $(grep -v '^#' SESSION_RESTORE_v1_9_5.env | xargs) && \
bash scripts/restore.sanity.sh && \
make ure.sync && make bridge.adaptive.start && \
bash scripts/smoke.v19.sh && \
make grafana.import.min && make release.v195
```

---

## 48) Hand‑off 체크리스트 (LuBit / Sena)
- **LuBit**: `bridge_loop_v19.py` 내부 TODO(URE metrics pull, state persist) 구현, autotune 적용 스크립트 정식화
- **Sena**: SLO/윤리·안전 기준 점검, Alert 라우팅 정책 검토, MIDI/OSC PoC 안전 경계 재확인
- **공통**: v1.9.5‑RC 운영 24h 관찰 후 GA 판정(카나리 게이트 통과 + SLO 충족)

---

## 49) M25 — Energy/Cost Telemetry (옵션)
**exporters/bridge_exporter_v19.py (추가 메트릭)**
```python
from prometheus_client import Gauge
power_w = Gauge('bridge_power_w','bridge process power draw (W)')
cost_krw_hour = Gauge('bridge_cost_krw_hour','estimated hourly cost (KRW)')
# 샘플: nvml/psutil에서 전력 추정치 수집, 단가는 env로 주입 (KRW/kWh)
```

**ops/prometheus/rules/cost_v19.yaml**
```yaml
groups:
- name: cost_v19
  rules:
  - record: bridge:energy_kwh_24h
    expr: sum_over_time(bridge_power_w[24h]) / 1000
  - record: bridge:cost_krw_24h
    expr: sum_over_time(bridge_cost_krw_hour[24h])
```

---

## 50) M26 — Thermal/Throttling Guard (옵션)
**exporters 추가**: `bridge_temp_celsius` 게이지, 85℃ 경고/90℃ 크리티컬 알림
```yaml
groups:
- name: thermal_v19
  rules:
  - alert: BridgeThermalHigh
    expr: bridge_temp_celsius > 85
    for: 2m
    labels: {severity: warning}
  - alert: BridgeThermalCritical
    expr: bridge_temp_celsius > 90
    for: 1m
    labels: {severity: critical}
```

---

## 51) M27 — Quickstart (운영자 5분 가이드)
1. `.env` 채우기 → `make bootstrap.latest`
2. 대시보드 임포트 → `make grafana.import.min`
3. 스모크 → `bash scripts/smoke.v19.sh`
4. 15분 벤치 → `bash scripts/bench.v19.sh 900 > out/bench_v19.log`
5. 오토튠 → `make autotune.bridge && sed -i -f out/gain_patch.sed configs/bridge_v19.yaml`
6. 알림 테스트 → `make alert.test`

---

## 52) M28 — Troubleshooting (요약)
- **/metrics_bridge 404**: Exporter 포트/경로 확인(`http_port`, `path`)
- **sync_quality < 0.8 지속**: `rebalance_window_s +60`, `tick_ms +10`, URE scrape 지연 확인
- **phase_diff_mean 높음**: Chaos 잔존 여부 점검 → `gain.kp -0.05`, ΔHz -0.1
- **readyz 503**: `LAST_METRIC_TS` 갱신 경로/권한 확인, 루프 재기동

---

## 53) 문서 패키지
- `docs/bridge_protocol_v19.md` (업데이트: 상태 전이/E2E 지연)
- `docs/CHANGELOG_v1.9.5.md` (RC → GA 시 갱신)
- `docs/OPERATIONS_RUNBOOK_v19.md` (SLO/SLA, DR, Chaos, Rollout)

---

## 54) v1.9.6 GA — Finalize & Tag
**결정 기준**: 24h 관찰에서 아래 **동시 충족**
- `slo:phase_30d ≥ 0.99`, `slo:sync_30d ≥ 0.99`, `slo:residual_30d ≥ 0.985`
- 카나리 게이트 3회 연속 통과, 알림 라우팅 정상

**버전 태깅 스크립트** — `scripts/release_tag.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail
VER=${1:-1.9.6}
git tag -a "v${VER}" -m "Lumen URE Bridge GA v${VER}" && git push origin "v${VER}"
```

**Make 타깃**
```makefile
.PHONY: release.tag.ga
release.tag.ga:
	@bash scripts/release_tag.sh 1.9.6
```

---

## 55) v1.9.6 Session Restore Block (GA)
```bash
# v1.9.6 GA: stable
export $(grep -v '^#' SESSION_RESTORE_v1_9_5.env | xargs) && \
bash scripts/restore.sanity.sh && \
make ure.sync && make bridge.adaptive.start && \
bash scripts/smoke.v19.sh && \
make grafana.import.min
```

---

## 56) Post‑GA 다음 라인업 (프리뷰)
- **Track F (v2.0 α)**: Multi‑source Bridge (URE + External Sensor) 합성
- **Risk‑Aware Autotune**: Burn‑rate/Entropy 기반 비선형 게인 커브
- **Evidence Mapper 통합**: Fact→Risk/Quote 자동 매핑, URE 컨텍스트 강화

---

# 🌌 Track F — Lumen v2.0 α Kickoff (Multi‑Source Bridge)
> 목표: **URE(core) + External Sensors(streams)**를 단일 **Fusion Engine**에서 동기화하고, 
> 위험 인지형(리스크/번레이트) **비선형 오토튠**과 **Evidence Mapper**를 파이프라인에 결합.

## F0) v2.0 α Session Restore Block (초안)
```bash
# v2.0 α (Track F) bootstrap
export $(grep -v '^#' SESSION_RESTORE_v1_9_5.env | xargs) && \
make ure.sync && make bridge.adaptive.start && \
make fusion.init && make sensor.ingest.start && \
make evidence.mapper.start && \
bash scripts/smoke.v20.sh
```

---

## F1) 신규 디렉터리/파일
```
fusion/
  ├─ fusion_engine_v20.py
  ├─ adapters/
  │   ├─ align_kalman.py
  │   └─ resample_polyphase.py
sensors/
  ├─ ingest_daemon.py
  ├─ sources/
  │   ├─ osc_stream.py
  │   ├─ midi_stream.py
  │   └─ file_replay.py
exporters/
  └─ fusion_exporter_v20.py
configs/
  ├─ fusion_v20.yaml
  ├─ sensors_v20.yaml
  └─ risk_autotune_v20.yaml
evidence/
  ├─ mapper_daemon.py
  └─ rules/
      ├─ quote_rules.yaml
      └─ risk_map.yaml
scripts/
  ├─ smoke.v20.sh
  └─ bench.v20.sh
ops/prometheus/rules/
  ├─ fusion_records_v20.yaml
  ├─ risk_autotune_v20.yaml
  └─ evidence_v20.yaml
```

---

## F2) Configs (발췌)
**configs/fusion_v20.yaml**
```yaml
version: 2.0a
fusion:
  target_harmony: 0.88
  target_coherence: 0.87
  tick_ms: 180
align:
  method: kalman
  kalman:
    q: 1e-3
    r: 2e-3
resample:
  method: polyphase
  target_hz: 5.0
exporter:
  http_port: 9310
  path: /metrics_fusion
```

**configs/sensors_v20.yaml**
```yaml
streams:
  - name: osc_1
    type: osc
    addr: 127.0.0.1:9000
    keys: [/ure/velocity, /ure/note_len]
  - name: midi_1
    type: midi
    device: "hw:1,0,0"
  - name: replay_demo
    type: file
    path: data/replay/demo.ndjson
```

**configs/risk_autotune_v20.yaml**
```yaml
nonlinear_gain:
  # entropy 상승 구간에서 kp 완만 감소, kd 증가
  kp_curve: [[0.00,0.35],[0.10,0.33],[0.20,0.28],[0.30,0.22]]
  kd_curve: [[0.00,0.10],[0.10,0.12],[0.20,0.14],[0.30,0.18]]
  ki_base: 0.08
burn_rate_thresholds:
  phase: {fast: 0.03, slow: 0.025}
  entropy: {warn: 0.18, crit: 0.22}
```

---

## F3) Fusion Engine 스켈레톤 (fusion/fusion_engine_v20.py)
```python
#!/usr/bin/env python3
import time, yaml
from prometheus_client import start_http_server, Gauge
coh_g = Gauge('fusion_coherence_level','fusion coherence [0,1]')
har_g = Gauge('fusion_harmony_index','fusion harmony [0,1]')
pd_g  = Gauge('fusion_phase_diff_mean','phase diff mean fused')

class Fusion:
  def __init__(self,cfg):
    self.cfg = cfg
    self.tick = cfg['fusion']['tick_ms']
  def step(self):
    # TODO: pull URE + sensor streams → align(resample+kalman) → fuse
    pd, har, coh = 0.016, 0.88, 0.87
    pd_g.set(pd); har_g.set(har); coh_g.set(coh)
    time.sleep(self.tick/1000.0)

if __name__=='__main__':
  cfg = yaml.safe_load(open('configs/fusion_v20.yaml'))
  start_http_server(cfg['exporter']['http_port'])
  f = Fusion(cfg)
  while True: f.step()
```

---

## F4) Evidence Mapper (evidence/mapper_daemon.py)
```python
#!/usr/bin/env python3
# 입력: facts[], quotes[] 원천 → risk/quote/evidence bundle 가공 → 파일 + API 제공
import time, json, http.server
DB='data/evidence_bundle.jsonl'
class H(http.server.BaseHTTPRequestHandler):
  def do_GET(self):
    if self.path=='/evidence/bundle':
      self.send_response(200); self.end_headers()
      with open(DB,'rb') as f: self.wfile.write(f.read())

def run():
  while True:
    # TODO: 수집 → rules/quote_rules.yaml, risk_map.yaml 적용 → bundle append
    time.sleep(2)

if __name__=='__main__':
  run()
```

---

## F5) Exporter & 룰
**exporters/fusion_exporter_v20.py** — `/metrics_fusion`에서 `fusion_*` 지표 노출

**ops/prometheus/rules/fusion_records_v20.yaml**
```yaml
groups:
- name: fusion_records_v20
  rules:
  - record: fusion:coherence_p95_10m
    expr: quantile_over_time(0.95, fusion_coherence_level[10m])
  - record: fusion:phase_diff_mean_5m
    expr: avg_over_time(fusion_phase_diff_mean[5m])
```

**ops/prometheus/rules/risk_autotune_v20.yaml**
```yaml
groups:
- name: risk_autotune_v20
  rules:
  - alert: FusionEntropyHigh
    expr: bridge_entropy_ratio > 0.2
    for: 2m
    labels: {severity: warning}
  - alert: FusionPhaseDrift
    expr: fusion:phase_diff_mean_5m > 0.025
    for: 5m
    labels: {severity: critical}
```

---

## F6) Make 타깃
```makefile
.PHONY: fusion.init sensor.ingest.start evidence.mapper.start
fusion.init:
	@python3 fusion/fusion_engine_v20.py &
sensor.ingest.start:
	@python3 sensors/ingest_daemon.py --config configs/sensors_v20.yaml &
evidence.mapper.start:
	@python3 evidence/mapper_daemon.py &
```

---

## F7) Smoke/Bench
**scripts/smoke.v20.sh**
```bash
#!/usr/bin/env bash
set -euo pipefail
curl -fsS localhost:9310/metrics_fusion | grep fusion_coherence_level
```

**scripts/bench.v20.sh**
```bash
#!/usr/bin/env bash
set -euo pipefail
DUR=${1:-1200}
S=0
while [ $S -lt $DUR ]; do
  curl -fsS localhost:9310/metrics_fusion | awk '/fusion_phase_diff_mean|fusion_harmony_index|fusion_coherence_level/{print strftime("%Y-%m-%dT%H:%M:%S"), $1, $2}'
  sleep 5; S=$((S+5))
done
```

---

## F8) 대시보드(최소)
- **Stat**: `fusion:coherence_p95_10m` (green ≥0.9 / yellow 0.86~0.9 / red <0.86)
- **Timeseries**: `fusion_phase_diff_mean`
- **Stat**: `fusion_harmony_index`

---

## F9) 운영 기준(초안)
- `fusion:phase_diff_mean_5m` ≤ **0.02**, `fusion:coherence_p95_10m` ≥ **0.9**
- 외부 센서 장애 → Fusion Engine은 **URE 단독 모드**로 자동 폴백(알림)

---

## F10) 마이그레이션 메모 (v1.9.6 → v2.0 α)
- 포트 충돌 점검: Bridge 9306, Fusion 9310
- Bench 경로 분리: `out/bench_v19.log` vs `out/bench_v20.log`
- Risk‑Aware Autotune 커브는 **선형 패치 금지**(곡선 테이블만 수정)

---

## F11) Sensor Ingest 스켈레톤
**sensors/sources/osc_stream.py**
```python
#!/usr/bin/env python3
from pythonosc import dispatcher, osc_server
from queue import Queue
Q=Queue(maxsize=1024)

def handler(addr, *args):
    Q.put((addr, args))

def run(addr='127.0.0.1', port=9000):
    disp=dispatcher.Dispatcher(); disp.set_default_handler(handler)
    server=osc_server.ThreadingOSCUDPServer((addr,port), disp)
    server.serve_forever()
```

**sensors/sources/midi_stream.py**
```python
#!/usr/bin/env python3
import mido
from queue import Queue
Q=Queue(maxsize=1024)

def run(device_name=None):
    with mido.open_input(device_name) as port:
        for msg in port: Q.put(('midi', msg.dict()))
```

**sensors/sources/file_replay.py**
```python
#!/usr/bin/env python3
import json, time
from queue import Queue
Q=Queue(maxsize=1024)

def run(path, speed=1.0):
    t0=None
    for line in open(path):
        rec=json.loads(line)
        ts=rec.get('ts')
        if t0 is None: t0=ts
        delay=max(0.0,(ts-t0)/speed)
        time.sleep(delay)
        Q.put(rec)
```

**sensors/ingest_daemon.py (접착)**
```python
#!/usr/bin/env python3
import yaml, threading
from sources.osc_stream import run as run_osc
from sources.midi_stream import run as run_midi
from sources.file_replay import run as run_replay

if __name__=='__main__':
  cfg=yaml.safe_load(open('configs/sensors_v20.yaml'))
  for s in cfg['streams']:
    if s['type']=='osc': threading.Thread(target=run_osc, kwargs={'addr':s['addr'].split(':')[0],'port':int(s['addr'].split(':')[1])}, daemon=True).start()
    if s['type']=='midi': threading.Thread(target=run_midi, kwargs={'device_name':s['device']}, daemon=True).start()
    if s['type']=='file': threading.Thread(target=run_replay, kwargs={'path':s['path']}, daemon=True).start()
  threading.Event().wait()
```

---

## F12) 정렬/리샘플 어댑터
**fusion/adapters/align_kalman.py**
```python
import numpy as np
class SimpleKalman:
  def __init__(self,q=1e-3,r=2e-3):
    self.q=q; self.r=r; self.x=0; self.p=1
  def update(self,z):
    # predict
    self.p += self.q
    # update
    k = self.p/(self.p+self.r)
    self.x = self.x + k*(z-self.x)
    self.p = (1-k)*self.p
    return self.x
```

**fusion/adapters/resample_polyphase.py**
```python
import numpy as np
from scipy.signal import resample_poly

def to_target_hz(series, src_hz, tgt_hz):
  up=int(tgt_hz); down=int(src_hz)
  return resample_poly(series, up, down)
```

---

## F13) URE Pull 통합 (Bridge→Fusion)
**fusion/fusion_engine_v20.py (보강 발췌)**
```python
import requests
URE_URL='http://localhost:9305/metrics_ure'

def pull_ure_metrics():
  # very simple text parse
  m=requests.get(URE_URL, timeout=1.0).text
  def grab(key):
    for line in m.splitlines():
      if line.startswith(key+' '):
        return float(line.split()[1])
  return {
    'ure_phase_diff': grab('ure_phase_diff_mean') or 0.02,
    'ure_harmony': grab('ure_harmony_index') or 0.86,
    'ure_coherence': grab('ure_coherence_level') or 0.85,
  }
```

---

## F14) Risk‑Aware Autotune 엔진(초안)
**tools/risk_autotune_v20.py**
```python
#!/usr/bin/env python3
import yaml, json, sys
cfg=yaml.safe_load(open('configs/risk_autotune_v20.yaml'))
curve_kp=cfg['nonlinear_gain']['kp_curve']
curve_kd=cfg['nonlinear_gain']['kd_curve']
ki=cfg['nonlinear_gain']['ki_base']

# simple piecewise linear interpolation on entropy_ratio
entropy=float(sys.argv[1]) if len(sys.argv)>1 else 0.12

def interp(curve, x):
  for i in range(1,len(curve)):
    x0,y0=curve[i-1]; x1,y1=curve[i]
    if x<=x1:
      t=(x-x0)/(x1-x0) if x1!=x0 else 0
      return y0+(y1-y0)*t
  return curve[-1][1]

kp=interp(curve_kp, entropy)
kd=interp(curve_kd, entropy)
print(json.dumps({'gain':{'kp':round(kp,2),'ki':round(ki,2),'kd':round(kd,2)}}, indent=2))
```

**Make 타깃**
```makefile
.PHONY: autotune.risk
autotune.risk:
	@python3 tools/risk_autotune_v20.py $$ENTROPY > configs/fusion_autotune.json
```

---

## F15) Evidence Rules (샘플)
**evidence/rules/risk_map.yaml**
```yaml
- if: "phase_diff > 0.025 and entropy_ratio > 0.18"
  risk: "sync_degradation"
  action: "increase kd by 0.02; alert warn"
```

**evidence/rules/quote_rules.yaml**
```yaml
- match: "coherence improves with lower entropy"
  quote: "Stability favors clarity; clarity invites harmony."
```

---

## F16) OpenAPI (Fusion)
**api/openapi_v20.yaml (발췌)**
```yaml
openapi: 3.0.3
info: {title: Lumen Fusion API, version: 2.0a}
paths:
  /metrics_fusion: {get: {summary: Fusion Prom metrics}}
  /evidence/bundle: {get: {summary: Evidence bundle stream}}
```

---

## F17) v2.0 α1 Session Restore Block (증분)
```bash
# v2.0 α1: sensor ingest + fusion align + risk‑aware autotune scaffold
bash scripts/smoke.v20.sh && \
make fusion.init && make sensor.ingest.start && \
make autotune.risk ENTROPY=0.14 && \
bash scripts/bench.v20.sh 1200
```

---

## F18) 다음 액션 (루멘 제안)
1) `bench.v20.sh 20m` 관측 후 `fusion:coherence_p95_10m ≥ 0.90` 달성 여부 확인
2) 미달 시: `risk_autotune_v20.yaml` 커브 상향/완화, 칼만 Q/R 미세조정(Q↘︎, R↗︎)
3) Evidence bundle에 **risk_map 적용 결과** 10분 누적 스냅샷 생성

---

## F19) Sensor Schema & Normalization
**schemas/sensor_event_v20.json (초안)**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SensorEventV20",
  "type": "object",
  "required": ["ts", "source", "key", "value"],
  "properties": {
    "ts": {"type": "number", "description": "unix epoch seconds with ms"},
    "source": {"type": "string"},
    "key": {"type": "string"},
    "value": {"type": ["number", "string", "array", "object"]},
    "meta": {"type": "object"}
  }
}
```

**sensors/normalize.py**
```python
#!/usr/bin/env python3
# OSC/MIDI/File → SensorEventV20
from dataclasses import dataclass, asdict
@dataclass
class Event: ts: float; source: str; key: str; value: float; meta: dict

def from_osc(addr, args):
    return Event(ts=time.time(), source='osc', key=addr, value=float(args[0]), meta={})
```

---

## F20) Outlier/Clock‑Drift Guards
**fusion/adapters/outlier_clip.py**
```python
def clip(series, p_low=0.01, p_high=0.99):
    s=sorted(series); n=len(s);
    lo=s[int(p_low*n)]; hi=s[int(p_high*n)];
    return [min(hi, max(lo, x)) for x in series]
```

**fusion/adapters/clock_drift.py**
```python
# NTP 기반 보정치 입력 가정; 단순 선형 보정
class ClockDrift:
    def __init__(self, ppm=0): self.ppm=ppm
    def apply(self, ts): return ts*(1+self.ppm/1e6)
```

---

## F21) Cross‑Correlation Align (초안)
**fusion/adapters/xcorr_align.py**
```python
import numpy as np
from numpy.fft import rfft, irfft

def lag_by_xcorr(a, b, max_lag=200):
    # returns best lag(samples) to align b to a
    n = 1<< (max(len(a),len(b)).bit_length())
    fa, fb = rfft(a, n), rfft(b, n)
    corr = irfft(fa*np.conj(fb))
    idx = np.argmax(corr[:max_lag])
    return int(idx)
```

---

## F22) Fusion Weighting & Failover
**configs/fusion_v20.yaml (추가)**
```yaml
weights:
  ure: 0.7
  sensors: 0.3
failover:
  min_streams: 1
  fallback: ure_only  # ure_only | sensors_only | degrade
```

**fusion/fusion_engine_v20.py (발췌)**
```python
# fused = w_ure*ure + w_sens*sensors; sensors가 부족하면 failover 정책 적용
```

---

## F23) Monitoring & Alerts (Fusion)
**ops/prometheus/rules/fusion_alerts_v20.yaml**
```yaml
groups:
- name: fusion_alerts_v20
  rules:
  - alert: FusionStreamLoss
    expr: increase(fusion_stream_ingest_total[2m]) == 0
    for: 2m
    labels: {severity: warning}
    annotations: {summary: "No sensor ingest", description: "ingest halted"}
  - alert: FusionCoherenceLow
    expr: fusion:coherence_p95_10m < 0.86
    for: 10m
    labels: {severity: critical}
```

---

## F24) Tests & CI (추가)
**tests/fusion_align.spec.py**
```python
from fusion.adapters.xcorr_align import lag_by_xcorr

def test_xcorr_align_basic():
    a=[0,1,2,3,4,5,6,7,8,9]; b=[2,3,4,5,6,7,8,9]
    assert lag_by_xcorr(a,b) >= 0
```

**.github/workflows/fusion-ci.yml**
```yaml
name: fusion-ci
on: {push: {branches: [main]}, pull_request: {}}
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.11'}
      - run: pip install -r requirements.txt
      - run: pytest -q
```

---

## F25) v2.0 α2 Session Restore Block (보강)
```bash
# v2.0 α2: schema/normalize, guards, xcorr, weighting/failover, alerts, tests
make fusion.init && make sensor.ingest.start && \
python -m pytest -q && \
bash scripts/bench.v20.sh 1800
```
