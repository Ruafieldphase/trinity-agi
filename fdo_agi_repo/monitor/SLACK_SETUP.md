# 📱 Slack 알림 설정 가이드

AGI 시스템의 헬스 체크 결과를 Slack으로 받을 수 있습니다.

---

## 🚀 빠른 설정 (5분)

### 1. Slack Incoming Webhook 생성

1. Slack 앱에서 **워크스페이스 설정** 열기
2. **앱 관리** → **커스텀 통합** 클릭
3. **Incoming WebHooks** 검색 후 선택
4. **Slack에 추가** 클릭
5. 알림을 받을 **채널 선택** (예: `#agi-alerts`)
6. **Incoming WebHooks 통합 추가** 클릭
7. **Webhook URL** 복사 (예: `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX`)

### 2. 환경변수 설정

#### Windows PowerShell

**임시 설정** (현재 세션만):
```powershell
$env:SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

**영구 설정** (시스템 전체):
```powershell
[Environment]::SetEnvironmentVariable(
    "SLACK_WEBHOOK_URL",
    "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    "User"
)
```

#### Linux/macOS

**임시 설정**:
```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

**영구 설정** (`.bashrc` 또는 `.zshrc`에 추가):
```bash
echo 'export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"' >> ~/.bashrc
source ~/.bashrc
```

### 3. 테스트

```powershell
cd D:\nas_backup\fdo_agi_repo\monitor
python slack_notifier.py
```

성공하면 Slack 채널에 테스트 메시지가 도착합니다! 🎉

---

## 📋 알림 종류

### 1. 헬스 체크 실패 알림

시스템이 임계값을 벗어날 때 자동 알림:

```
🚨 AGI 시스템 헬스 체크 실패

시간: 2025-10-26 12:00:00
상태: ❌ UNHEALTHY

실패한 체크 항목:
❌ Confidence: 0.550 (목표: ≥0.600)
❌ Quality: 0.600 (목표: ≥0.650)

[대시보드 열기]
```

### 2. 헬스 체크 복구 알림

시스템이 정상으로 돌아올 때:

```
✅ AGI 시스템 헬스 체크 복구

시간: 2025-10-26 12:15:00
상태: ✅ HEALTHY

Confidence: 0.684
Quality: 0.800
Second Pass Rate: 0.500
```

### 3. 일일 메트릭 요약

매일 정해진 시간에 요약 리포트:

```
📊 AGI 일일 메트릭 요약

기간: 최근 24시간
생성 시간: 2025-10-26 09:00:00

평균 Confidence: 0.684
평균 Quality: 0.750
총 작업: 125
자기교정: 42회

페르소나 성능:
• thesis: 85.0% 성공률, 26.5s 평균응답
• antithesis: 80.0% 성공률, 25.0s 평균응답
• synthesis: 75.0% 성공률, 28.0s 평균응답
```

---

## 🔧 사용 방법

### 자동 헬스 모니터링 시작

```powershell
cd D:\nas_backup\fdo_agi_repo\monitor
.\start_health_monitor.ps1
```

**옵션**:
- `-Interval 30`: 30초마다 체크 (기본: 60초)
- `-Duration 3600`: 1시간 동안만 실행 (기본: 무한)
- `-NoRecoveryNotify`: 복구 알림 비활성화

**예시**:
```powershell
# 30초마다 체크, 1시간 동안 실행
.\start_health_monitor.ps1 -Interval 30 -Duration 3600

# 복구 알림 없이 실행
.\start_health_monitor.ps1 -NoRecoveryNotify
```

### 수동 알림 테스트

```python
from metrics_collector import MetricsCollector
from slack_notifier import SlackNotifier

collector = MetricsCollector()
notifier = SlackNotifier()

# 헬스 체크 알림
health = collector.get_health_status()
notifier.send_health_alert(health)

# 일일 요약 알림
metrics = collector.get_realtime_metrics(hours=24)
notifier.send_metrics_summary(metrics)
```

---

## 🎨 커스터마이징

### 알림 채널 변경

Webhook을 생성할 때 다른 채널을 선택하거나, 여러 Webhook을 만들어 환경변수로 전환:

```powershell
# 개발용
$env:SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/.../dev"

# 프로덕션용
$env:SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/.../prod"
```

### 알림 임계값 조정

`metrics_collector.py`의 `THRESHOLDS` 수정:

```python
THRESHOLDS = {
    'min_confidence': 0.70,  # 0.60 → 0.70
    'min_quality': 0.75,     # 0.65 → 0.75
    'max_second_pass_rate': 1.5,  # 2.0 → 1.5
}
```

### 알림 메시지 커스터마이징

`slack_notifier.py`의 `send_health_alert()` 수정:

```python
blocks = [
    {
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": "🔥 긴급! AGI 시스템 이상!",  # 커스텀 메시지
            "emoji": true
        }
    },
    # ... 추가 블록
]
```

---

## 📊 모니터링 전략

### 전략 1: 실시간 모니터링 (개발 중)

```powershell
# 30초마다 체크, 복구 알림 포함
.\start_health_monitor.ps1 -Interval 30
```

**용도**: 성능 최적화 작업 중 실시간 피드백

### 전략 2: 백그라운드 모니터링 (프로덕션)

```powershell
# 5분마다 체크, 복구 알림 없이
.\start_health_monitor.ps1 -Interval 300 -NoRecoveryNotify
```

**용도**: 장기 운영 중 이상 감지

### 전략 3: 정기 리포트

Cron/Task Scheduler로 매일 요약 알림:

```python
# daily_summary.py
from metrics_collector import MetricsCollector
from slack_notifier import SlackNotifier

collector = MetricsCollector()
notifier = SlackNotifier()

metrics = collector.get_realtime_metrics(hours=24)
notifier.send_metrics_summary(metrics)
```

**Windows Task Scheduler**:
- 트리거: 매일 09:00
- 동작: `python daily_summary.py`

---

## 🐛 트러블슈팅

### 알림이 전송되지 않음

**확인 사항**:
1. `SLACK_WEBHOOK_URL` 환경변수가 올바르게 설정되었는지 확인
   ```powershell
   echo $env:SLACK_WEBHOOK_URL
   ```

2. Webhook URL이 유효한지 테스트
   ```powershell
   python slack_notifier.py
   ```

3. 방화벽/프록시 설정 확인

### 중복 알림 발생

**원인**: 여러 모니터 인스턴스가 동시 실행 중

**해결**: 실행 중인 프로세스 확인
```powershell
Get-Process python | Where-Object {$_.CommandLine -like "*health_monitor*"}
```

### 알림이 너무 많음

**해결 1**: 체크 간격 늘리기
```powershell
.\start_health_monitor.ps1 -Interval 300  # 5분
```

**해결 2**: 복구 알림 비활성화
```powershell
.\start_health_monitor.ps1 -NoRecoveryNotify
```

---

## 📱 Slack 앱 권장 설정

### 알림 채널 생성

```
채널명: #agi-alerts
설명: AGI 시스템 헬스 체크 알림
멤버: @깃코, @세나, @루빛
```

### 알림 소리 설정

1. 채널 설정 열기
2. **알림** → **알림 소리** 설정
3. **모든 메시지에 대해 알림** 또는 **키워드 알림** 선택

### 모바일 푸시 알림

1. Slack 모바일 앱 설치
2. **설정** → **알림** → **채널별 알림**
3. `#agi-alerts` 채널에 대해 **모든 메시지 알림** 활성화

---

## 🎯 다음 단계

- [ ] Webhook URL 생성 및 환경변수 설정
- [ ] 테스트 알림 전송 확인
- [ ] 헬스 모니터 백그라운드 실행
- [ ] 대시보드와 함께 사용하여 시각화 + 알림 통합

---

**작성자**: 세나 (Sena)
**작성일**: 2025-10-26
**버전**: 1.0
