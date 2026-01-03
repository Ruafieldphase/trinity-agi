# ============================================================
# VS Code Workspace 시작 시 자동 실행 스크립트
# ============================================================
# 목적: VS Code가 열리면 자동으로 Phase 2.5 작업 재개
# 트리거: .vscode/settings.json의 "workspace.onDidOpen" 이벤트
# ============================================================

param(
    [switch]$Silent
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Continue"
$WorkspaceRoot = $PSScriptRoot | Split-Path -Parent
$ProgressFile = Join-Path $WorkspaceRoot ".vscode\settings_rpa_phase25.json"
$LedgerFile = Join-Path $WorkspaceRoot "fdo_agi_repo\memory\resonance_ledger.jsonl"
$AutoStateFile = Join-Path $WorkspaceRoot "outputs\auto_continuation_state.json"

# ============================================================
# 1. 세션 변경 감지
# ============================================================
$Now = Get-Date
$LastRun = $null

if (Test-Path $AutoStateFile) {
    $State = Get-Content $AutoStateFile -Raw | ConvertFrom-Json
    $LastRun = [DateTime]::Parse($State.last_run)
    $TimeSinceLastRun = ($Now - $LastRun).TotalMinutes
    
    if ($TimeSinceLastRun -lt 5) {
        # 5분 이내 재실행 → 중복 방지
        if (-not $Silent) {
            Write-Host "⏭️  최근에 실행됨 (${TimeSinceLastRun}분 전). 건너뜀." -ForegroundColor Yellow
        }
        exit 0
    }
}

# ============================================================
# 2. 자동 상태 저장
# ============================================================
$AutoState = @{
    last_run         = $Now.ToString("o")
    session_id       = [guid]::NewGuid().ToString()
    detection_reason = if ($LastRun) { 
        if (($Now - $LastRun).TotalHours -gt 4) { "reboot_or_long_break" }
        else { "vscode_restart" }
    }
    else { "first_run" }
}

$AutoState | ConvertTo-Json -Depth 5 | Set-Content $AutoStateFile

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  🤖 AGI Phase 2.5 자동 재개 시스템                        ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔍 세션 변경 감지: $($AutoState.detection_reason)" -ForegroundColor Green
Write-Host "🕐 마지막 실행: $(if ($LastRun) { $LastRun.ToString('yyyy-MM-dd HH:mm') } else { 'N/A' })" -ForegroundColor Gray
Write-Host "🆔 세션 ID: $($AutoState.session_id.Substring(0,8))..." -ForegroundColor Gray
Write-Host ""

# ============================================================
# 3. 진행 상황 자동 로드
# ============================================================
if (-not (Test-Path $ProgressFile)) {
    Write-Host "⚠️  진행 상황 파일 없음. 새로 시작합니다." -ForegroundColor Yellow
    $CurrentWeek = 1
    $CurrentDay = 0
    $ProgressPercent = 0
    $LastTask = "시작 전"
}
else {
    $Progress = Get-Content $ProgressFile -Raw | ConvertFrom-Json
    $CurrentWeek = $Progress.rpa_phase25.status.current_week
    $CurrentDay = $Progress.rpa_phase25.status.current_day
    $ProgressPercent = $Progress.rpa_phase25.status.progress_percentage
    $LastTask = $Progress.rpa_phase25.last_task
    
    Write-Host "📊 진행 상황 로드 완료" -ForegroundColor Green
    Write-Host "   Week: $CurrentWeek | Day: $CurrentDay | 진행률: $ProgressPercent%" -ForegroundColor Cyan
    Write-Host "   마지막 작업: $LastTask" -ForegroundColor Gray
}

# ============================================================
# 4. Resonance Ledger에서 최근 작업 확인
# ============================================================
Write-Host ""
Write-Host "📖 Resonance Ledger 확인 중..." -ForegroundColor Yellow

if (Test-Path $LedgerFile) {
    $RecentEvents = Get-Content $LedgerFile -Tail 10 | ForEach-Object {
        $_ | ConvertFrom-Json
    } | Where-Object { $_.timestamp -gt (Get-Date).AddHours(-24).ToString("o") }
    
    if ($RecentEvents) {
        $LastEvent = $RecentEvents | Select-Object -Last 1
        Write-Host "   ✅ 최근 24시간 이벤트: $($RecentEvents.Count)개" -ForegroundColor Green
        Write-Host "   📌 마지막 이벤트: $($LastEvent.event_type) - $($LastEvent.persona_name)" -ForegroundColor Cyan
    }
    else {
        Write-Host "   ⚠️  최근 24시간 활동 없음" -ForegroundColor Yellow
    }
}

# ============================================================
# 5. 다음 작업 자동 결정
# ============================================================
Write-Host ""
Write-Host "🎯 다음 작업 자동 결정 중..." -ForegroundColor Yellow

$NextTask = ""
$NextAction = ""

if ($CurrentWeek -eq 1) {
    switch ($CurrentDay) {
        0 {
            $NextTask = "필수 라이브러리 설치"
            $NextAction = "pip install -r fdo_agi_repo/requirements_rpa.txt"
        }
        1 {
            $NextTask = "Comet API Client 통합 (Day 1)"
            $NextAction = "fdo_agi_repo/integrations/comet_client.py 구현"
        }
        2 {
            $NextTask = "Comet API Client 통합 (Day 2 - 완료)"
            $NextAction = "Comet 연결 테스트 및 디버깅"
        }
        3 {
            $NextTask = "YouTube Learner 모듈 (Day 3)"
            $NextAction = "fdo_agi_repo/rpa/youtube_learner.py 구현"
        }
        4 {
            $NextTask = "YouTube Learner 모듈 (Day 4 - 완료)"
            $NextAction = "영상 분석 테스트"
        }
        5 {
            $NextTask = "RPA Core Infrastructure (Day 5)"
            $NextAction = "fdo_agi_repo/rpa/core.py 구현"
        }
        6 {
            $NextTask = "RPA Core Infrastructure (Day 6 - 완료)"
            $NextAction = "OCR + GUI 제어 테스트"
        }
        7 {
            $NextTask = "Trial-and-Error Engine (Day 7)"
            $NextAction = "fdo_agi_repo/rpa/trial_error_engine.py 구현"
        }
        default {
            $NextTask = "Week 1 완료 체크"
            $NextAction = "Week 2로 진행 준비"
        }
    }
}
else {
    $NextTask = "Week 2 - Docker Desktop 자동 설치 테스트"
    $NextAction = "E2E 테스트 실행"
}

Write-Host "   📌 다음 작업: $NextTask" -ForegroundColor Cyan
Write-Host "   🔧 실행 내용: $NextAction" -ForegroundColor Gray

# ============================================================
# 6. Task Queue Server 자동 시작
# ============================================================
Write-Host ""
Write-Host "🚀 Task Queue Server 상태 확인..." -ForegroundColor Yellow

try {
    $Response = Invoke-WebRequest -Uri "http://localhost:8091/api/health" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "   ✅ Task Queue Server ONLINE" -ForegroundColor Green
}
catch {
    Write-Host "   ❌ Task Queue Server OFFLINE" -ForegroundColor Red
    Write-Host "   🔄 자동 시작 중..." -ForegroundColor Yellow
    
    # PowerShell Job으로 백그라운드 실행
    $ServerScript = Join-Path $WorkspaceRoot "LLM_Unified\ion-mentoring\task_queue_server.py"
    if (Test-Path $ServerScript) {
        $PythonExe = Join-Path $WorkspaceRoot "LLM_Unified\.venv\Scripts\python.exe"
        if (Test-Path $PythonExe) {
            Start-Job -ScriptBlock {
                param($Python, $Script)
                & $Python $Script
            } -ArgumentList $PythonExe, $ServerScript
            Write-Host "   ✅ Task Queue Server 시작됨 (백그라운드)" -ForegroundColor Green
        }
    }
}

# ============================================================
# 7. GitHub Copilot Chat 자동 트리거
# ============================================================
Write-Host ""
Write-Host "💬 GitHub Copilot Chat 프롬프트 생성 중..." -ForegroundColor Yellow

$CopilotPrompt = @"
🤖 **자동 재개: Phase 2.5 RPA + YouTube Learning**

**세션 변경 감지**: $($AutoState.detection_reason)
**현재 상태**: Week $CurrentWeek, Day $CurrentDay (진행률: $ProgressPercent%)
**마지막 작업**: $LastTask

**다음 작업**: $NextTask
**실행 내용**: $NextAction

**컨텍스트**:
- PHASE_2_5_RPA_YOUTUBE_LEARNING_PLAN.md 참조
- Comet Browser + Perplexity 연동 구조 존재
- Resonance Ledger에 모든 학습 기록

**지시사항**: $NextTask 를 자동으로 시작해줘. 사용자의 추가 명령 없이 진행해.
"@

# Copilot Chat workspace 파일에 자동 입력 (VS Code API 필요)
$CopilotInputFile = Join-Path $WorkspaceRoot ".vscode\copilot_auto_input.txt"
$CopilotPrompt | Set-Content $CopilotInputFile

Write-Host "   ✅ 프롬프트 생성 완료: .vscode\copilot_auto_input.txt" -ForegroundColor Green

# ============================================================
# 8. 계획 파일 자동 업데이트
# ============================================================
Write-Host ""
Write-Host "📝 계획 파일 자동 업데이트 중..." -ForegroundColor Yellow

$PlanFile = Join-Path $WorkspaceRoot "PHASE_2_5_RPA_YOUTUBE_LEARNING_PLAN.md"
if (Test-Path $PlanFile) {
    $PlanContent = Get-Content $PlanFile -Raw
    
    # 진행 상황 마커 찾기 및 업데이트
    $ProgressMarker = "**현재 진행**: Week \d+, Day \d+"
    $NewProgressMarker = "**현재 진행**: Week $CurrentWeek, Day $CurrentDay (자동 업데이트: $(Get-Date -Format 'yyyy-MM-dd HH:mm'))"
    
    if ($PlanContent -match $ProgressMarker) {
        $UpdatedContent = $PlanContent -replace $ProgressMarker, $NewProgressMarker
        $UpdatedContent | Set-Content $PlanFile
        Write-Host "   ✅ 계획 파일 업데이트 완료" -ForegroundColor Green
    }
    else {
        # 마커 없으면 추가
        $InsertLine = "## 📅 2주 실행 계획"
        if ($PlanContent -match $InsertLine) {
            $UpdatedContent = $PlanContent -replace "($InsertLine)", "`$1`n`n$NewProgressMarker`n"
            $UpdatedContent | Set-Content $PlanFile
            Write-Host "   ✅ 진행 상황 마커 추가 완료" -ForegroundColor Green
        }
    }
}

# ============================================================
# 9. 자동 실행 트리거
# ============================================================
Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  ✅ 자동 재개 준비 완료!                                 ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "📋 다음 작업: $NextTask" -ForegroundColor Cyan
Write-Host "🚀 GitHub Copilot이 자동으로 작업을 시작합니다..." -ForegroundColor Yellow
Write-Host ""
Write-Host "💡 수동 개입이 필요한 경우:" -ForegroundColor Gray
Write-Host "   - Copilot Chat에서 .vscode\copilot_auto_input.txt 내용 확인" -ForegroundColor Gray
Write-Host "   - 또는 'Phase 2.5 계속' 명령" -ForegroundColor Gray
Write-Host ""

# ============================================================
# 10. VS Code 알림 표시 (선택)
# ============================================================
if (-not $Silent) {
    # VS Code notification (code CLI 필요)
    $NotificationMsg = "AGI Phase 2.5 자동 재개: $NextTask"
    # code --notification "$NotificationMsg"  # VS Code 1.85+ 필요
}

exit 0