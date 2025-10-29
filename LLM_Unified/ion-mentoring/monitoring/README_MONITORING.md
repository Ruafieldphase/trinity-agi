# ION & Lumen Production Monitoring

## 📊 Dashboard

**Production Monitoring Dashboard**
- URL: https://console.cloud.google.com/monitoring/dashboards/custom/f3b6074b-2d46-40f2-a35f-7b2942fc2d31?project=naeda-genesis
- 생성일: 2025-10-23
- 포함 메트릭:
  - ✅ Request Rate (요청/분)
  - ✅ Latency P50/P95/P99 (밀리초)
  - ✅ Error Rate 4xx/5xx (에러/분)
  - ✅ Container Instance Count
  - ✅ CPU Utilization (%)
  - ✅ Memory Utilization (%)

## 🔍 Monitored Services

### ION API Production
- **Service Name**: `ion-api`
- **URL**: https://ion-api-x4qvsargwa-uc.a.run.app
- **Region**: us-central1
- **Health Endpoint**: `/health`
- **Current Version**: v1.1.1

### Lumen Gateway Production
- **Service Name**: `lumen-gateway`
- **URL**: https://lumen-gateway-x4qvsargwa-uc.a.run.app
- **Region**: us-central1
- **Health Endpoint**: `/health`
- **Current Version**: v2.0.0

## 📈 Key Metrics

### Request Rate
- **ION API**: 요청/분 추적
- **Lumen Gateway**: 요청/분 추적
- **Aggregation**: 60초 정렬, SUM

### Latency
- **P50 (Median)**: 일반적인 응답 시간
- **P95**: 95% 요청의 응답 시간
- **P99**: 99% 요청의 응답 시간 (worst case)
- **Aggregation**: 60초 정렬, PERCENTILE

### Error Rate
- **4xx Errors**: 클라이언트 오류 (잘못된 요청)
- **5xx Errors**: 서버 오류 (서비스 장애)
- **Aggregation**: 60초 정렬, SUM

### Container Instances
- **Auto-scaling 상태**: 현재 실행 중인 컨테이너 수
- **ION API**: Min 1, Max 20
- **Lumen Gateway**: Min 1, Max 20

### Resource Utilization
- **CPU**: 평균 CPU 사용률 (%)
- **Memory**: 평균 메모리 사용률 (%)

## 🚨 Uptime Checks (수동 설정 필요)

GCP Console에서 다음 Uptime Check를 설정하세요:

### ION API Health Check

```
Display Name: ION API Production Health Check
Protocol: HTTPS
Resource Type: URL
Hostname: ion-api-x4qvsargwa-uc.a.run.app
Path: /health
Port: 443
Check Frequency: 1 minute
Timeout: 10 seconds
Regions: USA, Asia Pacific
```

### Lumen Gateway Health Check

```
Display Name: Lumen Gateway Production Health Check
Protocol: HTTPS
Resource Type: URL
Hostname: lumen-gateway-x4qvsargwa-uc.a.run.app
Path: /health
Port: 443
Check Frequency: 1 minute
Timeout: 10 seconds
Regions: USA, Asia Pacific
```

**설정 방법:**
1. GCP Console → Monitoring → Uptime checks
2. "CREATE UPTIME CHECK" 클릭
3. 위 설정값 입력
4. Alert policy 설정 (optional)

## 📝 Alert Policies (권장 설정)

### High Error Rate Alert

```
Condition: 5xx error rate > 5% for 5 minutes
Severity: Critical
Notification: Email, SMS
```

### High Latency Alert

```
Condition: P99 latency > 2000ms for 5 minutes
Severity: Warning
Notification: Email
```

### Service Down Alert

```
Condition: Uptime check fails for 2 consecutive checks
Severity: Critical
Notification: Email, SMS, PagerDuty
```

### Low Instance Count Alert

```
Condition: Container instances = 0 for 1 minute
Severity: Critical
Notification: Email, SMS
```

## 🔧 Dashboard 업데이트

대시보드 JSON 파일 수정 후 업데이트:

```bash
gcloud monitoring dashboards update f3b6074b-2d46-40f2-a35f-7b2942fc2d31 \
  --config-from-file=ion-mentoring/monitoring/production_monitoring_dashboard.json \
  --project=naeda-genesis
```

## 📦 파일 구조

```
ion-mentoring/monitoring/
├── production_monitoring_dashboard.json  # Main dashboard config
├── ion_api_uptime_check.json           # ION API uptime config (reference)
├── lumen_gateway_uptime_check.json     # Lumen Gateway uptime config (reference)
├── ion_dashboard_backup.json           # Original ION dashboard backup
└── README_MONITORING.md                # This file
```

## 🎯 Monitoring Best Practices

1. **정기 점검**: 매일 대시보드 확인
2. **Alert 검증**: 주간 테스트 알림 발생시켜 동작 확인
3. **Threshold 조정**: 트래픽 패턴에 따라 alert threshold 최적화
4. **로그 통합**: Cloud Logging과 연계하여 상세 분석
5. **SLO 설정**: Service Level Objectives 정의 및 추적

## 🔗 관련 링크

- [GCP Cloud Monitoring](https://console.cloud.google.com/monitoring?project=naeda-genesis)
- [Cloud Run Services](https://console.cloud.google.com/run?project=naeda-genesis)
- [Cloud Logging](https://console.cloud.google.com/logs?project=naeda-genesis)
- [Alert Policies](https://console.cloud.google.com/monitoring/alerting?project=naeda-genesis)

## 🗂️ Local Timeseries Collector (Optional)

운영 환경 외에도 로컬/온프레미스에서 가벼운 헬스 체크를 주기적으로 수집해 추세를 확인할 수 있습니다.

- 스냅샷 포맷: JSON Lines (JSONL)
- 권장 파일: `outputs/status_snapshots.jsonl`
- 수집 소스: 내부 헬스 프로브 스크립트(예: `quick_status.ps1`)에서 `-LogJsonl` 옵션으로 append

예시 흐름
1. 헬스 체크 수행 → 요약 출력 + JSONL 스냅샷 1행 append
2. 리포트 생성기(예: `generate_monitoring_report.ps1 -Hours 24`)로 지난 24시간 메트릭/이벤트 집계 및 대시보드 렌더링

Windows에서의 예약 실행 가이드(개요)
- 작업 스케줄러를 이용해 5~10분 간격으로 헬스 체크 스크립트를 실행합니다.
- 각 실행은 1회 샘플만 수집하고 빠르게 종료하도록 구성하면 리소스 사용을 최소화할 수 있습니다.
- 스냅샷 파일은 주기적으로 압축/로테이션하거나, 리포트 생성 시 기간 필터(`-Hours`)를 적용해 관리하세요.

### Snapshot Rotation (Optional)

수집 파일이 장기적으로 커지는 것을 방지하려면 주기적 로테이션을 권장합니다.

- 기준: 최대 라인 수 또는 파일 크기 기준으로 회전 (예: 50,000 lines 또는 50MB)
- 방법: 로테이션 스크립트로 아카이브 디렉터리에 이동 후 신규 빈 파일 생성, 필요 시 ZIP 압축
- 주기: 하루 1회 새벽 시간대 등 트래픽이 낮을 때 예약 실행

참고 구현(로컬 환경 예시)
- 수집: 5분 간격 헬스 체크 → JSONL 1행 append
- 로테이션: 매일 03:15에 회전(옵션으로 ZIP 압축)
