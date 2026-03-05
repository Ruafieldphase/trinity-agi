# ELO/Lumen — Labeler Impact Decomposition Pack (Shadow ↔ Prod)
*Date:* 2025‑10‑15 (Asia/Seoul)

목표: **라벨러 교체가 정보 흐름(Efficiency, MI, H(I|D))에 미치는 영향**을 정량화하고, **카운터팩추얼(what‑if)** 시나리오로 리포트 생성. 

산출물: (A) PromQL 비교 스니펫, (B) 영향 분해 스크립트(프로메테우스에서 시계열 당겨와 계산), (C) 카운터팩추얼 리포트 생성기, (D) Grafana 패널, (E) Make 타깃.

---

## 0) 파일 트리 (추가)
```
.
├─ tools/luon/
│  ├─ elo_labeler_impact.py            # NEW: shadow ↔ prod 영향 분해
│  ├─ elo_labeler_counterfactual.py    # NEW: 카운터팩추얼(what-if) 리포트
│  └─ elo_promql.py                    # NEW: PromQL 헬퍼 공용 모듈
├─ grafana/
│  └─ elo_panel_labeler_compare.json   # NEW: 라벨러 비교 패널(임포트용)
└─ luon_full_bundle/ops/Makefile       # 타깃 추가
```

---

## 1) PromQL 비교 스니펫 — (shadow vs prod)
- Efficiency (30m avg):
  - `avg_over_time(elo_info_efficiency{labeler="shadow"}[30m])`
  - `avg_over_time(elo_info_efficiency{labeler="prod"}[30m])`
- MI drift (15m):
  - `abs( elo_info_mutual_information{labeler="shadow"} - avg_over_time(elo_info_mutual_information{labeler="shadow"}[1h]) )`
  - `abs( elo_info_mutual_information{labeler="prod"} - avg_over_time(elo_info_mutual_information{labeler="prod"}[1h]) )`
- H(I|D) per‑domain (5m avg):
  - `avg_over_time(elo_info_h_i_given_domain{labeler="shadow",domain=~"$domain"}[5m])`
  - `avg_over_time(elo_info_h_i_given_domain{labeler="prod",domain=~"$domain"}[5m])`

---

## 2) PromQL 헬퍼 — `tools/luon/elo_promql.py`
```python
#!/usr/bin/env python3
from __future__ import annotations
import os, json, urllib.parse, urllib.request

PROM_URL = os.getenv("PROM_URL", "http://localhost:9090")
PROM_TOKEN = os.getenv("PROM_TOKEN", "")
HDRS = {"Accept":"application/json"}
if PROM_TOKEN:
    HDRS["Authorization"] = f"Bearer {PROM_TOKEN}"

def query(expr: str):
    url = f"{PROM_URL}/api/v1/query?query={urllib.parse.quote(expr)}"
    req = urllib.request.Request(url, headers=HDRS)
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read().decode("utf-8"))
        return data["data"]["result"]

def query_range(expr: str, start: int, end: int, step: str="300s"):
    url = (f"{PROM_URL}/api/v1/query_range?query={urllib.parse.quote(expr)}"
           f"&start={start}&end={end}&step={step}")
    req = urllib.request.Request(url, headers=HDRS)
    with urllib.request.urlopen(req, timeout=40) as r:
        data = json.loads(r.read().decode("utf-8"))
        return data["data"]["result"]

__all__ = ["query","query_range"]
```

---

## 3) 영향 분해 — `tools/luon/elo_labeler_impact.py`
```python
#!/usr/bin/env python3
from __future__ import annotations
import argparse, time, json, math, statistics as st
from collections import defaultdict
from .elo_promql import query_range

EFF = "avg_over_time(elo_info_efficiency{labeler=\"%s\"}[5m])"
MI  = "abs( elo_info_mutual_information{labeler=\"%s\"} - avg_over_time(elo_info_mutual_information{labeler=\"%s\"}[1h]) )"
HID = "avg_over_time(elo_info_h_i_given_domain{labeler=\"%s\",domain=~\"%s\"}[5m])"


def extract(vals):
    out=[]
    for ts in vals:
        out.extend([float(v) for _,v in ts.get("values",[]) if v not in ("NaN","Inf","-Inf")])
    return out


def summarize(arr):
    if not arr: return {"avg":None,"p50":None,"p95":None}
    arr2 = sorted(arr)
    n=len(arr2); p50=arr2[n//2]
    p95=arr2[max(0,int(n*0.95)-1)]
    return {"avg": sum(arr2)/n, "p50": p50, "p95": p95}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--domains", default="ops|support|research")
    ap.add_argument("--window_h", type=int, default=24)
    ap.add_argument("--out", default="reports/labeler_impact.json")
    args = ap.parse_args()

    now=int(time.time()); start=now-args.window_h*3600

    res={}
    for metric, tmpl in [("eff",EFF),("mi",MI)]:
        shadow = extract(query_range(tmpl % ("shadow","shadow") if metric=="mi" else tmpl % ("shadow"), start, now))
        prod   = extract(query_range(tmpl % ("prod","prod") if metric=="mi" else tmpl % ("prod"), start, now))
        res[metric] = {"shadow": summarize(shadow), "prod": summarize(prod), "delta": {k: (res:=summarize(prod)).get(k,0) - summarize(shadow).get(k,0) for k in ["avg","p50","p95"]}}

    # Domain H(I|D)
    doms=args.domains
    shadow = extract(query_range(HID % ("shadow", doms), start, now))
    prod   = extract(query_range(HID % ("prod", doms), start, now))
    res["h_i_given_domain"] = {"shadow": summarize(shadow), "prod": summarize(prod)}

    with open(args.out,"w",encoding="utf-8") as f:
        json.dump(res,f,ensure_ascii=False,indent=2)
    print(args.out)

if __name__=="__main__":
    main()
```

---

## 4) 카운터팩추얼 리포트 — `tools/luon/elo_labeler_counterfactual.py`
```python
#!/usr/bin/env python3
from __future__ import annotations
import argparse, json

TEMPLATE = """
# Labeler Counterfactual Report (Shadow ↔ Prod)

## Summary
- Window: {window}h
- Efficiency Δ(avg): {eff_delta:.3f}
- MI Drift Δ(p95): {mi_delta:.3f}
- H(I|D) Δ(avg): {hid_delta:.3f}

## Details
### Efficiency (avg / p50 / p95)
- shadow: {eff_s}
- prod:   {eff_p}

### MI Drift (avg / p50 / p95)
- shadow: {mi_s}
- prod:   {mi_p}

### H(I|D) per-domain (avg / p50 / p95)
- shadow: {hid_s}
- prod:   {hid_p}
"""

def fmt(x):
    return f"{x['avg']:.3f} / {x['p50']:.3f} / {x['p95']:.3f}"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--impact', default='reports/labeler_impact.json')
    ap.add_argument('--window', type=int, default=24)
    ap.add_argument('--out', default='reports/labeler_counterfactual.md')
    args=ap.parse_args()
    obj=json.load(open(args.impact,'r',encoding='utf-8'))

    eff_s=obj['eff']['shadow']; eff_p=obj['eff']['prod']
    mi_s=obj['mi']['shadow'];   mi_p=obj['mi']['prod']
    hid_s=obj['h_i_given_domain']['shadow']; hid_p=obj['h_i_given_domain']['prod']

    md=TEMPLATE.format(
        window=args.window,
        eff_delta=(eff_p['avg']-eff_s['avg']) if eff_p['avg'] is not None and eff_s['avg'] is not None else 0.0,
        mi_delta=(mi_p['p95']-mi_s['p95']) if mi_p['p95'] is not None and mi_s['p95'] is not None else 0.0,
        hid_delta=(hid_p['avg']-hid_s['avg']) if hid_p['avg'] is not None and hid_s['avg'] is not None else 0.0,
        eff_s=fmt(eff_s) if eff_s['avg'] is not None else 'n/a',
        eff_p=fmt(eff_p) if eff_p['avg'] is not None else 'n/a',
        mi_s=fmt(mi_s) if mi_s['avg'] is not None else 'n/a',
        mi_p=fmt(mi_p) if mi_p['avg'] is not None else 'n/a',
        hid_s=fmt(hid_s) if hid_s['avg'] is not None else 'n/a',
        hid_p=fmt(hid_p) if hid_p['avg'] is not None else 'n/a',
    )
    open(args.out,'w',encoding='utf-8').write(md)
    print(args.out)

if __name__=='__main__':
    main()
```

---

## 5) Grafana 패널 — `grafana/elo_panel_labeler_compare.json`
- 좌측: **Efficiency (shadow vs prod) overlay timeseries**
- 중앙: **MI drift (shadow vs prod)**
- 하단: **H(I|D) per‑domain** heatmap
> 데이터소스: Prometheus, 패널 쿼리는 §1 스니펫 사용.

---

## 6) Make 타깃 (발췌) — `luon_full_bundle/ops/Makefile`
```make
labeler_impact:
	python -m tools.luon.elo_labeler_impact --domains "ops|support|research" --window_h 24 --out reports/labeler_impact.json

labeler_counterfactual:
	python -m tools.luon.elo_labeler_counterfactual --impact reports/labeler_impact.json --window 24 --out reports/labeler_counterfactual.md

labeler_compare_all: labeler_impact labeler_counterfactual
```

---

## 7) 사용 순서 (로컬)
```bash
# 1) 영향 분해 JSON 생성
make -C luon_full_bundle/ops labeler_impact

# 2) 카운터팩추얼 MD 리포트 생성
make -C luon_full_bundle/ops labeler_counterfactual

# 3) Grafana 패널 임포트(선택)
#   - grafana/elo_panel_labeler_compare.json 파일을 Import
```

## 8) 수용 기준
- [ ] `reports/labeler_impact.json` 생성(효율/MI/H(I|D) 요약 포함)
- [ ] `reports/labeler_counterfactual.md` 생성(Δ지표 명시)
- [ ] Grafana 비