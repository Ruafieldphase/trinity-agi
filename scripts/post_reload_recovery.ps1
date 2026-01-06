#Requires -Version 5.1
<#
.SYNOPSIS
    VS Code 재실행 후 필수 서비스를 자동으로 복구합니다.

.DESCRIPTION
    최적화 완료 후 VS Code 재실행 시 필요한 모든 서비스를 자동으로 시작합니다.
    - Task Queue Server (8091)
    - RPA Worker
    - Task Watchdog
    
    중복 실행 방지: 이미 실행 중인 프로세스는 스킵하고 중복은 자동 정리합니다.

.NOTES
    Author: AGI System
    Date: 2025-11-03
#>

param(
    [switch]$Silent,
    [switch]$SkipHealthCheck,
    [switch]$Force
)

$ErrorActionPreference = "Continue"
$workspaceRoot = Split-Path -Parent $PSScriptRoot

# 중복 실행 방지: Lock 파일 체크
$lockFile = Join-Path $workspaceRoot "outputs\.recovery_lock"
if ((Test-Path $lockFile) -and -not $Force) {
    $lockAge = (Get-Date) - (Get-Item $lockFile).LastWriteTime
    if ($lockAge.TotalSeconds -lt 10) {
        if (-not $Silent) {
            Write-Host "⏭️  Recovery already running (lock age: $([math]::Round($lockAge.TotalSeconds, 1))s)" -ForegroundColor Yellow
        }
        exit 0
    }
}

# Lock 파일 생성
New-Item -Path $lockFile -ItemType File -Force | Out-Null

function Write-Status {
    param([string]$Message, [string]$Color = "Cyan")
    if (-not $Silent) {
        Write-Host $Message -ForegroundColor $Color
    }
}

function Test-ServerRunning {
    param([int]$Port)
    try {
        $null = Invoke-WebRequest -Uri "http://127.0.0.1:${Port}/api/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
        return $true
    }
    catch {
        return $false
    }
}

function Start-ServiceWithRetry {
    param(
        [string]$ServiceName,
        [scriptblock]$StartAction,
        [scriptblock]$HealthCheck,
        [int]$MaxRetries = 3
    )
    
    Write-Status "🔄 Starting: $ServiceName" "Yellow"
    
    for ($i = 1; $i -le $MaxRetries; $i++) {
        try {
            & $StartAction
            Start-Sleep -Seconds 2
            
            if (& $HealthCheck) {
                Write-Status "  ✅ ${ServiceName}: ONLINE" "Green"
                return $true
            }
        }
        catch {
            Write-Status "  ⚠️  Retry $i/$MaxRetries..." "Yellow"
        }
    }
    
    Write-Status "  ❌ ${ServiceName}: FAILED" "Red"
    return $false
}

# Main Recovery Process
Write-Status "`n=== 🔄 Post-Reload Recovery Starting ===" "Cyan"
Write-Status ""

$results = @{
    TaskQueueServer = $false
    RPAWorker       = $false
    TaskWatchdog    = $false
    CoreProbe      = $false
}

# 1. Task Queue Server
Write-Status "1. Task Queue Server (8091)" "White"
if (Test-ServerRunning -Port 8091) {
    Write-Status "  ✅ Already running" "Green"
    $results.TaskQueueServer = $true
}
else {
    $results.TaskQueueServer = Start-ServiceWithRetry `
        -ServiceName "Task Queue Server" `
        -StartAction {
        & "$workspaceRoot\scripts\ensure_task_queue_server.ps1" -Port 8091 -ErrorAction SilentlyContinue | Out-Null
    } `
        -HealthCheck { Test-ServerRunning -Port 8091 }
}

Start-Sleep -Seconds 1

# 2. RPA Worker
Write-Status "`n2. RPA Worker" "White"
$existingWorkers = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -and $_.CommandLine -like '*rpa_worker.py*' }

# 중복 제거: 최신 1개만 유지
if ($existingWorkers -and $existingWorkers.Count -gt 1) {
    $sorted = $existingWorkers | Sort-Object CreationDate -Descending
    $keep = $sorted | Select-Object -First 1
    $kill = $sorted | Select-Object -Skip 1
    Write-Status "  🧹 Cleaning duplicates: keeping PID $($keep.ProcessId), killing $($kill.Count)" "Yellow"
    foreach ($p in $kill) {
        try { Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop } catch {}
    }
    $existingWorkers = @($keep)
}

if ($existingWorkers -and $existingWorkers.Count -eq 1) {
    Write-Status "  ✅ Already running (PID $($existingWorkers[0].ProcessId))" "Green"
    $results.RPAWorker = $true
}
else {
    $results.RPAWorker = Start-ServiceWithRetry `
        -ServiceName "RPA Worker" `
        -StartAction {
        & "$workspaceRoot\scripts\ensure_rpa_worker.ps1" -ErrorAction SilentlyContinue | Out-Null
    } `
        -HealthCheck {
        $workers = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -and $_.CommandLine -like '*rpa_worker.py*' }
        return ($null -ne $workers -and $workers.Count -gt 0)
    }
}

Start-Sleep -Seconds 1

# 3. Task Watchdog
Write-Status "`n3. Task Watchdog (Background)" "White"
$existingWatchdog = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -and $_.CommandLine -like '*task_watchdog.py*' }

# 중복 제거: 최신 1개만 유지
if ($existingWatchdog -and $existingWatchdog.Count -gt 1) {
    $sorted = $existingWatchdog | Sort-Object CreationDate -Descending
    $keep = $sorted | Select-Object -First 1
    $kill = $sorted | Select-Object -Skip 1
    Write-Status "  🧹 Cleaning duplicates: keeping PID $($keep.ProcessId), killing $($kill.Count)" "Yellow"
    foreach ($p in $kill) {
        try { Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop } catch {}
    }
    $existingWatchdog = @($keep)
}

if ($existingWatchdog -and $existingWatchdog.Count -eq 1) {
    Write-Status "  ✅ Already running (PID $($existingWatchdog[0].ProcessId))" "Green"
    $results.TaskWatchdog = $true
}
else {
    $results.TaskWatchdog = Start-ServiceWithRetry `
        -ServiceName "Task Watchdog" `
        -StartAction {
        $py = "$workspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe"
        if (!(Test-Path -LiteralPath $py)) { $py = "python" }
        Start-Process -FilePath $py -ArgumentList "$workspaceRoot\fdo_agi_repo\scripts\task_watchdog.py --server http://127.0.0.1:8091 --interval 60 --auto-recover" -WindowStyle Hidden -ErrorAction SilentlyContinue | Out-Null
    } `
        -HealthCheck {
        $watchdog = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -and $_.CommandLine -like '*task_watchdog.py*' }
        return ($null -ne $watchdog -and $watchdog.Count -gt 0)
    }
}

Start-Sleep -Seconds 1

# 4. Core Health Probe (if not skipped)
if (-not $SkipHealthCheck) {
    Write-Status "`n4. Core Health Probe" "White"
    try {
        & "$workspaceRoot\scripts\core_quick_probe.ps1" -ErrorAction SilentlyContinue | Out-Null
        $results.CoreProbe = $true
        Write-Status "  ✅ Health check completed" "Green"
    }
    catch {
        Write-Status "  ⚠️  Health check skipped" "Yellow"
        $results.CoreProbe = $false
    }
}

# Summary
Write-Status "`n=== 📊 Recovery Summary ===" "Cyan"
Write-Status ""

$successCount = ($results.Values | Where-Object { $_ -eq $true }).Count
$totalCount = $results.Count

Write-Status "Results: $successCount/$totalCount services started" "White"
Write-Status ""

# Python 프로세스 개수 체크
$pyProcs = Get-Process python* -ErrorAction SilentlyContinue
Write-Status "Python processes: $($pyProcs.Count)" $(if ($pyProcs.Count -le 5) { "Green" } else { "Yellow" })
Write-Status ""

# Lock 파일 제거
Remove-Item -Path $lockFile -Force -ErrorAction SilentlyContinue

foreach ($service in $results.Keys) {
    $status = if ($results[$service]) { "✅ OK" } else { "❌ FAILED" }
    $color = if ($results[$service]) { "Green" } else { "Red" }
    Write-Status "  $status - $service" $color
}

Write-Status ""

if ($successCount -eq $totalCount) {
    Write-Status "🎉 All services recovered successfully!" "Green"
    exit 0
}
elseif ($successCount -ge ($totalCount * 0.75)) {
    Write-Status "⚠️  Most services recovered (some failed)" "Yellow"
    exit 0
}
else {
    Write-Status "❌ Recovery failed - manual intervention needed" "Red"
    exit 1
}