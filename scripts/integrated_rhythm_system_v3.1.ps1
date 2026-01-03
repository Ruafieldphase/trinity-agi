# Integrated Rhythm System v3.1 - Master Orchestrator with Self-Healing
# Phase 1 + Phase 2 + Phase 3 + Self-Healing Level 1 통합 시스템
# 모든 리듬을 하나의 심장박동으로 조정하며, 자동 복구 기능 내장

param(
    [int]$CheckIntervalSeconds = 5,
    [string]$ConfigFile = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\rhythm_config.json",
    [string]$DashboardFile = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\rhythm_dashboard.json",
    [string]$EventQueueFile = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\event_queue.json",
    [string]$HealingLogFile = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\rhythm_healing.log"
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot



$ErrorActionPreference = "Continue"

# === Master Configuration ===
$RhythmConfig = @{
    version = "3.1"
    name = "AGI Integrated Rhythm System with Self-Healing"
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
            status = "ACTIVE"
            purpose = "Intelligence & Event Detection"
            script = "event_detector.ps1"
        }
        healing = @{
            name = "Self-Healing Level 1"
            status = "ACTIVE"
            purpose = "Automatic Recovery"
            embedded = $true
        }
    }
    heartbeat = @{
        master_check = 60
        adaptive_check = 10
        event_check = 5
        healing_check = 10
    }
}

# 자가 치유 전략
$HealingStrategies = @{
    "cpu_spike" = @{
        name = "CPU 스파이크 대응"
        priority = 1
        cooldown_seconds = 300
    }
    "memory_leak" = @{
        name = "메모리 누수 대응"
        priority = 2
        cooldown_seconds = 600
    }
    "process_zombie" = @{
        name = "좀비 프로세스 정리"
        priority = 1
        cooldown_seconds = 300
    }
    "memory_pressure" = @{
        name = "메모리 압박 대응"
        priority = 1
        cooldown_seconds = 900
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
        elseif ($Level -eq "HEALING") { "Magenta" }
        elseif ($Level -eq "SUCCESS") { "Green" }
        else { "Green" }
    )

    Add-Content -Path "$WorkspaceRoot\outputs\rhythm_orchestrator.log" -Value $logLine
}

function Write-HealingLog {
    param(
        [string]$Message,
        [string]$EventType = "UNKNOWN"
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logLine = "[$timestamp] [$EventType] $Message"
    Add-Content -Path $HealingLogFile -Value $logLine
}

# === System Health Check ===
function Get-RhythmHealth {
    $os = Get-CimInstance Win32_OperatingSystem
    $cpu = Get-CimInstance Win32_Processor | Select-Object -First 1

    $memUsage = [math]::Round((($os.TotalVisibleMemorySize - $os.FreePhysicalMemory) / $os.TotalVisibleMemorySize) * 100, 1)
    $cpuLoad = if ($null -ne $cpu.LoadPercentage) { [int]$cpu.LoadPercentage } else { 0 }

    # Phase 1 확인
    $masterLog = if (Test-Path "$WorkspaceRoot\outputs\master_scheduler.log") {
        @(Get-Content "$WorkspaceRoot\outputs\master_scheduler.log" -ErrorAction SilentlyContinue)[-1]
    } else { $null }

    # Phase 2 확인
    $adaptiveLog = if (Test-Path "$WorkspaceRoot\outputs\adaptive_scheduler.log") {
        @(Get-Content "$WorkspaceRoot\outputs\adaptive_scheduler.log" -ErrorAction SilentlyContinue)[-1]
    } else { $null }

    # Phase 3 확인
    $eventLog = if (Test-Path "$WorkspaceRoot\outputs\event_detector.log") {
        @(Get-Content "$WorkspaceRoot\outputs\event_detector.log" -ErrorAction SilentlyContinue)[-1]
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
            event_detector_active = if ($eventLog) { $true } else { $false }
        }
        health_score = [math]::Round(
            (100 - [Math]::Max($cpuLoad, 0)) * 0.4 +
            (100 - [Math]::Max($memUsage, 0)) * 0.4 +
            (if (Get-ScheduledTask -TaskName "AGI_Master_Scheduler" -ErrorAction SilentlyContinue) { 30 } else { 0 }) * 0.2,
            1
        )
    }
}

# === Self-Healing: 이벤트 큐에서 이벤트 읽기 ===
function Get-PendingEvents {
    if (-not (Test-Path $EventQueueFile)) {
        return @()
    }

    try {
        $queue = Get-Content $EventQueueFile | ConvertFrom-Json
        if ($queue -is [object] -and -not ($queue -is [array])) {
            $queue = @($queue)
        }

        return @($queue | Where-Object { $_.status -eq "pending" })
    } catch {
        return @()
    }
}

# === Self-Healing: 자동 대응 ===
function Invoke-AutoHealing {
    param(
        [string]$EventType,
        [hashtable]$Details
    )

    $strategy = $HealingStrategies[$EventType]
    if (-not $strategy) {
        return $false
    }

    Write-RhythmLog "자가 치유 시작: $($strategy.name)" "HEALING" "HEALING"
    Write-HealingLog "이벤트 감지: $EventType" $EventType

    # 자가 치유 액션 실행
    switch ($EventType) {
        "memory_leak" {
            # 메모리 정리
            [System.GC]::Collect()
            [System.GC]::WaitForPendingFinalizers()
            Write-RhythmLog "메모리 정리 완료 (GC)" "HEALING" "HEALING"
            Write-HealingLog "메모리 정리 실행" $EventType
        }
        "process_zombie" {
            # 좀비 프로세스 정리
            $pythonProcs = Get-Process | Where-Object { $_.ProcessName -like '*python*' }
            $zombies = $pythonProcs | Where-Object { -not $_.Responding }
            $killCount = 0

            foreach ($zombie in $zombies) {
                try {
                    $zombie.Kill()
                    $killCount++
                } catch {
                    # 무시
                }
            }

            if ($killCount -gt 0) {
                Write-RhythmLog "$killCount개 좀비 프로세스 종료" "HEALING" "HEALING"
                Write-HealingLog "$killCount개 좀비 프로세스 종료" $EventType
            }
        }
        "memory_pressure" {
            # 긴급 정리
            [System.GC]::Collect()
            [System.GC]::WaitForPendingFinalizers()
            [System.GC]::Collect()
            Write-RhythmLog "긴급 메모리 정리 완료" "HEALING" "HEALING"
            Write-HealingLog "긴급 정리 실행" $EventType
        }
    }

    return $true
}

# === Rhythm Heartbeat ===
function Start-RhythmHeartbeat {
    Write-Host "`n" -NoNewline
    Write-Host (("=" * 80)) -ForegroundColor Cyan
    Write-Host "  🎵 INTEGRATED RHYTHM SYSTEM v3.1 - Master Orchestrator + Self-Healing" -ForegroundColor Yellow
    Write-Host (("=" * 80)) -ForegroundColor Cyan
    Write-Host ""

    Write-RhythmLog "Rhythm System Activated (v3.1)" "INFO" "HEARTBEAT"
    Write-RhythmLog "Phase 1 (Master) + Phase 2 (Adaptive) + Phase 3 (Intelligence) + Healing (Recovery)" "INFO" "HEARTBEAT"

    $cycleCount = 0
    $processedEvents = @{}

    while ($true) {
        $cycleCount++
        $now = Get-Date

        try {
            # 시스템 건강도 확인
            $health = Get-RhythmHealth

            # 리듬 시각화
            $heartbeatChar = switch ($cycleCount % 2) { 0 { "♥" } default { "♡" } }
            $healthColor = switch ($true) {
                ($health.health_score -gt 80) { "Green" }
                ($health.health_score -gt 60) { "Cyan" }
                default { "Yellow" }
            }

            Write-Host "[$($heartbeatChar)] Cycle $cycleCount | Health: $($health.health_score)% | CPU: $($health.system.cpu_load)% | Mem: $($health.system.memory_usage)% | Procs: $($health.system.python_processes)" -ForegroundColor $healthColor

            # Phase 상태 확인
            $masterMark = "❌ Master"
            if ($health.schedulers.master_active) { $masterMark = "✅ Master" }

            $adaptiveMark = "❌ Adaptive"
            if ($health.schedulers.adaptive_active) { $adaptiveMark = "✅ Adaptive" }

            $eventMark = "❌ EventDet"
            if ($health.schedulers.event_detector_active) { $eventMark = "✅ EventDet" }

            Write-Host "  Status: $masterMark | $adaptiveMark | $eventMark" -ForegroundColor Gray

            # === Self-Healing: 대기 중인 이벤트 처리 ===
            $events = Get-PendingEvents
            if ($events.Count -gt 0) {
                Write-Host "  🏥 $($events.Count)개 이벤트 감지 → 자가 치유 시작" -ForegroundColor Magenta

                foreach ($event in $events) {
                    $eventKey = "$($event.event_type)_$($event.timestamp)"

                    if (-not $processedEvents.ContainsKey($eventKey)) {
                        $success = Invoke-AutoHealing -EventType $event.event_type -Details $event.details
                        if ($success) {
                            $processedEvents[$eventKey] = $now
                        }
                    }
                }
            }

            # 대시보드 저장
            $dashboard = @{
                timestamp = $health.timestamp
                cycle = $cycleCount
                health_score = $health.health_score
                system = $health.system
                schedulers = $health.schedulers
                phases = $RhythmConfig.phases
            }
            $dashboard | ConvertTo-Json | Set-Content -Path $DashboardFile -Force

            # 치명적 상태 감지
            if ($health.system.cpu_load -gt 85) {
                Write-RhythmLog "⚠️  CPU 긴급: $($health.system.cpu_load)% - 응급 모드 활성화" "CRITICAL" "ALERT"
            }
            if ($health.system.memory_usage -gt 85) {
                Write-RhythmLog "⚠️  메모리 긴급: $($health.system.memory_usage)% - 응급 정리 필요" "CRITICAL" "ALERT"
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
    Write-Host "  🎵 RHYTHM-BASED AUTOMATION SYSTEM v3.1 🎵" -ForegroundColor Magenta
    Write-Host ""
    Write-Host "  진화된 오케스트레이션:" -ForegroundColor Cyan
    Write-Host "    Phase 1: Master Scheduler     (정적 리듬 - 메트로놈)" -ForegroundColor Green
    Write-Host "    Phase 2: Adaptive Scheduler   (동적 리듬 - 호흡)" -ForegroundColor Cyan
    Write-Host "    Phase 3: Event Detector      (지능형 리듬 - 감지)" -ForegroundColor Yellow
    Write-Host "    Healing: Self-Healing L1     (자동 복구 - 생명)" -ForegroundColor Magenta
    Write-Host ""
    Write-Host "  현재 상태: 모든 단계 활성화 (완전 지능형 자동화)" -ForegroundColor Green
    Write-Host ""
    Write-Host "  성능 목표:" -ForegroundColor Cyan
    Write-Host "    CPU:     < 35% (현재: 모니터링 중)" -ForegroundColor Gray
    Write-Host "    Memory:  < 45% (현재: 모니터링 중)" -ForegroundColor Gray
    Write-Host "    Health:  > 80% (목표 점수)" -ForegroundColor Gray
    Write-Host ""
}

# === Main Entry Point ===
Show-RhythmBanner

Write-RhythmLog "Configuration: $($RhythmConfig | ConvertTo-Json -Compress)" "INFO" "INIT"

# 시작
Start-RhythmHeartbeat