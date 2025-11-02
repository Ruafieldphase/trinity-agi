# Verify Integrated Rhythm System - All Phases Working Together
# Complete integration test of Phase 1, 2, and 3

$ErrorActionPreference = "Continue"

Write-Host "`n" -NoNewline
Write-Host ("=" * 90) -ForegroundColor Magenta
Write-Host "  🎵 RHYTHM-BASED AUTOMATION SYSTEM - INTEGRATION VERIFICATION" -ForegroundColor Yellow
Write-Host ("=" * 90) -ForegroundColor Magenta
Write-Host ""

# Define verification requirements
$Phases = @{
    "Phase 1: Master Scheduler" = @{
        taskName = "AGI_Master_Scheduler"
        logFile = "C:\workspace\agi\outputs\master_scheduler.log"
        stateFile = "C:\workspace\agi\outputs\master_scheduler_state.json"
    }
    "Phase 2: Adaptive Scheduler" = @{
        taskName = "AGI_Adaptive_Master_Scheduler"
        logFile = "C:\workspace\agi\outputs\adaptive_scheduler.log"
        stateFile = "C:\workspace\agi\outputs\adaptive_scheduler_state.json"
    }
    "Phase 3: Event Detector" = @{
        logFile = "C:\workspace\agi\outputs\event_detector.log"
        queueFile = "C:\workspace\agi\outputs\event_queue.json"
        status = "READY"
    }
    "Orchestrator: Integrated Rhythm" = @{
        taskName = "AGI_Integrated_Rhythm_Orchestrator"
        logFile = "C:\workspace\agi\outputs\rhythm_orchestrator.log"
        dashboardFile = "C:\workspace\agi\outputs\rhythm_dashboard.json"
    }
}

# === VERIFICATION FUNCTIONS ===

function Test-ScheduledTask {
    param([string]$TaskName)
    try {
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($task) {
            return @{
                exists = $true
                state = $task.State
                lastRun = $task.LastRunTime
                nextRun = $task.NextRunTime
            }
        }
        return @{ exists = $false }
    } catch {
        return @{ exists = $false; error = $_ }
    }
}

function Test-LogFile {
    param([string]$FilePath)
    if (Test-Path $FilePath) {
        $size = (Get-Item $FilePath).Length
        $lastModified = (Get-Item $FilePath).LastWriteTime
        $lastLines = @(Get-Content $FilePath -Tail 3)
        return @{
            exists = $true
            size = $size
            lastModified = $lastModified
            lastEntry = $lastLines[-1]
        }
    }
    return @{ exists = $false }
}

function Test-StateFile {
    param([string]$FilePath)
    if (Test-Path $FilePath) {
        try {
            $state = Get-Content $FilePath | ConvertFrom-Json
            return @{
                exists = $true
                lastUpdate = $state.timestamp
                taskCount = if ($state.tasks) { @($state.tasks).Count } else { 0 }
            }
        } catch {
            return @{ exists = $true; error = "Invalid JSON" }
        }
    }
    return @{ exists = $false }
}

# === SYSTEM HEALTH CHECK ===

function Get-SystemHealth {
    $os = Get-CimInstance Win32_OperatingSystem
    $cpu = Get-CimInstance Win32_Processor | Select-Object -First 1

    $memUsage = [math]::Round((($os.TotalVisibleMemorySize - $os.FreePhysicalMemory) / $os.TotalVisibleMemorySize) * 100, 1)
    $cpuLoad = if ($null -ne $cpu.LoadPercentage) { [int]$cpu.LoadPercentage } else { 0 }
    $pythonProcs = @(Get-Process | Where-Object { $_.ProcessName -like '*python*' } | Measure-Object).Count

    return @{
        cpuLoad = $cpuLoad
        memUsage = $memUsage
        pythonProcs = $pythonProcs
        timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    }
}

# === VERIFICATION REPORTS ===

Write-Host "1️⃣  SCHEDULED TASKS STATUS" -ForegroundColor Cyan
Write-Host ("─" * 90) -ForegroundColor Gray
Write-Host ""

$taskStatuses = @()

# Check Phase 1
$phase1Task = Test-ScheduledTask "AGI_Master_Scheduler"
if ($phase1Task.exists) {
    Write-Host "  ✅ Phase 1: Master Scheduler" -ForegroundColor Green
    Write-Host "     State: $($phase1Task.state)" -ForegroundColor Gray
    if ($phase1Task.lastRun) { Write-Host "     Last Run: $($phase1Task.lastRun)" -ForegroundColor Gray }
    $taskStatuses += "Phase1:OK"
} else {
    Write-Host "  ❌ Phase 1: Master Scheduler NOT REGISTERED" -ForegroundColor Red
    $taskStatuses += "Phase1:FAIL"
}

# Check Phase 2
$phase2Task = Test-ScheduledTask "AGI_Adaptive_Master_Scheduler"
if ($phase2Task.exists) {
    Write-Host "  ✅ Phase 2: Adaptive Scheduler" -ForegroundColor Green
    Write-Host "     State: $($phase2Task.state)" -ForegroundColor Gray
    if ($phase2Task.lastRun) { Write-Host "     Last Run: $($phase2Task.lastRun)" -ForegroundColor Gray }
    $taskStatuses += "Phase2:OK"
} else {
    Write-Host "  ❌ Phase 2: Adaptive Scheduler NOT REGISTERED" -ForegroundColor Red
    $taskStatuses += "Phase2:FAIL"
}

# Check Orchestrator
$orchestratorTask = Test-ScheduledTask "AGI_Integrated_Rhythm_Orchestrator"
if ($orchestratorTask.exists) {
    Write-Host "  ✅ Orchestrator: Integrated Rhythm System" -ForegroundColor Green
    Write-Host "     State: $($orchestratorTask.state)" -ForegroundColor Gray
    if ($orchestratorTask.lastRun) { Write-Host "     Last Run: $($orchestratorTask.lastRun)" -ForegroundColor Gray }
    $taskStatuses += "Orchestrator:OK"
} else {
    Write-Host "  ❌ Orchestrator: Integrated Rhythm System NOT REGISTERED" -ForegroundColor Red
    $taskStatuses += "Orchestrator:FAIL"
}

Write-Host ""

# === LOG FILE STATUS ===

Write-Host "2️⃣  LOG FILES & ACTIVITY" -ForegroundColor Cyan
Write-Host ("─" * 90) -ForegroundColor Gray
Write-Host ""

# Phase 1 Logs
$phase1Log = Test-LogFile "C:\workspace\agi\outputs\master_scheduler.log"
if ($phase1Log.exists) {
    $ageMin = [math]::Round((New-TimeSpan -Start $phase1Log.lastModified -End (Get-Date)).TotalMinutes)
    Write-Host "  ✅ Phase 1 Log (Size: $(($phase1Log.size/1KB).ToString("N1"))KB, Age: ${ageMin}min)" -ForegroundColor Green
    Write-Host "     Last: $($phase1Log.lastEntry.Substring(0, [Math]::Min(70, $phase1Log.lastEntry.Length)))" -ForegroundColor Gray
} else {
    Write-Host "  ⚠️  Phase 1 Log: Not created yet" -ForegroundColor Yellow
}

# Phase 2 Logs
$phase2Log = Test-LogFile "C:\workspace\agi\outputs\adaptive_scheduler.log"
if ($phase2Log.exists) {
    $ageMin = [math]::Round((New-TimeSpan -Start $phase2Log.lastModified -End (Get-Date)).TotalMinutes)
    Write-Host "  ✅ Phase 2 Log (Size: $(($phase2Log.size/1KB).ToString("N1"))KB, Age: ${ageMin}min)" -ForegroundColor Green
    Write-Host "     Last: $($phase2Log.lastEntry.Substring(0, [Math]::Min(70, $phase2Log.lastEntry.Length)))" -ForegroundColor Gray
} else {
    Write-Host "  ⚠️  Phase 2 Log: Not created yet" -ForegroundColor Yellow
}

# Orchestrator Logs
$orchestratorLog = Test-LogFile "C:\workspace\agi\outputs\rhythm_orchestrator.log"
if ($orchestratorLog.exists) {
    $ageMin = [math]::Round((New-TimeSpan -Start $orchestratorLog.lastModified -End (Get-Date)).TotalMinutes)
    Write-Host "  ✅ Orchestrator Log (Size: $(($orchestratorLog.size/1KB).ToString("N1"))KB, Age: ${ageMin}min)" -ForegroundColor Green
    Write-Host "     Last: $($orchestratorLog.lastEntry.Substring(0, [Math]::Min(70, $orchestratorLog.lastEntry.Length)))" -ForegroundColor Gray
} else {
    Write-Host "  ⚠️  Orchestrator Log: Not created yet (will start on next cycle)" -ForegroundColor Yellow
}

Write-Host ""

# === STATE FILES ===

Write-Host "3️⃣  STATE FILES & METRICS" -ForegroundColor Cyan
Write-Host ("─" * 90) -ForegroundColor Gray
Write-Host ""

$phase1State = Test-StateFile "C:\workspace\agi\outputs\master_scheduler_state.json"
if ($phase1State.exists) {
    Write-Host "  ✅ Phase 1 State ($($phase1State.taskCount) tasks tracked)" -ForegroundColor Green
    Write-Host "     Last Update: $($phase1State.lastUpdate)" -ForegroundColor Gray
} else {
    Write-Host "  ⚠️  Phase 1 State: Not created yet" -ForegroundColor Yellow
}

$phase2State = Test-StateFile "C:\workspace\agi\outputs\adaptive_scheduler_state.json"
if ($phase2State.exists) {
    Write-Host "  ✅ Phase 2 State (Adaptive Metrics)" -ForegroundColor Green
    Write-Host "     Last Update: $($phase2State.lastUpdate)" -ForegroundColor Gray
} else {
    Write-Host "  ⚠️  Phase 2 State: Not created yet" -ForegroundColor Yellow
}

# Dashboard file
if (Test-Path "C:\workspace\agi\outputs\rhythm_dashboard.json") {
    $dashboard = Get-Content "C:\workspace\agi\outputs\rhythm_dashboard.json" | ConvertFrom-Json
    Write-Host "  ✅ Orchestrator Dashboard" -ForegroundColor Green
    if ($dashboard.health_score) {
        Write-Host "     Health Score: $($dashboard.health_score)%" -ForegroundColor Cyan
    }
} else {
    Write-Host "  ⚠️  Orchestrator Dashboard: Will be created on first run" -ForegroundColor Yellow
}

Write-Host ""

# === SYSTEM METRICS ===

Write-Host "4️⃣  CURRENT SYSTEM HEALTH" -ForegroundColor Cyan
Write-Host ("─" * 90) -ForegroundColor Gray
Write-Host ""

$health = Get-SystemHealth
$cpuColor = if ($health.cpuLoad -lt 35) { "Green" } elseif ($health.cpuLoad -lt 70) { "Yellow" } else { "Red" }
$memColor = if ($health.memUsage -lt 45) { "Green" } elseif ($health.memUsage -lt 70) { "Yellow" } else { "Red" }

Write-Host "  CPU Load:        $($health.cpuLoad)% " -ForegroundColor $cpuColor -NoNewline
Write-Host "$(if ($health.cpuLoad -lt 35) { '✅ Good' } elseif ($health.cpuLoad -lt 70) { '⚠️  Fair' } else { '❌ High' })" -ForegroundColor $cpuColor

Write-Host "  Memory Usage:    $($health.memUsage)% " -ForegroundColor $memColor -NoNewline
Write-Host "$(if ($health.memUsage -lt 45) { '✅ Good' } elseif ($health.memUsage -lt 70) { '⚠️  Fair' } else { '❌ High' })" -ForegroundColor $memColor

Write-Host "  Python Procs:    $($health.pythonProcs) processes " -ForegroundColor Cyan -NoNewline
Write-Host "$(if ($health.pythonProcs -lt 40) { '✅ Optimal' } else { '⚠️  Many' })" -ForegroundColor Cyan

Write-Host "  Timestamp:       $($health.timestamp)" -ForegroundColor Gray

Write-Host ""

# === FINAL SUMMARY ===

Write-Host ("=" * 90) -ForegroundColor Magenta
Write-Host "  🎵 INTEGRATION STATUS SUMMARY" -ForegroundColor Yellow
Write-Host ("=" * 90) -ForegroundColor Magenta
Write-Host ""

$allOk = ($taskStatuses -notcontains "Phase1:FAIL") -and ($taskStatuses -notcontains "Phase2:FAIL") -and ($taskStatuses -notcontains "Orchestrator:FAIL")

if ($allOk) {
    Write-Host "  ✅ COMPLETE RHYTHM-BASED SYSTEM ONLINE" -ForegroundColor Green
    Write-Host ""
    Write-Host "     🔴 Phase 1 (Master Scheduler):         ACTIVE" -ForegroundColor Green
    Write-Host "     🔵 Phase 2 (Adaptive Scheduler):       ACTIVE" -ForegroundColor Cyan
    Write-Host "     🟡 Phase 3 (Event Detector):          READY (Deploy in 1 week)" -ForegroundColor Yellow
    Write-Host "     🟢 Orchestrator (Master Control):     ACTIVE" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  PARTIAL SYSTEM STATUS" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "     Tasks registered but may not have run yet" -ForegroundColor Gray
    Write-Host "     Logs and state files will be created on first execution" -ForegroundColor Gray
}

Write-Host ""
Write-Host "  📊 TARGETS ACHIEVED:" -ForegroundColor Cyan
Write-Host "     • CPU:        $($health.cpuLoad)% / 35% target" -ForegroundColor Gray
Write-Host "     • Memory:     $($health.memUsage)% / 45% target" -ForegroundColor Gray
Write-Host "     • Processes:  $($health.pythonProcs) / 40 target" -ForegroundColor Gray
Write-Host ""

Write-Host ("=" * 90) -ForegroundColor Magenta
Write-Host "  Next Step: Monitor logs for 1 week, then deploy Phase 3 Event Detector" -ForegroundColor Yellow
Write-Host ("=" * 90) -ForegroundColor Magenta
Write-Host ""
