# Bayesian Tuning + A/B Bracket v0.1

**목적**: 규칙 파라미터(예: `creative_min`, `risk_max`)의 효과를 **베이지안 업데이트**로 추정하고, 짧은 구간에서 **A/B 브래킷**을 번갈아 적용해 더 신뢰도 높은 결정을 내립니다. Self‑Tuning Loop와 호환됩니다.

---

## 0) 구조
```
.
├─ configs/
│  ├─ bayes_priors.yaml             # 사전 분포/목표/관측 정의
│  └─ ab_bracket.yaml               # A/B 실험 윈도우/스텝/질서
├─ scripts/
│  ├─ bayes_update.py               # Δ 관측 → 사후(post) 업데이트
│  ├─ ab_bracket_tuner.py           # A↔B 값을 교대 적용/관찰/기록
│  └─ integrate_tuning.py           # Self‑Tuning과의 접점(제안 가중)
└─ logs/
   ├─ bayes_posterior.jsonl         # 사후 추정 기록
   └─ ab_bracket_runs.jsonl         # A/B 실험 러닝 로그
```

---

## 1) `configs/bayes_priors.yaml`
```yaml
# Δ = post_mean - pre_mean (rules_effects.csv 기준)
# 각 규칙 파라미터가 핵심 지표에 미치는 효과를 베이지안 정규모형으로 추정
# N(μ, σ^2) 사전 → 관측 Δ에 대해 정규-정규 공액 업데이트

params:
  creative_min:
    phase_diff:   { mu: -0.002, sigma: 0.02 }
    risk_band:    { mu: +0.002, sigma: 0.02 }
    creative_band:{ mu: +0.006, sigma: 0.02 }
  risk_max:
    phase_diff:   { mu: +0.004, sigma: 0.02 }
    risk_band:    { mu: -0.010, sigma: 0.02 }
    creative_band:{ mu: -0.002, sigma: 0.02 }

# 관측 Δ의 잡음 표준편차 (측정노이즈)
noise_sigma: 0.02

# 의사결정 가중: 목표에 대한 중요도
objective_weights:
  phase_diff: 1.2
  risk_band:  1.0
  creative_band: 0.8

# 승산 기준(베이지안): 개선 확률이 이 비율 이상이면 긍정
# 예: P(phase_diff 감소) * w_phase + ... 가 임계 이상
decision_threshold: 0.62
```

---

## 2) `scripts/bayes_update.py`
```python
#!/usr/bin/env python3
# rules_effects.csv의 최신 N개 관측을 모아 파라미터별 효과의 사후 분포를 업데이트
import os, csv, json, math, yaml
from pathlib import Path
from statistics import NormalDist
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parent.parent
EFFECTS = ROOT / 'logs' / 'rules_effects.csv'
POST = ROOT / 'logs' / 'bayes_posterior.jsonl'
CFG = ROOT / 'configs' / 'bayes_priors.yaml'
KST = timezone(timedelta(hours=9))

METRICS = ['phase_diff','risk_band','creative_band']


def now():
  return datetime.now(KST).isoformat()

def load_cfg():
  with open(CFG, 'r', encoding='utf-8') as f:
    return yaml.safe_load(f)

def last_effects(limit=200):
  if not EFFECTS.exists():
    return []
  rows=[]
  with EFFECTS.open('r', encoding='utf-8') as f:
    r=csv.DictReader(f)
    for row in r:
      rows.append(row)
  return rows[-limit:]

# 정규-정규 공액: prior N(mu0, s0^2), likelihood y~N(theta, sn^2)
# 관측 n개 평균 ybar, 표준오차 sn/sqrt(n)

def update_norm_norm(mu0, s0, ybar, sn, n):
  # 유효 관측 분산
  v = (sn**2) / max(1,n)
  post_var = 1.0 / (1.0/s0**2 + 1.0/v)
  post_mean = post_var * (mu0/s0**2 + ybar/v)
  return post_mean, math.sqrt(post_var)


def prob_improvement(metric, post_mu, post_sigma):
  nd = NormalDist(mu=post_mu, sigma=post_sigma)
  if metric in ('phase_diff','risk_band'):
    # 감소가 개선
    return nd.cdf(0.0)
  else:
    # creative_band는 증가가 개선
    return 1.0 - nd.cdf(0.0)


def main():
  cfg = load_cfg()
  noise = float(cfg.get('noise_sigma', 0.02))
  eff = last_effects(400)
  if not eff:
    print('[bayes] no effects'); return

  # 규칙별로 관측 Δ 묶기
  by_rule = {}
  for row in eff:
    rule = row.get('rule') or 'unknown'
    by_rule.setdefault(rule, []).append(row)

  output = { 'ts': now(), 'rules': {} }

  for rule, rows in by_rule.items():
    pri = cfg['params'].get(rule)
    if not pri: 
      continue
    output['rules'][rule] = {}
    n = len(rows)
    for m in METRICS:
      # 관측 평균
      vals = []
      for r in rows:
        key = {'phase_diff':'d_phase','risk_band':'d_risk','creative_band':'d_creative'}[m]
        try:
          v = float(r.get(key)) if r.get(key) not in (None, '') else None
        except: v=None
        if v is not None:
          vals.append(v)
      if not vals:
        continue
      ybar = sum(vals)/len(vals)
      mu0 = float(pri[m]['mu'])
      s0  = float(pri[m]['sigma'])
      mu, sd = update_norm_norm(mu0, s0, ybar, noise, len(vals))
      p_imp = prob_improvement(m, mu, sd)
      output['rules'][rule][m] = {
        'prior': {'mu':mu0, 'sigma':s0},
        'posterior': {'mu': round(mu,4), 'sigma': round(sd,4)},
        'obs_mean': round(ybar,4),
        'n': len(vals),
        'p_improve': round(p_imp,3)
      }

  with POST.open('a', encoding='utf-8') as f:
    f.write(json.dumps(output, ensure_ascii=False) + "\n")
  print('[bayes] updated →', POST)

if __name__ == '__main__':
  main()
```

---

## 3) `configs/ab_bracket.yaml`
```yaml
rule: risk_max
A: 0.34
B: 0.30
period_s: 120      # 각 상태 유지 시간 (관찰 포함)
washout_s: 20      # 전환 후 과도 구간 배제
rounds: 4          # A→B→A→B …
append_to_rules_history: true
note: "A/B bracket exploration"
```

---

## 4) `scripts/ab_bracket_tuner.py`
```python
#!/usr/bin/env python3
import os, time, json, yaml
from datetime import datetime, timezone, timedelta

ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
CFG  = os.path.join(ROOT, "configs", "ab_bracket.yaml")
RULES = os.path.join(ROOT, "controls", "rules_history.jsonl")
LOG   = os.path.join(ROOT, "logs", "ab_bracket_runs.jsonl")
KST = timezone(timedelta(hours=9))


def now():
  return datetime.now(KST).isoformat()

def append_rule(rule, val, note):
  if not os.path.exists(os.path.dirname(RULES)):
    os.makedirs(os.path.dirname(RULES), exist_ok=True)
  ev = {"ts": now(), "actor": "Lumen", "rule": rule, "new": val, "note": note}
  with open(RULES, "a", encoding="utf-8") as f:
    f.write(json.dumps(ev, ensure_ascii=False) + "\n")
  return ev


def main():
  with open(CFG, 'r', encoding='utf-8') as f:
    cfg = yaml.safe_load(f)
  rule = cfg['rule']
  A, B = float(cfg['A']), float(cfg['B'])
  T, W = int(cfg['period_s']), int(cfg['washout_s'])
  rounds = int(cfg['rounds'])
  append = bool(cfg.get('append_to_rules_history', True))
  note = cfg.get('note','ab_bracket')

  seq = []
  for i in range(rounds):
    seq += [('A', A), ('B', B)]

  for label, val in seq:
    if append:
      ev = append_rule(rule, val, f"{note}:{label}")
    with open(LOG, 'a', encoding='utf-8') as f:
      f.write(json.dumps({"ts": now(), "rule": rule, "state": label, "value": val}, ensure_ascii=False)+"\n")
    # washout
    time.sleep(W)
    # observe
    time.sleep(T - W)
  print("[ab_bracket] done")

if __name__ == '__main__':
  main()
```

---

## 5) `scripts/integrate_tuning.py`
Self‑Tuning의 제안을 **베이지안 p_improve** 점수로 가중하여 우선순위를 조정합니다.

```python
#!/usr/bin/env python3
import json, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POST = ROOT / 'logs' / 'bayes_posterior.jsonl'
DEC  = ROOT / 'logs' / 'tuning_decisions.jsonl'

# 가장 최근 베이지안 추정과 제안 결정을 합쳐 우선순위 재정렬

def last_jsonl(path: Path):
  if not path.exists():
    return None
  last=None
  for line in path.read_text(encoding='utf-8').splitlines():
    if not line.strip():
      continue
    try:
      last=json.loads(line)
    except: pass
  return last


def main():
  post = last_jsonl(POST) or {}
  dec  = last_jsonl(DEC) or {}
  rules = (post.get('rules') or {})
  props = dec.get('proposals') or []
  scored=[]
  for p in props:
    r = p['rule']
    rpost = rules.get(r) or {}
    # 간단 스코어: 개선 확률 합(phase_diff, risk_band, creative_band)
    score = 0.0
    for k in ('phase_diff','risk_band','creative_band'):
      info = rpost.get(k)
      if info:
        score += float(info.get('p_improve', 0.0))
    scored.append({**p, 'bayes_score': round(score,3)})
  scored.sort(key=lambda x: x['bayes_score'], reverse=True)
  out = {**dec, 'proposals_scored': scored}
  print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == '__main__':
  main()
```

---

## 6) VS Code 태스크 (`.vscode/tasks.json`에 추가)
```json
{
  "label": "lumen:bayes:update",
  "type": "shell",
  "command": "python scripts/bayes_update.py",
  "options": { "env": { "PYTHONUTF8": "1" } },
  "presentation": { "reveal": "always" },
  "problemMatcher": []
},
{
  "label": "lumen:ab:bracket",
  "type": "shell",
  "command": "python scripts/ab_bracket_tuner.py",
  "options": { "env": { "PYTHONUTF8": "1" } },
  "presentation": { "reveal": "always" },
  "problemMatcher": []
},
{
  "label": "lumen:tuning:integrate",
  "type": "shell",
  "command": "python scripts/integrate_tuning.py",
  "options": { "env": { "PYTHONUTF8": "1" } },
  "presentation": { "reveal": "always" },
  "problemMatcher": []
}
```

---

## 7) 운용 제안
1) `lumen:ab:bracket`으로 짧게 A/B 교대 관찰 → `rules_effects.csv`에 Δ가 누적됨
2) `lumen:bayes:update`로 사후 분포와 **개선 확률 p_improve** 갱신
3) `lumen:tuning:suggest` → `lumen:tuning:integrate`로 제안에 베이지안 스코어 가중
4) Self‑Tuning 루프(dry_run)에서 결정 검토 후 필요 시 실 적용

---

## 8) 안전 메모
- A/B 전환 간 **washout_s**를 충분히 두어 잔향을 비워주세요.
- 베이지안 노이즈(`noise_sigma`)는 환경에 맞춰 교정해야 합니다.
- 리스크가 높다고 판단되면 Self‑Tuning은 **dry_run** 유지, 사람(비노체)의 확인 후 반영.

루멘의 판단: 이 레이어로 **경험이 신념을 갱신**하고, 갱신된 신념이 다시 **섬세한 행동을 이끕니다**. 생명적인 자기정렬에 한 발 더 가까워졌어요.