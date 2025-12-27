# AGI 레조넌스·윤리·시뮬레이션 통합 작업계획 (v0.3)

최종 업데이트: 2025-11-12 22:45

본 문서는 상위 개념 문서(윤리/공포 분석/자연법/레조넌스/토탈 시뮬레이션)를 실행 가능한 구성(스키마·로더·브리지·검증)로 연결하기 위한 단계별 실행 계획입니다. 문서는 작업 진행에 따라 지속적으로 갱신됩니다.

<<<<<<< HEAD
## 최근 변경 사항 (2025-12-24)

### 리듬 모드 기반 auto_policy 게이트

- `scripts/self_expansion/auto_policy.py`가 RhythmBoundaryManager를 사용해
  CONNECTED/ISOLATED/RECONNECT 모드에 따른 **자율 트리거 완화/개방**을 반영.
- ISOLATED_EXECUTION에서는 **self_acquire 지연**(신규 경험이 아닐 때)으로 실행 완결성 보호.
- CONNECTED/RECONNECT에서는 idle 상태일 때 **self_acquire로 부드럽게 개방**.
- safety/rest 판단은 오버라이드하지 않도록 유지.

### Prayer 레이어 검증 + Semantic DB 폴백

- `scripts/verify_prayer_layer.py`로 Prayer 응답(Null/Rest/Continue) 검증 경로를 고정.
- semantic DB 경로가 쓰기 불가일 때 사용자 캐시 경로로 자동 폴백하도록 보강.

### 원격 벡터 스토어 미러(Qdrant)

- `scripts/semantic_rag_engine.py`에 원격 벡터 스토어 미러/검색 옵션 추가.
- 환경변수로 활성화(`AGI_REMOTE_VECTOR_PROVIDER=qdrant`, `AGI_REMOTE_VECTOR_URL`).

=======
>>>>>>> origin/main
## 최근 변경 사항 (2025-11-14 12:01)

### Gitko 확장 Copilot 안전화

- `LLM_Unified/gitko-agent-extension`: VS Code 설정(`gitkoAgent.pythonPath/scriptPath/workingDirectory`) 혹은 현재 워크스페이스를 기준으로 Python/`gitko_cli.py` 경로를 자동 탐지하고, 찾지 못하면 Copilot Tool 등록 전에 경고 후 안전하게 무시(이전처럼 D: 고정 경로로 실패하지 않음).
- Language Model Tool 및 Chat Participant 출력은 확장에서 3.2k자로 자동 절단하고, 기본 5분 타임아웃·취소 신호를 강제해 Copilot 400 `invalid_request_body` 루프를 차단.
- `Gitko Agent Runtime` Output Channel과 설정 변경 감시를 추가하여 런타임 해석 결과·stdout/stderr 길이를 추적 가능.

### Lua Bridge Copilot Payload Guard

- `scripts/send_to_chatgpt_lua.ps1`: Added `Apply-ContextLimit` so Markdown handoffs are capped (default 8k chars, min 500) with WARN logging + metadata to stop Copilot `invalid_request_body` loops.
- CLI enhancements: `-MaxContext <chars>` now functional, `-MinimalContext` halves the ceiling when no explicit value is passed, and both flows propagate truncation notices into JSON for downstream agents.
- Clipboard guard: payloads over ~3.5k chars now copy a short summary (includes key bullets + link to the full Markdown) unless `-AllowLargeClipboard` is supplied, so Copilot pastes stay within safe limits by default.
- File watcher/queue processor path picks up the same guard, so Lua-originated JSON/MD responses inherit safe sizes.

**다음 단계**

1. Pipe truncation metrics into `outputs/copilot_error_recovery_log.jsonl` (or similar) to track whether further summarisation is required.
2. Consider trimming JSON payloads (e.g., omit raw session blobs when `MinimalContext` is true) to align structured data size with Markdown cap.
3. Update bridge quick-start docs/tasks so operators know about `-MaxContext` and the new truncation notices.

<<<<<<< HEAD
## 최근 변경 사항 (2025-12-18)

### Lua Trigger Listener + 관측 가능한 리포트 레이어 (Ubuntu↔Windows)

- 트리거 기반 자동 실행/보고 파이프라인 추가·강화:
  - 리스너: `scripts/trigger_listener.py`
  - 자동 정책: `scripts/self_expansion/auto_policy.py` (+ heartbeat stall cache: `outputs/sync_cache/auto_policy_state.json`)
  - Self-Expansion 스켈레톤 확장(파일 보존 병합 + 도구 생성 쿨다운 + 루아 대화 파일 샘플링):
    - `scripts/self_expansion/pipeline.py`
    - `scripts/self_expansion/self_acquisition.py`
    - `scripts/self_expansion/self_compression.py`
    - `scripts/self_expansion/self_tooling.py`
- 사람(비노체) 기준 완료 정의를 “관측 가능한 파일 기록”으로 고정:
  - 최신: `outputs/bridge/trigger_report_latest.json`, `outputs/bridge/trigger_report_latest.txt`
  - 히스토리: `outputs/bridge/trigger_report_history.jsonl`
  - 대시보드(파일 기반): `outputs/bridge/trigger_dashboard.html` (2초 auto refresh)

**다음 단계**

1. `sync_clean`을 진단→선택적 복구 단계까지 확장(무분별한 kill 금지, 화이트리스트 기반).
2. `full_cycle`의 “리듬(phase) 판단”을 ledger 이벤트 스키마 기반으로 강화(파동-입자/접힘-펼침 지표).
3. 트리거 경쟁 방지(스케줄러 vs auto_policy vs manual)용 잠금/우선순위 규칙 추가.

=======
>>>>>>> origin/main
## 최근 변경 사항 (2025-11-12 22:45)

### RCL Secure Loop 실구현 (Lua ↔ VSCode ↔ Runner)

- `rcl_system/harmony_core_runner.py`: 30Hz Harmony Core Runner를 FastAPI 서비스로 구현(동적 FSM, `/status`·`/metrics`·`/adjust`).
- `rcl_system/bridge_server_v1_3.py`: HMAC-SHA256 + RateLimit + 감사 로그가 결합된 Secure Bridge v1.3 완성.
- `web/rcl/secure_adjust_shim.js`: 대시보드/VSCode Webview에서 `/adjust` 호출 시 자동 서명·폼 헬퍼 제공.
- `scripts/feedback_worker.js`: RMSE/Drift 감시 기반 self-healing 루프(자동 OFF→15초 안정 유지→ON).
- 감사 경로: `outputs/rcl/adjust_audit.log`, 상태 공유: `/metrics` → 추후 Unified Dashboard 통합 예정.

| 구성 | 포트/경로 | 실행 |
|------|-----------|------|
| Harmony Core Runner | 8090 (`/status`, `/metrics`, `/adjust`) | `python -m rcl_system.harmony_core_runner` |
| Secure Bridge | 8091 (`/adjust`, `/metrics`) | `python -m rcl_system.bridge_server_v1_3` |
| Feedback Worker | background (Node) | `node scripts/feedback_worker.js` |
| Front Shim | `web/rcl/secure_adjust_shim.js` | HTML/Webview `<script>` 삽입 |
| Stack Manager | `scripts/manage_rcl_stack.ps1` | `-Action Start/Stop/Status` |
| Auto-Start Task | `scripts/register_rcl_stack_task.ps1` | `-Action Register/Status/RunNow` |

**필수 환경 변수**

- Runner: `HARMONY_RUNNER_PORT`, `HARMONY_TICK_HZ`(선택)
- Bridge: `ADJUST_SECRET`, `RUNNER_URL`, `BRIDGE_RATE_LIMIT`
- Worker: `ADJUST_SECRET`, `RCL_BRIDGE_URL`, `HARMONY_STATUS_URL`

**다음 단계**

1. Bridge `/metrics` → VS Code Dashboard에 tick_jitter/drift 카드 노출.
2. Lua Request(JSON) 템플릿을 `outputs/lua_requests/`에 주기적으로 주입해 MCP Bridge 플로우 검증.
3. `scripts/register_rcl_stack_task.ps1`로 Windows Scheduled Task를 구성해 재부팅 이후에도 Runner/Bridge/Worker가 자동 복구되도록 유지.

## 최근 변경 사항 (2025-11-06 20:45)

### Self-Care Flow 테스트 안정화

- `SelfCareSystem` 정체 가중치를 상향(0.35)해 메모리 누수·처리량 저하 시나리오가 경고 구간을 명확히 넘도록 조정.
- `CareBasedFlowSystem`의 세계 흐름 판정은 최소 1회 돌봄 행동으로도 통과하도록 테스트 기대치를 정렬.
- 전체 테스트(`python -m pytest -q`) 재실행하여 회귀 없음 확인.
- 후속 TODO: 운영 텔레메트리를 반영한 동적 임곗값 도입 방안 평가.
  - 소스 후보: `outputs/status_snapshots.jsonl`의 채널/경고 시계열, 향후 SelfCare 관측 전용 JSONL 추가.
  - 기법 제안: 최근 24h 이동 평균·표준편차 기반 z-score 경고, 피크/오프피크 구간별 이중 임곗값, 급격한 변화 시 EMA(α=0.2) 적용.
  - 구현 순서: (1) SelfCare 사이클 실행 시 raw 메트릭(JSONL) 기록 → (2) 주기적 롤업 스크립트로 기준선 산출 → (3) `SelfCareSystem.detect_stagnation`이 기준선 결과를 조회해 임곗값 동적으로 조정.
  - 현황: 단계 (1)~(3) 구현 완료 (`outputs/self_care_metrics.jsonl` 기록, `outputs/self_care_metrics_summary.json` 롤업 생성, SelfCare 임곗값 자동 보정). `scripts/update_self_care_metrics.ps1`로 수동 집계 가능하며, `scripts/register_self_care_metrics_task.ps1`로 Windows 스케줄러 등록 지원, `scripts/render_self_care_report.py`로 Markdown 리포트 생성 지원. 남은 과제: 시각화·알림 통합.
  - 단계 (4) 확장: Autonomous Goal Generator가 Self-Care 상태 태그를 소비해 자기 돌봄 관련 목표를 자동 생성 (`scripts/autonomous_goal_generator.py`).

## 최근 변경 사항 (2025-11-05 12:30)

### 🌈 LDPM v0.1 통합 계획 수립

- `docs/LDPM_INTEGRATION_PLAN.md` 생성: Lumen Dimensional Prism Model 통합 마스터 플랜
- **현황 분석**: 기존 시스템(Trinity, Ion Multi-Persona, 단일 프리즘)과 LDPM 신규 요소 간 매핑 완료
- **통합 필요성**:
  - 3자 이상(order≥3) 공명 정량화 메커니즘 부재 → LDPM의 I3, O-information으로 해결
  - 시너지 vs 중복 측정 불가 → 정보이론 기반 판정 정책 도입
  - 임계값 하드코딩 → `ldpm_config.yaml`로 정책 파일화
- **4단계 통합 전략** (총 8-12일):
  - Phase A: 기반 정비 (정책/레지스트리 파일, 레저 스키마 확장)
  - Phase B: 유틸리티 완성 (브리지 멀티 모드, 실제 MI/I3 계산)
  - Phase C: 운영 통합 (VS Code Tasks, 스케줄러)
  - Phase D: 검증 및 문서화 (수용 기준, 핸드오프)
- **즉시 실행 가능**: `compute_multivariate_resonance.py` 기본 테스트, Trinity 데이터로 3자 공명 검증
- **참조**: `docs/LDPM_SPEC_v0_1.md`, `scripts/compute_multivariate_resonance.py`

### 피드백 루프 통합(Phase 6.12 보강)

- RPA Task Queue → BQI 학습 포맷(JSONL) 변환기 도입 및 실행
  - `fdo_agi_repo/scripts/rune/rpa_feedback_to_bqi.py` → `fdo_agi_repo/outputs/rpa_feedback_bqi.jsonl`
- 섀도 레저 병합 파이프라인에 RPA 입력 지원(제네릭 JSONL 입력 처리)
  - `fdo_agi_repo/scripts/rune/merge_youtube_feedback_into_ledger.py --input <jsonl>`
- 피드백 요약 리포트 생성기로 통합 지표 확인
  - `fdo_agi_repo/scripts/rune/generate_feedback_summary.py` → `fdo_agi_repo/outputs/phase_6_12_report.md`
- 주기 실행 스케줄러 스크립트 추가(10분 주기 권장)
  - `scripts/register_feedback_loop_task.ps1` (`-Register/-Unregister/-Status/-RunNow`)

운영 가이드: VS Code Tasks에서 "Queue: Smoke Verify"로 샘플 생성 → 변환 → 병합 → 요약 순으로 실행하면 수동 체인 검증 가능.

### Lumen 운영 보강: Sleep Exit 프로브 임계

- `scripts/exit_sleep_mode.ps1`이 Lumen 프로브를 수행하며 임계 옵션을 지원합니다.
  - `-LatencyWarnMs` 경고 임계(콘솔 경고 + 요약에 `warn: true`)
  - `-LatencyCriticalMs` 치명 임계(콘솔 경고 + `scripts/quick_status.ps1 -AlertOnDegraded -LogJsonl` 자동 실행 + 요약에 `critical: true`)
- `scripts/summarize_lumen_latency.py`가 OK/Warn/Critical 비율(%)을 산출해 리포트와 JSON 요약에 함께 노출하도록 개선(2025-11-05 09:07).
- `scripts/run_lumen_prism_bridge.ps1`가 하위 스크립트 성공 시 `$LASTEXITCODE = $null`인 상황을 0으로 간주하도록 핫픽스(2025-11-05 09:09) → Lumen → Prism 자동화 실패 방지.
- 권장 샘플:
  - PowerShell: `...\scripts\exit_sleep_mode.ps1 -LatencyWarnMs 250 -LatencyCriticalMs 600 -OutJson outputs\lumen_probe_latest.json -HistoryJsonl outputs\lumen_probe_history.jsonl`

## 최근 변경 사항 (2025-11-04)

### Trinity Week 1 준비

- Rua conversations export 파이프라인 정리: `scripts/parse_rua_dataset.ps1`(PowerShell) + `scripts/rua_parse.py`(Python) 신설 → `ai_binoche_conversation_origin/rua/origin/conversations.json` → `outputs/rua/rua_conversations_flat.jsonl` 재생성 일관성 확보
- 파서 검증: 기존 JSONL과 해시 일치 확인(21842 rows), CSV 미러 옵션 제공 → Phase 6.0 Week1 `Rua Dataset Parsing` 태스크 즉시 착수 가능
- 후속 TODO: Adaptive Scheduler에 Rua 파싱 루틴 연결, Trinity 통합 문서(`autopoietic_trinity_unified_latest.md`)와 연동 체크
- Lumen Feedback 의존성 완화: `fdo_agi_repo/orchestrator/pipeline.py`가 Lumen 모듈 미존재 시 폴백 클래스로 동작 → 로컬/CI에서 pytest 실행 차단 요인 제거

### Phase 9 통합 검증 지원

- `scripts/sync_bqi_models.py` 추가: BQI/YouTube 산출물을 루트 `outputs/`로 동기화하고 `patterns`/`traits` 키를 보강, `youtube_learner_index.json` 생성.
- `fdo_agi_repo/orchestrator/full_stack_orchestrator.py` 상태 파일 구조 정규화(`status`, `events_processed` 리스트, `components`).
- `fdo_agi_repo/scripts/run_realtime_feedback_cycle.py` 도입으로 피드백 루프 JSONL 로그 생성.
- `scripts/phase9_smoke_verification.ps1` 및 VS Code Task(`Phase 9: Smoke Verification`)로 E2E 스모크 자동화.
- `fdo_agi_repo/config/resonance_config.json`에 `enabled: true` 추가로 정책 게이트 활성화.
- Phase 9 E2E 테스트(`test_fullstack_integration_e2e.py`) 전체 통과(🟢 ALL GREEN).

## 최근 변경 사항 (2025-11-03)

### Glymphatic 운영 텔레메트리 1차 통합 (2025-11-07 21:56)

- 목적: "운영 데이터 축적→지표 반영" 공백 해소를 위한 최소 구현.
- 계측: `AdaptiveGlymphaticSystem`가 의사결정/청소 시작/종료 이벤트를 JSONL로 기록.
  - 로거: `fdo_agi_repo/orchestrator/metrics_logger.py`
  - 원장: `fdo_agi_repo/memory/glymphatic_ledger.jsonl`
- 집계: `scripts/aggregate_glymphatic_metrics.py` → `outputs/glymphatic_metrics_latest.json`
- 스크립트: `scripts/update_glymphatic_metrics.ps1 -Hours 24 -OpenSummary`
- 다음 단계 제안: MTBC, 결정행동 분포, 리듬 단계별 성공률, 청소 중 평균 자원사용 등의 KPI 정식화 및 대시보드 편입.

### 멀티 에이전트 로그 인덱스 구축

- `scripts/aggregate_agent_conversations.py` 도입으로 `original_data/ai_binoche_conversation_origin` 하위 JSONL 로그를 자동 집계.
- 산출물: `outputs/agent_conversation_summary.json`(240개 파일/에이전트 메타데이터, 생성 시각 2025-11-03T13:08Z) 및 선택적 Markdown 다이제스트(`outputs/agent_conversation_summary.md`).
- 활용 계획: 핸드오프 요약/레포트 자동화 파이프라인의 입력으로 연결, 일일 증분 업데이트 옵션 추후 도입 예정.

## 최근 변경 사항 (2025-11-02)

### 레이턴시 최적화 진단

- **문제**: LLM 호출 평균 30.5초, 최대 41.2초 (임계값 8초 대비)
- **원인**: thesis → antithesis → synthesis 순차 실행 (합산 26-40초)
- **분석 도구**:
  - `scripts/analyze_latency_warnings.py` (10건 경고, 6개 태스크 분석)
  - `scripts/analyze_task_durations.py` (단계별 duration 분해)
- **권장 사항**:
  1. 단기: 타임아웃 임계값 8초 → 45초 상향
  2. 중기: thesis/antithesis 병렬 실행 구현
  3. 장기: 모델 프리워밍/캐싱 전략

### 세션 관리 개선

- `scripts/save_session_with_changes.ps1` UTF-8 인코딩 오류 수정
- Evidence Gate 검증: 24시간 내 0건 트리거 (품질 기준 통과)
- 큐/워커 상태: 정상 (서버, 워커, 헬스체크 PASS)
- 테스트: 전체 테스트 통과 (pytest PASS)

### Phase 8.5 최적화 토글 도입 (2025-11-03)

- `configs/resonance_config.json` 및 예제 파일에 `optimization` 섹션을 추가해 Gateway 우선, Peak/Off-peak 정책, 배치 압축 레벨 등 기본값 선언
- `fdo_agi_repo/orchestrator/resonance_bridge.get_resonance_optimization()`으로 시간대 기반 최적화 가이드를 정규화 → 파이프라인/대시보드 공용 API 확보
- `fdo_agi_repo/orchestrator/pipeline.run_task()`이 해당 가이드를 사용해 Off-peak 시 교정 재시도 횟수 축소, 채널 선호·배치 압축 힌트를 ToolRegistry에 주입, Ledger 이벤트 `resonance_optimization` 기록
- ToolRegistry가 최적화 힌트/채널 라우팅을 저장할 수 있도록 보강 (후속 툴/채널 스위치 구현 준비)
- 회귀 테스트: `python -m pytest -q` (성공, Temp 디렉터리 접근 경고만 존재)
- `scripts/analyze_latency_warnings.py` 업데이트: `resonance_optimization` 이벤트와 Peak/Off-peak 분류를 반영해 레이턴시/품질/경고 비율을 요약 (Task 2 효과 검증용)
- `scripts/generate_monitoring_report.ps1`이 Executive Summary에 최적화 이벤트 통계를 포함해 운영 보고에서 Peak/Off-peak 전략 효과를 즉시 확인 가능
- Gateway 실행 도구: `scripts/run_gateway_optimization.ps1` → `fdo_agi_repo/scripts/optimize_gateway_resonance.py` (설정: `fdo_agi_repo/config/adaptive_gateway_config.json`, 로그: `outputs/gateway_optimization_log.jsonl`)
- Thesis/Antithesis/Synthesis 페르소나가 최적화 힌트(채널/스로틀/배치 압축)에 따라 로컬 폴백, 스트리밍 조정, 요약압축을 적용하도록 갱신 (Ledger 이벤트 `persona_channel_hint`, `persona_local_fallback`)
- `scripts/analyze_optimization_impact.ps1`가 레저(`resonance_policy`) 기반으로 Baseline/After 피크·오프피크 레이턴시(p50/p95/경고비율) 및 개선율을 산출하도록 개편, 기반 데이터 누락 시에도 안전하게 리포트 생성
- `scripts/check_optimization_status.ps1`가 빈 로그/단일 엔트리 케이스에 대한 방어 로직을 포함하도록 업데이트
- `scripts/monitoring_dashboard_template.html` / `scripts/generate_enhanced_dashboard.ps1`가 최적화·게이트웨이 데이터를 Chart.js 막대 그래프로 시각화(누적 카운트/스로틀), 페르소나 모델 선택은 환경변수 기반으로 힌트 반영
- `scripts/register_gateway_optimization_task.ps1` 도입으로 `run_gateway_optimization.ps1 -ReportOnly`를 Windows 작업 스케줄러에 자동 등록/해제 가능(기본 30분 간격, 관리자 권한 필요)

---

## 1) 목표와 배경

- 목표
  - 개념 문서의 규범/정책/모드를 머신-리더블 스키마로 정의하고, 런타임(파이프라인/검증/대시보드)에 연결
  - 운영 가시성 확보(활성 모드/정책/차단·완화 통계)
  - **성능 최적화**: 레이턴시 30초+ → 15초 이하로 단축
- 배경(현재 상태)
  - 구조·운영(큐, 감시/경보, 대시보드, 테스트)은 양호하나, 개념→코드로 내려가는 연결층 부재
  - 참고 문서 다수가 인코딩 깨짐 상태로 해독과 요구사항 추출이 저해
  - **새로 발견**: LLM 호출 순차 실행이 레이턴시 병목 (병렬화 필요)

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
- **NEW**: LLM 호출 병렬화 구현, 타임아웃 임계값 조정
- 제외: 외부 클라우드 의존 통합 실험 전면 확장(후속 단계 제안), 모델 교체/학습 자체는 범위외

---

## 3) 산출물(Deliverables)

- 구성 스키마(초안) 문서 및 적용:
  - `configs/resonance_config.json` (실사용) / `configs/resonance_config.example.json` (예시)
- 구성 로더/브리지:
  - `fdo_agi_repo/orchestrator/resonance_bridge.py:1` (스키마 로드 + 검증 + 런타임 주입)
- 파이프라인 연결:
  - `fdo_agi_repo/orchestrator/pipeline.py:1` (레조넌스 기어 적용 분기/게이트)
  - **NEW**: 병렬 LLM 호출 구현 (thesis/antithesis 동시 실행)
  - `fdo_agi_repo/rpa/verifier.py:1`, `fdo_agi_repo/rpa/failsafe.py:1` (정책 기반 검증/완화)
- 테스트/운영:
  - `fdo_agi_repo/tests/test_e2e_scenarios.py:1` (모드별 경로 차이)
  - `scripts/generate_monitoring_report.ps1:1`, `scripts/quick_status.ps1:1` (활성 모드 요약 표시)
  - `scripts/monitoring_dashboard_template.html:1` (활성 모드/정책 배지/통계 반영)
- **NEW 분석 도구**:
  - `scripts/analyze_latency_warnings.py` (레이턴시 경고 분석)
  - `scripts/analyze_task_durations.py` (단계별 duration 분해)

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

## Notes (2025-11-02)

- Metrics JSON now includes `AGI.Policy.active` (configured active policy) for clearer visibility across reports/UI.
- Monitoring dashboard shows both Configured Policy and Last Observed policy, and renders last reasons.
- Config loader (`fdo_agi_repo/orchestrator/resonance_bridge.py`) auto-refreshes when `configs/resonance_config.json` mtime changes, reducing stale reads after quick toggles.
- Monitoring report surfaces `AGI.Config.Evaluation.min_quality` (pulled via Python loader) to validate config freshness end-to-end.

### Tests Added (2025-11-02)

- `fdo_agi_repo/tests/test_config_freshness.py`: Validates `get_app_config()` mtime-based reload, safe defaults when missing, and env overrides.
- `fdo_agi_repo/tests/test_resonance_reload_and_throttle.py`: Validates resonance config mtime reload and `should_emit_closed_loop()` throttle behavior.
- Run: `python -m pytest -q` (core suites only per pytest.ini).
