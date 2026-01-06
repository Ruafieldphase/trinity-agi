# ============================================================
# auto_resume_on_startup.ps1 (Fixed Version)
# ============================================================
# Purpose: VS Code 열릴 때 또는 Windows 로그온 시 자동 실행
#          Phase 2.5 진행 상황을 자동으로 로드하고 다음 작업 결정
# ============================================================

param(
    [switch]$Silent
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot



$ErrorActionPreference = "Continue"
$AutoStateFile = "$WorkspaceRoot\outputs\auto_continuation_state.json"
$ProgressFile = "$WorkspaceRoot\.vscode\settings_rpa_phase25.json"
$LedgerFile = "$WorkspaceRoot\fdo_agi_repo\memory\resonance_ledger.jsonl"
$CopilotPromptFile = "$WorkspaceRoot\.vscode\copilot_auto_input.txt"

if (-not $Silent) {
    Write-Host ""
    Write-Host "================================" -ForegroundColor Cyan
    Write-Host "🤖 AGI Phase 2.5 자동 재개" -ForegroundColor Green
    Write-Host "================================" -ForegroundColor Cyan
}

# ============================================================
# 1. 세션 변경 감지 (Debounce: 5분)
# ============================================================
$Now = Get-Date
$DetectionReason = "first_run"

if (Test-Path $AutoStateFile) {
    $State = Get-Content $AutoStateFile -Raw | ConvertFrom-Json
    $LastRun = [DateTime]::Parse($State.last_run)
    $TimeSinceLastRun = ($Now - $LastRun).TotalMinutes
    
    if ($TimeSinceLastRun -lt 5) {
        if (-not $Silent) {
            Write-Host "⏱️  5분 이내 재실행 감지. 중복 방지 종료." -ForegroundColor Yellow
        }
        exit 0
    }
    
    if ($TimeSinceLastRun -gt 240) {
        $DetectionReason = "reboot_or_long_break"
    }
    else {
        $DetectionReason = "vscode_restart"
    }
}

$AutoState = @{
    last_run         = $Now.ToString("o")
    session_id       = [guid]::NewGuid().ToString()
    detection_reason = $DetectionReason
}

$AutoState | ConvertTo-Json | Set-Content $AutoStateFile

if (-not $Silent) {
    Write-Host "✅ 세션 감지: $DetectionReason" -ForegroundColor Green
}

# ============================================================
# 3. 진행 상황 로드
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
    
    if (-not $Silent) {
        Write-Host ""
        Write-Host "📊 진행 상황 로드 완료" -ForegroundColor Green
        Write-Host "   Week: $CurrentWeek | Day: $CurrentDay | 진행률: $ProgressPercent%" -ForegroundColor Cyan
        Write-Host "   마지막 작업: $LastTask" -ForegroundColor Gray
    }
}

# ============================================================
# 5. 다음 작업 자동 결정
# ============================================================
$NextTask = ""
$NextAction = ""

if ($CurrentWeek -eq 1) {
    switch ($CurrentDay) {
        0 {
            $NextTask = "필수 라이브러리 설치 (Day 0)"
            $NextAction = "Tesseract OCR, FFmpeg 설치 + pip install"
        }
        1 {
            $NextTask = "Comet API Client 통합 (Day 1)"
            $NextAction = "comet_client.py 구현"
        }
        2 {
            $NextTask = "Comet API Client 통합 (Day 2)"
            $NextAction = "Comet 연결 테스트"
        }
        3 {
            $NextTask = "YouTube Learner 모듈 (Day 3)"
            $NextAction = "youtube_learner.py 구현"
        }
        4 {
            $NextTask = "YouTube Learner 모듈 (Day 4)"
            $NextAction = "영상 분석 테스트"
        }
        5 {
            $NextTask = "RPA Core Infrastructure (Day 5)"
            $NextAction = "rpa/core.py 구현"
        }
        6 {
            $NextTask = "RPA Core Infrastructure (Day 6)"
            $NextAction = "OCR + GUI 제어 테스트"
        }
        7 {
            $NextTask = "Trial-and-Error Engine (Day 7)"
            $NextAction = "trial_error_engine.py 구현"
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

if (-not $Silent) {
    Write-Host ""
    Write-Host "🎯 다음 작업: $NextTask" -ForegroundColor Cyan
    Write-Host "   실행 계획: $NextAction" -ForegroundColor Gray
}

# ============================================================
# 6. Task Queue Server 자동 시작
# ============================================================
try {
    $Response = Invoke-WebRequest -Uri "http://localhost:8091/api/health" -TimeoutSec 2 -ErrorAction Stop
    if (-not $Silent) {
        Write-Host "✅ Task Queue Server 실행 중" -ForegroundColor Green
    }
}
catch {
    if (-not $Silent) {
        Write-Host "⚠️  Task Queue Server 오프라인. 자동 시작 중..." -ForegroundColor Yellow
    }
    
    $PythonExe = "$WorkspaceRoot\LLM_Unified\.venv\Scripts\python.exe"
    $ServerScript = "$WorkspaceRoot\LLM_Unified\ion-mentoring\task_queue_server.py"
    
    if (Test-Path $PythonExe) {
        Start-Job -ScriptBlock {
            param($Python, $Script)
            & $Python $Script
        } -ArgumentList $PythonExe, $ServerScript | Out-Null
        
        Start-Sleep -Seconds 2
        
        if (-not $Silent) {
            Write-Host "✅ Task Queue Server 시작 완료" -ForegroundColor Green
        }
    }
}

# ============================================================
# 7. Copilot Chat 프롬프트 자동 생성
# ============================================================
$CopilotPrompt = @"
🤖 **자동 재개 시스템이 세션 변경을 감지했습니다**

**감지 이유**: $DetectionReason
**현재 진행**: Week $CurrentWeek, Day $CurrentDay ($ProgressPercent% 완료)
**마지막 작업**: $LastTask

---

**다음 작업**: $NextTask
**실행 계획**: $NextAction

---

**지시사항**:
- "$NextTask" 작업을 자동으로 시작해줘
- 사용자의 추가 명령 없이 진행
- 완료 후 진행 상황 업데이트

**참고**:
- 진행 파일: .vscode/settings_rpa_phase25.json
- Resonance Ledger: fdo_agi_repo/memory/resonance_ledger.jsonl
"@

$CopilotPrompt | Set-Content $CopilotPromptFile -Encoding UTF8

if (-not $Silent) {
    Write-Host ""
    Write-Host "✅ Copilot 프롬프트 생성 완료" -ForegroundColor Green
    Write-Host "   파일: .vscode\copilot_auto_input.txt" -ForegroundColor Gray
    Write-Host ""
    Write-Host "================================" -ForegroundColor Cyan
    Write-Host "🚀 자동 재개 준비 완료!" -ForegroundColor Green
    Write-Host "================================" -ForegroundColor Cyan
}

exit 0