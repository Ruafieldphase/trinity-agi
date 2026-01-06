# Event Detector - Real-time System Event Detection
# Phase 3 Foundation: Detects anomalies and triggers intelligent responses

param(
    [int]$CheckIntervalSeconds = 10,
    [string]$LogFile = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\event_detector.log",
    [string]$EventQueueFile = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\event_queue.json"
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot



$ErrorActionPreference = "Continue"

# === Configuration ===
$EventThresholds = @{
    cpu_spike = 80              # CPU % threshold
    memory_leak = 75            # Memory % threshold
    high_latency = 500          # Latency in ms
    process_zombie = 30         # Seconds without response
    task_failure_rate = 0.05    # 5% failure rate
}

$EventPriority = @{
    critical = 1
    high = 2
    medium = 3
    low = 4
}

# === Event Types ===
$EventTypes = @{
    "cpu_spike" = @{
        priority = "high"
        description = "CPU usage exceeded threshold"
        action = "performance_analysis"
    }
    "memory_leak" = @{
        priority = "high"
        description = "Memory usage increasing continuously"
        action = "memory_cleanup"
    }
    "high_latency" = @{
        priority = "medium"
        description = "System latency increased"
        action = "optimization_check"
    }
    "process_zombie" = @{
        priority = "critical"
        description = "Zombie process detected"
        action = "process_cleanup"
    }
    "task_failure" = @{
        priority = "medium"
        description = "Task failure rate exceeded threshold"
        action = "task_recovery"
    }
    "circuit_breaker_open" = @{
        priority = "high"
        description = "Circuit breaker activated (fallback)"
        action = "activate_fallback"
    }
    "cascade_failure" = @{
        priority = "critical"
        description = "Multiple related tasks failing"
        action = "emergency_recovery"
    }
}

# === Logging ===
function Write-EventLog {
    param(
        [string]$EventType,
        [string]$Message,
        [string]$Priority = "info",
        [hashtable]$Details = @{}
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = @{
        timestamp = $timestamp
        event_type = $EventType
        priority = $Priority
        message = $Message
        details = $Details
    } | ConvertTo-Json

    Write-Host "[$timestamp] [$EventType] [$Priority] $Message" -ForegroundColor $(
        if ($Priority -eq "critical") { "Red" }
        elseif ($Priority -eq "high") { "Yellow" }
        elseif ($Priority -eq "medium") { "Cyan" }
        else { "Green" }
    )

    Add-Content -Path $LogFile -Value $logEntry
}

# === Metrics Collection ===
function Get-SystemMetrics {
    $os = Get-CimInstance Win32_OperatingSystem
    $cpu = Get-CimInstance Win32_Processor | Select-Object -First 1

    $memUsagePercent = [math]::Round((($os.TotalVisibleMemorySize - $os.FreePhysicalMemory) / $os.TotalVisibleMemorySize) * 100, 1)
    $cpuLoad = if ($null -ne $cpu.LoadPercentage) { [int]$cpu.LoadPercentage } else { 0 }

    $pythonProcs = @(Get-Process | Where-Object { $_.ProcessName -like '*python*' })
    $zombieProcs = $pythonProcs | Where-Object { $_.TotalProcessorTime.TotalSeconds -eq 0 -and $_.Responding -eq $false }

    return @{
        cpu_load = $cpuLoad
        memory_usage = $memUsagePercent
        python_process_count = $pythonProcs.Count
        zombie_process_count = $zombieProcs.Count
        timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    }
}

# === Event Detection ===
function Detect-Events {
    param([hashtable]$Metrics, [hashtable]$PreviousMetrics)

    $events = @()

    # 1. CPU Spike Detection
    if ($Metrics.cpu_load -gt $EventThresholds.cpu_spike) {
        $events += @{
            type = "cpu_spike"
            severity = "high"
            details = @{
                current = $Metrics.cpu_load
                threshold = $EventThresholds.cpu_spike
            }
        }
    }

    # 2. Memory Leak Detection
    if ($Metrics.memory_usage -gt $EventThresholds.memory_leak) {
        if ($PreviousMetrics -and $Metrics.memory_usage -gt $PreviousMetrics.memory_usage) {
            $events += @{
                type = "memory_leak"
                severity = "high"
                details = @{
                    current = $Metrics.memory_usage
                    previous = $PreviousMetrics.memory_usage
                    threshold = $EventThresholds.memory_leak
                    trend = "increasing"
                }
            }
        }
    }

    # 3. Process Zombie Detection
    if ($Metrics.zombie_process_count -gt 0) {
        $events += @{
            type = "process_zombie"
            severity = "critical"
            details = @{
                zombie_count = $Metrics.zombie_process_count
                total_processes = $Metrics.python_process_count
            }
        }
    }

    # 4. Memory Pressure
    if ($Metrics.memory_usage -gt 85) {
        $events += @{
            type = "memory_pressure"
            severity = "critical"
            details = @{
                memory_usage = $Metrics.memory_usage
                action = "emergency_cleanup"
            }
        }
    }

    return $events
}

# === Event Queue Management ===
function Queue-Event {
    param([hashtable]$Event)

    $queue = @()
    if (Test-Path $EventQueueFile) {
        $queue = Get-Content $EventQueueFile | ConvertFrom-Json -AsHashtable
        if ($queue -is [object] -and -not ($queue -is [array])) {
            $queue = @($queue)
        }
    }

    $queue += @{
        event_type = $Event.type
        severity = $Event.severity
        timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        details = $Event.details
        status = "pending"
    }

    # Keep last 100 events
    if ($queue.Count -gt 100) {
        $queue = $queue[-100..-1]
    }

    $queue | ConvertTo-Json | Set-Content -Path $EventQueueFile -Force
}

# === Main Loop ===
function Start-EventDetector {
    Write-Host "`n" -NoNewline
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host "  Event Detector - Real-time Anomaly Detection (Phase 3)" -ForegroundColor Yellow
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host ""

    Write-EventLog -EventType "detector" -Message "Event Detector Started" -Priority "info"

    $previousMetrics = $null
    $cycleCount = 0

    while ($true) {
        $cycleCount++
        $now = Get-Date

        try {
            # Collect metrics
            $metrics = Get-SystemMetrics

            # Detect events
            $events = Detect-Events -Metrics $metrics -PreviousMetrics $previousMetrics

            # Process detected events
            if ($events.Count -gt 0) {
                Write-Host "`n[Cycle $cycleCount @ $($now.ToString('HH:mm:ss'))] Detected $($events.Count) event(s)" -ForegroundColor Red

                foreach ($event in $events) {
                    $priority = $EventTypes[$event.type].priority ?? "unknown"

                    Write-EventLog -EventType $event.type -Message "Event detected" -Priority $priority -Details $event.details
                    Queue-Event -Event $event

                    Write-Host "  🔴 $($event.type): $(ConvertTo-Json $event.details -Compress)" -ForegroundColor Yellow
                }
            }

            # Show metrics summary
            $statusColor = if ($metrics.cpu_load -gt 70) { "Yellow" } else { "Green" }
            Write-Host "[Metrics] CPU: $($metrics.cpu_load)% | Memory: $($metrics.memory_usage)% | Processes: $($metrics.python_process_count)" -ForegroundColor $statusColor

            $previousMetrics = $metrics
        } catch {
            Write-EventLog -EventType "detector_error" -Message "Detection error: $_" -Priority "high"
        }

        Start-Sleep -Seconds $CheckIntervalSeconds
    }
}

# === Main Entry ===
Write-Host "Starting Event Detector..." -ForegroundColor Cyan
Start-EventDetector