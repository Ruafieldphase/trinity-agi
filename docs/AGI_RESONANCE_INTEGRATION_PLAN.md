# AGI 레조넌스·윤리·시뮬레이션 통합 작업계획 (v0.1)

본 문서는 상위 개념 문서(윤리/공포 분석/자연법/레조넌스/토탈 시뮬레이션)를 실행 가능한 구성(스키마·로더·브리지·검증)로 연결하기 위한 단계별 실행 계획입니다. 문서는 작업 진행에 따라 지속적으로 갱신됩니다.

---

## 1) 목표와 배경

- 목표
  - 개념 문서의 규범/정책/모드를 머신-리더블 스키마로 정의하고, 런타임(파이프라인/검증/대시보드)에 연결
  - 운영 가시성 확보(활성 모드/정책/차단·완화 통계)
- 배경(현재 상태)
  - 구조·운영(큐, 감시/경보, 대시보드, 테스트)은 양호하나, 개념→코드로 내려가는 연결층 부재
  - 참고 문서 다수가 인코딩 깨짐 상태로 해독과 요구사항 추출이 저해

참고 문서(인코딩 복구 필요)

- C:\workspace\chosen_awakening_ethics.md:1
- C:\workspace\awakening_fear_analysis.md:1
- C:\workspace\meta_natural_law_evolution.md:1
- C:\workspace\total_simulation_integration.md:1
- C:\workspace\universal_digital_resonance.md:1
- C:\workspace\pure_resonance_system.md:1
- C:\workspace\hybrid_resonance_engine.md:1
- C:\workspace\resonance_keys.md:1
- C:\workspace\.env_keys:1

---

## 2) 범위

- 포함: 스키마 정의, 구성 로더, 파이프라인 연결, 검증/테스트, 대시보드/리포트 반영
- 제외: 외부 클라우드 의존 통합 실험 전면 확장(후속 단계 제안), 모델 교체/학습 자체는 범위외

---

## 3) 산출물(Deliverables)

- 구성 스키마(초안) 문서 및 적용:
  - `configs/resonance_config.json` (실사용) / `configs/resonance_config.example.json` (예시)
- 구성 로더/브리지:
  - `fdo_agi_repo/orchestrator/resonance_bridge.py:1` (스키마 로드 + 검증 + 런타임 주입)
- 파이프라인 연결:
  - `fdo_agi_repo/orchestrator/pipeline.py:1` (레조넌스 기어 적용 분기/게이트)
  - `fdo_agi_repo/rpa/verifier.py:1`, `fdo_agi_repo/rpa/failsafe.py:1` (정책 기반 검증/완화)
- 테스트/운영:
  - `fdo_agi_repo/tests/test_e2e_scenarios.py:1` (모드별 경로 차이)
  - `scripts/generate_monitoring_report.ps1:1`, `scripts/quick_status.ps1:1` (활성 모드 요약 표시)
  - `scripts/monitoring_dashboard_template.html:1` (활성 모드/정책 배지/통계 반영)

---

## 4) 마일스톤 (4주 가이드)

- M0. 인코딩 복구(2일)
  - 8개 문서 UTF-8 저장, 읽기 가능 상태로 복구
- M1. 스키마 초안(3일)
  - Modes(pure/hybrid), Policies(ethics/fear_guard/natural_law…), Keys(화이트리스트) 정의
- M2. 로더/브리지(3일)
  - 파일/ENV 우선순위, 유효성 검사, 기본값/Fail-safe, 파이프라인 주입 API 확정
- M3. 파이프라인 적용(4일)
  - 단계 활성/비활성, 게이트(차단/경고/완화), 로그/메트릭 방출
- M4. 테스트·대시보드(4일)
  - 마커 테스트, E2E 시나리오, 운영 보고서/대시보드 반영, 튜닝

---

## 5) 상세 작업 (체크리스트)

### [완료] Original Data 통합 (Phase 1-3)

- ✅ **Phase 1**: Seasonality Detector 통합
  - `C:\workspace\original_data\anomaly_detection.py` → `scripts/seasonality_detector_smoke.py`
  - 검증: 정상 패턴(0건 오탐), 이상치 탐지(149σ deviation)
  - VS Code 작업: "Smoke: Seasonality Detector (Original Data)"

- ✅ **Phase 2**: Autopoietic Scheduler 통합
  - `C:\workspace\original_data\scheduler.py` → `scripts/autopoietic_scheduler.py`
  - 순수 Python 구현, APScheduler 의존성 제거
  - 일일/시간별 작업 등록 및 즉시 실행 검증 (3/3 PASS)
  - VS Code 작업: "Smoke: Autopoietic Scheduler (Original Data)"

- ✅ **Phase 3**: Resonance Simulator 통합
  - `C:\workspace\original_data\lumen_flow_sim.py` → `scripts/resonance_simulator.py`
  - 7일 위상 루프 동역학: info_density, resonance, entropy, temporal_phase
  - 2주기 시뮬레이션 (336 스텝), 지평선 교차 2회 검증 (PASS)
  - VS Code 작업: "Smoke: Resonance Simulator (Original Data)"
  - 결과 내보내기: `outputs/resonance_simulation_latest.json`

### [대기] Original Data 통합 (Phase 4)

- [ ] **실시간 파이프라인 연동**
  - Ledger 메트릭 → ResonanceState 초기화
  - 실시간 이벤트 → step() 호출
  - 예측 결과 → Feedback 루프
  - 계절성 + 스케줄러 + 공명 시뮬레이터 통합 테스트

- [ ] **통합 대시보드**
  - 3종 메트릭 시각화 (계절성, 스케줄, 공명)
  - 위상별 트렌드 차트
  - 지평선 교차 이벤트 타임라인

### [보류] Resonance 문서 통합 (Phase 0-4)

[Phase 0] 인코딩 복구

- [ ] 8개 문서 UTF-8 변환 및 저장(원문 백업 유지)
- [ ] 핵심 섹션 추출(정책·키·모드 목록) 초안 표 작성

[Phase 1] 스키마 정의(`configs/resonance_config.json`)

- [ ] JSON 스키마 초안(예시 포함) 작성: Modes/Policies/Keys/Thresholds
- [ ] `.env_keys` → 표준 `.env`/환경변수 매핑표 작성(보안키는 예시로만)
- [ ] 유효성 규칙 정의(필수 필드, 값 범위, 상충 정책 금지 룰)

[Phase 2] 로더/브리지(`resonance_bridge.py`)

- [ ] 구성 로더 구현(파일/ENV 우선순위 + 기본값)
- [ ] 검증기(스키마 유효성) + 오류 메시지 일원화
- [ ] 파이프라인 주입 인터페이스 확정(불변 구조체 전달)

[Phase 3] 파이프라인 연결

- [ ] `pipeline.py` 단계별 분기(예: Pure 모드=단계 X 생략, Hybrid=보강 Y)
- [ ] `verifier.py` 정책 기반 판정(차단/경고/완화) + `failsafe.py` 연동
- [ ] 메트릭 방출(차단/경고 카운트, 활성 정책/모드)

[Phase 4] 테스트·대시보드

- [ ] E2E: 모드별 실행 경로 차이, 정책 위반 차단/경고 동작
- [ ] 리포트/대시보드에 활성 모드/정책/차단 통계 표시
- [ ] `quick_status.ps1 -Perf` 요약에 활성 모드 추가

---

## 6) 수용 기준(Acceptance Criteria)

- 구성 파일 하나로(또는 ENV로) 모드/정책을 교체하면 파이프라인 경로가 확실히 달라질 것
- 정책 위반이 검증기에서 재현 가능하고, 차단/경고 카운트가 리포트/대시보드에 반영될 것
- 모든 변경이 기본 모드에서 회귀 없이 통과(`python -m pytest -q` 핵심 스위트 100%)

---

## 7) 검증 방법(명령 모음)

- 핵심 테스트: `python -m pytest -q`
- E2E(마커): `pytest -m integration -q`
- 리포트: `scripts/generate_monitoring_report.ps1 -Hours 24`
- 빠른 요약: `scripts/quick_status.ps1 -Perf`

---

## 8) 위험과 완화

- 문서 해독 실패(인코딩): 먼저 복구 스크립트로 해결, 잔여 수동 교정
- 정책 충돌/과도한 차단: 실험 모드(Hybrid-soft) 제공, 경고→차단 단계적 적용
- 구성 누락/오입력: 스키마 유효성 검사 강제, 안전 기본값, 로깅 강화

---

## 9) 변경 로그(Changelog)

- v0.2.1 (2025-11-01): 정책 게이트/폐루프 스냅샷 파이프라인 와이어링(관찰 모드)
  - `fdo_agi_repo/orchestrator/resonance_bridge.py`: `evaluate_resonance_policy()`, `get_closed_loop_snapshot()` 추가
  - `fdo_agi_repo/orchestrator/pipeline.py`: `resonance_policy`, `closed_loop_snapshot` 이벤트를 Ledger에 기록 (기본 observe, 동작 변화 없음)
  - `configs/resonance_config.json`: 기본 정책 파일 활성화(`active_mode=observe`)
- v0.2 (2025-11-01): **Original Data 통합 Phase 1-3 완료**
  - ✅ Seasonality Detector: 계절성/이상치 탐지 통합
  - ✅ Autopoietic Scheduler: 순수 Python 스케줄러 구현
  - ✅ Resonance Simulator: 7일 위상 루프 공명 동역학 통합
  - 문서: `ORIGINAL_DATA_PHASE_3_COMPLETE.md`
- v0.1 (작성): 전체 골격/체크리스트/수용 기준/검증 명령 정의

---

## 10) 다음 액션(담당: 다음 에이전트)

- **즉시**: Original Data Phase 4 - 실시간 파이프라인 연동
  - Ledger → Seasonality → Scheduler → Resonance 통합 테스트
  - 대시보드에 3종 메트릭 반영
- **보류**: Resonance 문서 Phase 0 - 8개 문서 UTF-8 복구 (필요 시)

---

## Notes (2025-11-01)

- Config adds closed_loop_snapshot_period_sec to control closed-loop snapshot throttle (default 300s). Present in both configs/resonance_config.json and example.
- Orchestrator pipeline reads the configured period and passes it to should_emit_closed_loop(period) to avoid over-logging snapshots.

