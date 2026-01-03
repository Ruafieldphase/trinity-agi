param(
    [int]$WorkerIntervalSeconds = 300,
    [switch]$StartIfMissing,
    [switch]$Quiet
)

$ErrorActionPreference = 'SilentlyContinue'

$workspace = Split-Path -Parent $PSScriptRoot
$startScript = Join-Path $workspace 'scripts\start_autonomous_work_worker.ps1'

Write-Host "🔎 Ensuring Autonomous Worker (meta-layer check)" -ForegroundColor Cyan

# 런타임 상태 확인
$procs = @()
try {
    $procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'simple_autonomous_worker.py' }
}
catch {}

if ($procs -and $procs.Count -gt 0) {
    Write-Host "✅ Worker running (count: $($procs.Count))" -ForegroundColor Green
    if (-not $Quiet) {
        $procs | Select-Object ProcessId, Name, CommandLine | Format-Table -AutoSize | Out-String | Write-Host
    }
    exit 0
}

Write-Host "⚠️  Worker not running" -ForegroundColor Yellow
if ($StartIfMissing) {
    Write-Host "↪️  Starting worker in detached mode..." -ForegroundColor Yellow
    try {
        & $startScript -Detached -KillExisting -IntervalSeconds $WorkerIntervalSeconds | Out-Host
        Write-Host "✅ Started worker (detached)" -ForegroundColor Green
        exit 0
    }
    catch {
        Write-Host "❌ Failed to start worker: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}
else {
    exit 1
}