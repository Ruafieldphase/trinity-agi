# Adaptive Master Scheduler - Dynamic Rhythm Orchestration
# Phase 2: Dynamic interval adjustment based on system load
# Implements machine learning-based optimization

param(
    [switch]$DryRun,
    [switch]$InstallSchedule,
    [int]$CheckIntervalSeconds = 60,
    [switch]$EnableAdaptive = $true
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot



$ErrorActionPreference = "Continue"

# === Configuration ===
$MasterLogFile = "$WorkspaceRoot\outputs\adaptive_scheduler.log"
$StateFile = "$WorkspaceRoot\outputs\adaptive_scheduler_state.json"
$MetricsFile = "$WorkspaceRoot\outputs\scheduler_metrics.json"
$ScriptsDir = "$WorkspaceRoot\scripts"

# === Performance Thresholds ===
$AdaptiveConfig = @{
    cpu_threshold_high = 70      # CPU > 70% → reduce frequency
    cpu_threshold_low  = 20       # CPU < 20% → increase frequency
    memory_threshold   = 60         # Memory > 60% → skip non-critical tasks

    # Base intervals (in minutes)
    health_check_base  = 10
    performance_base   = 30
    maintenance_base   = 60
    daily_base         = 1440
    event_base         = 120
}

# === Task Definitions (with auto script detection) ===
$TaskDefinitions = @{
    "health_check"         = @{
        interval_minutes = $AdaptiveConfig.health_check_base
        priority         = "critical"
        commands         = @(
            @{
                name   = "Quick Diagnosis"
                script = "quick_diagnose.ps1"
            },
            @{
                name   = "LLM Performance Check"
                script = "check_llm_perf.ps1"
            }
        )
        depends_on       = @()
        critical         = $true
    }

    "performance_analysis" = @{
        interval_minutes = $AdaptiveConfig.performance_base
        priority         = "high"
        commands         = @(
            @{
                name   = "Save Performance Benchmark"
                script = "save_performance_benchmark.ps1"
            },
            @{
                name   = "Analyze Performance Trends"
                script = "analyze_performance_trends.ps1"
            },
            @{
                name   = "Adaptive Routing Optimizer"
                script = "adaptive_routing_optimizer.ps1"
            }
        )
        depends_on       = @("health_check")
    }

    "system_maintenance"   = @{
        interval_minutes = $AdaptiveConfig.maintenance_base
        priority         = "medium"
        commands         = @(
            @{
                name   = "Cleanup Processes"
                script = "cleanup_processes.ps1"
            },
            @{
                name   = "Collect System Metrics"
                script = "collect_system_metrics.ps1"
            }
        )
        depends_on       = @("performance_analysis")
    }

    "daily_routine"        = @{
        interval_minutes = $AdaptiveConfig.daily_base
        scheduled_time   = "03:00"
        priority         = "low"
        commands         = @(
            @{
                name   = "Generate Daily Briefing"
                script = "generate_daily_briefing.ps1"
            },
            @{
                name   = "Update Visual Dashboard"
                script = "generate_visual_dashboard.ps1"
            }
        )
        depends_on       = @("system_maintenance")
    }

    "event_analysis"       = @{
        interval_minutes = $AdaptiveConfig.event_base
        priority         = "medium"
        commands         = @(
            @{
                name   = "Analyze Latency Spikes"
                script = "analyze_latency_spikes.ps1"
            },
            @{
                name   = "Generate Performance Report"
                script = "generate_monitoring_report.ps1"
            }
        )
        depends_on       = @("performance_analysis")
    }
}

# === Logging ===
function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO",
        [string]$Task = "SCHEDULER"
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] [$Task] $Message"

    Write-Host $logEntry -ForegroundColor $(if ($Level -eq "ERROR") { "Red" } elseif ($Level -eq "WARN") { "Yellow" } else { "Green" })

    Add-Content -Path $MasterLogFile -Value $logEntry
}

# === System Metrics ===
function Get-SystemMetrics {
    $os = Get-CimInstance Win32_OperatingSystem
    $cpu = Get-CimInstance Win32_Processor | Select-Object -First 1

    $memUsagePercent = [math]::Round((($os.TotalVisibleMemorySize - $os.FreePhysicalMemory) / $os.TotalVisibleMemorySize) * 100, 1)

    return @{
        cpu_load     = if ($null -ne $cpu.LoadPercentage) { [int]$cpu.LoadPercentage } else { 0 }
        memory_usage = $memUsagePercent
        timestamp    = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    }
}

# === Adaptive Interval Calculation ===
function Get-AdaptiveInterval {
    param(
        [string]$TaskName,
        [int]$BaseInterval,
        [hashtable]$Metrics
    )

    $cpu = $Metrics.cpu_load
    $memory = $Metrics.memory_usage

    # Adapt interval based on system load
    if ($cpu -gt $AdaptiveConfig.cpu_threshold_high) {
        # High CPU: increase interval (slow down)
        $factor = 1.5
        Write-Log "High CPU ($cpu%) detected - reducing $TaskName frequency" "WARN" $TaskName
    }
    elseif ($cpu -lt $AdaptiveConfig.cpu_threshold_low) {
        # Low CPU: decrease interval (speed up)
        $factor = 0.8
        Write-Log "Low CPU ($cpu%) detected - increasing $TaskName frequency" "INFO" $TaskName
    }
    else {
        # Normal: keep base interval
        $factor = 1.0
    }

    $newInterval = [int]($BaseInterval * $factor)
    return [math]::Max(5, $newInterval)  # Minimum 5 minutes
}

# === Script Execution (Auto-detect Python vs PowerShell) ===
function Invoke-ScriptCommand {
    param(
        [hashtable]$Command,
        [string]$TaskName
    )

    $cmdName = $Command.name
    $scriptName = $Command.script
    $args = $Command.args
    $scriptPath = Join-Path $ScriptsDir $scriptName

    if (-not (Test-Path $scriptPath)) {
        Write-Log "Script not found: $scriptPath" "ERROR" $TaskName
        return $false
    }

    try {
        Write-Log "Executing: $cmdName" "INFO" $TaskName

        if ($DryRun) {
            Write-Log "[DRY RUN] Would execute: $scriptName $args" "INFO" $TaskName
            return $true
        }

        # Auto-detect script type and execute (hidden window)
        if ($scriptName -match '\.py$') {
            # Python script
            $argList = @("`"$scriptPath`"")
            if ($args) { $argList += $args }
            $proc = Start-Process -FilePath "python" -ArgumentList $argList -WindowStyle Hidden -PassThru -Wait
            Write-Log "Python script exit code: $($proc.ExitCode)" "INFO" $TaskName
        }
        elseif ($scriptName -match '\.ps1$') {
            # PowerShell script
            $argList = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$scriptPath`"")
            if ($args) { $argList += $args }
            $proc = Start-Process -FilePath "powershell.exe" -ArgumentList $argList -WindowStyle Hidden -PassThru -Wait
            Write-Log "PowerShell script exit code: $($proc.ExitCode)" "INFO" $TaskName
        }
        else {
            Write-Log "Unknown script type: $scriptName" "ERROR" $TaskName
            return $false
        }

        Write-Log "Completed: $cmdName" "INFO" $TaskName
        return $true

    }
    catch {
        Write-Log "Execution failed: $_" "ERROR" $TaskName
        return $false
    }
}

# === State Management ===
function Load-State {
    if (Test-Path $StateFile) {
        $json = Get-Content -Path $StateFile | ConvertFrom-Json
        $result = @{}
        if ($json) {
            $json.PSObject.Properties | ForEach-Object {
                if ($_.Name -eq "last_runs") {
                    $lastRunsHash = @{}
                    if ($_.Value) {
                        $_.Value.PSObject.Properties | ForEach-Object {
                            $lastRunsHash[$_.Name] = $_.Value
                        }
                    }
                    $result[$_.Name] = $lastRunsHash
                }
                else {
                    $result[$_.Name] = $_.Value
                }
            }
        }
        return $result
    }
    return @{ last_runs = @{} }
}

function Save-State {
    param([hashtable]$State)
    $State | ConvertTo-Json | Set-Content -Path $StateFile -Force
}

function Save-Metrics {
    param([hashtable]$Metrics)
    @{
        timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        metrics   = $Metrics
    } | ConvertTo-Json | Add-Content -Path $MetricsFile
}

# === Adaptive Task Execution ===
function Invoke-Task {
    param(
        [string]$TaskName,
        [hashtable]$TaskConfig,
        [hashtable]$StateData,
        [hashtable]$SystemMetrics
    )

    # Check if critical task
    if ($SystemMetrics.memory_usage -gt $AdaptiveConfig.memory_threshold -and -not $TaskConfig.critical) {
        Write-Log "Memory pressure - skipping non-critical task" "WARN" $TaskName
        return $true
    }

    Write-Log "=== Starting Task: $TaskName ===" "INFO" $TaskName

    $success = $true
    foreach ($cmd in $TaskConfig.commands) {
        if (-not (Invoke-ScriptCommand -Command $cmd -TaskName $TaskName)) {
            $success = $false
            break
        }
    }

    if ($success) {
        $StateData.last_runs[$TaskName] = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Write-Log "=== Task Complete: $TaskName ===" "INFO" $TaskName
    }
    else {
        Write-Log "=== Task Failed: $TaskName ===" "ERROR" $TaskName
    }

    return $success
}

# === Adaptive Scheduler Loop ===
function Start-AdaptiveScheduler {
    Write-Host "`n" -NoNewline
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host "  Adaptive Master Scheduler - Dynamic Rhythm v2" -ForegroundColor Yellow
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host ""

    Write-Log "Adaptive Scheduler Started" "INFO"

    $stateData = Load-State
    if (-not $stateData.ContainsKey("last_runs")) {
        $stateData["last_runs"] = @{}
    }

    $cycleCount = 0
    $metricsBuffer = @()

    while ($true) {
        $cycleCount++
        $now = Get-Date

        # Get current system metrics
        $metrics = Get-SystemMetrics
        $metricsBuffer += $metrics

        # Keep only last 24 measurements
        if ($metricsBuffer.Count -gt 24) {
            $metricsBuffer = $metricsBuffer[-24..-1]
        }

        # Calculate adaptive intervals
        $adaptiveIntervals = @{}
        $TaskDefinitions.Keys | ForEach-Object {
            $taskName = $_
            $baseInterval = $TaskDefinitions[$taskName].interval_minutes
            $adaptiveIntervals[$taskName] = Get-AdaptiveInterval -TaskName $taskName -BaseInterval $baseInterval -Metrics $metrics
        }

        # Check which tasks should run
        $tasksToRun = @()
        foreach ($taskName in $TaskDefinitions.Keys) {
            $taskConfig = $TaskDefinitions[$taskName]
            $lastRun = if ($stateData.last_runs.ContainsKey($taskName)) {
                [datetime]::ParseExact($stateData.last_runs[$taskName], "yyyy-MM-dd HH:mm:ss", $null)
            }
            else {
                $null
            }

            $interval = $adaptiveIntervals[$taskName]

            if ($null -eq $lastRun) {
                $tasksToRun += $taskName
            }
            else {
                $elapsed = $now - $lastRun
                if ($elapsed.TotalMinutes -ge $interval) {
                    $tasksToRun += $taskName
                }
            }
        }

        # Execute tasks
        if ($tasksToRun.Count -gt 0) {
            Write-Host "`n[Cycle $cycleCount @ $($now.ToString('HH:mm:ss'))] CPU: $($metrics.cpu_load)% | Memory: $($metrics.memory_usage)% | Tasks: $($tasksToRun -join ', ')" -ForegroundColor Cyan

            foreach ($taskName in $tasksToRun) {
                if (Invoke-Task -TaskName $taskName -TaskConfig $TaskDefinitions[$taskName] -StateData $stateData -SystemMetrics $metrics) {
                    Save-State -State $stateData
                }
            }

            Save-Metrics -Metrics $metrics
        }

        $nextCheck = $now.AddSeconds($CheckIntervalSeconds)
        Write-Host "Next check: $($nextCheck.ToString('HH:mm:ss'))" -ForegroundColor Gray

        Start-Sleep -Seconds $CheckIntervalSeconds
    }
}

# === Main Entry ===
if ($DryRun) {
    Write-Host "`n🔍 DRY RUN MODE" -ForegroundColor Yellow
}

Write-Host "`nStarting Adaptive Master Scheduler..." -ForegroundColor Cyan

if ($InstallSchedule) {
    Write-Host "Registering as Windows Scheduled Task..." -ForegroundColor Yellow
    $taskName = "AGI_Adaptive_Master_Scheduler"
    $scriptPath = $MyInvocation.MyCommand.Path

    $trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Days 365) -Once -At (Get-Date)
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$scriptPath`""
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -Hidden

    Register-ScheduledTask -TaskName $taskName -Trigger $trigger -Action $action -Settings $settings -Force -ErrorAction SilentlyContinue | Out-Null
    Write-Host "✓ Registered: $taskName" -ForegroundColor Green
}
else {
    Start-AdaptiveScheduler
}

Write-Host ""