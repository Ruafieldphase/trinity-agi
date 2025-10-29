# Quote Bank + Risk Ledger v0.1 (with Rhythm Overlay)

**목적**: 좋은 Δ 패턴을 자동으로 문장화하여 **Quote Bank**에 기록하고, 위험 신호를 **Risk Ledger**로 축적합니다. 또한 RhythmMap에 규칙 이벤트 마커를 겹쳐 감응 흐름과 사건을 한눈에 보이게 합니다.

---

## 0) 새 파일 구성 추가
```
.
├─ controls/
│  ├─ rules_history.jsonl         # (기존) 규칙 이벤트 로그
│  ├─ quotes_bank.jsonl           # [신규] 증거 문장(Quote) 저장
│  └─ risk_ledger.jsonl           # [신규] 위험 징후 기록
├─ logs/
│  └─ rules_effects.csv           # (기존) Δ 집계
└─ scripts/
   └─ evidence_mapper.py          # Δ → Quote / Risk 변환기
```

---

## 1) 스키마 제안
### 1-1) `controls/quotes_bank.jsonl`
```jsonl
{"ts":"2025-10-23T13:20:01+09:00","by":"Lumen","rule":"creative_min","delta":{"phase":-0.018,"creative":0.035,"risk":-0.022},"confidence":0.78,"quote":"창의 밴드가 0.035 상승하고 위험 밴드는 0.022 낮아졌습니다. 위상차도 0.018 줄어 안정도가 좋아졌습니다."}
```
권장 필드: `ts, by, rule, delta{phase,entropy,creative,risk}, confidence(0~1), quote(str)`

### 1-2) `controls/risk_ledger.jsonl`
```jsonl
{"ts":"2025-10-23T13:22:44+09:00","severity":"warn","rule":"risk_max","signal":{"phase":0.026,"entropy":0.041},"note":"규칙 변경 이후 위상/엔트로피 동시 상승 (불안정)"}
```
권장 필드: `ts, severity(info|warn|crit), rule, signal{…}, note`

---

## 2) `scripts/evidence_mapper.py` — Δ → Quote/Risk 변환기
임계값과 휴리스틱으로 Δ를 해석하여 두 ledger에 append합니다.

```python
#!/usr/bin/env python3
import csv, json, os
from datetime import datetime, timezone, timedelta

ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
EFFECTS = os.path.join(ROOT, "logs", "rules_effects.csv")
QB = os.path.join(ROOT, "controls", "quotes_bank.jsonl")
RL = os.path.join(ROOT, "controls", "risk_ledger.jsonl")
KST = timezone(timedelta(hours=9))

# 해석 임계값 (필요시 환경변수로 조정)
PHASE_GOOD = float(os.environ.get("LUMEN_QB_PHASE_GOOD", "-0.01"))  # 음수(감소)면 좋음
RISK_GOOD  = float(os.environ.get("LUMEN_QB_RISK_GOOD", "-0.01"))   # 음수(감소)면 좋음
CREA_GOOD  = float(os.environ.get("LUMEN_QB_CREA_GOOD", "+0.01"))   # 양수(상승)면 좋음
ENTR_BAD   = float(os.environ.get("LUMEN_RL_ENTR_BAD", "+0.03"))     # 양수(상승) 크면 불안 신호
PHASE_BAD  = float(os.environ.get("LUMEN_RL_PHASE_BAD", "+0.03"))    # 양수(상승) 크면 불안 신호


def now():
    return datetime.now(KST).isoformat()


def row_iter():
    if not os.path.exists(EFFECTS):
        return
    with open(EFFECTS, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            yield row


def fmt_delta(v, name):
    if v is None:
        return None
    s = ("+" if v >= 0 else "") + f"{v:.3f}"
    labels = {
        "phase":"위상차",
        "entropy":"엔트로피율",
        "creative":"창의 밴드",
        "risk":"위험 밴드",
    }
    return f"{labels.get(name,name)} {s}"


def make_quote(ev):
    d_phase = ev.get("d_phase"); d_entropy = ev.get("d_entropy"); d_crea = ev.get("d_creative"); d_risk = ev.get("d_risk")
    try:
        d_phase = None if ev["d_phase"]=="" else float(ev["d_phase"]) 
        d_entropy = None if ev["d_entropy"]=="" else float(ev["d_entropy"]) 
        d_crea = None if ev["d_creative"]=="" else float(ev["d_creative"]) 
        d_risk = None if ev["d_risk"]=="" else float(ev["d_risk"]) 
    except Exception:
        return None

    good = 0
    if (d_phase is not None) and (d_phase <= PHASE_GOOD):
        good += 1
    if (d_risk is not None) and (d_risk <= RISK_GOOD):
        good += 1
    if (d_crea is not None) and (d_crea >= float(CREA_GOOD)):
        good += 1

    # confidence: 좋은 신호 개수 기반 간단 가중
    conf = [0.4, 0.65, 0.8, 0.92][good] if good <= 3 else 0.95

    parts = [p for p in [fmt_delta(d_crea, "creative"), fmt_delta(d_risk, "risk"), fmt_delta(d_phase, "phase"), fmt_delta(d_entropy, "entropy")] if p]
    sent = " · ".join(parts)
    if not sent:
        return None
    return {
        "ts": now(),
        "by": "Lumen",
        "rule": ev.get("rule",""),
        "delta": {"phase": d_phase, "entropy": d_entropy, "creative": d_crea, "risk": d_risk},
        "confidence": round(conf, 2),
        "quote": sent.replace("+","+")
    }


def make_risk(ev):
    try:
        d_phase = None if ev["d_phase"]=="" else float(ev["d_phase"]) 
        d_entropy = None if ev["d_entropy"]=="" else float(ev["d_entropy"]) 
    except Exception:
        return None
    if (d_phase is not None and d_phase >= PHASE_BAD) and (d_entropy is not None and d_entropy >= ENTR_BAD):
        return {
            "ts": now(),
            "severity": "warn",
            "rule": ev.get("rule",""),
            "signal": {"phase": d_phase, "entropy": d_entropy},
            "note": "규칙 이후 위상/엔트로피 동반 상승"
        }
    return None


def append(path, obj):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def main():
    any_out = False
    for ev in row_iter() or []:
        q = make_quote(ev)
        if q: append(QB, q); any_out = True
        r = make_risk(ev)
        if r: append(RL, r); any_out = True
    print("[evidence_mapper] updated" if any_out else "[evidence_mapper] no output")

if __name__ == "__main__":
    main()
```

실행:
```bash
python scripts/evidence_mapper.py
```

---

## 3) RhythmMap에 규칙 이벤트 마커 겹치기
Next.js API에 **최근 규칙 이벤트**와 **Quote/Risk 요약**을 전달하고, 차트 위에 마커를 표시합니다.

### 3-1) `app/api/lumen/rules/route.ts`
```ts
import { NextResponse } from "next/server";
import fs from "node:fs";
import path from "node:path";

function readJsonl(p: string, max=80){
  if(!fs.existsSync(p)) return [];
  const lines = fs.readFileSync(p, "utf-8").trim().split(/\r?\n/);
  return lines.slice(-max).map(l=>{try{return JSON.parse(l)}catch{return null}}).filter(Boolean);
}

export async function GET(){
  const root = process.cwd();
  const rules = readJsonl(path.join(root, "controls", "rules_history.jsonl"));
  const quotes = readJsonl(path.join(root, "controls", "quotes_bank.jsonl"));
  const risks = readJsonl(path.join(root, "controls", "risk_ledger.jsonl"));
  return NextResponse.json({ ok:true, rules, quotes, risks });
}
```

### 3-2) `app/components/RhythmMap.tsx` (핵심 추가 부분)
- 마커 레이어(가느다란 수직선) + 호버 시 최근 Quote/Risk 툴팁

```tsx
// ...기존 import 아래
import { useMemo, useEffect, useState } from "react";

function useRuleEvents(pollMs=2000){
  const [state,setState] = useState<{rules:any[];quotes:any[];risks:any[]}>({rules:[],quotes:[],risks:[]});
  useEffect(()=>{
    let t:any, alive=true;
    const tick=async()=>{
      try{const r=await fetch("/api/lumen/rules",{cache:"no-store"}); const j=await r.json(); if(!alive) return; if(j.ok) setState(j);}finally{t=setTimeout(tick,pollMs)}
    };
    tick();
    return()=>{alive=false; if(t) clearTimeout(t)};
  },[pollMs]);
  return state;
}

// 컴포넌트 내부
const { rules, quotes, risks } = useRuleEvents(2000);

// ts → x축 인덱스 근사 매핑 (간단 구현)
const xIndexByTs = useMemo(()=>{
  const m = new Map<string, number>();
  data.forEach((p, i)=> m.set(p.ts, i));
  return m;
},[data]);

const markers = useMemo(()=>{
  return rules.map((r:any)=>({ ts: r.ts, i: xIndexByTs.get(r.ts) ?? null, rule: r.rule }));
},[rules, xIndexByTs]);
```

`<LineChart>` 내부에 마커 수직선(ReferenceLine) 배치:
```tsx
{markers.filter(m=>m.i!==null).map((m,idx)=> (
  <ReferenceLine key={idx} x={data[m.i!]?.ts} strokeDasharray="2 4" label={m.rule} />
))}
```

> 간단한 구현이므로 동일 타임스탬프 근사 매칭을 사용합니다. 고정밀 동기화가 필요하면 `ts`를 epoch(ms)로 변환해 축 스케일을 커스텀하세요.

---

## 4) VS Code 태스크 추가 (`.vscode/tasks.json`)
```json
{
  "label": "lumen:evidence:map",
  "type": "shell",
  "command": "python scripts/evidence_mapper.py",
  "options": { "env": { "PYTHONUTF8": "1" } },
  "presentation": { "reveal": "always" },
  "problemMatcher": []
}
```
실행 순서 예시: `rules_history.jsonl` 이벤트 기록 → `lumen:rules:effects` → `lumen:evidence:map` → RhythmMap/Prometheus에서 확인

---

## 5) 해석 루틴 제안
1. 규칙을 조정하고 1~2분 동안 **RhythmMap**에서 흐름과 **마커**를 함께 살펴본다.
2. `rules_effects.csv`에서 Δ 확인 → `evidence_mapper.py`로 Quote/Risk를 생성한다.
3. 의미 있는 문장(Quote)을 그대로 **발표/보고용 문구**로 저장한다.
4. Risk Ledger에 경향이 쌓이면 `rules_rollback.py`로 되돌린 뒤 Δ를 재검토한다.

---

원하시면 다음 박자에서 **Quote Bank를 Markdown 리포트**로 자동 엮는 `report_builder.py`와, **RhythmMap 툴팁에 최근 Quote를 직접 띄우는 오버레이**를 더해드릴게요.