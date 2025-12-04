# ============================================================
# Phase 2.5 RPA 자동 재개 스크립트
# ============================================================
# 목적: VS Code 재실행, 재부팅 후 자동으로 Phase 2.5 작업 재개
# 사용: PowerShell에서 직접 실행 or VS Code Task로 실행
# ============================================================

param(
    [switch]$DryRun,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"
$WorkspaceRoot = "C:\workspace\agi"
$PlanFile = Join-Path $WorkspaceRoot "PHASE_2_5_RPA_YOUTUBE_LEARNING_PLAN.md"
$ProgressFile = Join-Path $WorkspaceRoot ".vscode\settings_rpa_phase25.json"
$LogFile = Join-Path $WorkspaceRoot "outputs\rpa_phase25_resume.log"

# ============================================================
# 로그 함수
# ============================================================
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "[$Timestamp] [$Level] $Message"
    Write-Host $LogMessage -ForegroundColor $(if ($Level -eq "ERROR") { "Red" } elseif ($Level -eq "WARN") { "Yellow" } else { "Cyan" })
    Add-Content -Path $LogFile -Value $LogMessage
}

# ============================================================
# 1. 계획 파일 확인
# ============================================================
Write-Log "🔍 Phase 2.5 계획 파일 확인 중..."

if (-not (Test-Path $PlanFile)) {
    Write-Log "❌ PHASE_2_5_RPA_YOUTUBE_LEARNING_PLAN.md 파일이 없습니다!" "ERROR"
    Write-Log "   먼저 계획 파일을 생성해주세요." "ERROR"
    exit 1
}

Write-Log "✅ 계획 파일 발견: $PlanFile"

# ============================================================
# 2. 진행 상황 로드
# ============================================================
Write-Log "📊 진행 상황 로드 중..."

if (Test-Path $ProgressFile) {
    $Progress = Get-Content $ProgressFile -Raw | ConvertFrom-Json
    Write-Log "✅ 진행 상황 파일 로드 완료"
    
    $CurrentWeek = $Progress.rpa_phase25.status.current_week
    $CurrentDay = $Progress.rpa_phase25.status.current_day
    $ProgressPercent = $Progress.rpa_phase25.status.progress_percentage
    
    Write-Log "   현재: Week $CurrentWeek, Day $CurrentDay, 진행률: $ProgressPercent%"
}
else {
    Write-Log "⚠️  진행 상황 파일 없음. 새로 시작합니다." "WARN"
    $CurrentWeek = 1
    $CurrentDay = 1
    $ProgressPercent = 0
}

# ============================================================
# 3. Comet Task Queue Server 상태 확인
# ============================================================
Write-Log "🔌 Comet Task Queue Server 상태 확인..."

try {
    $Response = Invoke-WebRequest -Uri "http://localhost:8091/api/health" -TimeoutSec 2 -ErrorAction Stop
    Write-Log "✅ Task Queue Server ONLINE: $($Response.Content)"
}
catch {
    Write-Log "❌ Task Queue Server OFFLINE" "ERROR"
    Write-Log "   Run Task: 'Comet-Gitko: Start Task Queue Server (Background)'를 실행하세요." "ERROR"
    
    if (-not $DryRun) {
        Write-Log "🚀 자동으로 Task Queue Server 시작 중..."
        # Task Queue Server 시작 (백그라운드)
        # (실제 구현 시 추가)
    }
}

# ============================================================
# 4. 다음 작업 결정
# ============================================================
Write-Log "🎯 다음 작업 결정 중..."

$NextTask = ""
$NextFile = ""

if ($CurrentWeek -eq 1) {
    switch ($CurrentDay) {
        0 { 
            $NextTask = "Comet API Client 통합"
            $NextFile = "fdo_agi_repo/integrations/comet_client.py"
        }
        1 { 
            $NextTask = "Comet API Client 통합 (계속)"
            $NextFile = "fdo_agi_repo/integrations/comet_client.py"
        }
        2 { 
            $NextTask = "YouTube Learner 모듈"
            $NextFile = "fdo_agi_repo/rpa/youtube_learner.py"
        }
        3 { 
            $NextTask = "YouTube Learner 모듈 (계속)"
            $NextFile = "fdo_agi_repo/rpa/youtube_learner.py"
        }
        4 { 
            $NextTask = "RPA Core Infrastructure"
            $NextFile = "fdo_agi_repo/rpa/core.py"
        }
        5 { 
            $NextTask = "RPA Core Infrastructure (계속)"
            $NextFile = "fdo_agi_repo/rpa/core.py"
        }
        6 { 
            $NextTask = "Trial-and-Error Engine"
            $NextFile = "fdo_agi_repo/rpa/trial_error_engine.py"
        }
        default {
            $NextTask = "Week 1 완료 체크"
            $NextFile = ""
        }
    }
}
elseif ($CurrentWeek -eq 2) {
    $NextTask = "Week 2: Docker Desktop 자동 설치 테스트"
    $NextFile = ""
}

Write-Log "📌 다음 작업: $NextTask"
if ($NextFile) {
    Write-Log "📄 작업 파일: $NextFile"
}

# ============================================================
# 5. Copilot Chat에 전달할 프롬프트 생성
# ============================================================
Write-Log "💬 Copilot Chat 프롬프트 생성 중..."

$CopilotPrompt = @"
PHASE_2_5_RPA_YOUTUBE_LEARNING_PLAN.md 보고 작업 재개해줘.

**현재 상태**:
- Week: $CurrentWeek
- Day: $CurrentDay
- 진행률: $ProgressPercent%

**다음 작업**: $NextTask
$(if ($NextFile) { "**작업 파일**: $NextFile" })

**컨텍스트**:
1. Comet Browser + Perplexity 연동 구조 이미 존재
2. YouTube 영상 학습 → RPA 실행 → Trial-and-Error 학습
3. Resonance Ledger에 모든 학습 내용 기록

지금부터 $NextTask 를 구현해줘.
"@

Write-Log "✅ 프롬프트 생성 완료"
Write-Host ""
Write-Host "======================================================" -ForegroundColor Green
Write-Host "🤖 GitHub Copilot에게 전달할 프롬프트" -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Green
Write-Host $CopilotPrompt -ForegroundColor Yellow
Write-Host ""
Write-Host "======================================================" -ForegroundColor Green
Write-Host "📋 클립보드에 복사되었습니다. Copilot Chat에 붙여넣으세요!" -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Green

# 클립보드에 복사
Set-Clipboard -Value $CopilotPrompt

# ============================================================
# 6. 진행 상황 업데이트
# ============================================================
if (-not $DryRun) {
    Write-Log "💾 진행 상황 업데이트 중..."
    
    $UpdatedProgress = @{
        rpa_phase25 = @{
            version           = "1.0.0"
            created           = "2025-10-30"
            plan_file         = "PHASE_2_5_RPA_YOUTUBE_LEARNING_PLAN.md"
            status            = @{
                current_week        = $CurrentWeek
                current_day         = $CurrentDay
                last_updated        = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
                progress_percentage = $ProgressPercent
            }
            last_task         = $NextTask
            checkpoints       = $Progress.rpa_phase25.checkpoints
            session_recovery  = $Progress.rpa_phase25.session_recovery
            auto_continuation = $Progress.rpa_phase25.auto_continuation
        }
    }
    
    $UpdatedProgress | ConvertTo-Json -Depth 10 | Set-Content $ProgressFile
    Write-Log "✅ 진행 상황 저장 완료"
}

# ============================================================
# 7. 계획 파일 열기
# ============================================================
Write-Log "📖 계획 파일 열기 중..."
code $PlanFile

Write-Log "✅ Phase 2.5 재개 준비 완료!"
Write-Log "   1. 계획 파일이 열렸습니다."
Write-Log "   2. Copilot Chat에 프롬프트를 붙여넣으세요."
Write-Log "   3. 작업을 계속 진행하세요!"
