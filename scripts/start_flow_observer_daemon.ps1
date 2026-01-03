<#
.SYNOPSIS
    Flow Observer 백그라운드 데몬 시작

.DESCRIPTION
    Desktop 활동을 실시간 모니터링하고 Flow 상태를 추적합니다.
    - 5초 간격 텔레메트리 수집
    - 5분 간격 Flow 분석
    - Perspective 전환 감지 및 알림
    - 정체 상태 자동 감지 및 제안

.PARAMETER IntervalSeconds
    Flow 분석 간격 (기본 300초 = 5분)

.PARAMETER KillExisting
    기존 데몬 종료 후 새로 시작

.EXAMPLE
    .\start_flow_observer_daemon.ps1
    # 기본 설정으로 시작

.EXAMPLE
    .\start_flow_observer_daemon.ps1 -KillExisting -IntervalSeconds 180
    # 기존 종료 후 3분 간격으로 시작
#>

param(
    [int]$IntervalSeconds = 300,  # 5분
    [switch]$KillExisting
)

$ErrorActionPreference = 'Stop'
$workspaceRoot = Split-Path -Parent $PSScriptRoot

# 기존 프로세스 종료
if ($KillExisting) {
    Write-Host "🔍 Checking for existing Flow Observer daemon..." -ForegroundColor Cyan
    $existing = Get-Process -Name 'pwsh', 'powershell' -ErrorAction SilentlyContinue | 
    Where-Object { $_.CommandLine -like '*flow_observer_daemon_loop.ps1*' }
    
    if ($existing) {
        Write-Host "🛑 Stopping $($existing.Count) existing daemon(s)..." -ForegroundColor Yellow
        $existing | Stop-Process -Force
        Start-Sleep -Seconds 2
        Write-Host "✅ Existing daemons stopped" -ForegroundColor Green
    }
}

# Python 경로 확인
$pythonPath = Join-Path $workspaceRoot "fdo_agi_repo\.venv\Scripts\python.exe"
if (-not (Test-Path $pythonPath)) {
    $pythonPath = "python"
    Write-Host "⚠️ Virtual env not found, using system python" -ForegroundColor Yellow
}

# 데몬 루프 스크립트 경로
$daemonScript = Join-Path $PSScriptRoot "flow_observer_daemon_loop.ps1"

# 백그라운드 Job으로 시작
Write-Host "🚀 Starting Flow Observer Daemon..." -ForegroundColor Cyan
Write-Host "   Analysis Interval: $IntervalSeconds seconds" -ForegroundColor Gray
Write-Host "   Python: $pythonPath" -ForegroundColor Gray

$job = Start-Job -ScriptBlock {
    param($Script, $Interval, $Python, $Root)
    
    Set-Location $Root
    & $Script -IntervalSeconds $Interval -PythonPath $Python
    
} -ArgumentList $daemonScript, $IntervalSeconds, $pythonPath, $workspaceRoot -Name "FlowObserverDaemon"

if ($job) {
    Write-Host "✅ Flow Observer Daemon started (Job ID: $($job.Id))" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Monitoring:" -ForegroundColor Cyan
    Write-Host "   • Desktop activity (5s interval)" -ForegroundColor Gray
    Write-Host "   • Flow state analysis (${IntervalSeconds}s interval)" -ForegroundColor Gray
    Write-Host "   • Perspective switching detection" -ForegroundColor Gray
    Write-Host "   • Stagnation alerts" -ForegroundColor Gray
    Write-Host ""
    Write-Host "💡 Commands:" -ForegroundColor Cyan
    Write-Host "   Check status: Get-Job -Name FlowObserverDaemon" -ForegroundColor Gray
    Write-Host "   View output:  Receive-Job -Name FlowObserverDaemon -Keep" -ForegroundColor Gray
    Write-Host "   Stop daemon:  Stop-Job -Name FlowObserverDaemon; Remove-Job -Name FlowObserverDaemon" -ForegroundColor Gray
    Write-Host ""
    Write-Host "📁 Outputs:" -ForegroundColor Cyan
    Write-Host "   • outputs/telemetry/stream_observer_*.jsonl" -ForegroundColor Gray
    Write-Host "   • outputs/flow_observer_report_latest.json" -ForegroundColor Gray
    Write-Host "   • outputs/flow_observer_daemon.log" -ForegroundColor Gray
    
    # Job 정보 출력
    $job | Format-List Id, Name, State, PSBeginTime
    
}
else {
    Write-Host "❌ Failed to start daemon" -ForegroundColor Red
    exit 1
}