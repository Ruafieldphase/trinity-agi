#Requires -Version 5.1
<#
.SYNOPSIS
    Bootstrap Autonomous System - AI 자율 관리 시스템 초기 설정
.DESCRIPTION
    이 스크립트는 단 한 번만 실행하면 됩니다.
    실행 후 AI가 스스로 모든 것을 관리합니다.
    
    수행 작업:
    1. Self-Managing Agent를 통한 모든 의존성 체크
    2. 가능한 것은 자동 등록/시작
    3. 관리자 권한 필요 시 사용자에게 명령어 제공
    4. 완료 후 AI 자율 관리 모드 활성화
.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File bootstrap_autonomous_system.ps1
#>

param(
    [switch]$Force,
    [switch]$DryRun
)

$ErrorActionPreference = "Continue"
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot

Write-Host @"

╔════════════════════════════════════════════════════════════╗
║                                                            ║
║       🤖 AI Self-Managing System Bootstrap v1.0           ║
║                                                            ║
║   This runs ONCE. After this, AI manages everything.      ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

Write-Host "Workspace: $WorkspaceRoot" -ForegroundColor Gray
Write-Host ""

# Step 1: Python venv 확인
Write-Host "[1/4] Checking Python environment..." -ForegroundColor Cyan
$pythonExe = "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    Write-Host "  ✗ Python venv not found at: $pythonExe" -ForegroundColor Red
    Write-Host "  Please create venv first:" -ForegroundColor Yellow
    Write-Host "    cd fdo_agi_repo" -ForegroundColor Gray
    Write-Host "    python -m venv .venv" -ForegroundColor Gray
    Write-Host "    .venv\Scripts\pip install -r requirements.txt" -ForegroundColor Gray
    exit 1
}
Write-Host "  ✓ Python venv ready" -ForegroundColor Green

# Step 2: Self-Managing Agent 실행 (체크 + 자동 수정)
Write-Host "`n[2/4] Running Self-Managing Agent..." -ForegroundColor Cyan
$agentScript = "$WorkspaceRoot\fdo_agi_repo\orchestrator\self_managing_agent.py"
if (-not (Test-Path $agentScript)) {
    Write-Host "  ✗ Self-Managing Agent not found: $agentScript" -ForegroundColor Red
    exit 1
}

if ($DryRun) {
    Write-Host "  [DRY RUN] Would run: $pythonExe $agentScript" -ForegroundColor Yellow
    $agentExitCode = 0
}
else {
    & $pythonExe $agentScript
    $agentExitCode = $LASTEXITCODE
}

Write-Host ""

# Step 3: 리포트 확인 및 사용자 액션 안내
Write-Host "[3/4] Checking agent report..." -ForegroundColor Cyan
$reportJson = "$WorkspaceRoot\outputs\self_managing_agent_latest.json"
if (Test-Path $reportJson) {
    $report = Get-Content $reportJson -Raw | ConvertFrom-Json
    
    if ($report.needs_human_approval -and $report.needs_human_approval.Count -gt 0) {
        Write-Host "  ⚠️  Some tasks need administrator privileges" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  Please run these commands as Administrator:" -ForegroundColor Yellow
        Write-Host ""
        
        foreach ($item in $report.needs_human_approval) {
            Write-Host "  📌 $($item.target) - $($item.reason)" -ForegroundColor Cyan
            Write-Host "     $($item.manual_command)" -ForegroundColor White
            Write-Host ""
        }
        
        Write-Host "  After running these, re-run this bootstrap script." -ForegroundColor Yellow
        Write-Host ""
    }
    else {
        Write-Host "  ✓ All dependencies auto-configured" -ForegroundColor Green
    }
    
    # 에러 표시
    if ($report.errors -and $report.errors.Count -gt 0) {
        Write-Host "  ⚠️  Some errors occurred:" -ForegroundColor Yellow
        foreach ($err in $report.errors) {
            Write-Host "    - $err" -ForegroundColor Red
        }
        Write-Host ""
    }
}
else {
    Write-Host "  ✗ Report not found: $reportJson" -ForegroundColor Red
}

# Step 4: 자율 모드 활성화 확인
Write-Host "[4/4] Autonomous mode status..." -ForegroundColor Cyan

if ($agentExitCode -eq 0) {
    Write-Host @"

╔════════════════════════════════════════════════════════════╗
║                                                            ║
║           ✅ AI Self-Managing System ACTIVATED             ║
║                                                            ║
║  From now on, AI manages itself autonomously.             ║
║  You only need to approve admin tasks (if any).           ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Green

    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. AI will auto-start on VS Code open (already configured)" -ForegroundColor Gray
    Write-Host "  2. AI will auto-recover from failures (watchdog active)" -ForegroundColor Gray
    Write-Host "  3. AI will auto-upgrade dependencies (detector active)" -ForegroundColor Gray
    Write-Host "  4. You just code. AI handles the rest. 🚀" -ForegroundColor Gray
    Write-Host ""
}
else {
    Write-Host @"

╔════════════════════════════════════════════════════════════╗
║                                                            ║
║           ⚠️  Manual Steps Required                        ║
║                                                            ║
║  See above for commands that need admin privileges.       ║
║  Run them, then re-run this bootstrap script.             ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Full report: $WorkspaceRoot\outputs\self_managing_agent_latest.md" -ForegroundColor Gray
Write-Host ""

exit $agentExitCode
