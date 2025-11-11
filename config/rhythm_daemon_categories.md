# Rhythm-Aware Daemon Categories

데몬/태스크를 리듬 모드(work/rest/auto)에 따라 분류합니다.

## 1. 필수 (24시간 유지)

항상 실행되어야 하는 핵심 시스템 구성요소:

- **Task Queue Server (8091)**: RPA 작업 큐 처리
- **Original Data API (8093)**: 데이터 인덱싱 서비스
- **Observer Server (8095)**: 텔레메트리 대시보드
- **Task Watchdog**: 작업 감시 및 자동 복구
- **Master Orchestrator**: 전체 시스템 조율

## 2. 업무시간 활성 (Work Mode)

집중 작업 시 필요한 데몬:

- **RPA Worker**: 고빈도 작업 처리 (0.3초 간격)
- **Worker Monitor**: 워커 상태 모니터링 (5초 간격)
- **Desktop Telemetry Observer**: 데스크톱 활동 관찰 (5초 간격)
- **Flow Observer (ADHD)**: 주의력 추적 및 흐름 상태 감지
- **Monitoring Collector**: 시스템 메트릭 수집 (5분 간격)
- **Goal Executor Loop**: 자율 목표 실행 (고빈도)
- **Music Daemon**: 적응형 음악 재생 (60초 간격)

## 3. 휴식시간 전용/중지 권장 (Rest Mode)

휴식 중 불필요하거나 시스템 부하를 줄이기 위해 중지:

- **Desktop Telemetry Observer**: 중지 (화면 변화 추적 불필요)
- **Flow Observer**: 일시 중지 또는 저빈도 모드 (10분 간격)
- **RPA Worker**: 중지 (작업 큐 비활성)
- **Worker Monitor**: 중지
- **Goal Executor Loop**: 일시 중지

## 4. 양면 (빈도 조절)

두 모드 모두 필요하지만 간격 조절 가능:

### Work Mode (고빈도)

- **Monitoring Collector**: 5분 간격
- **Music Daemon**: 60초 간격
- **Cache Validator**: 12시간 간격

### Rest Mode (저빈도)

- **Monitoring Collector**: 15분 간격
- **Music Daemon**: 300초 간격 (5분)
- **Cache Validator**: 24시간 간격

## 5. 야간 전용 (Scheduled)

특정 시간에만 실행:

- **Daily Maintenance (03:20)**: 스냅샷 로테이션
- **Snapshot Rotation (03:15)**: 아카이브 압축
- **BQI Phase 6 (03:05-03:20)**: 학습 파이프라인
- **Trinity Cycle (10:00)**: 자율 사이클

## Auto Mode 동작

### Time-based Detection

- **06:00-22:00**: Work Mode (업무/활동 시간)
- **22:00-06:00**: Rest Mode (휴식/저부하 시간)

### Rhythm File-based Detection

`outputs/RHYTHM_SYSTEM_STATUS_REPORT.md` 파싱:

- "REST PHASE" 키워드 → Rest Mode
- "ACTIVE PHASE" 또는 "EXCELLENT" 건강도 → Work Mode
- CPU > 80% 또는 메모리 < 512MB → Rest Mode (부하 감소)

## 전환 안전 규칙

1. **Kill 전 확인**: 프로세스가 실제 실행 중인지 확인
2. **Timeout**: 각 Start/Stop 작업은 10초 타임아웃
3. **Skip if Running**: 이미 실행 중이면 중복 실행 방지
4. **DryRun 기본**: 실제 변경 전 시뮬레이션 가능
5. **Logging**: 모든 전환을 `outputs/rhythm_mode_transitions.log`에 기록

## 구현 전략

```powershell
# Work Mode 전환
scripts/rhythm_mode_manager.ps1 -Mode work

# Rest Mode 전환
scripts/rhythm_mode_manager.ps1 -Mode rest

# Auto (시간/파일 기반)
scripts/rhythm_mode_manager.ps1 -Mode auto

# DryRun 시뮬레이션
scripts/rhythm_mode_manager.ps1 -Mode work -DryRun
```

## 기대 효과

### Work Mode

- 빠른 응답: RPA/Flow/Telemetry 고빈도
- 자율 목표 활발: Goal Executor 활성
- 실시간 피드백: Observer/Monitor 활성

### Rest Mode

- CPU 절약: 20-30% 감소 예상
- 메모리 확보: Worker/Observer 중지로 500MB+ 확보
- 배터리 수명: 노트북 사용 시 30% 향상
- 조용한 시스템: 디스크/네트워크 I/O 감소

### Auto Mode

- 사람 개입 없이 자동 전환
- 리듬 파일 + 시간대 조합 판별
- 예외 상황(고부하) 자동 감지
