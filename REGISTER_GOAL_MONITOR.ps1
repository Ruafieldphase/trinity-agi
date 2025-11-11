<#
.SYNOPSIS
    Goal Executor Monitor 등록/상태/삭제 (관리자 권한 자동 요청)

.DESCRIPTION
    관리자 권한을 감지하여 필요 시 자동으로 승격하고,
    내부 스크립트(scripts/register_goal_executor_monitor_task.ps1)를 호출합니다.

.PARAMETER Register
    Task 등록

.PARAMETER Unregister
    Task 제거

.PARAMETER Status
    Task 상태 확인

.PARAMETER IntervalMinutes
    실행 간격(분). Register 시에만 사용 (기본 10)

.PARAMETER ThresholdMinutes
    정체 임계(분). Register 시에만 사용 (기본 15)

.EXAMPLE
    .\REGISTER_GOAL_MONITOR.ps1 -Register -IntervalMinutes 10 -ThresholdMinutes 15

.EXAMPLE
    .\REGISTER_GOAL_MONITOR.ps1 -Status

.EXAMPLE
    .\REGISTER_GOAL_MONITOR.ps1 -Unregister
#>

param(
    [switch]$Register,
    [switch]$Unregister,
    [switch]$Status,
    [int]$IntervalMinutes = 10,
    [int]$ThresholdMinutes = 15
)

$ErrorActionPreference = "Stop"

# 경로 계산: 워크스페이스 루트 및 내부 등록 스크립트
$WorkspaceRoot = $PSScriptRoot
$InnerScript = Join-Path $WorkspaceRoot "scripts\register_goal_executor_monitor_task.ps1"

if (-not (Test-Path $InnerScript)) {
    Write-Host "❌ 내부 스크립트를 찾을 수 없습니다: $InnerScript" -ForegroundColor Red
    exit 1
}

# 관리자 권한 확인
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

function Invoke-InnerScript {
    param([string[]]$Args)
    & $InnerScript @Args
}

if ($isAdmin) {
    # 관리자 권한 경로
    if ($Register) {
        Write-Host "`n🔧 Goal Executor Monitor 등록 중..." -ForegroundColor Cyan
        Write-Host ("=" * 60) -ForegroundColor Gray
        Invoke-InnerScript -Args @('-Register', '-IntervalMinutes', "$IntervalMinutes", '-ThresholdMinutes', "$ThresholdMinutes")
        Write-Host "`n✅ 완료!" -ForegroundColor Green
    }
    elseif ($Unregister) {
        Write-Host "`n🗑️  Goal Executor Monitor 제거 중..." -ForegroundColor Yellow
        Invoke-InnerScript -Args @('-Unregister')
        Write-Host "✅ 제거 완료" -ForegroundColor Green
    }
    elseif ($Status -or (-not $Register -and -not $Unregister)) {
        Invoke-InnerScript -Args @('-Status')
    }
    Write-Host "아무 키나 눌러서 종료..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
    exit 0
}
else {
    # 비관리자: 승격 실행
    if ($Status) {
        # 상태 확인은 권한 불필요
        Invoke-InnerScript -Args @('-Status')
        exit 0
    }
    elseif ($Register) {
        # 비관리자: 사용자 모드로 바로 등록 시도
        Write-Host "`n🔧 Goal Executor Monitor 등록(사용자 모드) 시도..." -ForegroundColor Cyan
        Invoke-InnerScript -Args @('-Register', '-UserMode', '-IntervalMinutes', "$IntervalMinutes", '-ThresholdMinutes', "$ThresholdMinutes")
        Write-Host "`n✅ 완료!" -ForegroundColor Green
        exit 0
    }
    else {
        # 제거 등 관리자 필요한 작업은 승격
        Write-Host "`n🔐 관리자 권한이 필요합니다." -ForegroundColor Yellow
        Write-Host "   관리자 권한 PowerShell을 여는 중..." -ForegroundColor Cyan

        # 승격 창에서 실행할 명령 구성
        $cmd = @('cd', '"' + $WorkspaceRoot + '";')
        $cmd += '& "' + $InnerScript + '"'
        if ($Register) { $cmd += @('-Register', '-IntervalMinutes', "$IntervalMinutes", '-ThresholdMinutes', "$ThresholdMinutes") }
        elseif ($Unregister) { $cmd += @('-Unregister') }
        else { $cmd += @('-Status') }
        $cmd += '; Write-Host ""; Write-Host "아무 키나 눌러서 종료..." -ForegroundColor Yellow; $null = $Host.UI.RawUI.ReadKey(''NoEcho,IncludeKeyDown'')'

        $arguments = @(
            '-NoExit',
            '-ExecutionPolicy', 'Bypass',
            '-Command', ($cmd -join ' ')
        )

        Start-Process powershell -Verb RunAs -ArgumentList $arguments | Out-Null

        Write-Host "`n✅ 관리자 권한 PowerShell이 열렸습니다." -ForegroundColor Green
        Write-Host "   새 창에서 요청하신 작업이 진행됩니다." -ForegroundColor Cyan
    }
}
