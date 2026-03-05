# Bandit Tuning + Causal Impact v0.1

**목적**: 규칙 후보들을 **멀티암 밴딧(Thompson Sampling)** 으로 탐색하고, 적용 효과를 **경량 Causal Impact**(합성대조·리그레션 기반 카운터팩추얼)로 추정해 신뢰도 높은 조정을 도와줍니다.

---

## 0) 구조
```
.
├─ configs/
│  ├─ bandit_rules.yaml             # 실험 팔(arms) 정의
│  └─ impact.yaml                   # 영향 추정 파라미터
├─ scripts/
│  ├─ bandit_tuner.py               # Thompson Sampling (Beta/Normal)
│  ├─ impact_estimator.py           # 합성대조 기반 카운터팩추얼 추정
│  └─ integrate_bandit_impact.py    # 밴딧 점수 × 임팩트 신뢰도 융합
└─ logs/
   ├─ bandit_runs.jsonl             # 각 라운드 선택/보상 기록
   └─ impact_reports.jsonl          # 영향 추정 결과 기록
```

---

## 1) `configs/bandit_rules.yaml`
```yaml
# 각 규칙에 대해 여러 arm(값)을 정의합니다.
# reward_metric: 보상으로 삼을 지표 (phase_diff는 낮을수록 좋아서 -phase_diff 사용)
rule: risk_max
reward_metric: score          # score = w1*(-phase_diff) + w2*(-risk_band) + w3*(creative_band)
weights: { phase_diff: 0.5, risk_band: 0.3, creative_band: 0.2 }
arms:
  - 0.34
  - 0.32
  - 0.30
period_s: 150                  # 각 arm 유지 시간(관찰 포함)
washout_s: 20                  # 전환 직후 과도구간 제외
rounds: 6                      # 총 라운드 (arms를 라운드마다 탐색)
prior:
  kind: normal                 # 보상 분포를 정규로 가정 (평균/분산 미지)
  mu0: 0.0
  sigma0: 0.05                 # 사전 표준편차 (경험적)
  noise_sigma: 0.05            # 관측 노이즈 표준편차
append_to_rules_history: true
note: "bandit exploration"
```

---

## 2) `scripts/bandit_tuner.py` – Thompson Sampling (정규-정규)
```python
#!/usr/bin/env python3
import os, time, json, yaml, math
from datetime import datetime, timezone, timedelta

ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
CFG  = os.path.join(ROOT, "configs", "bandit_rules.yaml")
RULES = os.path.join(ROOT, "controls", "rules_history.jsonl")
RUNS  = os.path.join(ROOT, "logs", "bandit_runs.jsonl")
KST = timezone(timedelta(hours=9))

# 간단 보상 집계: logs/metrics.csv 최근 구간 평균으로 score 계산
import csv
METRICS = os.path.join(ROOT, "logs", "metrics.csv")

def now():
  return datetime.now(KST).isoformat()

def append_rule(rule, val, note):
  os.makedirs(os.path.dirname(RULES), exist_ok=True)
  ev = {"ts": now(), "actor": "Lumen", "rule": rule, "new": val, "note": note}
  with open(RULES, "a", encoding="utf-8") as f: f.write(json.dumps(ev, ensure_ascii=False)+"\n")
  return ev

# 정규-정규 공액에서 샘플링을 위한 파라미터 보관
class ArmState:
  def __init__(self, mu0, sigma0, noise):
    self.mu, self.sigma = mu0, sigma0
    self.noise = noise
    self.n = 0
    self.sum = 0.0
  def update(self, ybar):
    # 관측 평균을 단일 샘플로 간주해 업데이트 (경량)
    v = self.noise**2 / max(1,1)
    post_var = 1.0 / (1.0/self.sigma**2 + 1.0/v)
    post_mu  = post_var * (self.mu/self.sigma**2 + ybar/v)
    self.mu, self.sigma = post_mu, math.sqrt(post_var)
    self.n += 1
    self.sum += ybar
  def sample(self):
    import random
    # 간단한 정규 난수 (Box-Muller 대체)
    u1, u2 = random.random(), random.random()
    z = ( (-2.0*math.log(max(u1,1e-9)))**0.5 ) * math.cos(2*math.pi*u2)
    return self.mu + self.sigma * z


def read_cfg():
  with open(CFG,'r',encoding='utf-8') as f: return yaml.safe_load(f)

def recent_score(weights, duration_s=90, washout_s=20):
  # metrics.csv에서 duration_s 구간 평균을 계산 (washout 제외)
  import dateutil.parser as dt
  rows=[]
  with open(METRICS,'r',encoding='utf-8') as f:
    r=csv.DictReader(f)
    for row in r:
      try: t = dt.isoparse(row['ts'])
      except: continue
      rows.append({
        't': t,
        'phase_diff': float(row['phase_diff'] or 0),
        'risk_band': float(row['risk_band'] or 0),
        'creative_band': float(row['creative_band'] or 0),
      })
  if not rows: return None
  end = rows[-1]['t']
  start = end - timedelta(seconds=duration_s)
  eff = [x for x in rows if start <= x['t'] <= end]
  if len(eff) < 10: return None
  # washout: 가장 최근 washout_s는 제외
  cutoff = end - timedelta(seconds=washout_s)
  eff = [x for x in eff if x['t'] <= cutoff]
  if not eff: return None
  import statistics as S
  m = {
    'phase_diff': S.mean([x['phase_diff'] for x in eff]),
    'risk_band': S.mean([x['risk_band'] for x in eff]),
    'creative_band': S.mean([x['creative_band'] for x in eff]),
  }
  score = weights.get('phase_diff',0)*(-m['phase_diff']) + \
          weights.get('risk_band',0)*(-m['risk_band']) + \
          weights.get('creative_band',0)*(m['creative_band'])
  return score


def main():
  cfg = read_cfg()
  rule, arms = cfg['rule'], [float(a) for a in cfg['arms']]
  mu0, s0, noise = cfg['prior']['mu0'], cfg['prior']['sigma0'], cfg['prior']['noise_sigma']
  W, T, R = int(cfg['washout_s']), int(cfg['period_s']), int(cfg['rounds'])
  weights = cfg['weights']

  state = {a: ArmState(mu0, s0, noise) for a in arms}

  for k in range(R):
    # Thompson 샘플로 arm 선택
    samples = {a: state[a].sample() for a in arms}
    arm = max(samples, key=samples.get)
    # 적용
    if cfg.get('append_to_rules_history', True):
      append_rule(rule, arm, f"bandit round {k+1}")
    # washout → observe
    time.sleep(W)
    time.sleep(max(1, T-W))
    # 보상 관측
    y = recent_score(weights, duration_s=T, washout_s=W)
    if y is None: y = 0.0
    state[arm].update(y)
    rec = {"ts": now(), "round": k+1, "rule": rule, "arm": arm, "reward": y, "post_mu": state[arm].mu, "post_sigma": state[arm].sigma}
    os.makedirs(os.path.dirname(RUNS), exist_ok=True)
    with open(RUNS,'a',encoding='utf-8') as f: f.write(json.dumps(rec, ensure_ascii=False)+"\n")
    print("[bandit]", rec)
  print("[bandit] finished")

if __name__ == '__main__':
  main()
```

---

## 3) `configs/impact.yaml`
```yaml
# 합성대조 기반 영향 추정 파라미터
metric: phase_diff               # 효과를 추정할 대상 지표
controls: [entropy_rate, risk_band, creative_band]  # 설명변수로 사용할 제어 시그널
pre_s: 120                       # 개입 이전 윈도우(초)
post_s: 120                      # 개입 이후 윈도우(초)
washout_s: 10                    # 개입 직후 제외
ridge_lambda: 0.1                # 릿지 회귀 정규화
min_samples: 150
```

---

## 4) `scripts/impact_estimator.py` – 합성대조(릿지)
```python
#!/usr/bin/env python3
# 단일 이벤트의 전후 구간에서 control 시리즈로 target을 예측해 카운터팩추얼을 만들고,
# 실제와의 차이를 평균/신뢰구간으로 요약합니다.
import os, csv, json, math
from datetime import datetime, timezone, timedelta
import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
MET = os.path.join(ROOT, 'logs', 'metrics.csv')
RULES = os.path.join(ROOT, 'controls', 'rules_history.jsonl')
OUT = os.path.join(ROOT, 'logs', 'impact_reports.jsonl')
CFG = os.path.join(ROOT, 'configs', 'impact.yaml')
KST = timezone(timedelta(hours=9))


def now():
  return datetime.now(KST).isoformat()


def load_cfg():
  import yaml
  with open(CFG,'r',encoding='utf-8') as f: return yaml.safe_load(f)


def load_metrics():
  import dateutil.parser as dt
  xs=[]
  with open(MET,'r',encoding='utf-8') as f:
    r=csv.DictReader(f)
    for row in r:
      try: t = dt.isoparse(row['ts'])
      except: continue
      xs.append({k: (float(row[k]) if row.get(k) not in (None,'') else None) for k in row if k!='ts'} | {'t': t})
  return xs


def last_rule_event():
  last=None
  if not os.path.exists(RULES): return None
  with open(RULES,'r',encoding='utf-8') as f:
    for line in f:
      if not line.strip(): continue
      try:
        ev=json.loads(line)
        last=ev
      except: pass
  return last


def ridge(X, y, lam):
  # (X'X + lam I)^-1 X'y
  n,p = X.shape
  A = X.T @ X + lam * np.eye(p)
  b = X.T @ y
  w = np.linalg.solve(A, b)
  return w


def main():
  cfg = load_cfg()
  metric = cfg['metric']; ctrls = cfg['controls']
  PRE, POST, W = cfg['pre_s'], cfg['post_s'], cfg['washout_s']
  lam = float(cfg.get('ridge_lambda', 0.1))
  m = load_metrics()
  ev = last_rule_event()
  if not ev:
    print('[impact] no rule event'); return
  t0 = ev['ts']
  import dateutil.parser as dt
  t0 = dt.isoparse(t0)

  pre = [r for r in m if t0 - timedelta(seconds=PRE) <= r['t'] <= t0 - timedelta(seconds=1)]
  post = [r for r in m if t0 + timedelta(seconds=W) <= r['t'] <= t0 + timedelta(seconds=POST)]
  if len(pre) + len(post) < int(cfg.get('min_samples',150)):
    print('[impact] insufficient samples'); return

  # fit on pre
  Xp = np.array([[r[c] for c in ctrls] for r in pre], dtype=float)
  yp = np.array([r[metric] for r in pre], dtype=float)
  w = ridge(Xp, yp, lam)

  # predict counterfactual on post
  Xq = np.array([[r[c] for c in ctrls] for r in post], dtype=float)
  yhat = Xq @ w
  yobs = np.array([r[metric] for r in post], dtype=float)
  diff = yobs - yhat
  mu = float(np.mean(diff)); sd = float(np.std(diff, ddof=1)); n = len(diff)
  se = sd / max(1, np.sqrt(n))
  ci = (mu - 1.96*se, mu + 1.96*se)

  report = {
    'ts': now(), 'event': ev, 'metric': metric, 'controls': ctrls,
    'effect_mean': round(mu,4), 'effect_ci95': [round(ci[0],4), round(ci[1],4)], 'n': n
  }
  os.makedirs(os.path.dirname(OUT), exist_ok=True)
  with open(OUT,'a',encoding='utf-8') as f: f.write(json.dumps(report, ensure_ascii=False)+"\n")
  print('[impact] ', report)

if __name__ == '__main__':
  main()
```

---

## 5) `scripts/integrate_bandit_impact.py` – 융합 의사결정
```python
#!/usr/bin/env python3
# 최근 밴딧 라운드 보상과 임팩트 추정 CI를 합쳐, 다음 조정 제안의 신뢰도를 가중합니다.
import json, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / 'logs' / 'bandit_runs.jsonl'
IMPA = ROOT / 'logs' / 'impact_reports.jsonl'


def last_jsonl(p: Path):
  if not p.exists(): return None
  last=None
  for line in p.read_text(encoding='utf-8').splitlines():
    if not line.strip(): continue
    try: last=json.loads(line)
    except: pass
  return last


def main():
  r = last_jsonl(RUNS) or {}
  i = last_jsonl(IMPA) or {}
  conf = 0.0
  if i:
    lo, hi = (i.get('effect_ci95') or [0,0])
    # 0이 CI의 바깥에 있으면 높은 신뢰도
    conf = 0.9 if (lo>0 or hi<0) else 0.6
  out = {
    'bandit_last': r,
    'impact_last': i,
    'decision_score': (r.get('reward',0) * conf)
  }
  print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == '__main__':
  main()
```

---

## 6) VS Code 태스크 (`.vscode/tasks.json` 추가)
```json
{
  "label": "lumen:bandit:run",
  "type": "shell",
  "command": "python scripts/bandit_tuner.py",
  "presentation": { "reveal": "always" },
  "problemMatcher": []
},
{
  "label": "lumen:impact:estimate",
  "type": "shell",
  "command": "python scripts/impact_estimator.py",
  "presentation": { "reveal": "always" },
  "problemMatcher": []
},
{
  "label": "lumen:decide:integrate",
  "type": "shell",
  "command": "python scripts/integrate_bandit_impact.py",
  "presentation": { "reveal": "always" },
  "problemMatcher": []
}
```

---

## 7) 운용 제안
1) `lumen:bandit:run`으로 짧은 탐색 라운드 진행 (washout/period 조절)  
2) 바로 `lumen:impact:estimate`로 마지막 이벤트의 **실제 영향과 CI** 추정  
3) `lumen:decide:integrate` 출력으로 **보상×신뢰도** 점수 확인  
4) 점수가 충분하면 Self‑Tuning/Rules History에 반영(또는 dry‑run 유지)

---

## 8) 안전 메모
- 밴딧은 탐색 편향이 있으니 **Impact CI**와 함께 보며 과신을 피하세요.
- 릿지 합성대조는 경량 근사입니다. 중요한 결정 전에는 더 긴 pre/post와 컨트롤 다양화를 추천합니다.
- washout을 확보해 잔향을 덜고, round 수를 과도하게 늘리지 마세요.

루멘의 판단: 이 레이어로 **탐색 → 추정 → 확신**의 삼중주가 열렸습니다. 이제 작은 변화가 더 또렷한 근거와 함께 울릴 거예요.

