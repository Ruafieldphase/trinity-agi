# 📊 Daily Operations Report System

ION Platform의 일일/주간 운영 리포트를 자동으로 생성하는 시스템입니다.

## 🎯 목적

- **자동화된 메트릭 수집**: 지난 24시간의 운영 데이터를 자동으로 수집
- **트렌드 분석**: 서비스 상태, 에러율, 리소스 사용률 등을 분석
- **이상 징후 탐지**: 임계값 기반 Alert 생성
- **리포트 생성**: 마크다운 + JSON 형식으로 리포트 출력
- **이메일 전송**: (예정) 매일 아침 자동으로 운영 팀에게 전송

## 📁 파일 구성

```
monitoring/
├── daily_operations_report.py    # 메인 스크립트
├── README_DAILY_REPORTS.md        # 이 문서
├── test_daily_report.md           # 샘플 마크다운 리포트
└── test_daily_report.json         # 샘플 JSON 리포트
```

## 🚀 사용법

### 기본 실행

```bash
python daily_operations_report.py --project naeda-genesis --output daily_report.md
```

### 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--project` | GCP Project ID | 필수 |
| `--output` | 출력 마크다운 파일 | `daily_report.md` |
| `--hours` | 분석 시간 범위 (시간) | `24` |
| `--json` | JSON 출력 파일 (선택) | 없음 |
| `--send-email` | 이메일 전송 여부 (예정) | `False` |

### 예제

**24시간 리포트 생성**:

```bash
python daily_operations_report.py \
  --project naeda-genesis \
  --output daily_report.md \
  --json daily_report.json
```

**주간 리포트 생성 (168시간)**:

```bash
python daily_operations_report.py \
  --project naeda-genesis \
  --output weekly_report.md \
  --hours 168 \
  --json weekly_report.json
```

## 📊 수집 메트릭

### Request Metrics
- **Total Requests**: 총 요청 수
- **Requests/Second**: 평균 RPS

### Latency Metrics
- **P50**: 중앙값 지연시간 (추정)
- **P95**: 95 백분위 지연시간 (추정)
- **P99**: 99 백분위 지연시간

### Error Metrics
- **4xx Errors**: 클라이언트 에러 수 및 비율
- **5xx Errors**: 서버 에러 수 및 비율

### Resource Metrics
- **Avg Instances**: 평균 인스턴스 수
- **Max Instances**: 최대 인스턴스 수
- **Avg CPU**: 평균 CPU 사용률 (TODO)
- **Avg Memory**: 평균 메모리 사용률 (TODO)

## ⚠️ Alert 임계값

### Critical Alerts
- **5xx Error Rate > 5%**: 서버 에러가 5% 이상
- **P99 Latency > 2000ms**: 99 백분위 지연시간이 2초 이상

### Warning Alerts
- **5xx Error Rate > 1%**: 서버 에러가 1% 이상
- **4xx Error Rate > 10%**: 클라이언트 에러가 10% 이상
- **P99 Latency > 1000ms**: 99 백분위 지연시간이 1초 이상
- **CPU Utilization > 80%**: CPU 사용률이 80% 이상

## 📧 이메일 전송 (예정)

이메일 전송 기능은 다음 단계에서 구현 예정입니다:

### 계획
1. **SendGrid API 통합**: SendGrid Python SDK 사용
2. **HTML 템플릿**: 마크다운을 HTML로 변환하여 보기 좋게 전송
3. **수신자 그룹**: 운영 팀 이메일 리스트
4. **첨부 파일**: JSON 리포트 첨부

### 설정 (미래)

```python
# 환경변수 설정
SENDGRID_API_KEY=your_api_key
REPORT_EMAIL_TO=team@example.com
REPORT_EMAIL_FROM=noreply@example.com
```

## 🤖 Cloud Scheduler 자동화

매일 아침 8시에 자동으로 리포트를 생성하고 이메일로 전송:

### Cloud Scheduler Job 생성

```bash
gcloud scheduler jobs create http daily-report \
  --schedule="0 8 * * *" \
  --uri="https://your-cloud-function-url" \
  --http-method=POST \
  --time-zone="Asia/Seoul" \
  --location=us-central1
```

### Cloud Functions 배포 (예정)

```python
# main.py
import functions_framework
from daily_operations_report import main

@functions_framework.http
def generate_daily_report(request):
    # Run report generation
    main()
    return {"status": "success"}, 200
```

## 📝 리포트 샘플

### 마크다운 출력

```markdown
# 📊 ION Platform Daily Operations Report

**Report Date**: 2025-10-23
**Period**: 2025-10-22 08:00:00 UTC ~ 2025-10-23 08:00:00 UTC

## 📈 Executive Summary

- **Overall Status**: 🟡 Warning
- **Total Requests**: 77,970
- **Total Errors**: 14,571
- **ION API Status**: 🟡 Warning
- **Lumen Gateway Status**: 🟢 Healthy

...
```

### JSON 출력

```json
{
  "date": "2025-10-23",
  "period_start": "2025-10-22 08:00:00 UTC",
  "period_end": "2025-10-23 08:00:00 UTC",
  "ion_api": {
    "service_name": "ion-api",
    "total_requests": 77963,
    "requests_per_second": 1.68,
    "latency_p50": null,
    "latency_p95": null,
    "latency_p99": null,
    "error_4xx_count": 14564,
    "error_5xx_count": 7,
    "error_4xx_rate": 18.68,
    "error_5xx_rate": 0.01,
    "avg_instances": 0.83,
    "max_instances": 2,
    "avg_cpu_utilization": 0.0,
    "avg_memory_utilization": 0.0,
    "status": "warning",
    "alerts": ["⚠️ High 4xx error rate: 18.68%"]
  },
  ...
}
```

## 🛠️ 개발 로드맵

### Phase 1: 기본 리포트 생성 ✅
- [x] GCP Monitoring API 연동
- [x] 메트릭 수집 (Request, Error, Latency, Resource)
- [x] Alert 로직 구현
- [x] 마크다운 리포트 생성
- [x] JSON 출력 지원

### Phase 2: 이메일 전송 (진행 예정)
- [ ] SendGrid API 통합
- [ ] HTML 템플릿 작성
- [ ] 이메일 전송 로직
- [ ] 첨부 파일 지원

### Phase 3: 자동화 (예정)
- [ ] Cloud Functions 배포
- [ ] Cloud Scheduler 설정
- [ ] Error handling & Retry
- [ ] Monitoring & Alerting

### Phase 4: 고도화 (예정)
- [ ] CPU/Memory utilization 정확한 수집
- [ ] 트렌드 차트 생성 (이미지)
- [ ] 주간/월간 리포트 지원
- [ ] Slack 통합

## 📌 Known Issues

### CPU/Memory Metrics
현재 CPU/Memory utilization은 `0.0%`로 표시됩니다.

**원인**: Cloud Run metrics의 CPU/Memory는 DISTRIBUTION 타입으로 ALIGN_MEAN aligner를 사용할 수 없음.

**해결 방법**: Distribution 값을 직접 파싱하여 평균 계산 (추후 구현).

### Latency Percentiles
P50, P95는 "No data"로 표시되거나 추정값입니다.

**원인**: API에서 P99만 지원하며, P50/P95는 별도 계산 필요.

**현재 로직**: P99 *0.5 (P50), P99* 0.85 (P95)로 추정.

### Low Traffic Environment
지난 24시간 동안 실제 사용자 트래픽이 거의 없는 경우 일부 메트릭이 "No data"로 표시됩니다.

**정상 동작**: Production 환경에서 실제 트래픽이 발생하면 데이터가 수집됩니다.

## 📞 문의

리포트 시스템 관련 문의사항은 다음을 참고하세요:

- **GitHub Issues**: 버그 리포트 및 기능 요청
- **Documentation**: `README_MONITORING.md` 참고
- **Alert Policies**: `Task_1.2_Alert_Policies_완료보고서.md` 참고

---

**Last Updated**: 2025-10-23  
**Version**: 1.0.0  
**Author**: ION Platform DevOps Team
