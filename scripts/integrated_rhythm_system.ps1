# Integrated Rhythm System - Master Orchestrator
# Phase 1 + Phase 2 + Phase 3 통합 시스템
# 모든 리듬을 하나의 심장박동으로 조정

param(
    [int]$CheckIntervalSeconds = 5,
    [string]$ConfigFile = "C:\workspace\agi\outputs\rhythm_config.json",
    [string]$DashboardFile = "C:\workspace\agi\outputs\rhythm_dashboard.json"
)

$ErrorActionPreference = "Continue"

# === Master Configuration ===
$RhythmConfig = @{
    version = "3.0"
    name = "AGI Integrated Rhythm System"
    status = "RUNNING"
    phases = @{
        phase1 = @{
            name = "Master Scheduler"
            status = "ACTIVE"
            purpose = "Task Orchestration"
            script = "create_master_scheduler.ps1"
        }
        phase2 = @{
            name = "Adaptive Scheduler"
            status = "ACTIVE"
            purpose = "Dynamic Optimization"
            script = "adaptive_master_scheduler.ps1"
        }
        phase3 = @{
            name = "Event Detector"
            status = "STANDBY"
            purpose = "Intelligence & Self-Healing"
            script = "event_detector.ps1"
        }
    }
    heartbeat = @{
        master_check = 60
        adaptive_check = 10
        event_check = 5
    }
}

# === Logging ===
function Write-RhythmLog {
    param(
        [string]$Message,
        [string]$Level = "INFO",
        [string]$Component = "ORCHESTRATOR"
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff"
    $logLine = "[$timestamp] [$Component] [$Level] $Message"

    Write-Host $logLine -ForegroundColor $(
        if ($Level -eq "ERROR") { "Red" }
        elseif ($Level -eq "WARN") { "Yellow" }
        elseif ($Level -eq "CRITICAL") { "Magenta" }
        else { "Green" }
    )

    Add-Content -Path "C:\workspace\agi\outputs\rhythm_orchestrator.log" -Value $logLine
}

# === System Health Check ===
function Get-RhythmHealth {
    $os = Get-CimInstance Win32_OperatingSystem
    $cpu = Get-CimInstance Win32_Processor | Select-Object -First 1

    $memUsage = [math]::Round((($os.TotalVisibleMemorySize - $os.FreePhysicalMemory) / $os.TotalVisibleMemorySize) * 100, 1)
    $cpuLoad = if ($null -ne $cpu.LoadPercentage) { [int]$cpu.LoadPercentage } else { 0 }

    # Check if Master Scheduler is running
    $masterLog = if (Test-Path "C:\workspace\agi\outputs\master_scheduler.log") {
        @(Get-Content "C:\workspace\agi\outputs\master_scheduler.log" -ErrorAction SilentlyContinue)[-1]
    } else { $null }

    # Check if Adaptive Scheduler is running
    $adaptiveLog = if (Test-Path "C:\workspace\agi\outputs\adaptive_scheduler.log") {
        @(Get-Content "C:\workspace\agi\outputs\adaptive_scheduler.log" -ErrorAction SilentlyContinue)[-1]
    } else { $null }

    return @{
        timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        system = @{
            cpu_load = $cpuLoad
            memory_usage = $memUsage
            python_processes = @(Get-Process | Where-Object { $_.ProcessName -like '*python*' }).Count
        }
        schedulers = @{
            master_active = if ($masterLog) { $true } else { $false }
            adaptive_active = if ($adaptiveLog) { $true } else { $false }
            event_detector_ready = (Test-Path "C:\workspace\agi\scripts\event_detector.ps1")
        }
        health_score = [math]::Round(
            (100 - [Math]::Max($cpuLoad, 0)) * 0.4 +
            (100 - [Math]::Max($memUsage, 0)) * 0.4 +
            (if (Get-ScheduledTask -TaskName "AGI_Master_Scheduler" -ErrorAction SilentlyContinue) { 30 } else { 0 }) * 0.2,
            1
        )
    }
}

# === Rhythm Heartbeat ===
function Start-RhythmHeartbeat {
    Write-Host "`n" -NoNewline
    Write-Host ("=" * 80) -ForegroundColor Cyan
    Write-Host "  🎵 INTEGRATED RHYTHM SYSTEM v3.0 - Master Orchestrator" -ForegroundColor Yellow
    Write-Host ("=" * 80) -ForegroundColor Cyan
    Write-Host ""

    Write-RhythmLog "Rhythm System Activated" "INFO" "HEARTBEAT"
    Write-RhythmLog "Phase 1 (Master) + Phase 2 (Adaptive) + Phase 3 (Intelligence)" "INFO" "HEARTBEAT"

    $cycleCount = 0

    while ($true) {
        $cycleCount++
        $now = Get-Date

        try {
            # Get system health
            $health = Get-RhythmHealth

            # Display rhythmic heartbeat
            $heartbeatChar = switch ($cycleCount % 2) { 0 { "♥" } default { "♡" } }
            $healthColor = switch ($true) {
                ($health.health_score -gt 80) { "Green" }
                ($health.health_score -gt 60) { "Cyan" }
                default { "Yellow" }
            }

            Write-Host "[$($heartbeatChar)] Cycle $cycleCount | Health: $($health.health_score)% | CPU: $($health.system.cpu_load)% | Memory: $($health.system.memory_usage)% | Processes: $($health.system.python_processes)" -ForegroundColor $healthColor

            # Check scheduler status
            $masterMark = "❌ Master"
            if ($health.schedulers.master_active) { $masterMark = "✅ Master" }

            $adaptiveMark = "❌ Adaptive"
            if ($health.schedulers.adaptive_active) { $adaptiveMark = "✅ Adaptive" }

            $eventMark = "⚫ EventDet"
            if ($health.schedulers.event_detector_ready) { $eventMark = "🟡 EventDet(Ready)" }

            Write-Host "  Status: $masterMark | $adaptiveMark | $eventMark" -ForegroundColor Gray

            # Save health dashboard
            $dashboard = @{
                timestamp = $health.timestamp
                cycle = $cycleCount
                health_score = $health.health_score
                system = $health.system
                schedulers = $health.schedulers
                phases = $RhythmConfig.phases
            }
            $dashboard | ConvertTo-Json | Set-Content -Path $DashboardFile -Force

            # Intelligence: Decide if Phase 3 should activate
            if ($health.health_score -lt 70 -and $health.schedulers.event_detector_ready) {
                Write-RhythmLog "Health score below 70 - Phase 3 activation recommended" "WARN" "INTELLIGENCE"
            }

            # Critical condition detection
            if ($health.system.cpu_load -gt 85) {
                Write-RhythmLog "CRITICAL: CPU load $($health.system.cpu_load)% - Emergency mode" "CRITICAL" "ALERT"
            }
            if ($health.system.memory_usage -gt 85) {
                Write-RhythmLog "CRITICAL: Memory usage $($health.system.memory_usage)% - Emergency cleanup needed" "CRITICAL" "ALERT"
            }

        } catch {
            Write-RhythmLog "Heartbeat error: $_" "ERROR" "ORCHESTRATOR"
        }

        Start-Sleep -Seconds $CheckIntervalSeconds
    }
}

# === Display System Banner ===
function Show-RhythmBanner {
    Write-Host ""
    Write-Host "  🎵 RHYTHM-BASED AUTOMATION SYSTEM 🎵" -ForegroundColor Magenta
    Write-Host ""
    Write-Host "  Evolution of Orchestration:" -ForegroundColor Cyan
    Write-Host "    Phase 1: Master Scheduler     (정적 리듬 - 메트로놈)" -ForegroundColor Green
    Write-Host "    Phase 2: Adaptive Scheduler   (동적 리듬 - 호흡)" -ForegroundColor Cyan
    Write-Host "    Phase 3: Event Detector      (지능형 리듬 - 생명)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Current Status: Phase 1 + Phase 2 ACTIVE | Phase 3 STANDBY" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Performance Targets:" -ForegroundColor Cyan
    Write-Host "    CPU:     < 35% (current: monitoring)" -ForegroundColor Gray
    Write-Host "    Memory:  < 45% (current: monitoring)" -ForegroundColor Gray
    Write-Host "    Health:  > 80% (target score)" -ForegroundColor Gray
    Write-Host ""
}

# === Main Entry Point ===
Show-RhythmBanner

Write-RhythmLog "Configuration: $($RhythmConfig | ConvertTo-Json -Compress)" "INFO" "INIT"

# Start heartbeat
Start-RhythmHeartbeat
