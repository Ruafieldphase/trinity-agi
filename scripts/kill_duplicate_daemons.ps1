#Requires -Version 5.1
<#
.SYNOPSIS
    중복 실행 중인 데몬 프로세스를 정리합니다.
#>

param(
    [switch]$DryRun
)

$ErrorActionPreference = "Continue"

function Kill-DuplicateProcesses {
    param(
        [string]$ScriptPattern,
        [string]$DisplayName,
        [int]$KeepCount = 1
    )
    
    $procs = Get-CimInstance Win32_Process | Where-Object { 
        $_.CommandLine -and $_.CommandLine -like "*$ScriptPattern*" 
    } | Sort-Object CreationDate -Descending
    
    if (-not $procs) {
        Write-Host "  ℹ️  $DisplayName : Not running" -ForegroundColor Gray
        return
    }
    
    $total = ($procs | Measure-Object).Count
    if ($total -le $KeepCount) {
        Write-Host "  ✅ $DisplayName : $total running (OK)" -ForegroundColor Green
        return
    }
    
    $keep = $procs | Select-Object -First $KeepCount
    $kill = $procs | Select-Object -Skip $KeepCount
    
    Write-Host "  ⚠️  $DisplayName : $total running (keeping $KeepCount, killing $($kill.Count))" -ForegroundColor Yellow
    
    if (-not $DryRun) {
        foreach ($p in $kill) {
            try {
                Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop
                Write-Host "    🗑️  Killed PID $($p.ProcessId)" -ForegroundColor Gray
            }
            catch {
                Write-Host "    ❌ Failed to kill PID $($p.ProcessId)" -ForegroundColor Red
            }
        }
    }
    else {
        foreach ($p in $kill) {
            Write-Host "    [DRY-RUN] Would kill PID $($p.ProcessId)" -ForegroundColor Gray
        }
    }
}

Write-Host "`n=== 🧹 Cleaning Duplicate Daemons ===" -ForegroundColor Cyan
Write-Host ""

if ($DryRun) {
    Write-Host "🔍 DRY-RUN MODE (no actual changes)" -ForegroundColor Yellow
    Write-Host ""
}

# Clean duplicates
Kill-DuplicateProcesses -ScriptPattern "monitoring_daemon.py" -DisplayName "Monitoring Daemon" -KeepCount 0
Kill-DuplicateProcesses -ScriptPattern "task_watchdog.py" -DisplayName "Task Watchdog" -KeepCount 1
Kill-DuplicateProcesses -ScriptPattern "rpa_worker.py" -DisplayName "RPA Worker" -KeepCount 1

Write-Host ""
Write-Host "=== 📊 Summary ===" -ForegroundColor Cyan
Write-Host ""

$remaining = Get-Process python* -ErrorAction SilentlyContinue
Write-Host "Python processes remaining: $($remaining.Count)" -ForegroundColor $(if ($remaining.Count -le 5) { 'Green' } else { 'Yellow' })

Write-Host ""