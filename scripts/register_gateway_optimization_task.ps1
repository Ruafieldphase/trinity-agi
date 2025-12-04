#Requires -Version 5.1
<#
.SYNOPSIS
    Gateway 최적화 엔진 스케줄러 등록/해제

.DESCRIPTION
    Phase 8.5 Gateway 최적화 엔진을 Windows 작업 스케줄러에 등록하여
    주기적으로 최적화 상태를 모니터링하고 gateway_optimization_log.jsonl을 갱신합니다.

.PARAMETER Register
    작업 스케줄러에 등록합니다.

.PARAMETER Unregister
    작업 스케줄러에서 제거합니다.

.PARAMETER IntervalMinutes
    실행 간격 (분 단위, 기본값: 30)

.PARAMETER TaskName
    작업 스케줄러 작업 이름 (기본값: AGI_GatewayOptimization)

.EXAMPLE
    .\register_gateway_optimization_task.ps1 -Register -IntervalMinutes 30
    .\register_gateway_optimization_task.ps1 -Unregister
#>

param(
    [switch]$Register,
    [switch]$Unregister,
    [int]$IntervalMinutes = 30,
    [string]$TaskName = "AGI_GatewayOptimization"
)

$ErrorActionPreference = 'Stop'

# 관리자 권한 확인
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "❌ 관리자 권한이 필요합니다." -ForegroundColor Red
    Write-Host "   PowerShell을 관리자 권한으로 실행하세요." -ForegroundColor Yellow
    exit 1
}

$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
$ScriptPath = Join-Path $WorkspaceRoot "scripts\run_gateway_optimization.ps1"

if (-not (Test-Path $ScriptPath)) {
    Write-Host "❌ 최적화 스크립트를 찾을 수 없습니다: $ScriptPath" -ForegroundColor Red
    exit 1
}

# 등록 해제
if ($Unregister) {
    Write-Host "`n=== Gateway 최적화 스케줄러 등록 해제 ===" -ForegroundColor Cyan
    Write-Host ""
    
    $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "✅ 작업 제거 완료: $TaskName" -ForegroundColor Green
    }
    else {
        Write-Host "⚠️ 등록된 작업이 없습니다: $TaskName" -ForegroundColor Yellow
    }
    Write-Host ""
    exit 0
}

# 등록
if ($Register) {
    Write-Host "`n=== Gateway 최적화 스케줄러 등록 ===" -ForegroundColor Cyan
    Write-Host ""
    
    # 기존 작업 확인
    $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Write-Host "⚠️ 기존 작업이 존재합니다. 제거 후 재등록합니다." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }
    
    # 트리거: 주기적 실행
    $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) -RepetitionDuration ([TimeSpan]::MaxValue)
    
    # 액션: PowerShell 스크립트 실행 (-ReportOnly 모드)
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$ScriptPath`" -ReportOnly"
    
    # 설정: 백그라운드 실행, 네트워크 사용 가능 시에만
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 10)
$settings.Hidden = $true
    
    # 주체: 현재 사용자 (비관리자 실행 가능)
    $principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType S4U -RunLevel Limited
    
    # 작업 등록
    Register-ScheduledTask -TaskName $TaskName -Trigger $trigger -Action $action -Settings $settings -Principal $principal -Description "Phase 8.5 Gateway 최적화 엔진 - 주기적 상태 모니터링 및 로그 갱신" | Out-Null
    
    Write-Host "✅ 작업 등록 완료: $TaskName" -ForegroundColor Green
    Write-Host "   실행 간격: $IntervalMinutes 분" -ForegroundColor Gray
    Write-Host "   스크립트: $ScriptPath -ReportOnly" -ForegroundColor Gray
    Write-Host ""
    
    # 상태 확인
    $task = Get-ScheduledTask -TaskName $TaskName
    Write-Host "📊 작업 상태:" -ForegroundColor Cyan
    Write-Host "   이름: $($task.TaskName)" -ForegroundColor White
    Write-Host "   상태: $($task.State)" -ForegroundColor White
    Write-Host "   다음 실행: $((Get-ScheduledTaskInfo -TaskName $TaskName).NextRunTime)" -ForegroundColor White
    Write-Host ""
    
    Write-Host "💡 팁:" -ForegroundColor Yellow
    Write-Host "   - 작업 확인: Get-ScheduledTask -TaskName $TaskName" -ForegroundColor Gray
    Write-Host "   - 수동 실행: Start-ScheduledTask -TaskName $TaskName" -ForegroundColor Gray
    Write-Host "   - 등록 해제: .\register_gateway_optimization_task.ps1 -Unregister" -ForegroundColor Gray
    Write-Host ""
    
    exit 0
}

# 매개변수 없이 호출 시 현재 상태 표시
Write-Host "`n=== Gateway 최적화 스케줄러 상태 ===" -ForegroundColor Cyan
Write-Host ""

$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    $taskInfo = Get-ScheduledTaskInfo -TaskName $TaskName
    Write-Host "✅ 등록 상태: 활성화" -ForegroundColor Green
    Write-Host "   작업 이름: $($existingTask.TaskName)" -ForegroundColor Gray
    Write-Host "   상태: $($existingTask.State)" -ForegroundColor Gray
    Write-Host "   마지막 실행: $($taskInfo.LastRunTime)" -ForegroundColor Gray
    Write-Host "   다음 실행: $($taskInfo.NextRunTime)" -ForegroundColor Gray
    Write-Host "   마지막 결과: $($taskInfo.LastTaskResult)" -ForegroundColor Gray
}
else {
    Write-Host "❌ 등록되지 않음" -ForegroundColor Red
    Write-Host "   등록하려면: .\register_gateway_optimization_task.ps1 -Register" -ForegroundColor Yellow
}

Write-Host ""
