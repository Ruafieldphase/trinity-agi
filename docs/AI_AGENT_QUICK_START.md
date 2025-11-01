# AI-First Performance Monitoring - Quick Start Guide

**Date**: 2025-11-01  
**System**: AGI Autonomous Operations  
**Status**: ✅ Production Ready

---

## Overview

이 시스템은 **AI 에이전트가 자율적으로** 성능을 모니터링하고 문제를 해결하는 완전 자동화된 시스템입니다.

### Key Features

- 🤖 **AI-First Design**: AI 에이전트가 주 사용자
- 📊 **자동 분석**: 트렌드, 이상 징후 자동 탐지
- 🔄 **자율 복구**: 문제 발생 시 자동 조치
- 💬 **AI-to-AI 통신**: 에이전트 간 협력
- 📈 **예측 유지보수**: 문제 발생 전 예방
- 📢 **Smart Escalation**: 필요시 인간에게 자동 에스컬레이션

---

## Architecture

```text
┌─────────────────────────────────────────────────────────┐
│                   AI Performance Agent                   │
│  (Autonomous decision-making and action execution)      │
└───────────────┬──────────────────────┬──────────────────┘
                │                      │
    ┌───────────▼───────────┐  ┌──────▼──────────────┐
    │  Performance Monitor  │  │  AI Comms Hub       │
    │  (Metrics Collection) │  │  (Agent Messaging)  │
    └───────────┬───────────┘  └──────┬──────────────┘
                │                     │
    ┌───────────▼─────────────────────▼──────────────┐
    │         Action Executor & Recovery System      │
    └────────────────────────────────────────────────┘
```

---

## Quick Start

### 1. One-Time Dry Run (안전 테스트)

```powershell
# AI 에이전트가 분석만 하고 조치는 안함
.\scripts\ai_performance_agent.ps1 -DryRun
```

**결과**:

- ✅ 시스템 상태 분석
- ✅ AI 결정 로직 확인
- ✅ 권장 조치 확인
- ❌ 실제 조치 실행 안함

### 2. Single Run with Auto-Recovery

```powershell
# AI 에이전트가 자동으로 문제 해결 시도
.\scripts\ai_performance_agent.ps1 -AutoRecover
```

**결과**:

- ✅ 시스템 분석
- ✅ Critical 시스템 자동 복구 시도
- ✅ 조치 로그 기록
- ✅ 다른 AI 에이전트에게 통보

### 3. Continuous Autonomous Monitoring

```powershell
# 30분마다 자동으로 모니터링 (24시간 동안)
.\scripts\ai_agent_scheduler.ps1 -IntervalMinutes 30 -DurationMinutes 1440 -AutoRecover
```

**결과**:

- 🔄 백그라운드에서 지속 실행
- 🤖 완전 자율 운영
- 📊 주기적 상태 체크
- 🚨 문제 발생 시 자동 대응

### 4. Stop Background Monitoring

```powershell
# 백그라운드 모니터링 중지
.\scripts\ai_agent_scheduler.ps1 -StopOnly
```

### 5. Auto Start on Boot / VS Code Open (권장)

시간 기반(새벽) 대신, PC 부팅/로그온 또는 VS Code 워크스페이스가 열릴 때 자동으로 재개되도록 설정할 수 있습니다.

```powershell
# 1) 로그온 시 자동 재개 등록 (권장)
#    - 관리자 권한이 없어 스케줄러 등록이 실패하면, 자동으로 시작프로그램(Startup) 바로가기 방식으로 폴백됩니다.
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/register_auto_resume.ps1 -Register

# 2) VS Code 워크스페이스 열릴 때 자동 재개 (이미 구성됨)
#    - tasks.json의 "AGI: Auto Resume on Workspace Open"가 워크스페이스 오픈 시 scripts/auto_resume_on_startup.ps1를 실행합니다.
#    - auto_resume_on_startup.ps1는 다음을 자동 수행합니다:
#      - Task Queue Server 필요 시 자동 기동
#      - AI Agent Scheduler 미동작 시 자동 시작 (30분 주기/24시간/AutoRecover)

# 상태확인 / 해제
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/register_auto_resume.ps1 -Status
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/register_auto_resume.ps1 -Unregister
```

참고: `scripts/auto_resume_on_startup.ps1`는 중복 실행 방지를 위해 최근 5분 내 실행 기록이 있으면 안전하게 종료합니다. 또한 스케줄러 PID 파일을 점검하여 이미 동작 중인 경우 재시작하지 않습니다.

#### 스케줄러 상태 확인(추가)

```powershell
# 스케줄러(백그라운드 모니터)가 실제로 살아있는지 확인 (0=alive, 1=not running)
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check_scheduler_status.ps1

# JSON 출력이 필요하면
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check_scheduler_status.ps1 -Json
```

---

## AI-to-AI Communication

### Send Message to Other AI Agents

```powershell
# AI 에이전트가 다른 에이전트에게 메시지 전송
.\scripts\ai_comms_hub.ps1 -Action send `
    -SourceAgent "PerformanceAgent" `
    -TargetAgent "RecoveryAgent" `
    -Message "System degradation detected in Orchestration" `
    -Priority CRITICAL
```

### Receive Messages

```powershell
# 수신된 메시지 확인
.\scripts\ai_comms_hub.ps1 -Action receive -SourceAgent "RecoveryAgent"
```

### Broadcast to All Agents

```powershell
# 모든 AI 에이전트에게 브로드캐스트
.\scripts\ai_comms_hub.ps1 -Action broadcast `
    -SourceAgent "PerformanceAgent" `
    -Message "All systems operational" `
    -Priority SUCCESS
```

### Query Hub Status

```powershell
# 통신 허브 상태 조회
.\scripts\ai_comms_hub.ps1 -Action query -Json
```

---

## Output Files

### For AI Agents (JSON)

```text
outputs/
├── ai_agent_data_YYYY-MM-DD_HH-mm-ss.json      # 구조화된 데이터 (타임스탬프)
├── ai_agent_data_latest.json                   # 최신 데이터 별칭
├── performance_metrics_latest.json              # 최신 메트릭
└── ai_comms/
    ├── agent_comms_YYYY-MM-DD.jsonl            # 통신 로그
    └── alert_YYYY-MM-DD_HH-mm-ss.json          # Critical 알람
```

### For Humans (Markdown)

```text
outputs/
├── ai_agent_report_YYYY-MM-DD_HH-mm-ss.md     # AI 결정 리포트 (타임스탬프)
├── ai_agent_report_latest.md                  # 최신 리포트 별칭
├── performance_dashboard_latest.md             # 대시보드
└── daily_report_YYYY-MM-DD.md                  # 일일 요약
```

---

## AI Agent Decision Flow

```text
1. Collect Metrics
   ↓
2. Analyze Health
   ├── Critical (< 70%)   → Immediate Auto-Recovery
   ├── Warning (70-90%)   → Scheduled Monitoring
   ├── Healthy (> 90%)    → Continue Monitoring
   └── No Data            → Investigation
   ↓
3. Trend Analysis
   ├── Degrading → Preventive Action
   ├── Improving → Continue Monitoring
   └── Stable    → No Action
   ↓
4. Execute Actions
   ├── AutoRecover ON  → Execute recovery scripts
   └── AutoRecover OFF → Log recommended actions
   ↓
5. Notify Other Agents
   ├── Critical   → Broadcast CRITICAL alert
   ├── Warning    → Send to specific agents
   └── Success    → Update status
   ↓
6. Human Escalation (if needed)
   └── Multiple critical systems OR Low confidence
```

---

## Configuration

### Thresholds

```powershell
# 조치 임계값 조정
.\scripts\ai_performance_agent.ps1 `
    -ActionThreshold 70 `    # 이 이하면 즉시 조치
    -Days 7 `                # 분석 기간
    -AutoRecover             # 자동 복구 활성화
```

### Monitoring Interval

```powershell
# 모니터링 주기 조정
.\scripts\ai_agent_scheduler.ps1 `

---

## Testing

### Run Integration Tests

```powershell
# 전체 시스템 테스트
.\scripts\test_ai_agent_system.ps1
---

## Use Cases

### Use Case 1: Nightly Autonomous Operations

```powershell
# 매일 밤 자동 실행 (Task Scheduler 등록)
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File C:\workspace\agi\scripts\ai_performance_agent.ps1 -AutoRecover"
    -Action $action -Trigger $trigger
```

### Use Case 2: Real-Time Crisis Response

```powershell
# Critical 시스템 발견 시 즉시 복구 시도
.\scripts\ai_performance_agent.ps1 -AutoRecover -ActionThreshold 75
```

### Use Case 3: Multi-Agent Coordination

```powershell
# Agent A: 성능 모니터링
.\scripts\ai_performance_agent.ps1 -AutoRecover

# Agent B: 로그 분석 (다른 터미널)
# ... 별도 에이전트 실행

# Agent C: 통신 허브 모니터링
.\scripts\ai_comms_hub.ps1 -Action query
```

---

## Benefits

### For AI Agents 🤖

- **Structured JSON Data**: 쉽게 파싱 가능한 데이터
- **Predictable Schema**: 일관된 데이터 구조
- **Action-Oriented**: 명확한 조치 권장사항
- **Inter-Agent Communication**: 협력 가능한 메시징 시스템

- **Readable Reports**: Markdown 리포트
- **Executive Summary**: 빠른 상황 파악
- **Audit Trail**: 모든 AI 결정 기록

### For System 🖥️

- **Proactive**: 문제 발생 전 예방
- **Reduced Downtime**: 빠른 대응
- **24/7 Monitoring**: 지속적 감시

## Advanced: Custom Recovery Scripts

AI 에이전트가 실행할 커스텀 복구 로직을 추가하려면:

```powershell
param()

Write-Host "Running Orchestration recovery..." -ForegroundColor Cyan

# 1. Restart service
Restart-Service "OrchestrationService" -ErrorAction Continue

# 2. Clear cache
Remove-Item "C:\cache\orchestration\*" -Force -ErrorAction Continue

# 3. Validate config
& ".\validate_orchestration_config.ps1"

# 4. Report back to AI agent
.\ai_comms_hub.ps1 -Action send `
    -SourceAgent "OrchestrationRecovery" `
    -Message "Recovery completed" `
    -Priority SUCCESS

Write-Host "Recovery complete" -ForegroundColor Green
```

그런 다음 `ai_performance_agent.ps1`의 recovery 로직에서 호출합니다.

---

## Monitoring the AI Agent

```powershell
# AI 에이전트 자체 상태 확인
Get-Process -Name powershell | Where-Object { 
    $_.CommandLine -like '*ai_performance_agent*' 
}

# 최근 리포트 확인
Get-ChildItem outputs\ai_agent_report_*.md | 
    Sort-Object LastWriteTime -Descending | 
    Select-Object -First 1 | 
    Get-Content

# (또는 최신 별칭 사용)
Get-Content outputs\ai_agent_report_latest.md

# 통신 로그 확인
Get-Content outputs\ai_comms\agent_comms_$(Get-Date -Format yyyy-MM-dd).jsonl -Tail 10

# 퀵 상태 요약(JSON)
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/ai_agent_quick_status.ps1 -Json

# 에스컬레이션 시 실패 코드(1)로 반환하여 파이프라인 게이트로 사용
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/ai_agent_quick_status.ps1 -FailOnEscalation
```

노트: `-FailOnEscalation` 사용 시 에스컬레이션 조건이 참이면 종료 코드가 1로 반환됩니다. 이는 오류가 아니라 의도된 게이트 동작입니다.

---

## Troubleshooting

### AI Agent Not Making Decisions

**Check**:

```powershell
# JSON 데이터 확인
$data = Get-Content outputs\ai_agent_data_latest.json | ConvertFrom-Json
$data.Analysis
```

**Solution**: Threshold를 조정하거나 더 많은 테스트 데이터 수집

### Auto-Recovery Not Working

**Check**: `-AutoRecover` 플래그 사용했는지 확인

**Solution**:

```powershell
.\scripts\ai_performance_agent.ps1 -AutoRecover -Verbose
```

### Inter-Agent Communication Failing

**Check**:

```powershell
.\scripts\ai_comms_hub.ps1 -Action query
```

**Solution**: `outputs/ai_comms/` 디렉토리 권한 확인

---

## Next Steps

1. **통합 테스트 실행**: `.\scripts\test_ai_agent_system.ps1`
2. **DryRun 모드로 시작**: 안전하게 동작 확인
3. **AutoRecover 활성화**: 실제 자동 복구 테스트
4. **스케줄러 등록**: 지속적 자율 운영
5. **커스텀 복구 로직 추가**: 시스템별 맞춤 복구

---

## Contact & Support

- **AI Agent Issues**: outputs/ai_agent_report_*.md 확인
- **Human Escalation**: Critical 시스템 2개 이상 또는 Confidence LOW
- **System Logs**: outputs/ai_comms/agent_comms_*.jsonl

---

**Generated by**: AI Performance Agent System  
**Version**: 1.0.0  
**Last Updated**: 2025-11-01
