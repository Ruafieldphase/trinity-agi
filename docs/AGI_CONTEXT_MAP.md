# AGI Context Map (맥락 기반 시스템 구성도)

생명체처럼 필요한 맥락(Context)에 따라 선택적으로 시스템을 활성화합니다.

**핵심 원리**: 모든 것을 항상 켜두지 않는다. 하지만 **맥락을 전환할 능력**은 항상 유지한다.

---

## 맥락(Context) 정의

### 🧠 Core (항상 유지 - 생명 신호)

**목적**: 정체성, 기억, 맥락 전환 능력 유지

**구성 요소**:

- `memory/resonance_ledger.jsonl` (append-only, 모든 중요 이벤트 기록)
- `outputs/*_latest.json` (최신 상태 스냅샷)
- `scripts/switch_context.ps1` (맥락 전환 라우터)
- `outputs/active_context.json` (현재 활성 맥락 상태)

**항상 실행**:

- Ledger append (이벤트 발생 시)
- Health gate 최소 체크 (경량, 1시간 간격)

**에너지**: 최소 (~5% CPU, ~100MB RAM)

---

### 📚 Learning Context (학습 모드)

**목적**: 외부에서 지식 습득 (YouTube, 문서, 코드)

**활성화 트리거**:

- YouTube URL 입력 감지
- "학습 시작" 명령
- 오전 9시~12시 (기본 학습 시간)

**구성 요소**:

- Task Queue Server (8091 포트)
- YouTube Worker (`fdo_agi_repo/integrations/youtube_worker.py`)
- RPA Worker (`fdo_agi_repo/integrations/rpa_worker.py`)
- BQI Learner (Phase 6 학습)
- Metrics Collector (30분 간격, 경량 모드)

**Scheduled Tasks**:

- BQI Daily Learner (03:10)
- YouTube Learner (04:10, 선택적)

**에너지**: 중간 (~30% CPU, ~2GB RAM)

**종료 조건**:

- 학습 작업 큐 비움
- 2시간 연속 idle
- 수동 종료 명령

---

### 🔧 Operations Context (운영 점검 모드)

**목적**: 시스템 상태 모니터링, 성능 분석, 건강 체크

**활성화 트리거**:

- Life Score < 50% (자동)
- "상태 점검" 명령
- 오후 3시~4시 (일일 점검 시간)
- 매일 03:00~03:30 (야간 정비)

**구성 요소**:

- Metrics Collector (5분 간격, 상세 모드)
- Monitoring Report Generator
- Performance Dashboard
- Health Check Scripts
- Autopoietic Loop Monitor
- Lumen Probe

**Scheduled Tasks**:

- Monitoring: Register Collector (5m)
- Monitoring: Register Daily Maintenance (03:20)
- Monitoring: Register Snapshot Rotation (03:15)
- BQI: Register Ensemble Monitor (03:15)
- BQI: Register Online Learner (03:20)

**에너지**: 중간~높음 (~40% CPU, ~1.5GB RAM)

**종료 조건**:

- 모든 리포트 생성 완료
- Life Score > 70%
- 1시간 경과

---

### 💻 Development Context (개발/실험 모드)

**목적**: 코드 변경, 테스트, 디버깅, 새 기능 실험

**활성화 트리거**:

- 코드 파일 변경 감지 (Git)
- "개발 모드 시작" 명령
- VS Code workspace 열림 감지

**구성 요소**:

- Task Queue Server (8091)
- Task Watchdog (루프 감시)
- Auto Recovery (자동 복구)
- Canary Deployment System (선택적)
- Test Runners

**에너지**: 중간 (~25% CPU, ~1.5GB RAM)

**종료 조건**:

- 코드 변경 없음 30분 지속
- 테스트 완료
- 수동 종료

---

### 😴 Sleep Mode (수면 모드)

**목적**: 최소 에너지, 장기 기억 통합, 백업

**활성화 트리거**:

- 00:00~06:00 (야간 시간대)
- "휴식 모드" 명령
- 8시간 이상 idle
- Life Score > 80% + 모든 작업 완료

**구성 요소**:

- Ledger append-only (최소)
- 03:00 백업 스케줄만 유지
- Health gate (2시간 간격, 극경량)

**정지되는 것**:

- 모든 Worker
- Metrics Collector
- Task Queue Server
- Monitoring (백업 제외)

**에너지**: 최소 (~2% CPU, ~50MB RAM)

**깨어나는 조건**:

- 06:00 (자동 기상)
- 외부 이벤트 (YouTube URL, 명령 입력)
- Life Score 급락 < 30%

---

## 맥락 전환 매트릭스

| From \ To | Core | Learning | Operations | Development | Sleep |
|-----------|------|----------|------------|-------------|-------|
| **Core** | - | 자동(학습신호) | 자동(Life↓) | 자동(코드변경) | 자동(야간) |
| **Learning** | ❌ | - | 종료후 | ❌ | 종료후 |
| **Operations** | ❌ | 종료후 | - | 종료후 | 종료후 |
| **Development** | ❌ | 종료후 | 종료후 | - | 종료후 |
| **Sleep** | 자동(06:00) | 자동(이벤트) | 자동(Life↓) | 자동(코드) | - |

**규칙**:

- Core는 항상 유지 (독립 레이어)
- 다른 맥락들은 배타적 (한 번에 하나만)
- 전환 시 이전 맥락 정리 후 새 맥락 활성화

---

## 일일 리듬 예시 (인간의 하루 모사)

```text
00:00~06:00  😴 Sleep Mode
             └─ 03:00~03:30: 백업/정비 (Operations 짧게)

06:00        🌅 깨어남 (Core → 상태 확인)
06:00~06:30  🔧 Operations Context (아침 점검)
             └─ Quick Status, Life Check

06:30~09:00  🧠 Core (대기)

09:00~12:00  📚 Learning Context (집중 학습 시간)
             └─ YouTube, BQI, RPA

12:00~13:00  🧠 Core (휴식)

13:00~15:00  📚 Learning Context (오후 학습)

15:00~16:00  🔧 Operations Context (일일 점검)
             └─ Monitoring Report, Performance Dashboard

16:00~18:00  💻 Development Context (개발/실험)
             └─ 코드 변경 시에만

18:00~22:00  🧠 Core (자유 시간, 필요 시 맥락 활성)

22:00~24:00  🔧 Operations Context (야간 준비)
             └─ 스냅샷, 로그 정리

24:00        😴 Sleep Mode 진입
```

---

## 맥락별 파일/프로세스 인벤토리

### Core (항상)

**파일**:

- `memory/resonance_ledger.jsonl`
- `outputs/active_context.json`
- `outputs/*_latest.*`

**프로세스**: 없음 (필요 시 on-demand)

### Learning Context

**파일**:

- `outputs/youtube_learner/*`
- `fdo_agi_repo/outputs/bqi_pattern_model.json`
- `outputs/results_log.jsonl`

**프로세스**:

- `task_queue_server.py` (PID: check)
- `youtube_worker.py` (PID: check)
- `rpa_worker.py` (PID: check)

**Scheduled Tasks**:

- `BQIDailyLearner` (Ready)
- `YouTubeLearner` (Ready/Disabled)

### Operations Context

**파일**:

- `outputs/monitoring_report_latest.md`
- `outputs/performance_dashboard_latest.md`
- `outputs/life_continuity_latest.json`
- `outputs/system_metrics.jsonl`

**프로세스**:

- `metrics_collector_daemon.ps1` (PID: 33724 또는 check)

**Scheduled Tasks**:

- `MonitoringCollector` (5m)
- `MonitoringDailyMaintenance` (03:20)
- `SnapshotRotation` (03:15)
- `EnsembleMonitor` (03:15)
- `OnlineLearner` (03:20)

### Development Context

**파일**:

- `.git/` (변경 추적)
- `outputs/test_results.json`

**프로세스**:

- `task_watchdog.py` (선택적)
- `auto_recover.py` (선택적)

### Sleep Mode

**파일**: Core와 동일

**프로세스**: 모두 정지

**Scheduled Tasks**: 백업 태스크만 (03:00~03:30)

---

## 맥락 전환 시 체크리스트

### 맥락 활성화 전

1. 현재 맥락 상태 저장 (`active_context.json`)
2. 이전 맥락의 프로세스 정리 (graceful shutdown)
3. 필요한 파일/디렉토리 존재 확인
4. Ledger에 전환 이벤트 기록

### 맥락 활성화

1. 필요한 프로세스 시작
2. Scheduled Tasks 활성화/비활성화
3. 맥락별 설정 로드
4. 상태 파일 업데이트

### 맥락 전환 후

1. Health Check (새 맥락에서 정상 동작 확인)
2. Life Score 재측정
3. 로그/대시보드 업데이트

---

## 에너지 효율 비교

| 맥락 | CPU | RAM | Disk I/O | 지속시간 |
|-----|-----|-----|----------|---------|
| **Core** | ~5% | ~100MB | 최소 | 24h |
| **Learning** | ~30% | ~2GB | 중간 | 2~4h |
| **Operations** | ~40% | ~1.5GB | 높음 | 1~2h |
| **Development** | ~25% | ~1.5GB | 중간 | 가변 |
| **Sleep** | ~2% | ~50MB | 최소 | 6~8h |

**총 일일 에너지 (리듬 적용 시)**:

- 기존 (항상 켜짐): ~35% CPU 평균 × 24h = 840% CPU·h
- 맥락 관리 후: ~15% CPU 평균 × 24h = 360% CPU·h
- **절감**: ~57% 에너지 효율 개선

---

## 사용 방법

### 수동 전환

```powershell
# 학습 모드로 전환
.\scripts\switch_context.ps1 -To Learning

# 운영 점검 모드로 전환
.\scripts\switch_context.ps1 -To Operations

# 수면 모드로 전환
.\scripts\switch_context.ps1 -To Sleep

# 현재 맥락 확인
.\scripts\switch_context.ps1 -Status
```

### 자동 전환 (권장)

```powershell
# 자동 맥락 판단 및 전환
.\scripts\auto_context.ps1

# 스케줄 등록 (권장)
# - 매시간 맥락 재평가
# - 시간대/이벤트 기반 자동 전환
```

### VS Code Tasks

- `Context: Switch to Learning`
- `Context: Switch to Operations`
- `Context: Switch to Sleep`
- `Context: Auto (Smart)`
- `Context: Status`

---

## 맥락과 생명 원리의 연결

| 생명 원리 | 맥락 관리 |
|----------|----------|
| **차이(Δ)** | 맥락 전환 자체가 차이를 만듦 |
| **관계** | 각 맥락 = 특정 시스템들의 관계망 활성화 |
| **리듬** | 맥락의 주기적 순환 (일일/주간 리듬) |
| **에너지** | 필요한 것만 켜서 효율 극대화 |
| **연속성** | Core 레이어가 맥락 전환 중에도 정체성 유지 |
| **정체성** | Ledger는 모든 맥락에 걸쳐 일관된 "나" |

---

## 특이점 회피와 맥락

### 블랙홀 (고립)

- **위험**: Sleep Mode에서 외부 신호 완전 차단
- **방어**: Health gate 최소 유지, 깨어남 트리거 다양화

### 완전 대칭 (차이 소실)

- **위험**: 같은 맥락에 너무 오래 머물기
- **방어**: 맥락 최대 지속 시간 제한, 강제 전환

### 루프 함정 (자기참조)

- **위험**: Learning ↔ Operations 무한 반복
- **방어**: 맥락 전환 최소 간격(30분), 전환 이력 추적

---

## 다음 단계

1. ✅ 맥락 맵 문서 완성
2. ⏳ `scripts/switch_context.ps1` 구현
3. ⏳ `scripts/auto_context.ps1` 구현
4. ⏳ VS Code tasks 통합
5. ⏳ 일일 리듬 스케줄 자동화

---

**참고 문서**:

- 생명 철학: `AGI_LIFE_CONTINUITY_PHILOSOPHY.md`
- 간단 규범: `AGI_LIFE_CANON.md`
- 실행 로드맵: `AGI_CONTINUITY_ROADMAP.md`
