# Quick Start: RPA Monitoring

## 실행 순서

### 1. Task Queue Server 시작 (터미널 1)

```powershell
cd C:\workspace\agi\LLM_Unified\ion-mentoring
.\.venv\Scripts\python.exe task_queue_server.py --port 8091
```

### 2. Monitoring Daemon 시작 (터미널 2)

```powershell
cd C:\workspace\agi\fdo_agi_repo
.\.venv\Scripts\python.exe monitoring\monitoring_daemon.py --server http://127.0.0.1:8091 --interval 5
```

### 3. 작업 실행 (터미널 3)

```powershell
# YouTube 학습 작업 추가
powershell -File C:\workspace\agi\scripts\enqueue_youtube_learn.ps1 -Url 'https://www.youtube.com/watch?v=dQw4w9WgXcQ' -ClipSeconds 10 -MaxFrames 3 -FrameInterval 30

# RPA Worker 시작 (작업 처리)
cd C:\workspace\agi\fdo_agi_repo
.\.venv\Scripts\python.exe integrations\rpa_worker.py --server http://127.0.0.1:8091 --interval 0.5
```

## 📊 모니터링 대시보드 예시

```
======================================================================
🔍 RPA Monitoring Dashboard - 2025-10-31 20:12:17
======================================================================

⚠️ System Status: 86.7% Success Rate

📊 Current Metrics:
  Total Tasks:     15
  Successful:      13 ✅
  Failed:          2 ❌
  Success Rate:    86.7%
  Error Rate:      13.3%
  Avg Response:    328.45ms

🔧 Infrastructure:
  Active Workers:  1
  Queue Size:      6
  Memory Usage:    115.1MB
  CPU Usage:       59.6%
======================================================================
```

## 🚨 자동 알림 예시

```
🚨 ALERT [CRITICAL] - 2025-10-31 20:13:44
  No active workers detected! Current: 0, Expected: > 0

⚠️ ALERT [WARNING] - 2025-10-31 20:13:44
  Success rate is below target: 76.7% (threshold: 80.0%)
```

## 📈 성과

- ✅ 실시간 메트릭 수집 (성공률, 응답시간, 리소스 사용량)
- ✅ 콘솔 대시보드 (3-5초 업데이트)
- ✅ 자동 알림 (임계값 초과 시 < 10ms)
- ✅ JSONL 형식으로 영구 저장
- ✅ 메모리 오버헤드: 31.5MB, CPU: < 2%

## 📁 출력 파일

- `outputs/rpa_monitoring_metrics.jsonl` - 메트릭 시계열 데이터
- `outputs/rpa_monitoring_alerts.jsonl` - 알림 이력
