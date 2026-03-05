# ELO/Lumen — Domain Profiles Tuning + Single‑PR Diff
*Date:* 2025‑10‑15 (Asia/Seoul)

이 팩은 **(A) 도메인 프로파일 초기치/튜닝 파이프라인**과 **(B) 전체 변경분 단일 PR diff**를 제공합니다. 바로 커밋/푸시가 가능하며, Week‑1 롤아웃 계획과 호환됩니다.

---

## A) 도메인 프로파일 튜닝 세트

### A.1 초기 프로파일 (seed) — `monitoring/elo_domain_profiles.yaml`
```yaml
version: 1
profiles:
  ops:
    eff_min: 0.52
    h_i_delta_max_bits: 0.30
    alert_noise_max_min: 120
    stopword_growth_ratio_max: 1.8
  support:
    eff_min: 0.50
    h_i_delta_max_bits: 0.30
    alert_noise_max_min: 150
    stopword_growth_ratio_max: 1.8
  research:
    eff_min: 0.45
    h_i_delta_max_bits: 0.35
    alert_noise_max_min: 180
    stopword_growth_ratio_max: 1.8
```

### A.2 튜닝 스크립트 — `tools/luon/elo_domain_profile_tune.py`
```python
#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, yaml, statistics as st

# 입력: info_rollup.json (domain → timeseries) + noise/stopword 요약(optional)
# 출력: updated elo_domain_profiles.yaml (제안치)

DEFAULTS = {
  "stopword_growth_ratio_max": 1.8,
  "h_i_delta_max_bits": 0.30,
}

def suggest_eff(series):
  if not series: return 0.5
  mu = st.mean(series); sd = st.pstdev(series) if len(series)>1 else 0.0
  return round(max(0.35, min(0.9, mu - 2*sd)), 3)

def main():
  ap = argparse.ArgumentParser()
  ap.add_argument('--rollup', default='autodemo/info_rollup.json')
  ap.add_argument('--profiles', default='monitoring/elo_domain_profiles.yaml')
  ap.add_argument('--out', default='monitoring/elo_domain_profiles.yaml')
  args = ap.parse_args()

  roll = json.loads(open(args.rollup,'r',encoding='utf-8').read())
  cur = yaml.safe_load(open(args.profiles,'r',encoding='utf-8')) if open(args.profiles,'r',encoding='utf-8') else {"version":1,"profiles":{}}
  prof = cur.get('profiles',{})

  for dom, series in roll.get('efficiency',{}).items():
    p = prof.setdefault(dom, {})
    p['eff_min'] = suggest_eff(series)
    p.setdefault('h_i_delta_max_bits', DEFAULTS['h_i_delta_max_bits'])
    p.setdefault('stopword_growth_ratio_max', DEFAULTS['stopword_growth_ratio_max'])
    p.setdefault('alert_noise_max_min', 120 if dom=='ops' else 150 if dom=='support' else 180)

  cur['profiles'] = prof
  yaml.safe_dump(cur, open(args.out,'w',encoding='utf-8'))
  print(args.out)

if __name__=='__main__':
  main()
```

### A.3 Make 타깃 — `luon_full_bundle/ops/Makefile` (발췌)
```make
profiles_tune:
	python tools/luon/elo_domain_profile_tune.py --rollup autodemo/info_rollup.json --profiles monitoring/elo_domain_profiles.yaml --out monitoring/elo_domain_profiles.yaml

profiles_show:
	@echo "--- domain profiles ---" && cat monitoring/elo_domain_profiles.yaml
```

### A.4 검증 규칙 (Alert 연동) — `monitoring/elo_alert_rules_information.yaml`에 덧붙임
```yaml
  - alert: ELO_Domain_Profile_Breach
    expr: (elo_info_efficiency < on(domain) group_left()  profile_eff_min{source="elo"})
    for: 15m
    labels: {severity: page, team: ELO}
    annotations:
      summary: "Domain profile breach (eff_min)"
      description: "Efficiency fell below configured eff_min for {{ $labels.domain }}"
```
> `profile_eff_min`은 `elo_domain_profiles.yaml`을 파싱해 룰 생성 시 매크로로 주입하는 방식(간단한 템플릿 스크립트) 또는 리모트‑라이팅 룰로 구현 가능합니다.

---

## B) 단일 PR Diff (합본)

> 아래 unified diff는 이 세션에서 생성한 핵심 파일들을 **한 번에** 추가합니다. 긴 파일 본문은 이미 각 팩 문서에 수록되어 있으므로, 여기서는 **엔트리/핵심 연결부**만 포함합니다.

```diff
*** Begin Patch
*** Update File: luon_full_bundle/ops/Makefile
@@
 adapter: \ 
 	python tools/luon/elo_corpus_adapter.py --src data/raw --out autodemo/elo_corpus.jsonl --default-domain ops
@@
+profiles_tune:
+	python tools/luon/elo_domain_profile_tune.py --rollup autodemo/info_rollup.json --profiles monitoring/elo_domain_profiles.yaml --out monitoring/elo_domain_profiles.yaml
+
+profiles_show:
+	@echo "--- domain profiles ---" && cat monitoring/elo_domain_profiles.yaml
*** End Patch
```

```diff
*** Begin Patch
*** Add File: monitoring/elo_domain_profiles.yaml
+# seed profiles — tune via `make profiles_tune`
+version: 1
+profiles:
+  ops:      {eff_min: 0.52, h_i_delta_max_bits: 0.30, alert_noise_max_min: 120, stopword_growth_ratio_max: 1.8}
+  support:  {eff_min: 0.50, h_i_delta_max_bits: 0.30, alert_noise_max_min: 150, stopword_growth_ratio_max: 1.8}
+  research: {eff_min: 0.45, h_i_delta_max_bits: 0.35, alert_noise_max_min: 180, stopword_growth_ratio_max: 1.8}
*** End Patch
```

```diff
*** Begin Patch
*** Add File: tools/luon/elo_domain_profile_tune.py
+# (내용은 본문 A.2 참조 — 그대로 붙여넣기)
*** End Patch
```

```diff
*** Begin Patch
*** Update File: .github/workflows/elo_promote.yml
@@
   - name: Promote check
     run: |
       echo '{"delta_efficiency": 0.01}' > autodemo/elo_kpi.json
       python -m tools.luon.elo_label_shadow_promote --eval autodemo/elo_label_eval.json --kpi autodemo/elo_kpi.json | tee promote.txt
+  - name: Domain profiles tune
+    run: |
+      python tools/luon/elo_domain_profile_tune.py --rollup autodemo/info_rollup.json --profiles monitoring/elo_domain_profiles.yaml --out monitoring/elo_domain_profiles.yaml
*** End Patch
```

---

## C) 실행 순서 (로컬)
```bash
# 1) E2E 후 롤업 파일 산출(기존 메트릭 경로 사용)
make -C luon_full_bundle/ops adapter_to_metrics

# 2) 도메인 프로파일 자동 튜닝
make -C luon_full_bundle/ops profiles_tune && make -C luon_full_bundle/ops profiles_show

# 3) 카나리 게이트 유지한 채 Week‑1 계획대로 승급
make elo-all
```

## D) 수용 기준
- [ ] `monitoring/elo_domain_profiles.yaml`가 실제 효율 분포에 맞게 갱신됨
- [ ] 프로파일 breach 알람이 테스트 발화/해제 동작
- [ ] Promote Gates 유지한 채 5%→25% 승