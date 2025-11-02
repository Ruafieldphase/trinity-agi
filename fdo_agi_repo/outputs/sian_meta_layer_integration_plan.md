# Sian (Gemini CLI) 메타층 통합 계획

**날짜**: 2025-11-02 15:18  
**목적**: AI 페르소나(Sian)에게 메타층 관리 역할을 위임

## 현재 상태

### ✅ 작동 중인 시스템

1. **Autonomous Work Worker** (메타층)
   - OS 프로세스로 독립 실행
   - 5분마다 작업 확인 및 실행
   - 건강 체크 + 자동 복구 내장

2. **AutonomousWorkPlanner**
   - 작업 큐 관리
   - 우선순위 결정
   - 실행 기록 추적

3. **시안 (Copilot + Orchestrator)**
   - GitHub Copilot Chat
   - VS Code 통합 오케스트레이션
   - 사용자 대화 기반 작업 조정

### 🤔 현재 한계

- **시안의 범위**: VS Code 내부로 제한
- **메타층 접근**: 제한적 (터미널 명령만)
- **자율성**: 사용자 명령 대기 필요
- **지속성**: VS Code 세션 의존

## 메타층 페르소나 위임 아키텍처

### 개념: 다층 AI 거버넌스

```
┌─────────────────────────────────────────────┐
│  사용자 (Human)                              │
│  - 전략적 방향 제시                          │
│  - 예외 상황 판단                            │
└──────────────┬──────────────────────────────┘
               │ (자연어 대화)
┌──────────────▼──────────────────────────────┐
│  Layer 1: Copilot Sian (VS Code)            │
│  - 사용자 대화 이해                          │
│  - 코드 생성/편집                            │
│  - 작업 계획 수립                            │
└──────────────┬──────────────────────────────┘
               │ (HTTP API / 파일 기반 통신)
┌──────────────▼──────────────────────────────┐
│  Layer 2: Meta Sian (Gemini CLI)            │
│  - 메타층 상태 모니터링                      │
│  - 자율 복구 결정                            │
│  - 시스템 최적화                             │
│  - 작업 우선순위 재조정                      │
└──────────────┬──────────────────────────────┘
               │ (직접 실행 권한)
┌──────────────▼──────────────────────────────┐
│  Layer 3: Execution Layer (OS)               │
│  - Autonomous Work Worker                    │
│  - Task Queue Server                         │
│  - 백그라운드 프로세스들                     │
└─────────────────────────────────────────────┘
```

### 역할 분리

**Copilot Sian (Layer 1)**:

- 전술적 (Tactical)
- 사용자와 직접 대화
- 코드 레벨 작업
- 즉각적 응답

**Meta Sian (Layer 2)**:

- 전략적 (Strategic)
- 시스템 건강 감시
- 장기 최적화
- 자율 판단

**Worker (Layer 3)**:

- 작전적 (Operational)
- 정해진 작업 실행
- 로그 기록
- 상태 보고

## 구현 방안

### 방안 1: 파일 기반 통신 (간단, 즉시 적용 가능)

**아키텍처**:

```
Copilot → meta_tasks.json → Meta Sian → system_state.json → Worker
```

**장점**:

- 구현 간단
- 디버깅 용이
- VS Code 독립성

**단점**:

- 실시간성 낮음
- 파일 I/O 오버헤드

**구현**:

1. **Copilot이 메타 작업 생성**:

   ```json
   {
     "task_id": "optimize_bqi_weights",
     "priority": "high",
     "context": "Recent BQI accuracy dropped to 0.65",
     "requested_by": "copilot_sian",
     "timestamp": "2025-11-02T15:20:00"
   }
   ```

2. **Meta Sian이 주기적으로 체크**:

   ```bash
   # scripts/meta_sian_daemon.ps1
   while ($true) {
     gemini chat --prompt "Check meta_tasks.json and system health, decide actions"
     Start-Sleep -Seconds 60
   }
   ```

3. **결정을 시스템에 적용**:

   ```bash
   gemini chat --prompt "Execute recovery: restart local LLM proxy"
   # → PowerShell 명령 생성 → 실행
   ```

### 방안 2: HTTP API 기반 (중급, 더 반응적)

**아키텍처**:

```
Copilot → POST /api/meta/task → Meta Sian Server → Worker
```

**장점**:

- 실시간 응답
- RESTful 패턴
- 확장 용이

**단점**:

- 서버 관리 필요
- 복잡도 증가

### 방안 3: Gemini Live API (고급, 미래 지향)

**아키텍처**:

```
Copilot ←→ Gemini Live Session ←→ Meta Sian Agent
```

**장점**:

- 자연어 대화
- 컨텍스트 유지
- 진정한 AI 페르소나

**단점**:

- API 비용
- 복잡한 설정

## 추천 구현 단계

### Phase 1: 파일 기반 프로토타입 (즉시)

**목표**: Meta Sian이 건강 체크 + 복구 결정 수행

**작업**:

1. ✅ Worker에 건강 체크 내장 (완료)
2. ⬜ Meta Sian 데몬 스크립트 생성
3. ⬜ Gemini API 설정
4. ⬜ 파일 기반 작업 큐 구현
5. ⬜ 자동 시작 등록

**예상 시간**: 2-3시간

### Phase 2: 자율 판단 강화 (다음 주)

**목표**: Meta Sian이 시스템 최적화 제안

**작업**:

1. ⬜ 시스템 메트릭 수집 강화
2. ⬜ Gemini에게 컨텍스트 제공 (최근 로그, 성능 데이터)
3. ⬜ 판단 기록 및 학습
4. ⬜ 사용자 승인 워크플로

### Phase 3: HTTP API 전환 (향후)

**목표**: 실시간 메타층 관리

**작업**:

1. ⬜ Meta Sian API 서버 구현
2. ⬜ Copilot Extension에서 API 호출
3. ⬜ WebSocket 기반 실시간 상태 스트림

## 구체적 시나리오

### 시나리오 1: "unhealthy 자동 해결"

**현재**:

- Worker가 건강 문제 감지
- 미리 정의된 복구 스크립트 실행

**Meta Sian 적용 후**:

```
1. Worker: "Local LLM offline detected"
2. Meta Sian (Gemini):
   - 최근 로그 분석
   - "8080 포트 충돌 가능성 높음"
   - 결정: "포트 변경 후 재시작"
3. Worker: 지시사항 실행
4. Meta Sian: 결과 검증 및 기록
```

**장점**: 유연한 판단, 새로운 문제 대응 가능

### 시나리오 2: "BQI 가중치 최적화"

**현재**:

- 수동으로 성능 확인
- 사용자가 직접 조정

**Meta Sian 적용 후**:

```
1. Meta Sian: "BQI accuracy 0.65 → 0.72로 개선 가능"
2. 제안: "Judge A 가중치 0.3 → 0.4로 조정"
3. 사용자 승인 요청 (optional)
4. 적용 및 A/B 테스트
5. 결과 기록 및 학습
```

### 시나리오 3: "작업 우선순위 재조정"

**현재**:

- 고정된 우선순위
- AutonomousWorkPlanner의 단순 로직

**Meta Sian 적용 후**:

```
1. Meta Sian: 시스템 상태 분석
   - CPU 사용률 높음
   - BQI 학습 실행 중
2. 판단: "Performance dashboard 생성 연기"
3. 작업 큐 재조정
4. 리소스 집중
```

## 기술 스택

### Gemini CLI 설정

```bash
# 1. gcloud 인증
gcloud auth login

# 2. Gemini API 활성화
gcloud services enable generativelanguage.googleapis.com

# 3. API 키 설정
$env:GEMINI_API_KEY = "your-api-key"

# 4. 테스트
gemini chat --prompt "Hello, I'm Meta Sian. Check system health."
```

### PowerShell 데몬

```powershell
# scripts/start_meta_sian_daemon.ps1
param(
    [int]$IntervalSeconds = 60,
    [switch]$Detached
)

if ($Detached) {
    # 분리 프로세스로 실행
    Start-Process powershell -ArgumentList @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", "$PSScriptRoot\meta_sian_daemon_loop.ps1",
        "-IntervalSeconds", $IntervalSeconds
    ) -WindowStyle Hidden
} else {
    # 전경 실행
    & "$PSScriptRoot\meta_sian_daemon_loop.ps1" -IntervalSeconds $IntervalSeconds
}
```

### Meta Sian 루프

```powershell
# scripts/meta_sian_daemon_loop.ps1
param([int]$IntervalSeconds = 60)

$workspace = "C:\workspace\agi"
$metaTasksPath = "$workspace\fdo_agi_repo\outputs\meta_tasks.json"
$systemStatePath = "$workspace\outputs\health_check_latest.json"

while ($true) {
    # 1. 시스템 상태 읽기
    $systemState = Get-Content $systemStatePath | ConvertFrom-Json
    
    # 2. 메타 작업 확인
    $metaTasks = @()
    if (Test-Path $metaTasksPath) {
        $metaTasks = Get-Content $metaTasksPath | ConvertFrom-Json
    }
    
    # 3. Gemini에게 판단 요청
    $prompt = @"
You are Meta Sian, an AI persona managing the meta-layer of an AGI system.

Current system state:
$(ConvertTo-Json $systemState -Depth 5)

Pending meta tasks:
$(ConvertTo-Json $metaTasks -Depth 5)

Analyze the system health and decide:
1. Any immediate recovery actions needed?
2. Should any meta tasks be executed?
3. Any optimization opportunities?

Respond in JSON format:
{
  "actions": [
    {"type": "recovery", "script": "script_name.ps1", "reason": "..."},
    {"type": "optimize", "task": "task_id", "priority": "high"}
  ],
  "insights": "Brief analysis"
}
"@
    
    # Gemini 호출 (가상 코드 - 실제는 gemini CLI 또는 API 사용)
    $decision = gemini chat --prompt $prompt | ConvertFrom-Json
    
    # 4. 결정 실행
    foreach ($action in $decision.actions) {
        if ($action.type -eq "recovery") {
            Write-Host "🔧 Meta Sian: Executing recovery - $($action.reason)"
            & "$workspace\scripts\$($action.script)"
        } elseif ($action.type -eq "optimize") {
            Write-Host "⚡ Meta Sian: Optimizing - $($action.task)"
            # AutonomousWorkPlanner에 작업 추가
        }
    }
    
    # 5. 로그 기록
    $logEntry = @{
        timestamp = (Get-Date -Format "o")
        decision = $decision
        executed = $true
    }
    Add-Content "$workspace\outputs\meta_sian_log.jsonl" -Value (ConvertTo-Json $logEntry -Compress)
    
    Start-Sleep -Seconds $IntervalSeconds
}
```

## 장점 요약

### 🎯 핵심 가치

1. **진정한 자율성**
   - AI가 AI를 관리
   - 인간은 전략적 방향만 제시

2. **확장 가능한 지능**
   - Gemini 모델 업그레이드 시 자동 개선
   - 새로운 문제 패턴 학습

3. **레이어 분리**
   - Copilot: 코드 레벨
   - Meta Sian: 시스템 레벨
   - Worker: 실행 레벨

4. **페르소나 일관성**
   - "시안"이라는 통합된 정체성
   - 레이어 간 컨텍스트 공유

## 다음 단계

### 즉시 (오늘)

1. ✅ Worker에 건강 체크 추가 (완료)
2. ⬜ Gemini API 설정 테스트
3. ⬜ Meta Sian 데몬 프로토타입 작성
4. ⬜ 파일 기반 통신 테스트

### 단기 (이번 주)

1. ⬜ 자동 시작 등록
2. ⬜ 로그 분석 강화
3. ⬜ 복구 전략 확장

### 중기 (다음 주)

1. ⬜ HTTP API 전환
2. ⬜ Copilot Extension 통합
3. ⬜ 사용자 승인 워크플로

## 리스크 및 완화

### 리스크 1: Gemini API 비용

**완화**:

- 60초 간격으로 제한
- 상태 변화 감지 시에만 호출
- 로컬 모델 백업 (Ollama)

### 리스크 2: 잘못된 판단

**완화**:

- Dry-run 모드 (실행 전 사용자 승인)
- 판단 로그 기록
- 롤백 메커니즘

### 리스크 3: 복잡도 증가

**완화**:

- Phase별 점진적 도입
- 기존 시스템 유지 (폴백)
- 간단한 파일 기반으로 시작

## 결론

**Meta Sian 통합은 다음 단계로 타당함**:

- ✅ 기술적 실현 가능
- ✅ 점진적 도입 가능
- ✅ 명확한 가치 제공
- ✅ 리스크 관리 가능

**권장 접근**:

1. Phase 1 (파일 기반) 프로토타입으로 시작
2. 2주간 운영 데이터 수집
3. 효과 검증 후 Phase 2로 진행

**첫 마일스톤**:
"Meta Sian이 Worker의 unhealthy 상태를 감지하고, Gemini를 통해 복구 스크립트를 자율적으로 선택·실행"
