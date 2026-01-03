#Requires -Version 5.1
<#
.SYNOPSIS
    백그라운드에서 지속적으로 메트릭 수집

.DESCRIPTION
    - 관리자 권한 불필요
    - 5분마다 메트릭 수집
    - 백그라운드 PowerShell 작업으로 실행

.PARAMETER KillExisting
    기존 실행 중인 수집기 중지

.PARAMETER IntervalSeconds
    수집 간격 (기본: 300초 = 5분)

.EXAMPLE
    .\start_metrics_collector_daemon.ps1 -KillExisting
#>

param(
    [switch]$KillExisting,
    [int]$IntervalSeconds = 300
)

$ErrorActionPreference = 'Stop'

try {
    $scriptPath = "$PSScriptRoot\collect_system_metrics.ps1"
    
    if (-not (Test-Path $scriptPath)) {
        Write-Host "Script not found: $scriptPath" -ForegroundColor Red
        exit 1
    }

    # 기존 실행 중인 수집기 확인 및 종료
    if ($KillExisting) {
        Get-Process -Name 'pwsh', 'powershell' -ErrorAction SilentlyContinue | Where-Object {
            $_.CommandLine -like '*collect_system_metrics*daemon*'
        } | ForEach-Object {
            Write-Host "Stopping existing collector (PID: $($_.Id))..." -ForegroundColor Yellow
            Stop-Process -Id $_.Id -Force
        }
        Start-Sleep -Seconds 1
    }

    # 백그라운드 데몬 스크립트 생성
    $daemonScript = @"
`$scriptPath = '$scriptPath'
`$interval = $IntervalSeconds

while (`$true) {
    try {
        & `$scriptPath
        Write-Host "[\$(Get-Date -Format 'HH:mm:ss')] Metrics collected" -ForegroundColor Green
    } catch {
        Write-Host "[\$(Get-Date -Format 'HH:mm:ss')] Error: `$_" -ForegroundColor Red
    }
    Start-Sleep -Seconds `$interval
}
"@

    $daemonPath = "$PSScriptRoot\metrics_collector_daemon.ps1"
    $daemonScript | Out-File $daemonPath -Encoding UTF8

    # 백그라운드에서 실행
    $proc = Start-Process powershell `
        -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-File", "`"$daemonPath`"" `
        -PassThru `
        -WindowStyle Hidden

    Write-Host "Metrics collector daemon started!" -ForegroundColor Green
    Write-Host "  PID: $($proc.Id)" -ForegroundColor Cyan
    Write-Host "  Interval: Every $IntervalSeconds seconds" -ForegroundColor Cyan
    Write-Host "  Script: $scriptPath" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Stop with:" -ForegroundColor Yellow
    Write-Host "  Get-Process -Id $($proc.Id) | Stop-Process -Force" -ForegroundColor White
    Write-Host ""
    Write-Host "Or check status:" -ForegroundColor Yellow
    Write-Host "  .\check_metrics_collector_status.ps1" -ForegroundColor White

    exit 0

}
catch {
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}