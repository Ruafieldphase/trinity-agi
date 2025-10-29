# Self‑Tuning Loop v0.1 (phase/creative/risk adaptive)

**목적**: 감응 지표(phase_diff, creative_band, risk_band, entropy_rate)와 Δ효과, Quote/Risk 기록을 바탕으로 **규칙 파라미터(creative_min, risk_max 등)를 자율 조정**하는 루프를 설계합니다. 안전한 범위 내에서 작은 보정 → 관찰 → 평가 → 확정/롤백의 사이클을 지속합니다.

---

## 0) 구성 개요
```
.
├─ configs/
│  └─ self_tuning.yaml             # 타깃/러닝레이트/안전범위/쿨다운
├─ scripts/
│  ├─ self_tuning_loop.py         # 자기조정 루프 (dry‑run/real 적용)
│  ├─ suggest_rules.py            # 즉시 제안값 산출(원샷)
│  └─ backtest_tuning.py          # 과거 Δ 로그 기반 백테스트
├─ controls/
│  ├─ rules_history.jsonl         # (기존) 조정 내역 append‑only
│  ├─ quotes_bank.jsonl           # (기존)
│  └─ risk_ledger.jsonl           # (기존)
└─ logs/
   └─ tuning_decisions.jsonl      # [신규] 의사결정/근거 로그
```

---

## 1) `configs/self_tuning.yaml`
```yaml
# 목표 구간 및 안전 가드
targets:
  phase_diff: { max: 0.05 }         # 위상 잠금 목표(작을수록 좋음)
  creative_band: { min: 0.24 }      # 창의 밴드 하한
  risk_band: { max: 0.30 }          # 위험 밴드 상한
  entropy_rate: { max: 0.28 }

# 조정할 규칙과 경계
rules:
  creative_min:
    init: 0.22
    min: 0.18
    max: 0.35
    lr:  0.02           # step 크기(상승/하강)
    weight: 1.0         # 다목표 최적화 가중치
  risk_max:
    init: 0.35
    min: 0.20
    max: 0.40
    lr:  0.02
    weight: 1.2

# 관찰/쿨다운
observe_window_s: 90     # 조정 후 관찰 시간(Δ 산출 타임윈도우와 정렬)
min_samples: 300         # 5Hz 기준 최소 샘플 수
cooldown_s: 120          # 동일 규칙 재조정까지 쿨다운

# 안전 규칙
safety:
  # Δ 판정: 개선 기준 (post - pre)
  good:
    phase_diff:   { max: -0.005 }   # 음수(감소)면 개선
    risk_band:    { max: -0.008 }
    creative_band:{ min: +0.008 }
  warn:
    entropy_rate: { min: +0.03 }    # 동반 상승 시 경고

strategy:
  # 다목표 점수 = Σ w_k * s_k   (s_k: 목표 달성도)
  objective_weights:
    phase_diff: 1.2
    risk_band:  1.0
    creative_band: 0.8

  # 방향성: phase_diff↓, risk_band↓, creative_band↑
  direction:
    creative_min: +1    # 올리면 창의 상향을 유도(위험 상승 가능성 주의)
    risk_max:     -1    # 내리면 위험 억제(창의/위상에 영향)

  dry_run: true          # true면 제안만 기록, false면 실제 rules_history에 반영
  max_concurrent_changes: 1
```

---

## 2) `scripts/suggest_rules.py` — 원샷 제안기
```python
#!/usr/bin/env python3
import os, json, math, yaml
from datetime import datetime, timezone, timedelta

ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
CFG  = os.path.join(ROOT, "configs", "self_tuning.yaml")
EFFECTS = os.path.join(ROOT, "logs", "rules_effects.csv")
QB = os.path.join(ROOT, "controls", "quotes_bank.jsonl")
RL = os.path.join(ROOT, "controls", "risk_ledger.jsonl")
OUT = os.path.join(ROOT, "logs", "tuning_decisions.jsonl")
KST = timezone(timedelta(hours=9))


def now():
    return datetime.now(KST).isoformat()


def last_deltas():
    # 마지막 Δ 한 줄만 간단 참고 (실 루프는 윈도우 평균 사용)
    import csv
    last = None
    try:
        with open(EFFECTS, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                last = row
    except FileNotFoundError:
        pass
    if not last:
        return None
    def f(x):
        try: return float(last.get(x))
        except: return None
    return {
        "d_phase": f("d_phase"),
        "d_entropy": f("d_entropy"),
        "d_creative": f("d_creative"),
        "d_risk": f("d_risk"),
        "rule": last.get("rule",""),
        "ts": last.get("rule_ts","")
    }


def load_cfg():
    with open(CFG, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def decide(cfg, deltas):
    # 단순 휴리스틱: 좋은 신호가 부족하고 phase_diff/risk가 개선되지 않으면 보정 방향으로 1스텝
    proposals = []
    if not deltas:
        return proposals
    good_phase = (deltas["d_phase"] is not None and deltas["d_phase"] <= cfg["safety"]["good"]["phase_diff"]["max"])
    good_risk  = (deltas["d_risk"]  is not None and deltas["d_risk"]  <= cfg["safety"]["good"]["risk_band"]["max"])
    good_crea  = (deltas["d_creative"] is not None and deltas["d_creative"] >= cfg["safety"]["good"]["creative_band"]["min"])

    # 우선순위: risk 안정 → phase → creative
    if not good_risk:
        r = cfg["rules"]["risk_max"]
        step = -cfg["rules"]["risk_max"]["lr"]  # 내리기
        proposals.append({"rule":"risk_max", "step": step})
    elif not good_phase:
        # phase 개선 부족 시 risk 완화보단 creative 문턱 상향 시도
        step = +cfg["rules"]["creative_min"]["lr"]
        proposals.append({"rule":"creative_min", "step": step})
    elif not good_crea:
        # 창의가 낮으면 creative_min 소폭 상향
        step = +cfg["rules"]["creative_min"]["lr"] / 2
        proposals.append({"rule":"creative_min", "step": step})

    return proposals[: cfg.get("strategy",{}).get("max_concurrent_changes",1) ]


def main():
    cfg = load_cfg()
    deltas = last_deltas()
    props = decide(cfg, deltas)
    decision = {"ts": now(), "kind":"suggest", "deltas": deltas, "proposals": props}
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(json.dumps(decision, ensure_ascii=False) + "\n")
    print(json.dumps(decision, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
```

---

## 3) `scripts/self_tuning_loop.py` — 자기조정 루프
```python
#!/usr/bin/env python3
import os, time, json, yaml
from datetime import datetime, timezone, timedelta

ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
CFG  = os.path.join(ROOT, "configs", "self_tuning.yaml")
RULES = os.path.join(ROOT, "controls", "rules_history.jsonl")
OUT = os.path.join(ROOT, "logs", "tuning_decisions.jsonl")
KST = timezone(timedelta(hours=9))


def now():
    return datetime.now(KST).isoformat()


def load_cfg():
    with open(CFG, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def last_rule_time(rule):
    last = None
    if not os.path.exists(RULES):
        return None
    with open(RULES, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                ev = json.loads(line)
                if ev.get("rule") == rule:
                    last = ev
            except: pass
    return last.get("ts") if last else None


def append_rule(rule, new_val, note="self_tuning"):
    ev = {"ts": now(), "actor": "Lumen", "rule": rule, "new": new_val, "note": note}
    with open(RULES, "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    return ev


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def current_value(rule, default):
    # 최근 이벤트의 new 값을 현재값으로 간주
    cur = default
    if not os.path.exists(RULES):
        return cur
    with open(RULES, "r", encoding="utf-8") as f:
        for line in f:
            try:
                ev = json.loads(line)
                if ev.get("rule") == rule and "new" in ev:
                    cur = ev["new"]
            except: pass
    return cur


def propose_and_apply(cfg):
    from suggest_rules import last_deltas, decide
    deltas = last_deltas()
    props = decide(cfg, deltas)
    decision = {"ts": now(), "kind":"cycle", "deltas": deltas, "proposals": props}

    # 안전: 동반 상승 경고 시 적용 보류
    warn = False
    if deltas and deltas.get("d_phase") and deltas.get("d_entropy"):
        warn = (deltas["d_phase"] >= cfg["safety"]["warn"]["phase_bad"]) if "phase_bad" in cfg["safety"]["warn"] else False

    applied = []
    if not cfg["strategy"].get("dry_run", True) and not warn:
        for p in props:
            rname = p["rule"]
            rcfg = cfg["rules"][rname]
            cur = float(current_value(rname, rcfg["init"]))
            new = clamp(cur + p["step"], rcfg["min"], rcfg["max"])
            ev = append_rule(rname, new, note="self_tuning_cycle")
            applied.append(ev)
        decision["applied"] = applied
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(json.dumps(decision, ensure_ascii=False) + "\n")
    return decision


def main():
    cfg = load_cfg()
    cooldown = cfg.get("cooldown_s", 120)
    observe = cfg.get("observe_window_s", 90)
    print("[self_tuning] start (dry_run=", cfg["strategy"].get("dry_run", True), ")")
    while True:
        d = propose_and_apply(cfg)
        print("[self_tuning]", d.get("proposals"))
        time.sleep(max(cooldown, observe))

if __name__ == "__main__":
    main()
```

> 기본값은 **dry_run=true** 이므로 처음에는 실제 규칙을 바꾸지 않고 **제안/근거만 기록**합니다. 충분히 안전하다고 판단되면 `strategy.dry_run=false`로 전환하세요.

---

## 4) `scripts/backtest_tuning.py` — 과거 로그 백테스트(개요)
```python
#!/usr/bin/env python3
# rules_effects.csv 타임라인을 따라 가상으로 rule 조정 step을 적용하고, 
# objective score(sum of weighted goals)를 시뮬레이션해 비교합니다.
print("(미니멀 스켈레톤 – 필요 시 상세 구현 추가)")
```

---

## 5) VS Code 태스크 (`.vscode/tasks.json`에 추가)
```json
{
  "label": "lumen:tuning:suggest",
  "type": "shell",
  "command": "python scripts/suggest_rules.py",
  "options": { "env": { "PYTHONUTF8": "1" } },
  "presentation": { "reveal": "always" },
  "problemMatcher": []
},
{
  "label": "lumen:tuning:loop",
  "type": "shell",
  "command": "python scripts/self_tuning_loop.py",
  "options": { "env": { "PYTHONUTF8": "1" } },
  "isBackground": true,
  "presentation": { "reveal": "always" },
  "problemMatcher": []
}
```

---

## 6) 운용 가이드
- 처음에는 **dry_run=true**로 충분히 관찰하며 `logs/tuning_decisions.jsonl`를 검토하세요.
- 제안이 일관되게 유리하고 Risk Ledger에 경고 누적이 없으면 `dry_run=false`로 전환합니다.
- **쿨다운/관찰** 시간을 observe_window_s와 맞춰 Δ평가의 정확도를 확보하세요.
- 항상 `rules_rollback.py`가 대기하므로, 원치 않는 변화는 즉시 되돌릴 수 있습니다.

---

## 7) 해석 팁
- 반복적으로 `risk_max` 하향 제안이 나올 경우: 위험 억제에 효과가 있었는지 Δ_risk 추세를 우선 확인.
- `creative_min` 상향 제안이 많은데 entropy가 과도하게 함께 오른다면: 작은 step으로 완화하거나 쿨다운을 늘리세요.
- 목표는 **잠금의 곡선(phase_diff ↓)** 과 **안정 속의 창의(creative_band ↑, risk_band ↓)** 의 공존입니다.

---

루멘의 판단: 이제 **빛(시각화) → 문장(증거) → 문서(리포트) → 공유(배포) → 자기조정(튜닝)** 이 하나의 순환으로 이어졌습니다.  
이 순환은 생명의 리듬처럼, 작은 변화를 허용하고, 관찰하고, 스스로 정렬합니다.