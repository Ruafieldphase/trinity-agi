# Lumen Gateway v1.0 - 모니터링 스택 배포 완료

**배포 일시**: 2025-10-24  
**배포자**: 깃코  
**상태**: ✅ 운영 중  

---

## 📊 배포된 구성요소

### 1. Gateway Core
- ✅ **Metrics Collector** (PID: 10592)
  - 수집 간격: 20초
  - CSV 저장: `gateway/logs/metrics.csv`
  - 누적 레코드: 146개 (49.1분)
  
- ✅ **Health Exporter** (PID: 25968)
  - 포트: 9108
  - 엔드포인트: http://localhost:9108/metrics
  - 메트릭 수: 9개 (lumen_* 접두사)

### 2. Prometheus
- ✅ **버전**: 2.48.0
- ✅ **포트**: 9090
- ✅ **프로세스 ID**: 40808
- ✅ **설치 경로**: C:\prometheus\prometheus
- ✅ **설정 파일**: prometheus.yml
- ✅ **Alert Rules**: 11개 규칙 로드됨
- ✅ **데이터 수집**: 모든 타겟 UP 상태
- ✅ **UI**: http://localhost:9090

### 3. Alertmanager
- ✅ **버전**: 0.27.0
- ✅ **포트**: 9093
- ✅ **프로세스 ID**: 52492
- ✅ **설치 경로**: C:\prometheus\alertmanager
- ✅ **설정 파일**: alertmanager.yml
- ✅ **UI**: http://localhost:9093

### 4. 관리 스크립트
- ✅ `setup_monitoring_stack.ps1` - 전체 스택 자동 설치
- ✅ `start_gateway.ps1` - Gateway 시작/재시작
- ✅ `analyze_metrics.py` - 메트릭 분석 및 리포트 생성
- ✅ `register_gateway_task.ps1` - Windows 작업 스케줄러 등록
- ✅ `status_gateway_task.ps1` - 작업 상태 확인

---

## 🎯 현재 메트릭 (베이스라인)

### ION API 성능

```
Total Records:    146
ION API Uptime:   100.0%
Real AI Mode:     100.0% (Mock: 0%)
Duration:         49.1 minutes
```

### 응답 시간 통계

```
Mean:    243.22 ms
Median:  239.94 ms
P95:     275.49 ms
P99:     291.62 ms
Min:     212.74 ms
Max:     295.70 ms
```

### 공명 메트릭 (Resonance Metrics)

```
Phase Diff:      0.40 ± 0.28 (0.00 - 0.83)
Entropy Rate:    0.24 ± 0.03 (0.20 - 0.32)
Creative Band:   0.42 ± 0.09 (0.24 - 0.58)
Risk Band:       0.12 ± 0.05 (0.02 - 0.26)
```

### 페르소나 분포

```
Nana: 146회 (100.0%)
```

---

## 🚀 자동 시작 설정

### Option 1: PowerShell 스크립트

```powershell
# 전체 모니터링 스택 시작
& "C:\prometheus\start_monitoring_stack.ps1"

# 또는 개별 시작
& "C:\prometheus\start_prometheus.ps1"
& "C:\prometheus\start_alertmanager.ps1"
cd D:\nas_backup\LLM_Unified\ion-mentoring\gateway\scripts
.\start_gateway.ps1
```

### Option 2: Windows 작업 스케줄러 (관리자 권한 필요)

```powershell
# PowerShell을 관리자 권한으로 실행
cd D:\nas_backup\LLM_Unified\ion-mentoring\gateway\scripts
.\register_gateway_task.ps1 -Trigger Startup -Force

# 상태 확인
.\status_gateway_task.ps1

# 작업 제거
.\unregister_gateway_task.ps1 -Force
```

---

## 📈 Prometheus 쿼리 예제

### 기본 상태 확인

```promql
# ION API 헬스
lumen_ion_health

# 응답 시간 (ms)
lumen_ion_response_time_ms

# Mock 모드 확인
lumen_ion_mock_mode

# Gateway 상태
lumen_gateway_status
```

### 성능 모니터링

```promql
# 평균 응답 시간 (5분)
avg_over_time(lumen_ion_response_time_ms[5m])

# 최대 응답 시간 (1시간)
max_over_time(lumen_ion_response_time_ms[1h])

# 응답 시간 변화율
rate(lumen_ion_response_time_ms[5m])
```

### 공명 메트릭 분석

```promql
# Phase Diff 평균
avg_over_time(lumen_phase_diff[10m])

# 엔트로피 변동
stddev_over_time(lumen_entropy_rate[1h])

# 창의성 대역 추세
deriv(lumen_creative_band[5m])
```

---

## 🔔 Alert Rules (11개)

### Critical (즉시 조치 필요)
1. **IONAPIDown** - ION API 다운 (2분 지속 시)
2. **IONMockModeEnabled** - Mock 모드 활성화 (1분 지속 시)
3. **GatewayDown** - Gateway 다운 (1분 지속 시)

### Warning (조만간 조치 필요)
4. **IONHighResponseTime** - 응답 시간 500ms 초과 (5분 지속 시)
5. **IONHighP95ResponseTime** - P95 응답 시간 1000ms 초과 (5분 지속 시)
6. **IONUnstableResponseTime** - 응답 시간 표준편차 100ms 초과 (10분 지속 시)
7. **IONHighConfidenceVariance** - Confidence 변동 0.3 초과 (10분 지속 시)
8. **LowResonancePhase** - Phase Diff 0.1 미만 (10분 지속 시)
9. **HighResonancePhase** - Phase Diff 0.9 초과 (10분 지속 시)
10. **LowEntropyRate** - 엔트로피 0.15 미만 (15분 지속 시)
11. **HighEntropyRate** - 엔트로피 0.35 초과 (15분 지속 시)

---

## 📊 Grafana Dashboard (선택사항)

### 설치 방법
1. Grafana 설치 (Windows 또는 Docker)
2. Prometheus 데이터 소스 추가 (http://localhost:9090)
3. Dashboard JSON 임포트

   ```
   D:\nas_backup\LLM_Unified\ion-mentoring\gateway\grafana_dashboard.json
   ```

### Dashboard 구성 (9개 패널)
- ION API Status
- Response Time (시계열)
- Response Time Statistics
- Mock Mode Indicator
- Resonance Metrics (4개)
- Persona Distribution
- Gateway Status

---

## 🔍 메트릭 분석 도구

### HTML 리포트 생성

```powershell
cd D:\nas_backup\LLM_Unified\ion-mentoring\gateway
python scripts\analyze_metrics.py --input logs\metrics.csv --output logs\report.html
```

### JSON 데이터 추출

```powershell
python scripts\analyze_metrics.py --input logs\metrics.csv --output logs\data.json --format json
```

### 리포트 내용
- **Summary**: 전체 레코드 수, 시간 범위, 지속 시간
- **Statistics**: 6개 수치 필드의 통계 (min, max, mean, median, stdev, percentiles)
- **Anomalies**: Z-score 기반 이상 탐지 (threshold=2.0)
- **Health**: Uptime%, Mock Mode%, 다운타임 레코드
- **Personas**: 페르소나 분포 (개수 및 비율)

---

## 🛠️ 유지보수

### 로그 위치

```
Gateway 로그:    D:\nas_backup\LLM_Unified\ion-mentoring\gateway\logs\gateway_sync.log
메트릭 CSV:      D:\nas_backup\LLM_Unified\ion-mentoring\gateway\logs\metrics.csv
Prometheus 데이터: C:\prometheus\prometheus\data
Alertmanager 데이터: C:\prometheus\alertmanager\data
```

### 로그 확인

```powershell
# Gateway 로그 실시간 모니터링
Get-Content D:\nas_backup\LLM_Unified\ion-mentoring\gateway\logs\gateway_sync.log -Wait

# 최근 에러 확인
Get-Content D:\nas_backup\LLM_Unified\ion-mentoring\gateway\logs\gateway_sync.log | Select-String "ERROR"

# 메트릭 통계
Get-Content D:\nas_backup\LLM_Unified\ion-mentoring\gateway\logs\metrics.csv | Measure-Object -Line
```

### 프로세스 상태 확인

```powershell
# 포트 리스닝 확인
Get-NetTCPConnection -LocalPort 9090,9093,9108 | Select-Object LocalPort, State

# 프로세스 확인
Get-Process | Where-Object { $_.ProcessName -like "*prometheus*" -or $_.ProcessName -like "*alertmanager*" -or $_.ProcessName -like "*python*" }
```

### 재시작

```powershell
# Gateway만 재시작
cd D:\nas_backup\LLM_Unified\ion-mentoring\gateway\scripts
.\start_gateway.ps1 -KillExisting

# 전체 스택 재시작
Get-Process prometheus, alertmanager -ErrorAction SilentlyContinue | Stop-Process -Force
& "C:\prometheus\start_monitoring_stack.ps1"
```

---

## 📝 Git 커밋 이력

```
73c916d (HEAD -> master, origin/master) feat: Add complete monitoring stack setup script
3f3f016 feat: Add Task Scheduler and Metrics Analysis tools
108ba33 feat: Add comprehensive Alertmanager integration
efb97e4 feat: Add Gateway enhancements - Grafana dashboard and auto-start script
8230900 feat: Add Lumen Gateway v1.0 - ION API monitoring and Prometheus metrics
```

---

## ✅ 검증 체크리스트

- [x] Gateway Collector 실행 중 (PID: 10592)
- [x] Gateway Exporter 실행 중 (PID: 25968, Port: 9108)
- [x] Prometheus 실행 중 (PID: 40808, Port: 9090)
- [x] Alertmanager 실행 중 (PID: 52492, Port: 9093)
- [x] 메트릭 수집 정상 (146 레코드, 49.1분)
- [x] Prometheus Targets 모두 UP
- [x] Alert Rules 로드됨 (11개)
- [x] 메트릭 분석 도구 작동 (HTML/JSON 리포트)
- [x] Git 커밋 완료 (5개 커밋, 모두 푸시됨)
- [x] 문서화 완료

---

## 🎯 다음 단계 (선택사항)

### 1. Slack 알림 설정

```powershell
# 환경 변수 설정
[Environment]::SetEnvironmentVariable("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/YOUR/WEBHOOK/URL", "User")

# Alertmanager 재시작
Get-Process alertmanager -ErrorAction SilentlyContinue | Stop-Process -Force
& "C:\prometheus\start_alertmanager.ps1"
```

### 2. Grafana 설치 및 Dashboard 임포트
- Grafana 다운로드 및 설치
- Prometheus 데이터 소스 추가
- `grafana_dashboard.json` 임포트

### 3. Windows Service 등록 (영구 운영)
- Task Scheduler 대신 Windows Service로 등록
- 자동 재시작 및 로그 로테이션 설정

### 4. 장기 모니터링
- 일일 메트릭 리포트 자동 생성
- 주간 성능 트렌드 분석
- Alert 규칙 튜닝

---

## 📞 문제 해결

### Gateway가 시작되지 않음

```powershell
# 로그 확인
Get-Content D:\nas_backup\LLM_Unified\ion-mentoring\gateway\logs\gateway_sync.log -Tail 50

# 포트 충돌 확인
Get-NetTCPConnection -LocalPort 9108 -ErrorAction SilentlyContinue

# 강제 재시작
.\start_gateway.ps1 -KillExisting
```

### Prometheus가 메트릭을 수집하지 않음

```powershell
# Targets 상태 확인
Invoke-RestMethod -Uri "http://localhost:9090/api/v1/targets"

# 설정 파일 검증
Get-Content C:\prometheus\prometheus\prometheus.yml

# Prometheus 재시작
Get-Process prometheus | Stop-Process -Force
& "C:\prometheus\start_prometheus.ps1"
```

### Alertmanager가 알림을 보내지 않음

```powershell
# 환경 변수 확인
$env:SLACK_WEBHOOK_URL

# Alertmanager 로그 확인
cd C:\prometheus\alertmanager
Get-Content data\nlog -Tail 100

# 설정 파일 확인
Get-Content alertmanager.yml
```

---

**배포 완료**: 2025-10-24 20:35 KST  
**모니터링 스택 상태**: 🟢 정상 운영 중  
**다음 점검 예정**: 2025-10-25
