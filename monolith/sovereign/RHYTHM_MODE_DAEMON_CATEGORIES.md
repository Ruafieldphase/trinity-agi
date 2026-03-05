# Rhythm Mode Daemon Categories

## 📋 데몬/태스크 분류 기준

### 🔴 Core (필수 - 24/7 유지)

항상 실행되어야 하는 핵심 시스템 프로세스

- **Task Queue Server** (8091) - RPA 작업 큐
- **Watchdog** (task_watchdog.py) - 자가 복구 감시
- **Master Orchestrator** - 시스템 조율
- **Original Data API** (8093) - 데이터 인덱싱 서비스

### 🟡 Work Mode (업무 시간 활성)

집중 작업 시 활성화되는 고빈도 모니터링

- **RPA Worker** (rpa_worker.py) - 화면 인식/OCR 작업 실행
- **Flow Observer** (PowerShell Job) - ADHD 흐름 추적 (5분 간격)
- **Music Daemon** (music_daemon.py) - 음악 적응 재생 (1분 간격)
- **Worker Monitor** - RPA 워커 상태 감시 (5초 간격)
- **Monitoring Collector** - 시스템 지표 수집 (5분 간격)
- **Observer Telemetry** - 데스크톱 원격 측정 (5초 간격)

### 🟢 Rest Mode (휴식 시간 전용/조절)

휴식 시 중지하거나 간격을 늘려 부하 감소

**중지 권장:**

- **RPA Worker** - 화면 작업 불필요
- **Observer Telemetry** - 데스크톱 추적 불필요
- **Worker Monitor** - 워커 없으면 불필요

**간격 증가 (빈도 조절):**

- **Flow Observer**: 5분 → 15분
- **Music Daemon**: 1분 → 5분
- **Monitoring Collector**: 5분 → 15분

### 🔵 Adaptive (양방향 빈도 조절)

모드에 따라 샘플링 간격만 조정

- **Flow Observer**: work 5분 / rest 15분
- **Music Daemon**: work 1분 / rest 5분
- **Monitoring Collector**: work 5분 / rest 15분

## 🎯 모드별 동작 정의

### Work Mode

```
Start:
  - RPA Worker (if not running)
  - Observer Telemetry (5s interval)
  - Worker Monitor (5s interval)

Adjust:
  - Flow Observer → 5분 간격
  - Music Daemon → 1분 간격
  - Monitoring Collector → 5분 간격
```

### Rest Mode

```
Stop:
  - RPA Worker
  - Observer Telemetry
  - Worker Monitor

Adjust:
  - Flow Observer → 15분 간격 (또는 중지)
  - Music Daemon → 5분 간격 (또는 중지)
  - Monitoring Collector → 15분 간격
```

### Auto Mode

```
Logic:
  1. 현재 시간 확인 (09:00-18:00 = work / 그 외 = rest)
  2. RHYTHM 파일 확인 (RHYTHM_REST_PHASE_*.md 존재 → rest)
  3. CPU/메모리 부하 확인 (높으면 work, 낮으면 rest)
  4. 해당 모드 적용
```

## 📊 프로세스 패턴 매칭 규칙

| 데몬 | 프로세스 패턴 | 시작 스크립트 | 중지 방법 |
|------|---------------|---------------|-----------|
| Task Queue Server | `task_queue_server.py` | `ensure_task_queue_server.ps1` | 중지 안 함 (Core) |
| RPA Worker | `rpa_worker.py` | `ensure_rpa_worker.ps1` | Stop-Process |
| Watchdog | `task_watchdog.py` | `Watchdog: Start Task Watchdog` | 중지 안 함 (Core) |
| Flow Observer | Job: FlowObserverDaemon | `start_flow_observer_daemon.ps1` | Stop-Job |
| Music Daemon | `music_daemon.py` | `Music: Start Daemon` | Stop-Process |
| Worker Monitor | Job: WorkerMonitorDaemon | `start_worker_monitor_daemon.ps1` | Stop-Job |
| Observer Telemetry | Job: ObserverTelemetry | `observe_desktop_telemetry.ps1` | Stop-Job |
| Monitoring Collector | ScheduledTask: MonitoringCollector | Scheduled Task | 중지 안 함 (주기만 조절 불가) |

## ⚙️ 구현 우선순위

1. **Stop 가능**: RPA Worker, Observer Telemetry, Worker Monitor
2. **간격 조절 가능**: Flow Observer (Job 재시작), Music Daemon (프로세스 재시작)
3. **유지**: Task Queue Server, Watchdog, Original Data API

## 🔄 Next Steps

1. `config/rhythm_modes.json` 생성 (위 매핑 기반)
2. `scripts/rhythm_mode_manager.ps1` 구현 (Start/Stop/Adjust 로직)
3. DryRun으로 안전 검증
4. Auto 모드 스케줄링 (선택적)
