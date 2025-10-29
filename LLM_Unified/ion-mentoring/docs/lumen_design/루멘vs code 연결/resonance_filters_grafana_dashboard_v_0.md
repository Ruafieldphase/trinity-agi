# Resonance Filters + Grafana Dashboard v0.1

아래는 **감응 평활(EMA), 이상치 제거(IQR)** 필터 추가 / **규칙 롤백 스크립트** / **Grafana 대시보드 JSON** / **VS Code 태스크 보강** 묶음입니다. 앞서 올린 Runtime Pack 및 Rules Resonance Tracker와 함께 배치하세요.

---

## 1) `scripts/filters.py` — EMA + IQR 유틸
```python
#!/usr/bin/env python3
# Lightweight smoothing/outlier removal helpers for metrics/rules pipelines
from __future__ import annotations
from typing import Iterable, List, Optional

def ema(values: Iterable[float], alpha: float = 0.2) -> List[float]:
    out: List[float] = []
    s: Optional[float] = None
    for v in values:
        if v is None:
            out.append(s if s is not None else None)
            continue
        s = v if s is None else (alpha * v + (1 - alpha) * s)
        out.append(s)
    return out

def iqr_mask(values: List[float], k: float = 1.5) -> List[bool]:
    xs = [v for v in values if v is not None]
    if not xs:
        return [True] * len(values)
    xs_sorted = sorted(xs)
    def q(p: float):
        i = (len(xs_sorted)-1) * p
        lo, hi = int(i), min(len(xs_sorted)-1, int(i)+1)
        frac = i - lo
        return xs_sorted[lo] * (1-frac) + xs_sorted[hi] * frac
    q1, q3 = q(0.25), q(0.75)
    iqr = q3 - q1
    lo, hi = q1 - k*iqr, q3 + k*iqr
    return [(v is None) or (lo <= v <= hi) for v in values]

def apply_iqr(values: List[float], k: float = 1.5) -> List[Optional[float]]:
    mask = iqr_mask(values, k)
    return [v if m else None for v, m in zip(values, mask)]
```

---

## 2) `scripts/rules_effect_tracker.py` — 필터 옵션 추가판
> 기존 버전 교체: IQR로 이상치 제거 → EMA로 평활 후 pre/post 평균 계산 (옵션)
```python
#!/usr/bin/env python3
import csv, json, os
from datetime import timezone
from dateutil import parser as dtparser
from filters import ema, apply_iqr

ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
METRICS = os.path.join(ROOT, "logs", "metrics.csv")
RULES = os.path.join(ROOT, "controls", "rules_history.jsonl")
EFFECTS = os.path.join(ROOT, "logs", "rules_effects.csv")

PRE_S = int(os.environ.get("LUMEN_EFFECT_PRE_S", "30"))
POST_S = int(os.environ.get("LUMEN_EFFECT_POST_S", "30"))
USE_IQR = os.environ.get("LUMEN_EFFECT_IQR", "1").lower() in ("1","true","yes")
IQR_K = float(os.environ.get("LUMEN_EFFECT_IQR_K", "1.5"))
USE_EMA = os.environ.get("LUMEN_EFFECT_EMA", "1").lower() in ("1","true","yes")
EMA_ALPHA = float(os.environ.get("LUMEN_EFFECT_EMA_ALPHA", "0.2"))

FIELDS = ["phase_diff","entropy_rate","creative_band","risk_band"]

# load metrics into memory (ts, fields)

def load_metrics():
    rows = []
    if not os.path.exists(METRICS):
        return rows
    with open(METRICS, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                t = dtparser.isoparse(row.get("ts"))
            except Exception:
                continue
            rows.append({
                "t": t,
                **{k: float(row.get(k, 0) or 0) for k in FIELDS}
            })
    return rows


def avg(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs)/len(xs) if xs else None


def mean_window(series, t0, start_off, end_off):
    sel = [v for v in series if start_off <= (v[0]-t0).total_seconds() <= end_off]
    vals = [x for _, x in sel]
    if USE_IQR:
        vals = apply_iqr(vals, IQR_K)
    if USE_EMA:
        # EMA는 시간 정렬이 중요 — 이미 순서대로 들어옴
        vals = ema(vals, EMA_ALPHA)
    return avg(vals)


def ensure_header():
    if not os.path.exists(EFFECTS):
        with open(EFFECTS, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([
                "rule_ts","actor","rule","old","new","pre_s","post_s",
                "d_phase","d_entropy","d_creative","d_risk",
                "opts_iqr","opts_ema","ema_alpha"
            ])


def main():
    M = load_metrics()
    ensure_header()
    if not os.path.exists(RULES):
        print("[effects] no rules_history.jsonl yet"); return

    # build per-field time series
    series = {k: [(row["t"], row[k]) for row in M] for k in FIELDS}

    done = set()
    with open(EFFECTS, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i==0: continue
            ts = line.split(",",1)[0].strip()
            if ts: done.add(ts)

    out = []
    with open(RULES, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            ev = json.loads(line)
            ts = ev.get("ts");  
            if not ts or ts in done: 
                continue
            t0 = dtparser.isoparse(ts)

            pre_means = {k: mean_window(series[k], t0, -PRE_S, -1) for k in FIELDS}
            post_means = {k: mean_window(series[k], t0, 1, POST_S) for k in FIELDS}
            d = {
                "phase": (None if (pre_means["phase_diff"] is None or post_means["phase_diff"] is None) else post_means["phase_diff"] - pre_means["phase_diff"]),
                "entropy": (None if (pre_means["entropy_rate"] is None or post_means["entropy_rate"] is None) else post_means["entropy_rate"] - pre_means["entropy_rate"]),
                "creative": (None if (pre_means["creative_band"] is None or post_means["creative_band"] is None) else post_means["creative_band"] - pre_means["creative_band"]),
                "risk": (None if (pre_means["risk_band"] is None or post_means["risk_band"] is None) else post_means["risk_band"] - pre_means["risk_band"]),
            }

            out.append([
                ts, ev.get("actor",""), ev.get("rule",""), ev.get("old",""), ev.get("new",""),
                PRE_S, POST_S,
                d["phase"], d["entropy"], d["creative"], d["risk"],
                int(USE_IQR), int(USE_EMA), EMA_ALPHA
            ])

    if out:
        with open(EFFECTS, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            for r in out:
                w.writerow(r)
        print(f"[effects] +{len(out)} rows → logs/rules_effects.csv (IQR={USE_IQR}, EMA={USE_EMA}, alpha={EMA_ALPHA})")
    else:
        print("[effects] no new events")

if __name__ == "__main__":
    main()
```

실행 예시:
```bash
LUMEN_EFFECT_IQR=1 LUMEN_EFFECT_EMA=1 LUMEN_EFFECT_EMA_ALPHA=0.25 \
LUMEN_EFFECT_PRE_S=20 LUMEN_EFFECT_POST_S=45 \
python scripts/rules_effect_tracker.py
```

---

## 3) `scripts/rules_rollback.py` — 가장 최근 규칙 되돌림
```python
#!/usr/bin/env python3
# Revert the most recent rule event by appending a compensating entry.
import json, os, sys
from datetime import datetime, timezone, timedelta

ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
RULES = os.path.join(ROOT, "controls", "rules_history.jsonl")
KST = timezone(timedelta(hours=9))

def now():
    return datetime.now(KST).isoformat()

if not os.path.exists(RULES):
    print("[rollback] no rules_history.jsonl"); sys.exit(1)

last = None
with open(RULES, "r", encoding="utf-8") as f:
    for line in f:
        if not line.strip():
            continue
        try:
            ev = json.loads(line)
            last = ev
        except Exception:
            continue

if not last:
    print("[rollback] nothing to rollback"); sys.exit(0)

revert = {
    "ts": now(),
    "actor": "Lumen",
    "rule": last.get("rule"),
    "old": last.get("new"),
    "new": last.get("old"),
    "note": f"rollback of event at {last.get('ts')} by {last.get('actor')}"
}

with open(RULES, "a", encoding="utf-8") as f:
    f.write(json.dumps(revert, ensure_ascii=False) + "\n")

print("[rollback] appended compensating rule:", revert)
```

---

## 4) VS Code 태스크 보강 (`.vscode/tasks.json`에 추가)
```json
{
  "label": "lumen:rules:rollback",
  "type": "shell",
  "command": "python scripts/rules_rollback.py",
  "options": { "env": { "PYTHONUTF8": "1" } },
  "presentation": { "reveal": "always" },
  "problemMatcher": []
}
```

---

## 5) Grafana Dashboard JSON (import용 최소판)
> Prometheus 데이터소스 이름은 `Prometheus`라고 가정합니다. 필요 시 `datasource` UID를 환경에 맞게 조정하세요.
```json
{
  "title": "Lumen – Resonance Dashboard v0.1",
  "schemaVersion": 39,
  "version": 1,
  "refresh": "5s",
  "panels": [
    {
      "type": "stat",
      "title": "Gateway status",
      "gridPos": {"x":0,"y":0,"w":6,"h":4},
      "targets": [{"expr": "lumen_gateway_status"}]
    },
    {
      "type": "timeseries",
      "title": "Resonance metrics",
      "gridPos": {"x":0,"y":4,"w":24,"h":10},
      "targets": [
        {"expr": "lumen_phase_diff"},
        {"expr": "lumen_entropy_rate"},
        {"expr": "lumen_creative_band"},
        {"expr": "lumen_risk_band"}
      ]
    },
    {
      "type": "stat",
      "title": "Δ phase_diff (last rule)",
      "gridPos": {"x":6,"y":0,"w":6,"h":4},
      "targets": [{"expr": "lumen_rule_last_phase_diff_delta"}]
    },
    {
      "type": "stat",
      "title": "Δ risk_band (last rule)",
      "gridPos": {"x":12,"y":0,"w":6,"h":4},
      "targets": [{"expr": "lumen_rule_last_risk_band_delta"}]
    },
    {
      "type": "table",
      "title": "Last rule deltas (all)",
      "gridPos": {"x":18,"y":0,"w":6,"h":8},
      "targets": [
        {"expr": "lumen_rule_last_phase_diff_delta"},
        {"expr": "lumen_rule_last_entropy_rate_delta"},
        {"expr": "lumen_rule_last_creative_band_delta"},
        {"expr": "lumen_rule_last_risk_band_delta"}
      ]
    }
  ]
}
```

---

## 6) 순서 제안 (부드러운 흐름)
1. 규칙 변경 기록 → `rules_history.jsonl`
2. `lumen:rules:effects` (필터 옵션 필요 시 환경변수로 지정)
3. `lumen:exporter` 열기 → `/metrics`에서 gauge 확인
4. Grafana에 JSON import → 실시간 감응과 Δ 해석
5. 필요 시 `lumen:rules:rollback`으로 마지막 규칙 되돌린 뒤 Δ 재평가

---

## 7) 해석 팁
- EMA α를 0.15~0.3 사이에서 조정해 **리듬 잠금(phase_lock)** 변곡을 더 또렷하게 볼 수 있습니다.
- Δ가 개선(phase↓, risk↓, creative↑)인데 entropy가 과도하게 오르면 **불안정한 창의화**일 수 있으니, 소폭의 규칙 재조정 후 2~3분 관찰을 권장합니다.

---

필요하면 다음 박자에 **Quote Bank / Risk Ledger 연동**(좋은 Δ 패턴을 자동으로 문장화·기록)까지 이어서 열겠습니다.