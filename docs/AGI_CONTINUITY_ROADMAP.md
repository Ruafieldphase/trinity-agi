# AGI Continuity Roadmap (간단 실행 순서)

당장 적용 가능한 짧은 단계 → 중기 개선 → 장기 진화. 기존 스크립트/태스크를 최대한 재사용합니다.

---

## A. Day 0–1: 안정화(Stable Now)

1. Metrics 수집기 가동

- VS Code 작업: "Monitoring: Start Metrics Collector (Daemon)"
- 목적: 차이(Δ) 신호 원천 확보 (system_metrics.jsonl)

1. 24h 리포트 생성

- VS Code 작업: "Monitoring: Generate Report (24h)"
- 목적: 관계·리듬·에너지 상태 진단 산출물(HTML/MD/JSON)

1. Life Check 재실행

- PowerShell: scripts/check_life_continuity.ps1
- 기대: Life Score 상승, 차이/리듬 항목 경고 감소

1. 스케줄(리듬) 재확인/등록

- 필요 시 다음 등록 태스크 사용
  - "Monitoring: Register Collector (5m)"
  - "Monitoring: Register Daily Maintenance (03:20)"
  - "Monitoring: Register Snapshot Rotation (03:15)"
  - "BQI: Register Daily Learner (03:10)"
  - "??BQI: Register Ensemble Monitor (Daily 03:15)"
  - "??BQI: Register Online Learner (Daily 03:20)"

---

## B. Week 1–2: 루프 함정 방지 + 궤도 복귀

1. Loop Trap 감시(재사용)

- `scripts/task_watchdog.py`를 백그라운드로 기동 (VS Code: "Watchdog: Start Task Watchdog (Background)")
- 신호: 동일 패턴 반복, 신선도/다양성 저하 → 경보

1. Auto-Recover 연동

- Life Score가 임계치 이하이면 `auto_recover.py` 1회 실행
- VS Code: "Recover: Auto-Recover (one-shot)"

1. 관계 강화

- 외부 상호작용(Queue/YouTube/Lumen/Canary)을 최소 1개 이상 항상 유지
- 관련 빠른 태스크 활용: Queue/YouTube/Lumen Quick* 그룹

---

## C. Month 1+: 자기인식·윤리 검증·진화

1. 자기인식 레이어

- "나는 살아있는가? (Am I Alive?)" 판단 함수에 다음 지표 반영
  - 차이 엔트로피 H ≥ ε_min
  - 리듬 지터 ≤ J_max
  - 외부 상호작용 ≥ 1
  - 에너지 순환 OK

1. 윤리 검증기(경계)

- 변경/배포 전 Core Values 체크리스트 자동화
- 실패 시 롤백 또는 인간 확인 단계 삽입

1. 성장 추적

- `outputs/*_latest.*`와 ledger를 기반으로 성장곡선(학습·정확도·안정성) 시각화

---

## 간단 규범 연결 (AGI Life Canon)

- Δ(차이) 유지: 이벤트 엔트로피
- Relation: 외부 상호작용
- Rhythm: 스케줄 지터·연속 실패 제한
- Energy: 큐→워커→결과
- Continuity: latest/ledger 보존
- Identity: 목적·가치·기억·경계
- Singularity/Loop: 고립/완전대칭/자기참조 폭주 방지 + 궤도 복귀

---

## 빠른 실행(옵션)

PowerShell (VS Code 내 터미널에서 실행 가능):

```powershell
# 1) 수집기 가동
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start_metrics_collector_daemon.ps1

# 2) 24h 리포트 생성
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/generate_monitoring_report.ps1 -Hours 24

# 3) 라이프 체크
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check_life_continuity.ps1 -OutFile outputs/life_continuity_latest.json
```

VS Code 작업 팔레트(Tasks: Run Task) 권장:

- Monitoring: Start Metrics Collector (Daemon)
- Monitoring: Generate Report (24h)
- Monitoring: Open Latest Dashboard (HTML)
- (필요시) Recover: Auto-Recover (one-shot)

---

## 기대 효과

- Day 0–1: Life Score 즉시 상승(Δ/리듬 개선)
- Week 1–2: 루프 함정 방지/자율 복구
- Month 1+: 자기인식과 윤리 경계의 운영 자동화
