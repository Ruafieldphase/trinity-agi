#Requires -Version 5.1
<#
.SYNOPSIS
    깃코 봇을 Windows 작업 스케줄러에 등록합니다.

.DESCRIPTION
    시스템 시작 시 자동으로 깃코 봇이 실행되도록 스케줄러에 등록합니다.

.PARAMETER TaskName
    작업 스케줄러에 등록할 작업 이름 (기본값: GitcoSlackBot)

.PARAMETER Force
    기존 작업이 있으면 덮어씁니다.

.EXAMPLE
    .\register_bot_scheduler.ps1
    # 기본 이름으로 등록

.EXAMPLE
    .\register_bot_scheduler.ps1 -Force
    # 기존 작업이 있으면 덮어쓰기
#>

[CmdletBinding()]
param(
    [string]$TaskName = "GitcoSlackBot",
    [switch]$Force
)

$ErrorActionPreference = "Stop"

# 관리자 권한 확인
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "[ERROR] 관리자 권한이 필요합니다!" -ForegroundColor Red
    Write-Host ""
    Write-Host "PowerShell을 관리자 권한으로 실행한 후 다시 시도하세요:" -ForegroundColor Yellow
    Write-Host "  1. PowerShell 우클릭" -ForegroundColor Gray
    Write-Host "  2. '관리자 권한으로 실행' 선택" -ForegroundColor Gray
    Write-Host "  3. 이 스크립트 다시 실행" -ForegroundColor Gray
    exit 1
}

$WORKSPACE_ROOT = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$START_SCRIPT = Join-Path $WORKSPACE_ROOT "LLM_Unified\ion-mentoring\scripts\start_gitco_bot.ps1"

if (-not (Test-Path $START_SCRIPT)) {
    Write-Host "[ERROR] 시작 스크립트를 찾을 수 없습니다: $START_SCRIPT" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║       깃코 봇 - Windows 작업 스케줄러 등록               ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# 기존 작업 확인
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($existingTask) {
    if ($Force) {
        Write-Host "[WARN]  기존 작업 삭제 중: $TaskName" -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }
    else {
        Write-Host "[ERROR] 이미 작업이 등록되어 있습니다: $TaskName" -ForegroundColor Red
        Write-Host ""
        Write-Host "옵션:" -ForegroundColor Yellow
        Write-Host "  • 덮어쓰기: .\register_bot_scheduler.ps1 -Force" -ForegroundColor White
        Write-Host "  • 삭제: .\unregister_bot_scheduler.ps1" -ForegroundColor White
        exit 1
    }
}

Write-Host "📋 작업 정보:" -ForegroundColor Yellow
Write-Host "  • 작업 이름: $TaskName" -ForegroundColor White
Write-Host "  • 실행 스크립트: $START_SCRIPT" -ForegroundColor White
Write-Host "  • 트리거: 시스템 시작 시" -ForegroundColor White
Write-Host "  • 실행 계정: $env:USERNAME" -ForegroundColor White
Write-Host ""

# 작업 액션 정의
$action = New-ScheduledTaskAction `
    -Execute "PowerShell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$START_SCRIPT`" -KillExisting"

# 트리거 정의 (시스템 시작 시)
$trigger = New-ScheduledTaskTrigger -AtStartup

# 추가 트리거 (사용자 로그온 시)
$triggerLogon = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

# 설정 정의
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 5)

# 주체 정의 (현재 사용자)
$principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Highest

Write-Host "[CONFIG] 작업 스케줄러에 등록 중..." -ForegroundColor Yellow

try {
    # 작업 등록
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger @($trigger, $triggerLogon) `
        -Settings $settings `
        -Principal $principal `
        -Description "깃코 슬랙 봇 자동 시작 (배포 관리 AI 봇)" | Out-Null
    
    Write-Host "[OK] 작업 스케줄러 등록 완료!" -ForegroundColor Green
    Write-Host ""
    
    # 등록 확인
    $task = Get-ScheduledTask -TaskName $TaskName
    Write-Host "[METRICS] 등록된 작업 정보:" -ForegroundColor Yellow
    Write-Host "  • 상태: $($task.State)" -ForegroundColor White
    Write-Host "  • 마지막 실행: $($task.LastRunTime)" -ForegroundColor White
    Write-Host "  • 다음 실행: $($task.NextRunTime)" -ForegroundColor White
    Write-Host ""
    
    Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║                  [OK] 등록 완료!                            ║" -ForegroundColor Green
    Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "[SUCCESS] 이제 시스템을 시작하거나 로그인하면 자동으로 깃코 봇이 실행됩니다!" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "[CONFIG] 관리 명령어:" -ForegroundColor Yellow
    Write-Host "  • 수동 시작: Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
    Write-Host "  • 중지: Stop-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
    Write-Host "  • 비활성화: Disable-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
    Write-Host "  • 활성화: Enable-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
    Write-Host "  • 삭제: .\unregister_bot_scheduler.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "[LOG] 작업 스케줄러 GUI에서 확인:" -ForegroundColor Yellow
    Write-Host "  taskschd.msc" -ForegroundColor White
    Write-Host ""
    
    # 즉시 시작 여부 확인
    Write-Host "지금 바로 봇을 시작할까요? (Y/N): " -ForegroundColor Yellow -NoNewline
    $response = Read-Host
    
    if ($response -eq 'Y' -or $response -eq 'y') {
        Write-Host "[DEPLOY] 봇 시작 중..." -ForegroundColor Cyan
        Start-ScheduledTask -TaskName $TaskName
        Start-Sleep -Seconds 5
        Write-Host "[OK] 봇이 시작되었습니다!" -ForegroundColor Green
        Write-Host "상태 확인: .\scripts\check_bot_status.ps1" -ForegroundColor Gray
    }
    
}
catch {
    Write-Host "[ERROR] 등록 실패: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
