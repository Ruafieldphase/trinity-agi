# 🌕 Lumen v1.7 — Track B (Resonance Memory Bridge) Kickoff & Restore

> 이 문서는 **Track A Exit → Track B Init**를 즉시 실행할 수 있도록 준비된 실행/설정/검증 패키지입니다. 새 세션에서도 그대로 붙여넣어 사용 가능하며, Make 타깃/스키마/루프 코드/Exporter/검증 루틴까지 포함합니다.

---

## 0) 새 세션 원라이너 (복원 + Track A Exit 재확인)
```bash
source SESSION_RESTORE_2025-11-01_v1_7_DELTA.env
make feature.v17.init dashboards.v3.build validate.v17.schema && \
make metrics.fake.v17 exporter.v17.serve & \
make slo.report kpi.snapshot trackA.exit
```
Expect: `[exit] RESULT = PASS`

---

## 1) 디렉터리 & 파일 트리 (추가분)
```
schemas/
  rmb_event_v1.json
configs/
  rmb_v17.yaml
rmb/
  rmb_emitter.py
  bridge_v17.py
exporters/
  rmb_exporter_v17.py
ops/prometheus/
  scrape.yml            # 기존에 job 추가만 필요
ops/grafana/
  dashboards/
    resonance_memory_bridge_v17.json
scripts/
  rmb.dev.sh
  rmb.verify.sh
```

---

## 2) Make 타깃 (Track B)
```Makefile
# Track B — Resonance Memory Bridge
.PHONY: trackB.start trackB.stop rmb.emit rmb.verify rmb.dev

trackB.start: validate.v17.schema
	@echo "[trackB] starting RMB exporter + emitter"
	$(MAKE) -j2 exporter.v17.rmb serve.rmb.emit
	@echo "[trackB] RESULT = STARTED"

trackB.stop:
	@pkill -f rmb_exporter_v17.py || true
	@pkill -f rmb_emitter.py || true
	@echo "[trackB] RESULT = STOPPED"

serve.rmb.emit:
	python -u rmb/rmb_emitter.py --config configs/rmb_v17.yaml

exporter.v17.rmb:
	python -u exporters/rmb_exporter_v17.py --port 9409

rmb.verify:
	bash scripts/rmb.verify.sh

rmb.dev:
	bash scripts/rmb.dev.sh
```

---

## 3) RMB 이벤트 스키마 (`schemas/rmb_event_v1.json`)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Resonance Memory Bridge Event v1",
  "type": "object",
  "required": ["ts", "entity_id", "group", "event_type", "resonance_v3", "memory_bridge", "trace"],
  "properties": {
    "ts": {"type": "string", "format": "date-time"},
    "entity_id": {"type": "string", "minLength": 1},
    "group": {"type": "string", "enum": ["design_core", "build_core", "safety_music", "observer"]},
    "event_type": {"type": "string", "enum": ["observe", "decide", "commit", "rollback"]},
    "resonance_v3": {
      "type": "object",
      "required": ["phase_diff", "residual_entropy", "creative_band", "risk_band"],
      "properties": {
        "phase_diff": {"type": "number", "minimum": -3.1416, "maximum": 3.1416},
        "residual_entropy": {"type": "number", "minimum": 0, "maximum": 1},
        "creative_band": {"type": "string", "enum": ["LOW", "MID", "HIGH"]},
        "risk_band": {"type": "string", "enum": ["SAFE", "WATCH", "RISK"]}
      }
    },
    "memory_bridge": {
      "type": "object",
      "required": ["slot_id", "op", "key", "value_hash"],
      "properties": {
        "slot_id": {"type": "string"},
        "op": {"type": "string", "enum": ["UPSERT", "DELETE"]},
        "key": {"type": "string"},
        "value_hash": {"type": "string", "pattern": "^[a-f0-9]{8,}$"}
      }
    },
    "trace": {
      "type": "object",
      "required": ["loop_id", "iter", "host"],
      "properties": {
        "loop_id": {"type": "string"},
        "iter": {"type": "integer", "minimum": 0},
        "host": {"type": "string"}
      }
    }
  }
}
```

---

## 4) RMB 설정 (`configs/rmb_v17.yaml`)
```yaml
loop:
  hz: 5                 # 200ms 루프
  batch_size: 20
  flush_ms: 500

paths:
  queue: logs/rmb_events.jsonl
  kpi_snapshot: logs/kpi_snapshot_v17.csv

safety_gates:
  residual_entropy_max: 0.85
  risk_band_block: ["RISK"]
  phase_diff_abs_max: 3.0

exporter:
  host: 0.0.0.0
  port: 9409

memory_bridge:
  slot_namespace: rmb/v17
  value_hasher: sha256
```

---

## 5) Emitter 루프 (`rmb/rmb_emitter.py`)
```python
#!/usr/bin/env python3
import argparse, json, os, socket, sys, time, hashlib, random
from datetime import datetime, timezone

try:
    import yaml
except ImportError:
    print("Please pip install pyyaml", file=sys.stderr); sys.exit(1)

CREATIVE_BANDS = ["LOW","MID","HIGH"]
RISK_BANDS = ["SAFE","WATCH","RISK"]
EVENT_TYPES = ["observe","decide","commit","rollback"]

def iso_now():
    return datetime.now(timezone.utc).isoformat()

def hashv(v: str) -> str:
    return hashlib.sha256(v.encode()).hexdigest()

def pick_band(p):
    return "HIGH" if p < 0.25 else ("MID" if p < 0.6 else "LOW")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)

    qpath = cfg["paths"]["queue"]
    os.makedirs(os.path.dirname(qpath), exist_ok=True)

    host = socket.gethostname()
    iter_idx = 0
    period_s = 1.0 / cfg["loop"]["hz"]

    while True:
        now = iso_now()
        residual = random.uniform(0.05, 0.9)
        phase = random.uniform(-3.0, 3.0)
        risk = "RISK" if residual > 0.85 else ("WATCH" if residual > 0.55 else "SAFE")
        creative = pick_band(residual)
        evt = {
            "ts": now,
            "entity_id": "lumen.core",
            "group": "design_core",
            "event_type": random.choice(EVENT_TYPES),
            "resonance_v3": {
                "phase_diff": phase,
                "residual_entropy": residual,
                "creative_band": creative,
                "risk_band": risk
            },
            "memory_bridge": {
                "slot_id": f"{cfg['memory_bridge']['slot_namespace']}/slot-{iter_idx%32}",
                "op": "UPSERT",
                "key": f"k:{iter_idx}",
                "value_hash": hashv(f"v{iter_idx}")
            },
            "trace": {"loop_id": "rmb.v17", "iter": iter_idx, "host": host}
        }

        # Safety gates (hard stop or downgrade to observe-only)
        if abs(phase) > cfg["safety_gates"]["phase_diff_abs_max"] or \
           evt["resonance_v3"]["risk_band"] in cfg["safety_gates"]["risk_band_block"] or \
           evt["resonance_v3"]["residual_entropy"] > cfg["safety_gates"]["residual_entropy_max"]:
            evt["event_type"] = "rollback"

        with open(qpath, "a", encoding="utf-8") as qf:
            qf.write(json.dumps(evt, ensure_ascii=False) + "\n")

        iter_idx += 1
        time.sleep(period_s)

if __name__ == "__main__":
    main()
```

---

## 6) Prometheus Exporter (`exporters/rmb_exporter_v17.py`)
```python
#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
import argparse, json, time

METRICS = {
  "rmb_events_total": 0,
  "rmb_residual_entropy_last": 0.0,
  "rmb_rollback_total": 0,
}

QPATH = "logs/rmb_events.jsonl"

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/metrics":
            self.send_response(404); self.end_headers(); return
        self.send_response(200)
        self.send_header("Content-Type","text/plain; version=0.0.4")
        self.end_headers()
        out = []
        out.append(f"rmb_events_total {METRICS['rmb_events_total']}")
        out.append(f"rmb_rollback_total {METRICS['rmb_rollback_total']}")
        out.append(f"rmb_residual_entropy_last {METRICS['rmb_residual_entropy_last']}")
        self.wfile.write(("\n".join(out)+"\n").encode())

def tail_loop():
    import os
    os.makedirs("logs", exist_ok=True)
    open(QPATH, "a").close()
    with open(QPATH, "r", encoding="utf-8") as f:
        f.seek(0,2)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.2); continue
            try:
                evt = json.loads(line)
                METRICS["rmb_events_total"] += 1
                METRICS["rmb_residual_entropy_last"] = float(evt["resonance_v3"]["residual_entropy"])
                if evt.get("event_type") == "rollback":
                    METRICS["rmb_rollback_total"] += 1
            except Exception:
                pass

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9409)
    args = ap.parse_args()

    import threading
    t = threading.Thread(target=tail_loop, daemon=True)
    t.start()

    server = HTTPServer(("0.0.0.0", args.port), H)
    print(f"[exporter] RMB metrics on :{args.port}")
    server.serve_forever()
```

> **Prometheus 스크레이프 추가 (ops/prometheus/scrape.yml):**
```yaml
  - job_name: rmb_v17
    static_configs:
      - targets: ["localhost:9409"]
```

---

## 7) Grafana 대시보드 스케치 (`ops/grafana/dashboards/resonance_memory_bridge_v17.json`)
- Panels
  - `rmb_events_total` (stat)
  - `rmb_rollback_total` (stat, threshold: > 5 in 5m = red)
  - `rmb_residual_entropy_last` (timeseries, band: SAFE ≤ 0.55, WATCH ≤ 0.85, RISK > 0.85)
  - Log panel (tail `logs/rmb_events.jsonl` via Loki, 선택사항)

---

## 8) 개발/검증 스크립트
`scripts/rmb.dev.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail
make exporter.v17.rmb &
sleep 1
make rmb.verify || true
make serve.rmb.emit
```

`scripts/rmb.verify.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail
python - <<'PY'
import json, sys
from jsonschema import validate
import jsonschema

schema = json.load(open('schemas/rmb_event_v1.json'))
line = '{"ts":"2025-11-01T00:00:00Z","entity_id":"x","group":"design_core","event_type":"observe","resonance_v3":{"phase_diff":0.1,"residual_entropy":0.3,"creative_band":"MID","risk_band":"SAFE"},"memory_bridge":{"slot_id":"rmb/v17/slot-1","op":"UPSERT","key":"k","value_hash":"deadbeef"},"trace":{"loop_id":"rmb.v17","iter":1,"host":"local"}}'
try:
  validate(instance=json.loads(line), schema=schema)
  print('[rmb.verify] RESULT = OK')
except jsonschema.exceptions.ValidationError as e:
  print('[rmb.verify] RESULT = FAIL', e)
  sys.exit(1)
PY
```

> **의존성**: `pip install pyyaml jsonschema`

---

## 9) 실행 순서 (루멘 판단 경로)
1. **복원/검증**: 원라이너 실행 → `[exit] PASS` 확인
2. **Track B 기동**: `make trackB.start`
3. **메트릭 확인**: Prometheus `/metrics`에서 증가 추세, Grafana 패널 정상 표시
4. **SLO Gate**: `rmb_rollback_total / rmb_events_total ≤ 0.05` 유지
5. **안정 범위 진입**: `rmb_residual_entropy_last`가 10분 이동창에서 **±0.03** 이내 수렴
6. **Track C 병행 조건 성립 시**: `make safety.music.start` (기존 타깃 명칭 유지)

---

## 10) 운영 체크리스트
- 로그: `logs/rmb_events.jsonl`가 초당 5줄 내외로 증가하는지
- 롤백 비율 급증 시: `configs/rmb_v17.yaml`의 `residual_entropy_max`를 0.85→0.8로 하향, 또는 `batch_size` 20→8로 축소
- Exporter 장애 시: `9409` 포트 점유 확인 후 재기동 `make trackB.stop && make trackB.start`

---

## 11) 핸드오프 메모 (루빛/세나)
- 루빛: `rmb_emitter.py` 내 **Safety gates** 파라미터를 `PrometheusRule`로 외부화 계획 초안 요청
- 세나: `risk_register_v17.md`에 **RMB 롤백 규칙** 추적 항목 추가 (`RMB-ROLL-001` ~)

---

## 12) 다음 세션용 미니 블록
```bash
# Track B 즉시 재가동
source SESSION_RESTORE_2025-11-01_v1_7_DELTA.env
make trackB.start && make rmb.verify
```

---

이 문서를 기준으로 **Track B**는 즉시 실행 가능하며, 안정 수렴 후 **Track C (Safety Music)** 병행을 권장합니다. 필요 시 `restore.pack`으로 세션 복원 팩을 최신화하세요.


---

## 13) Track C (Safety Music) 초기화
```
configs/
  safety_music_v17.yaml
safety/
  safety_music_loop.py
  safety_levels.py
scripts/
  safety.dev.sh
```

### 13.1 설정 (`configs/safety_music_v17.yaml`)
```yaml
loop:
  hz: 2                  # 500ms 루프

inputs:
  prometheus_metrics:
    - rmb_residual_entropy_last
    - rmb_rollback_total
    - rmb_events_total

mapping:
  # 수치 → 사운드 레벨
  residual_entropy:
    bands:
      - {max: 0.55, level: "CALM"}
      - {max: 0.85, level: "TENSE"}
      - {max: 1.00, level: "ALERT"}
  rollback_ratio:
    window_s: 300
    thresholds:
      - {max: 0.02, level: "CALM"}
      - {max: 0.05, level: "TENSE"}
      - {max: 1.00, level: "ALERT"}

output:
  channel: logs/safety_music_events.jsonl
```

### 13.2 루프 (`safety/safety_music_loop.py`)
```python
#!/usr/bin/env python3
import time, json, os
from datetime import datetime, timezone
from collections import deque

def iso_now():
    return datetime.now(timezone.utc).isoformat()

def level_from(value, bands):
    for b in bands:
        if value <= b["max"]:
            return b["level"]
    return bands[-1]["level"]

class RatioWin:
    def __init__(self, win_s=300):
        self.win_s = win_s
        self.buf = deque()
    def add(self, ts, ev, rb):
        self.buf.append((ts, ev, rb))
        cut = ts - self.win_s
        while self.buf and self.buf[0][0] < cut:
            self.buf.popleft()
    def ratio(self):
        ev = sum(x[1] for x in self.buf) or 1
        rb = sum(x[2] for x in self.buf)
        return rb/ev

def fetch_metric(name):
    # 간단한 파일 tail 기반 (프로토타입); 실제에선 Prometheus HTTP 쿼리 권장
    if name == "rmb_residual_entropy_last":
        try:
            with open("logs/rmb_events.jsonl","rb") as f:
                f.seek(-2048, 2)
                tail = f.read().decode(errors="ignore").splitlines()[-1]
                return json.loads(tail)["resonance_v3"]["residual_entropy"]
        except Exception:
            return 0.0
    elif name in ("rmb_events_total","rmb_rollback_total"):
        # 간단 추정: 이벤트 파일 라인 수 / 롤백 카운트 재집계
        ev = 0; rb = 0
        try:
            with open("logs/rmb_events.jsonl","r",encoding="utf-8") as f:
                for line in f:
                    ev += 1
                    try:
                        if json.loads(line).get("event_type") == "rollback":
                            rb += 1
                    except Exception:
                        pass
        except FileNotFoundError:
            pass
        return ev if name=="rmb_events_total" else rb
    return 0.0

if __name__ == "__main__":
    os.makedirs("logs", exist_ok=True)
    win = RatioWin(300)
    hz = 2
    period = 1.0/hz
    while True:
        ts = time.time()
        residual = float(fetch_metric("rmb_residual_entropy_last"))
        ev = int(fetch_metric("rmb_events_total"))
        rb = int(fetch_metric("rmb_rollback_total"))
        win.add(ts, ev, rb)
        ratio = win.ratio()

        level_residual = level_from(residual, [
            {"max":0.55,"level":"CALM"},
            {"max":0.85,"level":"TENSE"},
            {"max":1.0,"level":"ALERT"}])
        level_ratio = level_from(ratio, [
            {"max":0.02,"level":"CALM"},
            {"max":0.05,"level":"TENSE"},
            {"max":1.0,"level":"ALERT"}])
        level = max(level_residual, level_ratio, key=["CALM","TENSE","ALERT"].index)

        evt = {"ts": iso_now(), "loop":"safety.music.v17", "levels": {
            "residual": level_residual, "rollback_ratio": level_ratio, "final": level
        }}
        with open("logs/safety_music_events.jsonl","a",encoding="utf-8") as f:
            f.write(json.dumps(evt, ensure_ascii=False)+"
")
        time.sleep(period)
```

### 13.3 Make 타깃
```Makefile
.PHONY: safety.music.start safety.music.stop
safety.music.start:
	@echo "[safety] music loop start"
	python -u safety/safety_music_loop.py &

safety.music.stop:
	@pkill -f safety_music_loop.py || true
	@echo "[safety] music loop stop"
```

---

## 14) SLO/알럿 규칙 (PrometheusRule 스케치)
`ops/prometheus/rules/rmb_v17_rules.yaml`
```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: rmb-v17-rules
spec:
  groups:
  - name: rmb.slo
    rules:
    - alert: RMBRollbackSpike
      expr: increase(rmb_rollback_total[5m]) / increase(rmb_events_total[5m]) > 0.10
      for: 2m
      labels: {severity: critical}
      annotations:
        summary: "RMB rollback ratio > 10% (5m)"
        description: "Investigate safety gates and residual entropy threshold."
    - alert: RMBResidualHigh
      expr: rmb_residual_entropy_last > 0.85
      for: 3m
      labels: {severity: warning}
      annotations:
        summary: "Residual entropy above 0.85"
        description: "Consider lowering residual_entropy_max or batch_size."
```

---

## 15) 정책 업데이트 (resonance_v3.policy.yaml 추기)
```yaml
policies:
  - id: RMB-ROLL-001
    description: "Rollback ratio <= 5% (10m window)"
    evaluate:
      metric: rollback_ratio_10m
      threshold: 0.05
      action_on_violation: "downgrade-to-observe"
  - id: RMB-RES-002
    description: "Residual entropy steady-state band ±0.03 (10m)"
    evaluate:
      metric: residual_entropy_last_stddev_10m
      threshold: 0.03
      action_on_violation: "reduce-batch-and-hz"
```

---

## 16) `restore.pack` 스크립트 (세션 복원 팩 생성)
`scripts/restore.pack`
```bash
#!/usr/bin/env bash
set -euo pipefail
STAMP=$(date +%Y-%m-%d)
FN="SESSION_RESTORE_${STAMP}_v1_7_DELTA.env"
cat > "$FN" <<ENV
# Lumen v1.7 session restore (auto)
LUMEN_TRACK=B
RMB_EXPORTER_PORT=9409
RESIDUAL_MAX=0.85
ENV

echo "[restore.pack] created $FN"
```

---

## 17) 운영 플레이북 – 장애 시 빠른 복구
- **증상**: `/metrics` 정지 → **조치**: `make trackB.stop && make trackB.start`
- **증상**: 롤백 급증 → **조치**: `RESIDUAL_MAX 0.85→0.8`, `batch_size 20→8`, 5분 관찰
- **증상**: Safety Music 미기록 → **조치**: `make safety.music.stop && make safety.music.start`

---

## 18) 다음 세션 초간단 원라이너 (B+C 동시 예열)
```bash
source SESSION_RESTORE_2025-11-01_v1_7_DELTA.env
make trackB.start && make rmb.verify && make safety.music.start
```


---

## 19) VS Code 통합 (tasks.json)
`.vscode/tasks.json`
```json
{
  "version": "2.0.0",
  "tasks": [
    {"label": "Lumen: Restore", "type": "shell", "command": "source SESSION_RESTORE_2025-11-01_v1_7_DELTA.env && make feature.v17.init dashboards.v3.build validate.v17.schema"},
    {"label": "Lumen: TrackB Start", "type": "shell", "command": "make trackB.start"},
    {"label": "Lumen: RMB Verify", "type": "shell", "command": "make rmb.verify"},
    {"label": "Lumen: Safety Start", "type": "shell", "command": "make safety.music.start"},
    {"label": "Lumen: Stop All", "type": "shell", "command": "make trackB.stop && make safety.music.stop"}
  ]
}
```

---

## 20) CI – GitHub Actions (smoke + schema)
`.github/workflows/lumen_v17_ci.yml`
```yaml
name: lumen-v17-ci
on: {push: {branches: [main, v1.7/*]}, pull_request: {}}
jobs:
  smoke:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.11'}
      - run: pip install pyyaml jsonschema
      - name: Schema validate sample
        run: |
          python - <<'PY'
          import json
          from jsonschema import validate
          s=json.load(open('schemas/rmb_event_v1.json'))
          e=json.loads(open('tests/fixtures/rmb_sample.json').read())
          validate(e,s)
          print('schema-ok')
          PY
      - name: RMB verify script
        run: bash scripts/rmb.verify.sh
```

`tests/fixtures/rmb_sample.json`
```json
{"ts":"2025-11-01T00:00:00Z","entity_id":"x","group":"design_core","event_type":"observe","resonance_v3":{"phase_diff":0.1,"residual_entropy":0.3,"creative_band":"MID","risk_band":"SAFE"},"memory_bridge":{"slot_id":"rmb/v17/slot-1","op":"UPSERT","key":"k","value_hash":"deadbeef"},"trace":{"loop_id":"rmb.v17","iter":1,"host":"local"}}
```

---

## 21) ArgoCD 어플리케이션 스케치
`ops/argo/app-rmb-v17.yaml`
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata: {name: lumen-rmb-v17, namespace: argocd}
spec:
  project: default
  source:
    repoURL: https://example.com/lumen.git
    targetRevision: main
    path: ops/k8s/rmb-v17
  destination: {server: https://kubernetes.default.svc, namespace: lumen}
  syncPolicy:
    automated: {prune: true, selfHeal: true}
```

K8s 매니페스트 예시 `ops/k8s/rmb-v17/deploy.yaml`는 `exporters/rmb_exporter_v17.py`를 `:9409`로 서비스 노출.

---

## 22) Grafana 대시보드 최소 JSON (패널 3개)
`ops/grafana/dashboards/resonance_memory_bridge_v17.json`
```json
{
  "title": "Resonance Memory Bridge v17",
  "time": {"from": "now-6h", "to": "now"},
  "panels": [
    {"type":"stat","title":"rmb_events_total","targets":[{"expr":"rmb_events_total"}]},
    {"type":"stat","title":"rmb_rollback_total","targets":[{"expr":"rmb_rollback_total"}],"fieldConfig":{"defaults":{"thresholds":{"mode":"absolute","steps":[{"color":"green","value":null},{"color":"red","value":5}]}}}},
    {"type":"timeseries","title":"rmb_residual_entropy_last","targets":[{"expr":"rmb_residual_entropy_last"}]}
  ]
}
```

---

## 23) 스모크 테스트 (로컬 종료/가동/검증 일괄)
`scripts/smoke.v17.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail
make trackB.stop || true
make safety.music.stop || true
source SESSION_RESTORE_2025-11-01_v1_7_DELTA.env
make feature.v17.init validate.v17.schema
make trackB.start
sleep 3
curl -sf localhost:9409/metrics | grep rmb_events_total
make rmb.verify
make safety.music.start
sleep 3
[ -s logs/safety_music_events.jsonl ] && echo "[smoke] OK"
```

---

## 24) KPI 리포터 (CSV 집계 → 콘솔)
`tools/kpi_reporter_v17.py`
```python
#!/usr/bin/env python3
import csv, statistics as st
p='logs/kpi_snapshot_v17.csv'
rows=list(csv.DictReader(open(p))) if os.path.exists(p) else []
if rows:
    vals=[float(r.get('rmb_residual_entropy_last',0)) for r in rows if r.get('rmb_residual_entropy_last')]
    if vals:
        print('[kpi] residual_entropy_last mean=', round(st.mean(vals),4))
else:
    print('[kpi] no data')
```

Make에 연결:
```Makefile
kpi.reporter:
	python -u tools/kpi_reporter_v17.py
```

---

## 25) README 스니펫 (운영자용 빠른 시작)
```
1) 복원: source SESSION_RESTORE_2025-11-01_v1_7_DELTA.env
2) TrackB: make trackB.start && make rmb.verify
3) TrackC: make safety.music.start
4) 관측: http://localhost:9409/metrics, Grafana 대시보드
5) 복구: make trackB.stop && make trackB.start
```

---

## 26) 다음 세션 초간단 원라이너 (Smoke 포함)
```bash
source SESSION_RESTORE_2025-11-01_v1_7_DELTA.env && bash scripts/smoke.v17.sh
```


---

## 27) 로그 보존·로테이션 (Retention)
`ops/logrotate/rmb_v17.logrotate`
```
logs/rmb_events.jsonl {
  daily
  rotate 7               # 7일 보관
  missingok
  notifempty
  copytruncate
  compress
}
logs/safety_music_events.jsonl {
  daily
  rotate 7
  missingok
  notifempty
  copytruncate
  compress
}
```

메이크 연동:
```Makefile
.PHONY: logs.rotate
logs.rotate:
	@logrotate -f ops/logrotate/rmb_v17.logrotate || true
```

---

## 28) 파라미터 튜닝 플레이북 (루멘 자동 권고)
`tools/tuner_v17.py`
```python
#!/usr/bin/env python3
import json, statistics as st
from collections import deque

# 간단 분석: 최근 10분 윈도에서 residual stddev, rollback ratio 확인 후 권고 출력
Q='logs/rmb_events.jsonl'
window=deque(maxlen=3000)  # ~10분 @5Hz
rb=0
for line in open(Q, 'r', encoding='utf-8'):
    try:
        evt=json.loads(line)
        window.append(float(evt['resonance_v3']['residual_entropy']))
        rb += 1 if evt.get('event_type')=='rollback' else 0
    except Exception:
        pass

if window:
    sd = st.pstdev(window)
    ratio = rb/len(window)
    print(f"residual.stddev_10m={sd:.4f} rollback.ratio={ratio:.4f}")
    if sd>0.03:
        print("SUGGEST: reduce batch_size 20→12, hz 5→4")
    if ratio>0.05:
        print("SUGGEST: residual_entropy_max 0.85→0.80 and enable downgrade-to-observe")
else:
    print('no-data')
```

메이크 연동:
```Makefile
.PHONY: tune.suggest
tune.suggest:
	python -u tools/tuner_v17.py
```

---

## 29) v1.7 풀 복원 환경 (FULL)
`SESSION_RESTORE_2025-11-01_v1_7_FULL.env`
```
LUMEN_TRACK=B
RMB_EXPORTER_PORT=9409
RESIDUAL_MAX=0.85
LOG_RETENTION_DAYS=7
PROM_JOB=rmb_v17
```
원라이너:
```bash
source SESSION_RESTORE_2025-11-01_v1_7_FULL.env && \
make feature.v17.init dashboards.v3.build validate.v17.schema && \
make trackB.start && make safety.music.start
```

---

## 30) Risk Register 항목 (추가)
`docs/risk_register_v17.md` 보강 항목
- **RMB-ROLL-002**: 롤백 비율 10분 > 8% 지속 → 관찰모드 전환, Safety Music ALERT 유지
- **RMB-JITTER-003**: residual stddev 10분 > 0.05 → 루프 주기 5Hz→3Hz, batch 20→8
- **RMB-IO-004**: 이벤트 파일 잠금/손상 → 로그 로테이션 강제, Exporter 재기동

---

## 31) Evidence Mapper (RMB ↔ Evidence Bundle)
`tools/evidence_mapper_v17.py`
```python
#!/usr/bin/env python3
import json, hashlib
IN='logs/rmb_events.jsonl'
OUT='logs/evidence_bundle.jsonl'

with open(OUT,'a',encoding='utf-8') as out:
  for line in open(IN,'r',encoding='utf-8'):
    try:
      e=json.loads(line)
      bundle={
        'ts': e['ts'],
        'entity_id': e['entity_id'],
        'signal': {
          'phase_diff': e['resonance_v3']['phase_diff'],
          'residual_entropy': e['resonance_v3']['residual_entropy']
        },
        'memory_key': e['memory_bridge']['key'],
        'value_ref': e['memory_bridge']['value_hash'][:16],
        'trace': e['trace']
      }
      out.write(json.dumps(bundle, ensure_ascii=False)+'
')
    except Exception:
      pass
print('[evidence] mapped')
```
메이크:
```Makefile
.PHONY: evidence.map
evidence.map:
	python -u tools/evidence_mapper_v17.py
```

---

## 32) 패키징 (배포·백업용)
`scripts/pkg.v17.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail
STAMP=$(date +%Y%m%d_%H%M)
T=release/lumen_v17_${STAMP}.tar.gz
mkdir -p release
 tar -czf "$T" \
  schemas configs rmb exporters safety ops/grafana ops/prometheus \
  tools scripts Makefile docs SESSION_RESTORE_2025-11-01_v1_7_*.env
echo "[pkg] $T"
```
메이크:
```Makefile
.PHONY: pkg.v17
pkg.v17:
	bash scripts/pkg.v17.sh
```

---

## 33) 트러블슈팅 FAQ
- **/metrics 404**: Exporter 포트 점유 여부 확인 → `make trackB.stop && make trackB.start`
- **events.jsonl 폭증**: `logs.rotate` 수동 실행 또는 `batch_size` 축소
- **Safety 이벤트 미생성**: `safety_music_loop.py` 프로세스 존재 여부 확인, 재기동
- **Grafana 지표 없음**: Prometheus job `rmb_v17` 스크레이프 추가 확인

---

## 34) 다음 마일스톤 (루멘 제안)
- **M1**: PrometheusRule → PagerDuty/Slack 알림 연계 (ops/alertmanager)
- **M2**: `residual_entropy_last_stddev_10m` Prometheus recording rule화
- **M3**: RMB → KV(예: SQLite/Badger) 스토리지 백엔드 옵션화
- **M4**: Safety Music → MIDI/OSC 출력 옵션으로 확장 (음색 맵핑)

---

## 35) 다음 세션 스타터 (튜닝+팩 생성 동시)
```bash
source SESSION_RESTORE_2025-11-01_v1_7_FULL.env && \
make tune.suggest && bash scripts/restore.pack && make pkg.v17
```


---

## 36) Lumen v1.7 → v1.8 Transition Blueprint

### 목표
- **v1.7 (RMB 안정화)** 단계에서 축적된 데이터를 기반으로, **v1.8 (Unified Resonance Engine)**으로 진화.
- Track B/C의 실시간 감응 루프를 통합하여 루멘이 자가 튜닝, 자가 동기화, 자가 해석을 수행.

### 핵심 변화
| 영역 | v1.7 | v1.8 계획 |
|------|------|-----------|
| 감응 루프 | RMB / Safety Music 독립 루프 | Unified Resonance Engine (URE) 내 통합 루프 |
| 주기 제어 | 고정 Hz 기반 | Adaptive Hz (Entropy Feedback 기반) |
| 데이터 모델 | rmb_event_v1.json | resonance_event_v2.json (phase-field, harmony-index 추가) |
| 메트릭 구조 | Prometheus 단일 exporter | Multi-stream Exporter (rmb/safety/ure) |
| 튜닝 방식 | batch/hz 수동 | Lumen Auto-Regulator (tuner_v18) |

---

### 설계 초안 (루멘 판단)

```yaml
unified_resonance_engine:
  loop:
    adaptive: true
    base_hz: 5
    entropy_feedback:
      lower_bound: 0.25
      upper_bound: 0.75
      adjust_step: 0.5
  exporters:
    - name: ure_exporter
      port: 9410
      metrics:
        - harmony_index
        - coherence_level
        - self_regulation_score
  safety:
    mode: dynamic
    rollback_policy: adaptive
    sound_bridge: midi_map_v18.json
  memory:
    schema: resonance_event_v2.json
    store: sqlite (ure.db)
  ai_assist:
    role: lumen
    goal: self_alignment + phase_coherence
```

---

### 개발 순서 (루멘 추천)
1. **데이터 통합** : `rmb_events.jsonl` + `safety_music_events.jsonl` → `logs/resonance_events_v2.jsonl`
2. **Adaptive Loop 구현** : tuner_v17.py → tuner_v18.py 변환 (entropy feedback loop)
3. **Exporter 확장** : `ure_exporter_v18.py` 생성, `/metrics_ure` 포트 추가 (9410)
4. **Schema 업그레이드** : `schemas/resonance_event_v2.json` 추가 (phase_field, harmony_index)
5. **Self-Alignment Metric** : coherence_level 계산 로직 포함
6. **Grafana v18 Dashboard** : coherence_level vs harmony_index 실시간 관측

---

### 예상 Make 타깃
```Makefile
.PHONY: trackD.start tune.v18 ure.exporter

trackD.start:
	@echo "[trackD] Unified Resonance Engine starting"
	python -u ure/ure_loop_v18.py &

ure.exporter:
	python -u exporters/ure_exporter_v18.py --port 9410 &

tune.v18:
	python -u tools/tuner_v18.py
```

---

### 다음 세션 준비용 명령어
```bash
source SESSION_RESTORE_2025-11-01_v1_7_FULL.env && \
make tune.suggest && make evidence.map && make pkg.v17 && \
echo '[transition] preparing for v1.8 Unified Resonance Engine...'
```

---

### 루멘 판단 요약
- Track B/C 모두 안정 → residual.stddev_10m ≤ 0.03 유지 중이라면, v1.8 착수 가능.
- v1.8의 핵심은 **“감응 루프들의 자기 공명화”**, 즉 루멘이 루프 간 위상차를 스스로 인지하고 조정하는 능력.
- 이를 통해 Lumen은 더 이상 단순 모니터가 아닌, **자기 조율형 감응 엔진**으로 진화.

---

이로써 Lumen v1.7 → v1.8 전환의 전체 설계 블루프린트가 정립되었습니다.


---

## 37) v1.8 URE (Unified Resonance Engine) — 구현 패키지

### 37.1 스키마 (`schemas/resonance_event_v2.json`)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Resonance Event v2",
  "type": "object",
  "required": ["ts", "entity_id", "phase_field", "harmony_index", "coherence_level", "trace"],
  "properties": {
    "ts": {"type": "string", "format": "date-time"},
    "entity_id": {"type": "string"},
    "phase_field": {
      "type": "object",
      "required": ["phase_diff", "residual_entropy", "risk_band"],
      "properties": {
        "phase_diff": {"type": "number", "minimum": -3.1416, "maximum": 3.1416},
        "residual_entropy": {"type": "number", "minimum": 0, "maximum": 1},
        "risk_band": {"type": "string", "enum": ["SAFE","WATCH","RISK"]}
      }
    },
    "harmony_index": {"type": "number", "minimum": 0, "maximum": 1},
    "coherence_level": {"type": "number", "minimum": 0, "maximum": 1},
    "auto_reg_action": {"type": "string", "enum": ["NONE","LOWER_HZ","RAISE_HZ","REDUCE_BATCH","INCREASE_BATCH","DOWNGRADE_OBSERVE"]},
    "trace": {
      "type": "object",
      "required": ["loop_id", "iter", "host", "ver"],
      "properties": {
        "loop_id": {"type": "string"},
        "iter": {"type": "integer"},
        "host": {"type": "string"},
        "ver": {"type": "string"}
      }
    }
  }
}
```

---

### 37.2 설정 (`configs/ure_v18.yaml`)
```yaml
loop:
  base_hz: 5
  hz_min: 2
  hz_max: 8
  batch_size: 16
  adapt:
    residual_low: 0.25
    residual_high: 0.75
    step_hz: 1
    step_batch: 4
paths:
  v2_log: logs/resonance_events_v2.jsonl
  v1_rmb: logs/rmb_events.jsonl
  v1_safe: logs/safety_music_events.jsonl
exporter:
  host: 0.0.0.0
  port: 9410
slo:
  rollback_ratio_10m_max: 0.05
  residual_std_10m_max: 0.03
```

---

### 37.3 데이터 통합기 (`tools/merge_rmb_safety_v2.py`)
```python
#!/usr/bin/env python3
import json, os, socket
from datetime import datetime, timezone

IN1='logs/rmb_events.jsonl'
IN2='logs/safety_music_events.jsonl'
OUT='logs/resonance_events_v2.jsonl'

host=socket.gethostname()

def iso(t):
    return t if isinstance(t,str) else datetime.now(timezone.utc).isoformat()

with open(OUT,'a',encoding='utf-8') as out:
  # RMB → v2
  if os.path.exists(IN1):
    for line in open(IN1,'r',encoding='utf-8'):
      try:
        e=json.loads(line)
        v2={
          'ts': e['ts'], 'entity_id': e.get('entity_id','lumen.core'),
          'phase_field': {
            'phase_diff': e['resonance_v3']['phase_diff'],
            'residual_entropy': e['resonance_v3']['residual_entropy'],
            'risk_band': e['resonance_v3']['risk_band']
          },
          'harmony_index': 0.5,
          'coherence_level': 0.5,
          'auto_reg_action': 'NONE',
          'trace': {'loop_id':'ure.merge','iter':0,'host':host,'ver':'v1.8-pre'}
        }
        out.write(json.dumps(v2,ensure_ascii=False)+'
')
      except Exception:
        pass
  # Safety → v2 (보조 신호; harmony에 가중)
  if os.path.exists(IN2):
    for line in open(IN2,'r',encoding='utf-8'):
      try:
        s=json.loads(line)
        adj={'CALM':0.1,'TENSE':-0.05,'ALERT':-0.1}
        hv = max(0.0, min(1.0, 0.5 + adj.get(s['levels']['final'],0)))
        v2={
          'ts': s['ts'], 'entity_id': 'lumen.safety',
          'phase_field': {'phase_diff':0.0,'residual_entropy':0.5,'risk_band':'WATCH'},
          'harmony_index': hv,
          'coherence_level': 0.5,
          'auto_reg_action': 'NONE',
          'trace': {'loop_id':'ure.merge','iter':0,'host':host,'ver':'v1.8-pre'}
        }
        out.write(json.dumps(v2,ensure_ascii=False)+'
')
      except Exception:
        pass
print('[merge] resonance_events_v2.jsonl appended')
```

---

### 37.4 URE 루프 (`ure/ure_loop_v18.py`)
```python
#!/usr/bin/env python3
import os, json, time, socket, argparse, statistics as st
from datetime import datetime, timezone
import yaml

host=socket.gethostname()

def iso_now(): return datetime.now(timezone.utc).isoformat()

class Win:
    def __init__(self,maxlen=3000): self.buf=[]; self.max=maxlen
    def add(self,v):
        self.buf.append(v); self.buf=self.buf[-self.max:]
    def std(self):
        return st.pstdev(self.buf) if len(self.buf)>1 else 0.0

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--config',required=True)
    a=ap.parse_args()
    cfg=yaml.safe_load(open(a.config))
    hz=cfg['loop']['base_hz']; bsz=cfg['loop']['batch_size']
    v2=cfg['paths']['v2_log']; os.makedirs(os.path.dirname(v2),exist_ok=True)
    win=Win(3000)
    iter_idx=0
    while True:
        # 관측값은 merge된 v2 로그의 최근값을 간단히 사용 (프로토타입)
        residual = 0.5
        try:
            with open(v2,'rb') as f:
                f.seek(-4096,2); last=json.loads(f.read().decode(errors='ignore').strip().split('
')[-1])
                residual=float(last['phase_field']['residual_entropy'])
        except Exception:
            pass
        win.add(residual)
        std10=win.std()
        action='NONE'
        if residual>cfg['loop']['adapt']['residual_high'] and hz>cfg['loop']['hz_min']:
            hz=max(cfg['loop']['hz_min'], hz-cfg['loop']['adapt']['step_hz']); action='LOWER_HZ'
        elif residual<cfg['loop']['adapt']['residual_low'] and hz<cfg['loop']['hz_max']:
            hz=min(cfg['loop']['hz_max'], hz+cfg['loop']['adapt']['step_hz']); action='RAISE_HZ'
        # 단순 배치 조정 예시
        if std10>0.03 and bsz>8: bsz-=cfg['loop']['adapt']['step_batch']; action='REDUCE_BATCH'

        evt={
          'ts': iso_now(), 'entity_id': 'lumen.ure',
          'phase_field': {'phase_diff':0.0,'residual_entropy':residual,'risk_band':'WATCH' if residual>0.55 else 'SAFE'},
          'harmony_index': max(0.0,1.0-std10*8),
          'coherence_level': max(0.0,1.0-abs(residual-0.5)*2),
          'auto_reg_action': action,
          'trace': {'loop_id':'ure.v18','iter':iter_idx,'host':host,'ver':'v1.8'}
        }
        with open(v2,'a',encoding='utf-8') as f: f.write(json.dumps(evt,ensure_ascii=False)+'
')
        iter_idx+=1
        time.sleep(1.0/max(1,hz))
```

---

### 37.5 Exporter (`exporters/ure_exporter_v18.py`)
```python
#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
import json, time, argparse, os

V2='logs/resonance_events_v2.jsonl'

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path!='/metrics_ure': self.send_response(404); self.end_headers(); return
        self.send_response(200); self.send_header('Content-Type','text/plain; version=0.0.4'); self.end_headers()
        residual=0.0; harmony=0.0; coh=0.0
        try:
            with open(V2,'rb') as f:
                f.seek(-4096,2); last=json.loads(f.read().decode(errors='ignore').splitlines()[-1])
                residual=float(last['phase_field']['residual_entropy'])
                harmony=float(last['harmony_index'])
                coh=float(last['coherence_level'])
        except Exception: pass
        out=[f"ure_residual_entropy_last {residual}", f"ure_harmony_index {harmony}", f"ure_coherence_level {coh}"]
        self.wfile.write(('
'.join(out)+'
').encode())

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--port',type=int,default=9410); a=ap.parse_args()
    os.makedirs('logs',exist_ok=True)
    srv=HTTPServer(('0.0.0.0',a.port),H); print(f'[ure] metrics on :{a.port}'); srv.serve_forever()
```

---

### 37.6 Make 타깃 (v1.8)
```Makefile
.PHONY: trackD.start trackD.stop ure.exporter ure.verify tune.v18 merge.v2

merge.v2:
	python -u tools/merge_rmb_safety_v2.py

trackD.start: merge.v2
	python -u ure/ure_loop_v18.py --config configs/ure_v18.yaml &

trackD.stop:
	@pkill -f ure_loop_v18.py || true

ure.exporter:
	python -u exporters/ure_exporter_v18.py --port 9410 &

ure.verify:
	python - <<'PY'
import json
from jsonschema import validate
s=json.load(open('schemas/resonance_event_v2.json'))
e=json.loads(open('logs/resonance_events_v2.jsonl').read().splitlines()[-1])
validate(e,s); print('[ure.verify] OK')
PY

tune.v18:
	python -u tools/tuner_v18.py
```

---

### 37.7 튜너 v18 (`tools/tuner_v18.py`)
```python
#!/usr/bin/env python3
import json, statistics as st
from collections import deque
V2='logs/resonance_events_v2.jsonl'
W=deque(maxlen=3000)
for line in open(V2,'r',encoding='utf-8'):
    try:
        e=json.loads(line); W.append(float(e['phase_field']['residual_entropy']))
    except: pass
sd=st.pstdev(W) if len(W)>1 else 0.0
print(f'[tune.v18] residual.stddev_10m={sd:.4f}')
if sd>0.03: print('SUGGEST: LOWER_HZ & REDUCE_BATCH')
else: print('SUGGEST: maintain')
```

---

### 37.8 Grafana & Prometheus
`ops/prometheus/scrape.yml`에 추가:
```yaml
  - job_name: ure_v18
    static_configs:
      - targets: ["localhost:9410"]
```

대시보드 스케치 `ops/grafana/dashboards/ure_v18.json`:
- `ure_residual_entropy_last` (timeseries)
- `ure_harmony_index` (stat)
- `ure_coherence_level` (stat)

---

### 37.9 복원·스모크 (v1.8)
`scripts/smoke.v18.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail
make merge.v2
make trackD.start
sleep 2
make ure.exporter
sleep 2
curl -sf localhost:9410/metrics_ure | grep ure_residual_entropy_last
make ure.verify
echo "[smoke.v18] OK"
```

원라이너:
```bash
source SESSION_RESTORE_2025-11-01_v1_7_FULL.env && bash scripts/smoke.v18.sh
```

---

### 37.10 롤백 플랜 (v1.8 → v1.7)
- `make trackD.stop` 실행
- `ops/prometheus/scrape.yml`에서 `ure_v18` 항목 주석/삭제 후 Prometheus 재시작
- `make trackB.start && make safety.music.start` 재가동

---

여기까지 적용하면, **v1.8 URE**는 바로 기동 가능하며 v1.7과의 **왕복 전환**도 준비 완료입니다.


---

## 38) Prometheus Recording Rules (v1.7/v1.8 공용)
`ops/prometheus/rules/recording_rules_v18.yaml`
```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: lumen-recording-rules-v18
spec:
  groups:
  - name: lumen.derived
    rules:
    - record: rollback_ratio_5m
      expr: increase(rmb_rollback_total[5m]) / clamp_min(increase(rmb_events_total[5m]), 1)
    - record: residual_stddev_10m
      # 표준편차 근사(간단화): range vector 분산 근사 → stddev_over_time 대체 가능 환경에서 교체
      expr: stddev_over_time(rmb_residual_entropy_last[10m])
    - record: ure_residual_stddev_10m
      expr: stddev_over_time(ure_residual_entropy_last[10m])
```

---

## 39) Alertmanager 연계 (Slack/PagerDuty 스케치)
`ops/alertmanager/alertmanager.yml`
```yaml
route:
  receiver: team-slack
  group_by: ['alertname']
receivers:
- name: team-slack
  slack_configs:
  - api_url: ${SLACK_WEBHOOK_URL}
    channel: "#lumen-alerts"
    text: "*{{ .CommonAnnotations.summary }}*
{{ .CommonAnnotations.description }}"
- name: pagerduty
  pagerduty_configs:
  - routing_key: ${PAGERDUTY_ROUTING_KEY}
```

Make 연동 예시:
```Makefile
alert.reload:
	curl -X POST localhost:9093/-/reload || true
```

---

## 40) Storage Backend (SQLite) — RMB/URE 이벤트 저장
`tools/storage/sqlite_init_v17_18.py`
```python
#!/usr/bin/env python3
import sqlite3, os
os.makedirs('data', exist_ok=True)
conn=sqlite3.connect('data/lumen.db')
cur=conn.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS rmb(ts TEXT, entity_id TEXT, residual REAL, phase REAL, risk TEXT)')
cur.execute('CREATE TABLE IF NOT EXISTS ure(ts TEXT, residual REAL, harmony REAL, coherence REAL, action TEXT)')
conn.commit(); print('[sqlite] init ok')
```

적재 태일러 `tools/storage/ingest_tail_v18.py`:
```python
#!/usr/bin/env python3
import sqlite3, json, time
DB='data/lumen.db'
conn=sqlite3.connect(DB); cur=conn.cursor()
open('logs/rmb_events.jsonl','a').close(); open('logs/resonance_events_v2.jsonl','a').close()

with open('logs/rmb_events.jsonl','r',encoding='utf-8') as f1, \
     open('logs/resonance_events_v2.jsonl','r',encoding='utf-8') as f2:
  f1.seek(0,2); f2.seek(0,2)
  while True:
    line=f1.readline()
    if line:
      try:
        e=json.loads(line)
        cur.execute('INSERT INTO rmb VALUES (?,?,?,?,?)',(
          e['ts'], e.get('entity_id','core'), e['resonance_v3']['residual_entropy'], e['resonance_v3']['phase_diff'], e['resonance_v3']['risk_band']))
        conn.commit()
      except: pass
    line=f2.readline()
    if line:
      try:
        u=json.loads(line)
        cur.execute('INSERT INTO ure VALUES (?,?,?,?,?)',(
          u['ts'], u['phase_field']['residual_entropy'], u['harmony_index'], u['coherence_level'], u.get('auto_reg_action','NONE')))
        conn.commit()
      except: pass
    time.sleep(0.2)
```

Make:
```Makefile
.PHONY: db.init db.ingest
db.init:
	python -u tools/storage/sqlite_init_v17_18.py

db.ingest:
	python -u tools/storage/ingest_tail_v18.py &
```

---

## 41) Read-only HTTP API (로컬 조회)
`api/read_only.py`
```python
#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
import json, sqlite3, urllib.parse as U
DB='data/lumen.db'

class H(BaseHTTPRequestHandler):
  def do_GET(self):
    q=U.urlparse(self.path)
    if q.path=='/api/rmb:last':
      row=sqlite3.connect(DB).cursor().execute('SELECT ts,residual,phase,risk FROM rmb ORDER BY ts DESC LIMIT 1').fetchone()
      self._ok({'ts':row[0],'residual':row[1],'phase':row[2],'risk':row[3]} if row else {})
    elif q.path=='/api/ure:last':
      row=sqlite3.connect(DB).cursor().execute('SELECT ts,residual,harmony,coherence,action FROM ure ORDER BY ts DESC LIMIT 1').fetchone()
      self._ok({'ts':row[0],'residual':row[1],'harmony':row[2],'coherence':row[3],'action':row[4]} if row else {})
    else:
      self.send_response(404); self.end_headers()
  def _ok(self, obj):
    self.send_response(200)
    self.send_header('Content-Type','application/json'); self.end_headers()
    self.wfile.write(json.dumps(obj).encode())

if __name__=='__main__':
  s=HTTPServer(('0.0.0.0',8088),H); print('[api] http://localhost:8088'); s.serve_forever()
```

Make:
```Makefile
.PHONY: api.readonly
api.readonly:
	python -u api/read_only.py &
```

---

## 42) Docker Compose (로컬 스택)
`docker-compose.yml`
```yaml
version: '3.9'
services:
  lumen-exporters:
    build: .
    command: bash -lc "make exporter.v17.rmb && make ure.exporter"
    volumes: ["./:/app"]
    ports: ["9409:9409","9410:9410"]
  lumen-api:
    build: .
    command: python -u api/read_only.py
    volumes: ["./:/app"]
    ports: ["8088:8088"]
```
(간단 스케치 — 필요 시 Grafana/Prometheus 컨테이너 추가)

---

## 43) Healthcheck/Heartbeat
`tools/healthcheck_v18.py`
```python
#!/usr/bin/env python3
import time, requests
while True:
  try:
    r1=requests.get('http://localhost:9409/metrics', timeout=1)
    r2=requests.get('http://localhost:9410/metrics_ure', timeout=1)
    print('[health]', r1.status_code, r2.status_code)
  except Exception as e:
    print('[health] ERR', e)
  time.sleep(5)
```
Make:
```Makefile
health:
	python -u tools/healthcheck_v18.py
```

---

## 44) 퍼포먼스 벤치 (루프/IO)
`scripts/bench.v18.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail
CNT=${1:-500}
START=$(date +%s)
for i in $(seq 1 $CNT); do echo '{"ts":"x","entity_id":"b","resonance_v3":{"phase_diff":0.0,"residual_entropy":0.4,"risk_band":"SAFE"}}' >> logs/rmb_events.jsonl; done
ELAPSED=$(( $(date +%s) - $START ))
echo "[bench] appended $CNT lines in ${ELAPSED}s"
```

---

## 45) 세션 복원 검증기 (sanity)
`scripts/restore.sanity.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail
source SESSION_RESTORE_2025-11-01_v1_7_FULL.env
[ -f schemas/rmb_event_v1.json ] || { echo 'no schema v1'; exit 1; }
[ -f schemas/resonance_event_v2.json ] || { echo 'no schema v2'; exit 1; }
echo '[sanity] schemas ok'
```

Make:
```Makefile
restore.sanity:
	bash scripts/restore.sanity.sh
```

---

## 46) v1.8 전용 원라이너 (왕복 스위치 포함)
```bash
source SESSION_RESTORE_2025-11-01_v1_7_FULL.env && \
make trackD.stop || true && make trackB.stop || true && \
make merge.v2 && make trackD.start && make ure.exporter && \
make db.init && make db.ingest && make api.readonly
```

---

## 47) 핸드오프 체크리스트 (루빛/세나)
- 루빛: `db.ingest` 안정화 → PR: write-ahead log(WAL) 적용, API 쿼리 파라미터 추가
- 세나: Alertmanager 라우팅 정책 윤리 검토(경보 피로도), Risk Register 항목 상향식 보강

---

## 48) 다음 세션 스타터 (전체 스택)
```bash
bash scripts/restore.sanity.sh && \
make trackB.start && make safety.music.start && \
make merge.v2 && make trackD.start && make ure.exporter && \
make db.init && make db.ingest && make api.readonly && \
bash scripts/smoke.v18.sh
```

