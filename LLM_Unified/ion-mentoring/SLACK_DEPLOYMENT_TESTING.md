# Slack 배포 알림 통합 테스트 가이드

**작성일:** 2025-01-24  
**목적:** Slack 알림 시스템의 실제 배포 시나리오 테스트

---

## 📋 목차

1. [사전 준비](#사전-준비)
2. [환경 설정](#환경-설정)
3. [단위 테스트](#단위-테스트)
4. [통합 테스트](#통합-테스트)
5. [프로덕션 테스트](#프로덕션-테스트)
6. [문제 해결](#문제-해결)

---

## 사전 준비

### 필수 요구사항

- ✅ Slack Workspace 접근 권한
- ✅ Slack App 생성 및 Bot Token 발급
- ✅ GCP 프로젝트 접근 권한 (배포 테스트용)
- ✅ PowerShell 5.1 이상
- ✅ Python 가상 환경 (.venv)

### Slack Bot 권한 확인

Slack App 설정에서 다음 권한이 있는지 확인:

- `chat:write` - 메시지 전송
- `chat:write.public` - 공개 채널에 메시지 전송

### 테스트 채널 생성

```
1. Slack에서 새 채널 생성: #test-deployments
2. Bot 초대: /invite @Gitco
3. 채널 ID 확인 (선택)
```

---

## 환경 설정

### 1단계: 환경 변수 설정

**자동 설정 (권장):**

```powershell
cd D:\nas_backup\LLM_Unified\ion-mentoring
.\scripts\setup_slack_env.ps1
```

대화형으로 다음 정보 입력:
- Slack Bot Token (xoxb-로 시작)
- Alert Channel (예: #test-deployments)

**수동 설정:**

```powershell
# Bot Token
[Environment]::SetEnvironmentVariable("SLACK_BOT_TOKEN", "xoxb-your-token-here", "User")

# Alert Channel
[Environment]::SetEnvironmentVariable("SLACK_ALERT_CHANNEL", "#test-deployments", "User")
```

### 2단계: 환경 변수 확인

```powershell
# 설정 검증
.\scripts\setup_slack_env.ps1 -Verify

# 또는 직접 확인
$env:SLACK_BOT_TOKEN
$env:SLACK_ALERT_CHANNEL
```

**예상 출력:**

```
✅ SLACK_BOT_TOKEN: xoxb-12345...
✅ SLACK_ALERT_CHANNEL: #test-deployments
```

### 3단계: PowerShell 재시작

환경 변수가 적용되도록 **새 PowerShell 창을 열거나** VS Code 터미널을 재시작하세요.

---

## 단위 테스트

### 테스트 1: Slack 알림 모듈 테스트

**목적:** SlackNotifications.ps1의 모든 함수가 정상 작동하는지 확인

```powershell
cd D:\nas_backup\LLM_Unified\ion-mentoring
.\scripts\test_slack_notifications.ps1
```

**예상 결과:**

```
╔════════════════════════════════════════════════════════════╗
║     Slack 알림 시스템 테스트                               ║
╚════════════════════════════════════════════════════════════╝

🔍 환경 변수 확인 중...
  ✅ Bot Token: xoxb-12345...
  ✅ 대상 채널: #test-deployments

🚀 테스트 시작: 2025-01-24 14:30:00

═══ 배포 알림 테스트 ═══

[1] 테스트: 배포 시작 알림 (5%)
  ✅ 성공

[2] 테스트: 배포 진행 알림 (deploying)
  ✅ 성공

... (총 15개 테스트)

╔════════════════════════════════════════════════════════════╗
║     테스트 결과 요약                                       ║
╚════════════════════════════════════════════════════════════╝

총 테스트: 15
성공: 15
소요 시간: 32.5초

✅ 모든 테스트가 성공했습니다!
```

**Slack에서 확인:**
- #test-deployments 채널에 15개 테스트 메시지 표시
- 각 메시지가 올바른 형식으로 렌더링되는지 확인
- Block Kit UI가 제대로 표시되는지 확인

### 테스트 2: 특정 알림 타입만 테스트

```powershell
# 배포 알림만
.\scripts\test_slack_notifications.ps1 -TestType deployment

# 대시보드만
.\scripts\test_slack_notifications.ps1 -TestType dashboard

# 모니터링 알림만
.\scripts\test_slack_notifications.ps1 -TestType monitoring
```

### 테스트 3: 다른 채널로 테스트

```powershell
.\scripts\test_slack_notifications.ps1 -Channel "#other-channel"
```

---

## 통합 테스트

### 시나리오 1: Dry-Run 배포 (실제 배포 없음)

**목적:** 배포 스크립트가 Slack 알림과 올바르게 통합되는지 확인 (실제 GCP 배포 제외)

```powershell
cd D:\nas_backup\LLM_Unified\ion-mentoring

# Dry-Run 배포 (Slack 알림 활성화)
.\scripts\deploy_phase4_canary.ps1 `
    -ProjectId "naeda-genesis" `
    -CanaryPercentage 50 `
    -DryRun `
    -EnableSlackNotifications
```

**예상 동작:**

1. **터미널 출력:**

   ```
   [14:30:00] 🚀 Phase 4 Canary Deployment Started
   [14:30:05] ✅ Slack 알림 전송: 배포 시작
   [14:30:10] [DRY RUN] Would create Artifact Repository...
   [14:31:00] ✅ Slack 대시보드 업데이트: deploying
   [14:32:00] ✅ Slack 대시보드 업데이트: validating
   [14:33:00] ✅ Slack 대시보드 업데이트: monitoring
   [14:33:30] ✅ Slack 알림 전송: 배포 완료
   ```

2. **Slack 채널:**
   - 배포 시작 알림 (5% or 50% 등)
   - 대시보드 업데이트 3회 (deploying → validating → monitoring)
   - 배포 완료 알림

**검증 포인트:**
- ✅ 각 알림이 올바른 순서로 전송되는가?
- ✅ 대시보드가 3단계로 업데이트되는가?
- ✅ Dry-Run임에도 알림이 정상 작동하는가?

### 시나리오 2: 의도적 실패 시나리오

**목적:** 배포 실패 시 Slack 알림이 올바르게 작동하는지 확인

```powershell
# 잘못된 Project ID로 배포 시도
.\scripts\deploy_phase4_canary.ps1 `
    -ProjectId "invalid-project-id" `
    -CanaryPercentage 50 `
    -EnableSlackNotifications
```

**예상 동작:**

1. **터미널:** 에러 메시지 + Slack 실패 알림 전송
2. **Slack:** 
   - 배포 시작 알림
   - 배포 실패 알림 (❌, 에러 메시지 포함)
   - 실패 대시보드 (failed 상태)

**검증 포인트:**
- ✅ 실패 알림에 에러 메시지가 포함되는가?
- ✅ 대시보드가 `failed` 상태로 표시되는가?
- ✅ 배포는 중단되었지만 알림은 전송되었는가?

---

## 프로덕션 테스트

### 시나리오 3: 실제 5% 카나리 배포

**⚠️ 주의:** 실제 GCP에 배포됩니다. 프로덕션 환경에서 테스트하기 전에 스테이징 환경에서 먼저 테스트하세요.

**사전 확인:**
- [ ] GCP 프로젝트 ID 확인
- [ ] 현재 배포 상태 확인 (`gcloud run services list`)
- [ ] 백업 계획 준비 (롤백 스크립트)

**실행:**

```powershell
cd D:\nas_backup\LLM_Unified\ion-mentoring

# 5% 카나리 배포 (Slack 알림 활성화)
.\scripts\deploy_phase4_canary.ps1 `
    -ProjectId "naeda-genesis" `
    -CanaryPercentage 5 `
    -EnableSlackNotifications
```

**예상 소요 시간:** 5-10분

**모니터링:**

1. **터미널 출력:**
   - 각 단계별 로그
   - Slack 알림 전송 확인 메시지

2. **Slack 채널:**
   - 실시간 진행 상황 업데이트
   - 메트릭 표시 (응답 시간, 상태 코드)
   - 완료 알림 (배포 시간, Gateway URL)

3. **GCP Console:**
   - Cloud Run 서비스 상태 확인
   - 트래픽 분할 확인 (Legacy 95% / Canary 5%)

**검증 포인트:**
- ✅ 배포가 성공적으로 완료되었는가?
- ✅ Slack에서 전체 배포 과정을 추적할 수 있었는가?
- ✅ 실시간 메트릭이 표시되었는가?
- ✅ 완료 알림에 배포 시간과 URL이 포함되었는가?

### 시나리오 4: 자동 카나리 진행 (5% → 100%)

**목적:** 자동 진행 시스템과 Slack 알림의 완전한 통합 테스트

**⚠️ 주의:** 
- 전체 진행에 4-5시간 소요
- 각 단계마다 1시간 모니터링 대기
- 백그라운드에서 실행 권장

**실행:**

```powershell
# 자동 카나리 진행 (Slack 알림 기본 활성화)
.\scripts\auto_canary_runner.ps1 -ProjectId "naeda-genesis"

# 또는 Slack 알림 명시적 활성화
.\scripts\auto_canary_runner.ps1 `
    -ProjectId "naeda-genesis" `
    -EnableSlackNotifications
```

**진행 단계:**
1. 0% → 5% (배포 + 60분 모니터링)
2. 5% → 10% (배포 + 60분 모니터링)
3. 10% → 25% (배포 + 60분 모니터링)
4. 25% → 50% (배포 + 60분 모니터링)
5. 50% → 100% (배포 완료)

**Slack에서 확인할 내용:**

각 단계마다:
- 🚀 배포 시작 알림
- 🔄 배포 진행 대시보드
- ✅ 배포 완료 알림
- ⏱️ 모니터링 시작 알림
- ... (60분 대기)
- ➡️ 다음 단계 진행 알림

**검증 포인트:**
- ✅ 모든 단계에서 알림이 전송되는가?
- ✅ 대시보드가 각 단계마다 업데이트되는가?
- ✅ 모니터링 타이머가 정확한가?
- ✅ 에러 발생 시 즉시 알림받는가?

---

## 문제 해결

### 문제 1: "SLACK_BOT_TOKEN이 설정되지 않았습니다"

**원인:** 환경 변수가 설정되지 않았거나 새 세션에서 로드되지 않음

**해결:**

```powershell
# 1. 환경 변수 재설정
.\scripts\setup_slack_env.ps1

# 2. PowerShell 재시작

# 3. 확인
$env:SLACK_BOT_TOKEN
```

### 문제 2: "Slack 알림 전송 실패"

**원인 1:** Bot Token이 유효하지 않음

```powershell
# Token 재확인
.\scripts\setup_slack_env.ps1 -Verify

# Token 재발급 (Slack App 페이지)
```

**원인 2:** Bot이 채널에 초대되지 않음

```
Slack 채널에서: /invite @Gitco
```

**원인 3:** Bot 권한 부족

1. Slack App 페이지 접속
2. OAuth & Permissions
3. Scopes 확인: `chat:write`, `chat:write.public`
4. 권한 추가 후 재설치

### 문제 3: "대시보드가 표시되지 않음"

**원인:** `send_deployment_dashboard.ps1` 경로 문제

```powershell
# 스크립트 존재 확인
Test-Path "D:\nas_backup\LLM_Unified\ion-mentoring\scripts\send_deployment_dashboard.ps1"

# 수동 실행 테스트
.\scripts\send_deployment_dashboard.ps1 `
    -Phase 50 `
    -Status monitoring
```

### 문제 4: "배포는 성공했지만 알림이 안 옴"

**원인:** `-EnableSlackNotifications` 플래그 누락

**해결:**

```powershell
# 올바른 명령
.\scripts\deploy_phase4_canary.ps1 `
    -ProjectId "naeda-genesis" `
    -CanaryPercentage 50 `
    -EnableSlackNotifications  # 이거 필수!
```

**확인:**

```powershell
# 스크립트 실행 로그에서 확인
# 다음 메시지가 보여야 함:
# "✅ Slack 알림 전송: ..."
```

### 문제 5: "Block Kit 메시지가 깨져서 보임"

**원인:** 특수 문자 이스케이핑 문제

**해결:**

```powershell
# SlackNotifications.ps1 최신 버전 확인
git pull origin master

# 또는 수동 확인
notepad "D:\nas_backup\LLM_Unified\ion-mentoring\scripts\SlackNotifications.ps1"
```

---

## 테스트 체크리스트

### 준비 단계
- [ ] Slack Workspace 접근 권한 확보
- [ ] Slack Bot Token 발급
- [ ] 테스트 채널 생성 (#test-deployments)
- [ ] Bot을 채널에 초대
- [ ] 환경 변수 설정 완료
- [ ] 환경 변수 검증 완료

### 단위 테스트
- [ ] `test_slack_notifications.ps1` 실행 성공
- [ ] 모든 알림 타입 테스트 통과
- [ ] Slack 채널에서 메시지 확인

### 통합 테스트
- [ ] Dry-Run 배포 테스트 (알림 확인)
- [ ] 의도적 실패 시나리오 테스트
- [ ] 대시보드 업데이트 흐름 확인

### 프로덕션 테스트
- [ ] 5% 카나리 배포 성공
- [ ] 실시간 메트릭 표시 확인
- [ ] 자동 카나리 진행 테스트 (선택)

### 문제 해결
- [ ] 모든 알려진 문제에 대한 해결책 확인
- [ ] 로그 확인 방법 숙지

---

## 다음 단계

테스트가 모두 완료되면:

1. **프로덕션 채널 설정**

   ```powershell
   [Environment]::SetEnvironmentVariable("SLACK_ALERT_CHANNEL", "#deployments", "User")
   ```

2. **자동화 활성화**
   - `auto_canary_runner.ps1`은 기본적으로 Slack 알림 활성화
   - 배포 스케줄러와 통합 (선택)

3. **팀 교육**
   - Slack에서 배포 상태 확인 방법
   - 에러 알림 대응 절차
   - 롤백 트리거 조건

4. **모니터링 개선**
   - 실시간 메트릭 대시보드 구축
   - 알람 임계값 설정
   - 자동 롤백 정책 수립

---

## 참고 자료

- **슬랙 알림 완료 보고서:** `깃코_Slack_배포알림_완료보고서_2025-01-24.md`
- **빠른 시작 가이드:** `QUICKSTART.md`
- **자동화 가이드:** `AUTOMATION_GUIDE.md`
- **Slack Block Kit Builder:** https://app.slack.com/block-kit-builder

---

**문서 끝**
