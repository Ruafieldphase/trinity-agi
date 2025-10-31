#Requires -Version 5.1
<#
.SYNOPSIS
    깃코 봇을 Windows 작업 스케줄러에서 제거합니다.

.PARAMETER TaskName
    제거할 작업 이름 (기본값: GitcoSlackBot)

.PARAMETER Force
    확인 없이 삭제합니다.

.EXAMPLE
    .\unregister_bot_scheduler.ps1
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
    Write-Host "PowerShell을 관리자 권한으로 실행한 후 다시 시도하세요." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║       깃코 봇 - Windows 작업 스케줄러 제거               ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# 작업 확인
$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if (-not $task) {
    Write-Host "[ERROR] 작업을 찾을 수 없습니다: $TaskName" -ForegroundColor Red
    Write-Host ""
    Write-Host "등록된 깃코 관련 작업 검색 중..." -ForegroundColor Yellow
    $relatedTasks = Get-ScheduledTask | Where-Object { $_.TaskName -like "*Gitco*" -or $_.TaskName -like "*Bot*" }
    
    if ($relatedTasks) {
        Write-Host "발견된 작업:" -ForegroundColor Yellow
        $relatedTasks | ForEach-Object {
            Write-Host "  • $($_.TaskName) ($($_.State))" -ForegroundColor White
        }
    }
    else {
        Write-Host "등록된 봇 작업이 없습니다." -ForegroundColor Gray
    }
    exit 1
}

Write-Host "📋 작업 정보:" -ForegroundColor Yellow
Write-Host "  • 작업 이름: $($task.TaskName)" -ForegroundColor White
Write-Host "  • 상태: $($task.State)" -ForegroundColor White
Write-Host "  • 설명: $($task.Description)" -ForegroundColor White
Write-Host ""

if (-not $Force) {
    Write-Host "이 작업을 삭제하시겠습니까? (Y/N): " -ForegroundColor Yellow -NoNewline
    $response = Read-Host
    
    if ($response -ne 'Y' -and $response -ne 'y') {
        Write-Host "[ERROR] 취소되었습니다." -ForegroundColor Yellow
        exit 0
    }
}

Write-Host "🗑️  작업 삭제 중..." -ForegroundColor Yellow

try {
    # 실행 중이면 먼저 중지
    if ($task.State -eq "Running") {
        Write-Host "  • 실행 중인 작업 중지..." -ForegroundColor Gray
        Stop-ScheduledTask -TaskName $TaskName
        Start-Sleep -Seconds 2
    }
    
    # 작업 삭제
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    
    Write-Host "[OK] 작업이 삭제되었습니다!" -ForegroundColor Green
    Write-Host ""
    Write-Host "[WARN]  시스템 시작 시 자동 실행이 비활성화되었습니다." -ForegroundColor Yellow
    Write-Host "수동으로 봇을 시작하려면:" -ForegroundColor Gray
    Write-Host "  .\scripts\start_gitco_bot.ps1" -ForegroundColor White
    Write-Host ""
    
}
catch {
    Write-Host "[ERROR] 삭제 실패: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
