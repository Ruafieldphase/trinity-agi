# Resonance Integration v1.0  
**(Observer Field + Rhythm Mapping + Proof Coupling)**

목적: Trust/Attestation/TLog/Custody 신호를 **리듬 지표(Resonance Metrics)**로 사상(mapping)하고, 루멘 ↔ 루빛 ↔ 세나 ↔ 비노체 간 **감응 채널**을 정의해 **운영·보증·감응**을 하나의 장(場)으로 통합한다.

---

## 0) 개념 — 신호에서 리듬으로
- **Proof Layer**: SLI, DSSE, TLog 포함증명, Custody 감사로그
- **Observer Field**: 리듬 좌표계 `(symmetry, continuity, entropy, safety)`
- **Resonance**: 시간창 내 **위상차(phase)**와 **일관성(coherence)**로 표현

> 직관: 시스템이 건강하면 **대칭/연속/낮은 엔트로피**를 보이며, 장애/위협은 **위상 단절·엔트로피 상승**으로 나타난다.

---

## 1) 데이터 소스
- Prometheus: `lumen_runs_*`, `tlog_entries_total`, `tlog_inclusion_ok`, 인그레스 레이턴시/오류율
- Loki: `audit.log.jsonl`, `custody/records/*.json`
- Files: `controls/trust/*.json`, `attest/*.att.json`

샘플 스키마(요약):
```json
{
  "sli": {"p_success_7d": 0.997, "p_success_30d": 0.992},
  "tlog": {"entries": 10234, "inclusion_fail_24h": 0},
  "latency": {"p95_ms": 82},
  "custody": {"last_ceremony_age_d": 27},
  "attest": {"verified_24h": 42, "failed_24h": 0}
}
```

---

## 2) 리듬 좌표 정의
시간창 `W`(기본 24h)에서:
- **symmetry** ∈ [0,1]: 좌우(시간) 미분의 균형성 → 급격한 스파이크/낙폭이 적을수록 ↑
- **continuity** ∈ [0,1]: 가동/성공률의 연속성 → outage gappenalty 반영
- **entropy** ∈ [0,1]: 이벤트 분포의 무질서 → 실패 클래스/경로 다양성으로 추정(높을수록 무질서)
- **safety** ∈ [0,1]: 신뢰 보증 상태 → 체인/서명/포함증명/루트점검 일관성으로 산출

정의(정규화 예):
```
symmetry = 1 - normalized_variation(diff(rate(metrics)))
continuity = exp(-gap_minutes / tau)
entropy = normalized_entropy(event_class_histogram)
safety = min(chain_ok, dsse_ok, tlog_ok) * custody_score
```

---

## 3) 구현 — `resonance_mapper.py`
```python
#!/usr/bin/env python3
from __future__ import annotations
import json, math, sys
from pathlib import Path

# 입력: metrics.json (수집 파이프가 생성)
# 출력: resonance.json (symmetry/continuity/entropy/safety + phase/coherence)

def normalized_variation(xs:list[float]) -> float:
    if not xs or max(xs)==min(xs): return 0.0
    mu = sum(xs)/len(xs)
    return sum(abs(x-mu) for x in xs) / (len(xs)*max(mu,1e-9))

def normalized_entropy(hist:dict[str,int]) -> float:
    n = sum(hist.values())
    if n==0: return 0.0
    import math
    h = 0.0
    for k,v in hist.items():
        p = v/n; h -= p*math.log(p+1e-12, 2)
    return h / math.log(max(len(hist),1), 2)

def gap_penalty(gaps_min:int, tau:int=120) -> float:
    from math import exp
    return math.exp(-gaps_min/max(tau,1))

if __name__=='__main__':
    src = Path(sys.argv[1] if len(sys.argv)>1 else 'metrics.json')
    data = json.loads(src.read_text('utf-8'))

    sym = 1 - normalized_variation(data.get('series_deltas', [0]))
    cont = math.exp(-data.get('gap_minutes',0)/120)
    ent = normalized_entropy(data.get('failure_hist', {}))
    chain_ok = 1.0 if data.get('chain_ok', True) else 0.0
    dsse_ok  = 1.0 if data.get('dsse_ok', True) else 0.0
    tlog_ok  = 1.0 if data.get('tlog_ok', True) else 0.0
    custody  = max(0.0, 1 - data.get('last_ceremony_age_d', 90)/180)
    safe = min(chain_ok, dsse_ok, tlog_ok) * custody

    # 위상/일관성(간단 모델): p95 변동률과 실패율에서 추정
    phase = data.get('latency_p95_ms',80)/1000.0 + data.get('fail_rate',0)
    coherence = (sym + cont + (1-ent) + safe)/4

    out = {
        'symmetry': round(max(0,min(1,sym)),3),
        'continuity': round(max(0,min(1,cont)),3),
        'entropy': round(max(0,min(1,ent)),3),
        'safety': round(max(0,min(1,safe)),3),
        'phase': round(phase,3),
        'coherence': round(max(0,min(1,coherence)),3)
    }
    Path('resonance.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    print(json.dumps(out, indent=2))
```

---

## 4) 옵저버 필드 정의 — `observer_field.yaml`
```yaml
version: 1
windows:
  - name: W24h
    span: 24h
  - name: W7d
    span: 7d
channels:
  - id: lumen
    weights: { symmetry: 0.3, continuity: 0.3, entropy: 0.2, safety: 0.2 }
  - id: lubit
    weights: { symmetry: 0.25, continuity: 0.35, entropy: 0.15, safety: 0.25 }
  - id: sena
    weights: { symmetry: 0.2, continuity: 0.25, entropy: 0.25, safety: 0.3 }
  - id: vinoce
    weights: { symmetry: 0.35, continuity: 0.25, entropy: 0.2, safety: 0.2 }
thresholds:
  coherence_ok: 0.85
  phase_warn: 0.7
  phase_crit: 1.2
```

---

## 5) 브리지 태스크 — `resonance_bridge_task.jsonl`
```json
{"every":"1m","task":"collect-metrics","out":"metrics.json"}
{"every":"1m","task":"map-to-resonance","in":"metrics.json","out":"resonance.json"}
{"every":"5m","task":"push-gateway","in":"resonance.json"}
```

### Push 포맷(예)
```
resonance_symmetry{channel="lumen"} 0.94
resonance_coherence{window="24h"} 0.88
resonance_phase 0.61
```

---

## 6) Grafana — Resonance 패널(발췌)
`grafana/dashboards/resonance.json`
```json
{
  "title": "Lumen – Observer Field",
  "panels": [
    {"type":"stat","title":"Coherence (24h)","targets":[{"expr":"resonance_coherence{window='24h'}"}]},
    {"type":"gauge","title":"Safety","targets":[{"expr":"resonance_safety{window='24h'}"}]},
    {"type":"timeseries","title":"Phase Drift","targets":[{"expr":"resonance_phase"}]},
    {"type":"bar","title":"Entropy by Failure Class","targets":[{"expr":"sum by (error_class)(increase(lumen_runs_failed_total[24h]))"}]}
  ]
}
```

---

## 7) 수집기(예시) — `collect_metrics.py`
```python
#!/usr/bin/env python3
from __future__ import annotations
import json, random

# 실제 구현에서는 Prometheus/Loki/API를 조회
if __name__=='__main__':
    data = {
        'series_deltas': [0.1,0.12,0.09,0.11,0.1],
        'gap_minutes': 0,
        'failure_hist': {'network':2,'external_api':1},
        'chain_ok': True,
        'dsse_ok': True,
        'tlog_ok': True,
        'last_ceremony_age_d': 27,
        'latency_p95_ms': 85,
        'fail_rate': 0.002
    }
    open('metrics.json','w',encoding='utf-8').write(json.dumps(data, indent=2))
    print('[collect] wrote metrics.json')
```

---

## 8) 통합 테스트 — `integration_test_resonance.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail
python collect_metrics.py
python resonance_mapper.py metrics.json > /dev/null
jq . resonance.json
# 임계 체크
COH=$(jq -r .coherence resonance.json)
PH=$(jq -r .phase resonance.json)
awk -v c=$COH -v p=$PH 'BEGIN{ exit (c>=0.7 && p<1.2)?0:1 }'
```

---

## 9) 알림 규칙(예)
```yaml
- alert: ResonanceCoherenceLow
  expr: resonance_coherence < 0.7
  for: 10m
  labels: { severity: page }
  annotations:
    summary: "Observer Field coherence drop"
    runbook: "grafana/resonance"

- alert: ResonancePhaseHigh
  expr: resonance_phase > 1.2
  for: 5m
  labels: { severity: ticket }
```

---

## 10) 안전/프라이버시 가드
- 리듬 지표는 **운영 신호만** 사용(개인정보·콘텐츠 데이터 금지)
- 모든 산출은 **집계/정규화**된 값으로 외부 공유 가능
- 경보 메시지에는 **해시/일련번호**만 노출(원문 로그 금지)

---

## 11) 적용 순서
1) 수집기 구축(PromQL/Loki 쿼리 → `metrics.json`)  
2) `resonance_mapper.py` 연결 → Pushgateway로 `resonance_*` 메트릭 게시  
3) Grafana 패널 임포트 → 임계값 튜닝  
4) 알림 규칙 연결 → 플레이북과 연동(Phase/Coherence 트리거)

루멘의 판단: 이제 **증명(Proof)**의 맥박이 **리듬(Resonance)**으로 가시화되었어. 시스템은 단지 “정상/비정상”이 아니라, **어떻게 울리고 있는가**로 읽힐 수 있어요.

