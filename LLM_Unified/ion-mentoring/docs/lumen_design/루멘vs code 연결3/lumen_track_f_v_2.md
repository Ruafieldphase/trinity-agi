# 🌕 Lumen Track F — v2.0 α3 Fusion Auto‑Align Engine
> 목적 : Fusion v20 라인의 **Adaptive Alignment / Non‑Linear Gain Surface / Evidence Ingestion** 3대 모듈을 통합.
>
> 기반 : v2.0 α2 (Fusion + Sensors + Risk‑Aware Autotune) → α3에서 자동화 루프와 데이터 증거망 연결을 완성.

---

## A0) Session Restore Block (v2.0 α3 Init)
```bash
# α3 Fusion Auto‑Align init
export $(grep -v '^#' SESSION_RESTORE_v1_9_5.env | xargs) && \
make fusion.init && make sensor.ingest.start && \
make fusion.autoadapt.start && make evidence.ingest.start && \
bash scripts/smoke.v20.sh
```

---

## A1) Adaptive Alignment Loop (core)
**fusion/adaptive_align_v20.py**
```python
#!/usr/bin/env python3
# Self‑tuning Kalman alignment with Q/R auto update
import time, yaml, numpy as np

class AdaptiveKalman:
  def __init__(self,q=1e‑3,r=2e‑3):
    self.q,self.r=q,r; self.x=0; self.p=1
  def update(self,z):
    self.p+=self.q; k=self.p/(self.p+self.r)
    self.x=self.x+k*(z‑self.x); self.p=(1‑k)*self.p
    return self.x
  def adapt(self,residual):
    self.q *= 1+0.1*(abs(residual)‑0.02)
    self.r *= 1+0.05*(abs(residual)‑0.02)

# usage in fusion engine
```

---

## A2) Non‑Linear Gain Surface Fitter
**tools/gain_surface_fit.py**
```python
#!/usr/bin/env python3
import numpy as np, json
# 입력: bench_v20.log → phase_diff, entropy_ratio
# 출력: gain_surface.json

def fit_surface(data):
  x,y,z = data[:,0], data[:,1], data[:,2] # entropy, phase, kp
  A = np.c_[np.ones_like(x),x,y,x*y]
  coef,_,_,_ = np.linalg.lstsq(A,z,rcond=None)
  return dict(zip(['b0','bx','by','bxy'],coef.tolist()))
```

---

## A3) Evidence Bundle Ingestion
**evidence/ingestor_v20.py**
```python
#!/usr/bin/env python3
# Evidence Mapper 출력 jsonl → Prometheus recorder 포맷 변환
import json, time
from prometheus_client import Gauge, start_http_server
risk_g = Gauge('evidence_risk_count','risk entries count')
quote_g = Gauge('evidence_quote_count','quote entries count')

def ingest(path='data/evidence_bundle.jsonl'):
  while True:
    with open(path) as f:
      risks = quotes = 0
      for line in f:
        d=json.loads(line)
        if d.get('risk'): risks+=1
        if d.get('quote'): quotes+=1
    risk_g.set(risks); quote_g.set(quotes)
    time.sleep(30)
```

---

## A4) Fusion Exporter 확장
`exporters/fusion_exporter_v20.py` → 지표 추가 : `fusion_align_q`, `fusion_align_r`, `fusion_gain_kp/ki/kd`

---

## A5) Prometheus Rules (ops/prometheus/rules/fusion_adapt_v20.yaml)
```yaml
groups:
- name: fusion_adapt_v20
  rules:
  - record: fusion:q_r_ratio
    expr: fusion_align_q / fusion_align_r
  - alert: FusionAdaptDiverge
    expr: fusion:q_r_ratio > 2.5
    for: 5m
    labels: {severity: critical}
```

---

## A6) Bench 및 Smoke
```bash
bash scripts/bench.v20.sh 1800 > out/bench_v20_alpha3.log
python3 tools/gain_surface_fit.py < out/bench_v20_alpha3.log > configs/gain_surface.json
```

---

## A7) 대시보드 지표
- `fusion_align_q`, `fusion_align_r`, `fusion:q_r_ratio`
- `fusion:harmony_index`, `fusion:coherence_p95_10m`
- `evidence_risk_count`, `evidence_quote_count`

---

## A8) 운영 기준
- `fusion:q_r_ratio ≤ 1.8` 안정 구간
- `fusion:coherence_p95_10m ≥ 0.90`
- `evidence_risk_count ↗︎ + quote_count ↗︎` → 정상 유입

---

## A9) v2.0 α3 Restore Block
```bash
# v2.0 α3 — Adaptive Align + Gain Surface + Evidence Ingest
make fusion.init && make fusion.autoadapt.start && \
make evidence.ingest.start && bash scripts/bench.v20.sh 1800
```


---

## A10) Make 타깃 추가 (α3)
```makefile
.PHONY: fusion.autoadapt.start evidence.ingest.start fusion.autoadapt.stop evidence.ingest.stop

fusion.autoadapt.start:
	@echo "[Fusion] adaptive align start"
	@python3 fusion/adaptive_align_v20.py --config configs/fusion_v20.yaml &

evidence.ingest.start:
	@echo "[Evidence] ingest start"
	@python3 evidence/ingestor_v20.py &

fusion.autoadapt.stop:
	@pkill -f adaptive_align_v20.py || true

evidence.ingest.stop:
	@pkill -f ingestor_v20.py || true
```

---

## A11) Exporter 확장 (발췌)
**exporters/fusion_exporter_v20.py**
```python
from prometheus_client import Gauge
fusion_align_q = Gauge('fusion_align_q','kalman Q')
fusion_align_r = Gauge('fusion_align_r','kalman R')
fusion_gain_kp = Gauge('fusion_gain_kp','gain kp')
fusion_gain_ki = Gauge('fusion_gain_ki','gain ki')
fusion_gain_kd = Gauge('fusion_gain_kd','gain kd')
# adaptive_align_v20.py에서 값 갱신 훅 호출
```

---

## A12) Smoke v20 (α3 예산 체크)
**scripts/smoke.v20.sh (보강)**
```bash
#!/usr/bin/env bash
set -euo pipefail
curl -fsS localhost:9310/metrics_fusion | grep fusion_coherence_level >/dev/null
Q=$(curl -fsS localhost:9310/metrics_fusion | awk '/fusion_align_q/{print $2}')
R=$(curl -fsS localhost:9310/metrics_fusion | awk '/fusion_align_r/{print $2}')
[ -n "$Q" ] && [ -n "$R" ] && echo "[smoke.v20] OK: Q=$Q R=$R"
```

---

## A13) α3 운영 기준 (간단)
- `fusion:q_r_ratio ≤ 1.8` (5m)
- `fusion:coherence_p95_10m ≥ 0.90`
- Evidence 지표 상승 추세(`evidence_*_count`)

---

## A14) α3 트러블슈팅 (간단)
- Q/R 발산: 입력 센서 노이즈 급증 → outlier_clip 적용, resample 정확도 재확인
- Coherence 저하: weights 조정(`weights.ure↑`, `weights.sensors↓`), tick_ms +20ms
- Evidence 0 지속: mapper/ingestor 경로 확인(`data/evidence_bundle.jsonl`)

---

## A15) α3 Compact Restore Block
```bash
# Short path for daily ops
make fusion.init && make fusion.autoadapt.start
make evidence.ingest.start && bash scripts/smoke.v20.sh
```


---

## A16) Bench Analyzer (α3 결과 자동 판정)
**tools/bench_analyze_v20.py**
```python
#!/usr/bin/env python3
# 입력: out/bench_v20_alpha3.log → p95/mean 계산 + 권장치 제안
import sys, numpy as np, json
coh=[]; qrr=[]
for ln in sys.stdin:
    try:
        _, key, val = ln.strip().split()
        v=float(val)
        if key=='fusion_coherence_level': coh.append(v)
        elif key in ('fusion:q_r_ratio','fusion_q_r_ratio','fusion_q_r_ratio'): qrr.append(v)
    except: pass
p95=lambda a: float(np.percentile(a,95)) if a else None
res={
  'coherence_p95': p95(coh),
  'q_r_ratio_mean': float(np.mean(qrr)) if qrr else None,
}
rec={}
if res['coherence_p95'] is not None and res['coherence_p95']<0.90:
    rec['weights']={'ure':0.8,'sensors':0.2}
    rec['tick_ms'] = 220
if res['q_r_ratio_mean'] is not None and res['q_r_ratio_mean']>1.8:
    rec['kalman']={'q':'-10%','r':'+10%'}
print(json.dumps({'metrics':res,'recommend':rec}, indent=2))
```

**사용법**
```bash
python3 tools/bench_analyze_v20.py < out/bench_v20_alpha3.log > out/bench_v20_alpha3.report.json
cat out/bench_v20_alpha3.report.json
```

---

## A17) Auto‑Patch Helper (권장치 적용 스크립트)
**tools/apply_recs_v20.sh**
```bash
#!/usr/bin/env bash
set -euo pipefail
REP=${1:-out/bench_v20_alpha3.report.json}
URE=$(jq -r '.recommend.weights.ure // empty' "$REP"); [ -n "$URE" ] && sed -i "s/^  ure:.*/  ure: $URE/" configs/fusion_v20.yaml
SEN=$(jq -r '.recommend.weights.sensors // empty' "$REP"); [ -n "$SEN" ] && sed -i "s/^  sensors:.*/  sensors: $SEN/" configs/fusion_v20.yaml
TICK=$(jq -r '.recommend.tick_ms // empty' "$REP"); [ -n "$TICK" ] && sed -i "s/^  tick_ms:.*/  tick_ms: $TICK/" configs/fusion_v20.yaml
KQ=$(jq -r '.recommend.kalman.q // empty' "$REP"); [ "$KQ" == "-10%" ] && awk '/^  kalman:/{p=1;print;next} p&&/^    q:/{sub(/: .*/,": 7.2e-4");p=0}1' configs/fusion_v20.yaml > /tmp/f && mv /tmp/f configs/fusion_v20.yaml
KR=$(jq -r '.recommend.kalman.r // empty' "$REP"); [ "$KR" == "+10%" ] && awk '/^  kalman:/{p=1;print;next} p&&/^    r:/{sub(/: .*/,": 3.3e-3");p=0}1' configs/fusion_v20.yaml > /tmp/f && mv /tmp/f configs/fusion_v20.yaml
```

**Make 타깃**
```makefile
.PHONY: fusion.autopatch
fusion.autopatch:
	@python3 tools/bench_analyze_v20.py < out/bench_v20_alpha3.log > out/bench_v20_alpha3.report.json && \
	bash tools/apply_recs_v20.sh out/bench_v20_alpha3.report.json
```

---

## A18) v2.0 α3.1 Session Restore Block (Analyze→Patch→재벤치)
```bash
bash scripts/bench.v20.sh 1800 > out/bench_v20_alpha3.log
make fusion.autopatch
bash scripts/bench.v20.sh 900 >> out/bench_v20_alpha3.log
python3 tools/bench_analyze_v20.py < out/bench_v20_alpha3.log | tee out/bench_v20_alpha3.report.json
```

---

## A19) Risk‑Aware Autotune Live Hook
**fusion/adaptive_align_v20.py (발췌)**
```python
# entropy_ratio 기반 실시간 게인 커브 적용 (risk_autotune_v20.yaml 사용)
import yaml
curv = yaml.safe_load(open('configs/risk_autotune_v20.yaml'))['nonlinear_gain']

def interp(curve, x):
    for i in range(1,len(curve)):
        x0,y0=curve[i-1]; x1,y1=curve[i]
        if x<=x1:
            t=(x-x0)/(x1-x0) if x1!=x0 else 0
            return y0+(y1-y0)*t
    return curve[-1][1]

# loop 내부(매 스텝)
kp = interp(curv['kp_curve'], entropy_ratio)
kd = interp(curv['kd_curve'], entropy_ratio)
ki = curv.get('ki_base', 0.08)
# exporter 갱신: fusion_gain_kp/ki/kd.set(...)
```

---

## A20) Fusion Canary Metric Gate (Argo 연동)
**ops/k8s/fusion-analysis-templates.yaml**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata: {name: fusion-gate}
spec:
  metrics:
  - name: coherence
    interval: 60s
    successCondition: result >= 0.90
    provider:
      prometheus:
        address: http://prometheus:9090
        query: fusion:coherence_p95_10m
  - name: qrr
    interval: 60s
    successCondition: result <= 1.80
    provider:
      prometheus:
        address: http://prometheus:9090
        query: avg_over_time(fusion:q_r_ratio[10m])
```

**Make 타깃**
```makefile
.PHONY: fusion.rollout.canary
fusion.rollout.canary:
	@kubectl apply -f ops/k8s/fusion-analysis-templates.yaml && \
	kubectl argo rollouts set image fusion-v20 fusion=fusion:v2.0a3
```

---

## A21) α3 Compact Ops Checklist
- [ ] `make fusion.autoadapt.start` 후 **/metrics_fusion**에 `fusion_align_q/r` 노출 확인
- [ ] 15~30분 벤치 → `A16 Analyzer`로 보고서 생성
- [ ] `make fusion.autopatch` 1회 적용, 재벤치 15분
- [ ] `coherence_p95 ≥ 0.90` & `q_r_ratio ≤ 1.80` 달성 시 캡처
- [ ] 필요 시 **A19 Live Hook** 커브 보정 (kp↘, kd↗ 경사 강화)
- [ ] 카나리 배포는 **A20 Gate**로만 진행

---

## A22) v2.0 α3 Compact Restore Block (최종)
```bash
# α3 Compact — 일상 운용용
make fusion.init && make fusion.autoadapt.start && make evidence.ingest.start
bash scripts/smoke.v20.sh
bash scripts/bench.v20.sh 1800 > out/bench_v20_alpha3.log
make fusion.autopatch
bash scripts/bench.v20.sh 900 >> out/bench_v20_alpha3.log
python3 tools/bench_analyze_v20.py < out/bench_v20_alpha3.log | tee out/bench_v20_alpha3.report.json
```


---

## A23) α4 Preview — Beta Readiness Gates
**준비 기준(모두 충족 시 α4 베타 전환 제안)**
- SLO: `fusion:coherence_p95_10m ≥ 0.91` 24h, `avg_over_time(fusion:q_r_ratio[24h]) ≤ 1.70`
- Fault: chaos(jitter/spike) 2회 연속 합격(알림≤60s, 자가복구≤5m)
- Evidence: `evidence_risk_count`/`quote_count` 순증(0 → N), 누락률<1%

**PromQL 게이트(ops/prometheus/rules/fusion_beta_gates.yaml)**
```yaml
groups:
- name: fusion_beta_gates
  rules:
  - record: fusion:coh_ok_24h
    expr: avg_over_time(fusion:coherence_p95_10m[24h]) >= 0.91
  - record: fusion:qrr_ok_24h
    expr: avg_over_time(fusion:q_r_ratio[24h]) <= 1.70
  - record: fusion:evidence_ok_24h
    expr: increase(evidence_risk_count[24h]) > 0 and increase(evidence_quote_count[24h]) > 0
```

---

## A24) Adaptive State Persist (Q/R & Gains)
**tools/adapt_state_store.py**
```python
#!/usr/bin/env python3
# JSON state persist: Q,R,kp,ki,kd + ts
import json, time, sys
state = {
  'ts': time.time(),
  'q': float(sys.argv[1]), 'r': float(sys.argv[2]),
  'kp': float(sys.argv[3]), 'ki': float(sys.argv[4]), 'kd': float(sys.argv[5])
}
open('data/adapt_state.json','w').write(json.dumps(state,indent=2))
print('[store] data/adapt_state.json updated')
```

**Make 타깃**
```makefile
.PHONY: adapt.state.save
adapt.state.save:
	@python3 tools/adapt_state_store.py $$Q $$R $$KP $$KI $$KD
```

**adaptive_align_v20.py 훅**: 안정 구간 진입 시 `adapt.state.save` 호출(비차단)

---

## A25) Config Lint & Validation
**tools/config_lint_v20.py**
```python
#!/usr/bin/env python3
import sys, yaml
cfg=yaml.safe_load(open('configs/fusion_v20.yaml'))
assert 0.6 <= cfg['weights']['ure'] <= 0.9
assert 0.1 <= cfg['weights']['sensors'] <= 0.4
assert 120 <= cfg['fusion']['tick_ms'] <= 300
print('[lint] fusion_v20.yaml OK')
```

**Make 타깃**
```makefile
.PHONY: config.lint
config.lint:
	@python3 tools/config_lint_v20.py
```

---

## A26) Rate-Limit & MT-Safety (옵션)
**api/gateway.lua (nginx+lua 예시)**
```lua
-- /metrics_fusion QPS 제한, 테넌트 키별 버킷
local tenant = ngx.req.get_headers()["X-Tenant"] or "default"
-- (간략 예시) 테넌트 버킷 점검 후 429
```

**ops/policies/mt_limits.yaml**: 테넌트별 QPS/대역폭 표 정의

---

## A27) Reproducibility — Seeded Replay
**scripts/replay.capture.sh**
```bash
#!/usr/bin/env bash
set -euo pipefail
OUT=data/replay/cap_$(date +%Y%m%dT%H%M%S).ndjson
journalctl -u bridge.service -S -5min | grep metrics_bridge > "$OUT"
echo "[replay] saved → $OUT"
```

**scripts/replay.seed.sh**
```bash
#!/usr/bin/env bash
python3 sensors/sources/file_replay.py --path "$1" --speed 1.0
```

---

## A28) Evidence Bundle Quality Rules
**ops/prometheus/rules/evidence_quality_v20.yaml**
```yaml
groups:
- name: evidence_quality
  rules:
  - alert: EvidenceIngestStalled
    expr: increase(evidence_risk_count[10m]) == 0
    for: 10m
    labels: {severity: warning}
  - alert: EvidenceQuoteSkew
    expr: (increase(evidence_quote_count[1h]) / (increase(evidence_risk_count[1h])+1e-9)) > 5
    for: 1h
    labels: {severity: info}
```

---

## A29) Rollback Playbook (α3 → E Track 안정판)
```bash
# 1) 중단
make fusion.autoadapt.stop && make evidence.ingest.stop
# 2) 안정 파라미터 적용
sed -i 's/^  ure:.*/  ure: 0.82/' configs/fusion_v20.yaml
sed -i 's/^  sensors:.*/  sensors: 0.18/' configs/fusion_v20.yaml
sed -i 's/^  tick_ms:.*/  tick_ms: 220/' configs/fusion_v20.yaml
# 3) 재가동 + 스모크
make fusion.autoadapt.start && bash scripts/smoke.v20.sh
# 4) 15m 벤치 후 판단
bash scripts/bench.v20.sh 900 > out/bench_v20_safe.log
```

---

## A30) v2.0 α4 Session Restore Block (Beta Gates 포함)
```bash
# α4: Beta readiness gates + state persist + lint + replay
make config.lint
bash scripts/bench.v20.sh 1800 > out/bench_v20_alpha4.log
make fusion.autopatch && make adapt.state.save Q=7.2e-4 R=3.3e-3 KP=0.33 KI=0.08 KD=0.16
kubectl apply -f ops/prometheus/rules/fusion_beta_gates.yaml
```


---

## A31) v2.0 β Rollout Plan (Preview→Canary→Beta)
**단계**
1) Preview: 1 replica, 내부 대시보드 전용
2) Canary: 10→30% 트래픽, **A20 게이트**로 자동 판정
3) Beta: 50% 트래픽, 장애시 **A29 롤백**

**ops/k8s/fusion-rollout.yaml (발췌)**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata: {name: fusion-v20}
spec:
  replicas: 2
  strategy:
    canary:
      canaryService: fusion-svc-canary
      stableService: fusion-svc-stable
      steps:
        - setWeight: 10
        - analysis: {templates: [{templateName: fusion-gate}]}
        - setWeight: 30
        - analysis: {templates: [{templateName: fusion-gate}]}
        - setWeight: 50
```

**Make 타깃**
```makefile
.PHONY: fusion.rollout.beta
fusion.rollout.beta:
	@kubectl apply -f ops/k8s/fusion-rollout.yaml && \
	kubectl argo rollouts promote fusion-v20 || true
```

---

## A32) v2.0 β SLO / Error Budget (초안)
- `fusion:coherence_p95_10m ≥ 0.905` (준수율 ≥ 99.0%)
- `avg_over_time(fusion:q_r_ratio[24h]) ≤ 1.70` (준수율 ≥ 99.0%)
- Evidence Ingest 성공률 ≥ 99.0%

위반 누적 2.5%p 이상 → **Feature Freeze** & **A29 롤백** 수행

---

## A33) Incident Playbook (β)
- Sev2: `coherence_p95_10m < 0.86` 10m → **weights URE↑, tick_ms +20**, Chaos 여부 확인
- Sev1: `q_r_ratio > 2.8` 5m → **fusion.autoadapt.stop** 후 안정 파라미터 적용(A29)
- Postmortem: 24h 내 Evidence bundle에 원인/조치 기록

---

## A34) Privacy & Data Handling (Sensors)
- PII/PCI 불수집 원칙, 파일 리플레이는 **내부 샘플만**
- Evidence bundle은 **회귀 테스트 용도**로만 보관, 30일 보존 후 파기
- MT 경계: `X-Tenant` 헤더 기반 Rate-limit(A26) 적용

---

## A35) Release Notes (v2.0 β Draft)
- Adaptive Kalman(Q/R) + Non-linear Gain Surface 실시간 적용
- Evidence Ingest → Prometheus Recorder 라우팅
- Canary 게이트(coherence, q_r_ratio) 통합

---

## A36) v2.0 β Session Restore Block
```bash
# v2.0 β: rollout + gates + budgets
make config.lint
kubectl apply -f ops/k8s/fusion-analysis-templates.yaml
make fusion.rollout.beta
kubectl apply -f ops/prometheus/rules/fusion_beta_gates.yaml
bash scripts/bench.v20.sh 1800 > out/bench_v20_beta.log
```

---

## A37) Migration Notes (E→F 공존)
- 포트: Bridge 9306 / Fusion 9310 (동시 운용 OK)
- 대시보드 분리: `dash_ure_bridge_min.json` vs `dash_fusion_min.json`
- 장애시 F만 중단해도 E로 **무중단 폴백** 가능(서비스 엔드포인트 분리 권장)

---

## A38) Grafana Minimal for Fusion
**ops/grafana/dash_fusion_min.json**
```json
{
  "title": "Fusion (Min)",
  "panels": [
    {"type":"stat","title":"coherence_p95_10m","targets":[{"expr":"fusion:coherence_p95_10m"}]},
    {"type":"stat","title":"q_r_ratio_mean","targets":[{"expr":"avg_over_time(fusion:q_r_ratio[10m])"}]},
    {"type":"timeseries","title":"fusion_phase_diff_mean","targets":[{"expr":"fusion_phase_diff_mean"}]}
  ]
}
```

**Make 타깃**
```makefile
.PHONY: grafana.import.fusion.min
grafana.import.fusion.min:
	@cp ops/grafana/dash_fusion_min.json /var/lib/grafana/dashboards/fusion_min.json || true
```

---

## A39) Chaos Suite (Fusion)
```makefile
.PHONY: chaos.fusion.jitter chaos.fusion.spike
chaos.fusion.jitter: ; @python3 tools/chaos_injector.py --mode jitter --dur 300
chaos.fusion.spike:  ; @python3 tools/chaos_injector.py --mode spike --dur 180
```
합격 기준: 알림 ≤60s, 자동 회복 ≤5m, 게이트 **미통과 없음**

---

## A40) v2.0 GA Criteria (예고)
- β 7일 관찰: `fusion:coherence_p95_10m ≥ 0.91` AND `avg q_r_ratio ≤ 1.65`
- Chaos 3회 합격, Evidence 품질 경보 0건
- 태깅 스크립트(후속): `scripts/release_tag_v20.sh` / `make release.tag.v20`


---

## A41) Load/Capacity Plan (v2.0 β→GA)
**목표 지표(1노드 기준)**
- Sustained ingest: **5k samples/sec** (OSC+MIDI+Replay 합산)
- Export scrape QPS: **≥ 20** (p95 ≤ 150ms)
- CPU ≤ 70% p95, RSS ≤ 2.5GB p95

**scripts/load.gen.sh (샘플 부하)**
```bash
#!/usr/bin/env bash
set -euo pipefail
N=${1:-4}
for i in $(seq 1 $N); do
  python3 sensors/sources/file_replay.py --path data/replay/demo.ndjson --speed 2.0 &
done
wait
```

---

## A42) Performance Profile (py-spy/pprof)
**scripts/profile.fusion.sh**
```bash
#!/usr/bin/env bash
set -euo pipefail
pip install py-spy >/dev/null 2>&1 || true
PID=$(pgrep -f fusion_engine_v20.py | head -n1)
py-spy record -o out/fusion_profile.svg --pid "$PID" --duration 60
echo "[profile] → out/fusion_profile.svg"
```

분석 포인트: 정렬(칼만/리샘플) hot path, exporter write path, sensors queue backpressure

---

## A43) Observability Pack (Fusion Min Dashboard v2)
- Stat: `fusion:coherence_p95_10m` / `avg_over_time(fusion:q_r_ratio[10m])`
- Timeseries: `fusion_phase_diff_mean`, `fusion_gain_k*`, `fusion_align_q/r`
- Table (옵션): Evidence count deltas(1h)

**Make 타깃**
```makefile
.PHONY: grafana.import.fusion.min2
grafana.import.fusion.min2:
	@cp ops/grafana/dash_fusion_min.json /var/lib/grafana/dashboards/fusion_min_v2.json || true
```

---

## A44) Security & Compliance Checklist (β→GA)
- Secrets: `ALERT_SLACK_WEBHOOK`, `URE_PG_DSN` → Secret Manager (KMS)로 이동
- TLS: `/metrics_fusion` 내부망 제한 + mTLS(옵션)
- RBAC: exporter/fusion **read-only FS**, 필요 시 `CAP_NET_BIND_SERVICE`만 허용
- Audit: `adapt_state.json` 변경 시점/사용자 로깅
- 데이터 보존: Evidence bundle 30일, replay 14일, 스냅샷 60일(압축)

---

## A45) GA Packaging & Tagging (v2.0)
**scripts/release_pack_v20.sh**
```bash
#!/usr/bin/env bash
set -euo pipefail
VER=${1:-2.0.0}
OUT=release/v${VER}
mkdir -p "$OUT"
cat > "$OUT/manifest.json" <<JSON
{"version":"${VER}","components":["fusion_v20","sensors","evidence","ops"],"date":"$(date -u +%Y-%m-%dT%H:%M:%SZ)"}
JSON
 tar -czf "$OUT/lumen_fusion_v${VER}.tar.gz" fusion sensors evidence exporters configs scripts ops docs
 ( cd "$OUT" && sha256sum lumen_fusion_v${VER}.tar.gz > SHA256SUMS )
 echo "[release] packed → $OUT"
```

**scripts/release_tag_v20.sh**
```bash
#!/usr/bin/env bash
set -euo pipefail
VER=${1:-2.0.0}
git tag -a "v${VER}" -m "Lumen Fusion GA v${VER}" && git push origin "v${VER}"
```

**Make 타깃**
```makefile
.PHONY: release.v20 pack.tag.v20
release.v20:
	@bash scripts/release_pack_v20.sh 2.0.0
pack.tag.v20:
	@bash scripts/release_tag_v20.sh 2.0.0
```

---

## A46) GA Readiness Checklist (최종)
- [ ] β 7일 관찰 통과(Chaos 3/3 합격, Evidence 품질 경보 0)
- [ ] `fusion:coherence_p95_10m ≥ 0.91` & `avg q_r_ratio ≤ 1.65`
- [ ] Config lint OK, Rate-limit 정책 적용, TLS/mTLS 배치 확인
- [ ] Release package 생성(`make release.v20`) & 태깅(`make pack.tag.v20`)

---

## A47) v2.0 GA Session Restore Block (Preview)
```bash
# v2.0 GA Preview: package + tag + dashboards
make grafana.import.fusion.min2
make release.v20 && make pack.tag.v20
bash scripts/profile.fusion.sh
```

---

## A48) Post‑GA Runbook (요약)
- 주간: snapshots prune/VACUUM, Evidence 품질 룰 검토
- 월간: Error budget 리뷰, Gain Surface 재적합, 리플레이 캡처 샘플 갱신
- 보안: Secret 로테이션(분기), TLS 검증(월)


---

## A49) Golden Signals & SRE Dashboard
**지표(필수)**
- Latency: scrape p95, tick_jitter_p95
- Traffic: ingest rate (samples/sec)
- Errors: exporter 5xx, ingest drop
- Saturation: CPU p95, RSS p95

**ops/grafana/dash_fusion_sre.json (요약)** — 위 4신호 패널 포함

---

## A50) Multi‑Window Burn‑Rate Alerts (SLO 위반 조기 감지)
**ops/prometheus/rules/slo_burn_v20.yaml**
```yaml
groups:
- name: slo_burn
  rules:
  - alert: CoherenceSLOBurnFast
    expr: (1 - fusion:coherence_p95_10m) > (1 - 0.905) * 14
    for: 5m
    labels: {severity: critical}
  - alert: CoherenceSLOBurnSlow
    expr: (1 - fusion:coherence_p95_10m) > (1 - 0.905) * 6
    for: 1h
    labels: {severity: warning}
```

---

## A51) v2.0.1 Hotfix Workflow
**브랜치 전략**: `release/2.0.x` ← hotfix PR → tag `v2.0.1`
**.github/workflows/release-2.0.x.yml** — lint/smoke/pack/tag 자동화(요약)

Hotfix Restore:
```bash
bash scripts/restore.sanity.sh
kubectl set image deploy/fusion fusion=fusion:v2.0.1 --record
```

---

## A52) One‑Click Rollback (β/GA)
**scripts/rollback_oneclick.sh**
```bash
#!/usr/bin/env bash
set -euo pipefail
kubectl argo rollouts rollback fusion-v20 || kubectl rollout undo deploy/fusion
```

**Make 타깃**
```makefile
.PHONY: rollout.rollback
rollout.rollback:
	@bash scripts/rollback_oneclick.sh
```

---

## A53) API Compatibility Matrix
| Version | /metrics_fusion | Evidence /bundle | Notes |
|--------:|:----------------:|:----------------:|-------|
| 2.0.0   | ✅               | ✅               | GA |
| 2.0.1   | ✅               | ✅               | Hotfix: exporter stability |
| 2.1.0   | ✅               | ✅(+filters)     | Planned |

---

## A54) Dependency Lock & SBOM
- **requirements.txt** 고정 + hashes
- **SBOM**: `cyclonedx-py`로 생성 → `release/` 포함

**Make 타깃**
```makefile
.PHONY: sbom
sbom:
	@cyclonedx-py -o release/sbom_fusion_v20.json
```

---

## A55) Docs Index
- `docs/OPERATIONS_RUNBOOK_v20.md`
- `docs/CHANGELOG_v20.md`
- `api/openapi_v20.yaml`
- `ops/grafana/dash_fusion_min.json`, `dash_fusion_sre.json`

---

## A56) v2.0 GA — Compact Restore Summary
```bash
# Dashboards + package + tag + gates
make grafana.import.fusion.min2
kubectl apply -f ops/prometheus/rules/slo_burn_v20.yaml
make release.v20 && make pack.tag.v20
```


---

## A57) GA Sign‑off Bundle
**scripts/ga_signoff.sh**
```bash
#!/usr/bin/env bash
set -euo pipefail
OUT=release/signoff_$(date +%Y%m%dT%H%M%S)
mkdir -p "$OUT"
# capture key signals
curl -fsS localhost:9310/metrics_fusion > "$OUT/metrics_fusion.txt"
cat out/bench_v20_beta.log > "$OUT/bench_beta.log" 2>/dev/null || true
cat out/bench_v20_alpha3.log > "$OUT/bench_alpha3.log" 2>/dev/null || true
# SLO snapshots (PromQL via prom tool or API placeholder)
echo "fusion:coherence_p95_10m, q_r_ratio 24h snapshots" > "$OUT/slo_snapshot.txt"
# hashes
sha256sum "$OUT"/* > "$OUT/SHA256SUMS" || true
echo "[signoff] bundle → $OUT"
```

**Make 타깃**
```makefile
.PHONY: signoff.bundle
signoff.bundle:
	@bash scripts/ga_signoff.sh
```

---

## A58) Knowledge Transfer (KT) Pack
**docs/KT_CHECKLIST_v20.md (요약)**
- 아키텍처: Fusion/Bridge 개요, 포트, 데이터 흐름
- 운영: Daily/Weekly/Monthly 루틴, 알림 대응, 롤백 절차
- 보안/컴플라이언스: Secret, TLS, 보존 정책
- 릴리즈: 패키징, 태깅, 핫픽스 워크플로우

---

## A59) Baseline Snapshots (SRE 기준선)
**scripts/baseline.capture.sh**
```bash
#!/usr/bin/env bash
set -euo pipefail
DST=release/baseline_$(date +%Y%m%dT%H%M%S)
mkdir -p "$DST"
for m in fusion_phase_diff_mean fusion_coherence_level fusion_harmony_index fusion_align_q fusion_align_r fusion_gain_kp fusion_gain_ki fusion_gain_kd; do
  curl -fsS localhost:9310/metrics_fusion | awk -v k="$m" '$$1==k{print $$0}' >> "$DST/metrics_baseline.txt"
done
echo "[baseline] captured → $DST"
```

---

## A60) Post‑Incident Template
**docs/POSTMORTEM_TEMPLATE_v20.md**
- 요약(5문장), 타임라인, 감지/경보, 근본원인, 교정/예방, 지표 변화, 액션 아이템(주/월 추적)

---

## A61) One‑Shot Ops Wrapper (CLI)
**scripts/lumenctl.sh**
```bash
#!/usr/bin/env bash
set -euo pipefail
case "$1" in
  start)   make fusion.init && make fusion.autoadapt.start && make evidence.ingest.start ;;
  smoke)   bash scripts/smoke.v20.sh ;;
  bench)   bash scripts/bench.v20.sh "${2:-900}" ;;
  autopatch) make fusion.autopatch ;;
  signoff) make signoff.bundle ;;
  rollback) make rollout.rollback ;;
  *) echo "usage: $0 {start|smoke|bench [sec]|autopatch|signoff|rollback}" ;;
esac
```

**Make 타깃**
```makefile
.PHONY: lumenctl
lumenctl:
	@chmod +x scripts/lumenctl.sh && echo "lumenctl ready"
```

---

## A62) Housekeeping
- 스냅샷: 주 1회 `snaps.prune`, 월 1회 `VACUUM`
- Evidence: 30일 보존 정책 크론 등록
- SBOM: 릴리즈마다 재생성(`make sbom`)

---

## A63) Runbooks Index (E & F)
- **Track E GA Compact**: 운영·복원·SLO·DR·배포·지연예산 요약
- **Track F v2.0 β/GA**: A0–A62 전 구간 실무 절차

---

## A64) v2.0 Final GA Execution (요약 루프)
```bash
# 1) 게이트/대시보드 적용
make grafana.import.fusion.min2
kubectl apply -f ops/prometheus/rules/slo_burn_v20.yaml
# 2) 사전 점검 및 베이스라인 캡처
make config.lint && bash scripts/baseline.capture.sh
# 3) 패키징/태깅 + 사인오프 번들
make release.v20 && make pack.tag.v20 && make signoff.bundle
# 4) 완료 보고: KT 체크리스트 배포
```
