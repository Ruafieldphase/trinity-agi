<#
.SYNOPSIS
Autonomous Work Worker 시작 (백그라운드)

.DESCRIPTION
자율 작업 워커를 백그라운드에서 실행:
- autonomous_work_planner에서 다음 작업 자동 선택
- auto_execute=True인 작업 자동 실행
- 결과를 ledger에 기록

.PARAMETER IntervalSeconds
작업 체크 간격 (초, 기본: 300 = 5분)

.PARAMETER KillExisting
기존 워커 종료 후 재시작

.PARAMETER Once
한 번만 실행하고 종료

.EXAMPLE
.\start_autonomous_work_worker.ps1

.EXAMPLE
.\start_autonomous_work_worker.ps1 -IntervalSeconds 180 -KillExisting
#>

param(
    [int]$IntervalSeconds = 300,
    [switch]$KillExisting,
    [switch]$Once,
    [switch]$Detached,
    [switch]$Stop,
    [switch]$Status,
    [int]$MaxScriptSeconds = 0
)

$ErrorActionPreference = "Stop"

$workspace = Split-Path -Parent $PSScriptRoot
$venvPy = Join-Path $workspace "fdo_agi_repo\.venv\Scripts\python.exe"
$workerScript = Join-Path $workspace "fdo_agi_repo\integrations\simple_autonomous_worker.py"
$pidFile = Join-Path $workspace "fdo_agi_repo\outputs\autonomous_worker.pid"

Write-Host "`n🤖 Autonomous Work Worker" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor DarkGray

# 유틸: 실행 중 프로세스 찾기
function Get-WorkerProcesses {
    try {
        $pattern = 'simple_autonomous_worker.py'
        $procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match [regex]::Escape($pattern) }
        return $procs
    }
    catch { return @() }
}

function Stop-WorkerProcesses {
    param([switch]$Quiet)
    $stopped = $false
    # 1) PID 파일 우선
    if (Test-Path $pidFile) {
        try {
            $pidFromFile = Get-Content -Path $pidFile -ErrorAction Stop | Select-Object -First 1
            if ($pidFromFile) {
                $p = Get-Process -Id [int]$pidFromFile -ErrorAction SilentlyContinue
                if ($p) {
                    Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
                    if (-not $Quiet) { Write-Host "   ✅ Stopped PID from pidfile: $($p.Id)" -ForegroundColor Green }
                    $stopped = $true
                }
            }
        }
        catch {}
        # pidfile 정리
        Remove-Item -Path $pidFile -Force -ErrorAction SilentlyContinue | Out-Null
    }
    # 2) 패턴 검색으로 추가 정리
    $procs = Get-WorkerProcesses
    foreach ($proc in $procs) {
        try {
            Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
            if (-not $Quiet) { Write-Host "   ✅ Stopped process: $($proc.ProcessId)" -ForegroundColor Green }
            $stopped = $true
        }
        catch {}
    }
    return $stopped
}

# 상태만 조회
if ($Status) {
    $procs = Get-WorkerProcesses
    if ($procs -and $procs.Count -gt 0) {
        Write-Host "📈 Worker processes running:" -ForegroundColor Green
        $procs | Select-Object ProcessId, Name, CommandLine | Format-List
    }
    else {
        Write-Host "ℹ️  No worker process found" -ForegroundColor Yellow
    }
    if (Test-Path $pidFile) {
        Write-Host ("📎 PID file: {0} (PID: {1})" -f $pidFile, (Get-Content $pidFile | Select-Object -First 1)) -ForegroundColor Gray
    }
    exit 0
}

# 기존 워커 종료 요구 시
if ($KillExisting -or $Stop) {
    Write-Host "🔍 Checking for existing workers..." -ForegroundColor Yellow
    $st = Stop-WorkerProcesses -Quiet:$false
    # PowerShell Job 정리도 추가 수행 (과거 방식 호환)
    $existingJobs = Get-Job | Where-Object { $_.Name -like "*AutonomousWork*" }
    if ($existingJobs) {
        foreach ($job in $existingJobs) { Stop-Job -Id $job.Id -ErrorAction SilentlyContinue; Remove-Job -Id $job.Id -Force -ErrorAction SilentlyContinue }
        Write-Host "   ✅ Stopped legacy PS jobs" -ForegroundColor Green
    }
    if (-not $st -and -not $existingJobs) { Write-Host "   No existing workers found" -ForegroundColor Gray }
    Write-Host ""
    # 중지만 요청된 경우, 여기서 종료
    if ($Stop -and -not $Once -and -not $Detached) {
        exit 0
    }
}

# Python 경로 확인
if (-not (Test-Path $venvPy)) {
    Write-Host "❌ Python venv not found: $venvPy" -ForegroundColor Red
    Write-Host "   Using system python instead" -ForegroundColor Yellow
    $venvPy = "python"
}

# 워커 스크립트 확인
if (-not (Test-Path $workerScript)) {
    Write-Host "❌ Worker script not found: $workerScript" -ForegroundColor Red
    exit 1
}

# 실행 모드: 단발 실행
if ($Once) {
    Write-Host "🎯 Running worker once..." -ForegroundColor Cyan
    Write-Host "   Script: $workerScript" -ForegroundColor Gray
    Write-Host ""
    
    $argsList = @($workerScript, '--once', '--workspace', $workspace)
    if ($MaxScriptSeconds -gt 0) { $argsList += @('--max-script-seconds', $MaxScriptSeconds) }
    & $venvPy @argsList
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✅ Worker execution completed" -ForegroundColor Green
    }
    else {
        Write-Host "`n❌ Worker execution failed" -ForegroundColor Red
        exit $LASTEXITCODE
    }
}
# 실행 모드: 분리(Detached) 프로세스
elseif ($Detached) {
    Write-Host "🚀 Starting worker as detached process..." -ForegroundColor Cyan
    Write-Host "   Interval: $IntervalSeconds seconds" -ForegroundColor Gray
    Write-Host "   Workspace: $workspace" -ForegroundColor Gray
    Write-Host ""

    if (-not (Test-Path $venvPy)) { $venvPy = "python" }
    $pyArgs = @($workerScript, '--interval', $IntervalSeconds, '--workspace', $workspace)
    if ($MaxScriptSeconds -gt 0) { $pyArgs += @('--max-script-seconds', $MaxScriptSeconds) }
    $proc = Start-Process -FilePath $venvPy -ArgumentList $pyArgs -WindowStyle Hidden -PassThru
    if ($proc -and $proc.Id) {
        New-Item -ItemType Directory -Path (Split-Path $pidFile -Parent) -Force | Out-Null
        Set-Content -Path $pidFile -Value $proc.Id -Encoding ASCII
        Write-Host "✅ Worker started (PID: $($proc.Id))" -ForegroundColor Green
        Write-Host "   PID file: $pidFile" -ForegroundColor Gray
        Write-Host ""
        Write-Host "💡 Worker 관리:" -ForegroundColor Yellow
        Write-Host "   상태 확인:  .\\scripts\\start_autonomous_work_worker.ps1 -Status" -ForegroundColor Gray
        Write-Host "   중지:      .\\scripts\\start_autonomous_work_worker.ps1 -Stop" -ForegroundColor Gray
    }
    else {
        Write-Host "❌ Failed to start detached worker" -ForegroundColor Red
        exit 1
    }
}
else {
    # 레거시: 세션 Job 방식(호환)
    Write-Host "🔄 Starting worker in background..." -ForegroundColor Cyan
    Write-Host "   Interval: $IntervalSeconds seconds" -ForegroundColor Gray
    Write-Host "   Workspace: $workspace" -ForegroundColor Gray
    Write-Host ""
    
    $job = Start-Job -Name "AutonomousWorkWorker" -ScriptBlock {
        param($pyExe, $script, $interval, $workspace)
        
        Set-Location $workspace
        
        & $pyExe $script --interval $interval --workspace $workspace
        
    } -ArgumentList $venvPy, $workerScript, $IntervalSeconds, $workspace
    
    Write-Host "✅ Worker started in background" -ForegroundColor Green
    Write-Host "   Job ID: $($job.Id)" -ForegroundColor Gray
    Write-Host "   Job Name: $($job.Name)" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "💡 Worker 관리:" -ForegroundColor Yellow
    Write-Host "   상태 확인:  Get-Job -Name 'AutonomousWorkWorker'" -ForegroundColor Gray
    Write-Host "   로그 보기:  Receive-Job -Name 'AutonomousWorkWorker' -Keep" -ForegroundColor Gray
    Write-Host "   중지:      Stop-Job -Name 'AutonomousWorkWorker'; Remove-Job -Name 'AutonomousWorkWorker'" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Write-Host "🎵 자율 작업 워커가 백그라운드에서 실행 중입니다!" -ForegroundColor Green
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
}

exit 0
