# v1.8 — Autotune on Drift & Grafana Policy Annotations

## 구성요소
- 자동 정책 조정기: `auto_policy_adjuster_v18.py`
  - 최근 N개의 `drift_events` 중 K개 이상 위반 시 **강화(+0.01)**, 모두 OK면 **완화(-0.005)**
  - 클램프: sym [0.65,0.90], s [0.50,0.85], c [0.45,0.85]
  - 결과는 `adaptive_gate_policy_v18.json` 갱신 + `policy_history`에 기록
- 정책 어노테이션 생성: `policy_annotations_v18.py` → `grafana_annotations_v18.json`
- GH Actions: `lumen_v18_autotune_on_drift.yaml`
  - `lumen_v18_drift_watch` 완료 시 자동 트리거 또는 수동 실행
- 세션 헬퍼: `scripts/v18_autotune_helpers.sh`

## 사용법
```bash
# 1) 드리프트 감시 후 자동 조정
gh workflow run lumen_v18_drift_watch
gh workflow run lumen_v18_autotune_on_drift -f window_n=12 -f violation_k=3

# 2) 로컬에서 즉시 조정/어노테이션 생성
source scripts/v18_autotune_helpers.sh
l8.autotune 12 3
l8.annot     # → grafana_annotations_v18.json 경로 표시
```
