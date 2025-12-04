# Master Scheduler - Unified Orchestration Engine
# Consolidates all 42 automation scripts into single coordinated rhythm
# Executes tasks based on time intervals and dependencies
# Replaces: 42 independent Scheduled Task scripts → 1 Master Scheduler

param(
    [switch]$DryRun,           # Show what would execute without running
    [switch]$InstallSchedule,  # Register as Windows Scheduled Task
    [int]$CheckIntervalSeconds = 60
)

$ErrorActionPreference = "Continue"

# === Configuration ===
$MasterLogFile = "C:\workspace\agi\outputs\master_scheduler.log"
$StateFile = "C:\workspace\agi\outputs\master_scheduler_state.json"
$ScriptsDir = "C:\workspace\agi\scripts"

# === Task Definitions ===
# Structure: interval (minutes), last_run, commands, depends_on
$TaskDefinitions = @{
    "health_check" = @{
        interval_minutes = 10
        last_run = $null
        commands = @(
            @{
                name = "Fast Health Check"
                script = "check_health.py"
                args = "--fast"
                type = "python"
            },
            @{
                name = "Circuit Breaker Status"
                script = "circuit_breaker_router.py"
                args = "--status-only"
                type = "python"
            }
        )
        depends_on = @()
    }

    "performance_analysis" = @{
        interval_minutes = 30
        last_run = $null
        commands = @(
            @{
                name = "Save Performance Benchmark"
                script = "save_performance_benchmark.ps1"
                type = "powershell"
            },
            @{
                name = "Analyze Performance Trends"
                script = "analyze_performance_trends.ps1"
                type = "powershell"
            },
            @{
                name = "Adaptive Routing Optimizer"
                script = "adaptive_routing_optimizer.ps1"
                type = "powershell"
            }
        )
        depends_on = @("health_check")
    }

    "system_maintenance" = @{
        interval_minutes = 60
        last_run = $null
        commands = @(
            @{
                name = "Cleanup Processes"
                script = "cleanup_processes.ps1"
                type = "powershell"
            },
            @{
                name = "Collect System Metrics"
                script = "collect_system_metrics.ps1"
                type = "powershell"
            }
        )
        depends_on = @("performance_analysis")
    }

    "daily_routine" = @{
        interval_minutes = 1440  # 24 hours
        scheduled_time = "03:00"
        last_run = $null
        commands = @(
            @{
                name = "Generate Daily Briefing"
                script = "generate_daily_briefing.ps1"
                type = "powershell"
            },
            @{
                name = "Update Visual Dashboard"
                script = "generate_visual_dashboard.ps1"
                type = "powershell"
            }
        )
        depends_on = @("system_maintenance")
    }

    "event_analysis" = @{
        interval_minutes = 120
        last_run = $null
        commands = @(
            @{
                name = "Analyze Latency Spikes"
                script = "analyze_latency_spikes.ps1"
                type = "powershell"
            },
            @{
                name = "Replan Pattern Analysis"
                script = "analyze_replan_patterns.ps1"
                type = "powershell"
            }
        )
        depends_on = @("performance_analysis")
    }
}

# === Logging Functions ===
function Write-MasterLog {
    param(
        [string]$Message,
        [string]$Level = "INFO",
        [string]$Task = "MASTER"
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] [$Task] $Message"

    Write-Host $logEntry -ForegroundColor $(if ($Level -eq "ERROR") { "Red" } elseif ($Level -eq "WARN") { "Yellow" } else { "Green" })

    Add-Content -Path $MasterLogFile -Value $logEntry
}

function Save-State {
    param([hashtable]$State)
    $State | ConvertTo-Json | Set-Content -Path $StateFile -Force
}

function Load-State {
    if (Test-Path $StateFile) {
        $json = Get-Content -Path $StateFile | ConvertFrom-Json
        $result = @{}
        if ($json) {
            $json.PSObject.Properties | ForEach-Object {
                if ($_.Name -eq "last_runs" -and $_.Value) {
                    # Convert last_runs to hashtable
                    $lastRunsHash = @{}
                    $_.Value.PSObject.Properties | ForEach-Object {
                        $lastRunsHash[$_.Name] = $_.Value
                    }
                    $result[$_.Name] = $lastRunsHash
                } else {
                    $result[$_.Name] = $_.Value
                }
            }
        }
        return $result
    }
    return @{ last_runs = @{} }
}

function ConvertTo-Hashtable {
    param([Parameter(ValueFromPipeline)]$InputObject)

    if ($null -eq $InputObject) { return @{} }
    if ($InputObject -is [hashtable]) { return $InputObject }
    if ($InputObject -is [pscustomobject]) {
        $hash = @{}
        $InputObject.PSObject.Properties | ForEach-Object { $hash[$_.Name] = $_.Value }
        return $hash
    }
    return @{}
}

# === Task Execution ===
function Should-RunTask {
    param(
        [string]$TaskName,
        [int]$IntervalMinutes,
        [object]$LastRun = $null,  # Allow null value
        [string]$ScheduledTime = $null
    )

    $now = Get-Date

    # For scheduled time tasks (daily at 03:00, etc.)
    if ($ScheduledTime) {
        $parts = $ScheduledTime -split ":"
        $targetTime = $now.Date.AddHours([int]$parts[0]).AddMinutes([int]$parts[1])

        if ($LastRun -eq $null) {
            # Never run, execute if past scheduled time or on first run
            return $targetTime -le $now
        }

        # Only run if scheduled time has passed since last run
        $lastRunDateTime = [datetime]$LastRun
        return ($targetTime -gt $lastRunDateTime) -and ($targetTime -le $now)
    }

    # For interval-based tasks
    if ($LastRun -eq $null) {
        return $true  # First run
    }

    $lastRunDateTime = [datetime]$LastRun
    $elapsed = $now - $lastRunDateTime
    return $elapsed.TotalMinutes -ge $IntervalMinutes
}

function Get-DependenciesMet {
    param(
        [string[]]$Dependencies,
        [hashtable]$LastRunState
    )

    if ($Dependencies.Count -eq 0) { return $true }

    foreach ($dep in $Dependencies) {
        if (-not $LastRunState.ContainsKey($dep) -or $null -eq $LastRunState[$dep]) {
            Write-MasterLog "Dependency not met: $dep" "WARN"
            return $false
        }
    }

    return $true
}

function Invoke-TaskCommand {
    param(
        [hashtable]$Command,
        [string]$TaskName
    )

    $cmdName = $Command.name
    $script = $Command.script
    $cmdArgs = $Command.args
    $type = $Command.type

    $scriptPath = Join-Path $ScriptsDir $script

    if (-not (Test-Path $scriptPath)) {
        Write-MasterLog "Script not found: $scriptPath" "ERROR" $TaskName
        return $false
    }

    try {
        Write-MasterLog "Starting: $cmdName" "INFO" $TaskName

        if ($DryRun) {
            Write-MasterLog "[DRY RUN] Would execute: $script $cmdArgs" "INFO" $TaskName
            return $true
        }

        if ($type -eq "powershell") {
            if ($cmdArgs) {
                & $scriptPath $cmdArgs -ErrorAction Stop 2>&1 | ForEach-Object {
                    Write-MasterLog $_ "INFO" $TaskName
                }
            } else {
                & $scriptPath -ErrorAction Stop 2>&1 | ForEach-Object {
                    Write-MasterLog $_ "INFO" $TaskName
                }
            }
        } elseif ($type -eq "python") {
            if ($cmdArgs) {
                python $scriptPath $cmdArgs -ErrorAction Stop 2>&1 | ForEach-Object {
                    Write-MasterLog $_ "INFO" $TaskName
                }
            } else {
                python $scriptPath -ErrorAction Stop 2>&1 | ForEach-Object {
                    Write-MasterLog $_ "INFO" $TaskName
                }
            }
        }

        Write-MasterLog "Completed: $cmdName" "INFO" $TaskName
        return $true

    } catch {
        Write-MasterLog "Failed to execute $cmdName : $_" "ERROR" $TaskName
        return $false
    }
}

function Invoke-Task {
    param(
        [string]$TaskName,
        [hashtable]$TaskConfig,
        [hashtable]$StateData
    )

    Write-MasterLog "=== Starting Task: $TaskName ===" "INFO" $TaskName

    # Check dependencies
    if (-not (Get-DependenciesMet -Dependencies $TaskConfig.depends_on -LastRunState $StateData.last_runs)) {
        Write-MasterLog "Dependencies not met, skipping" "WARN" $TaskName
        return $false
    }

    $success = $true

    # Execute all commands in sequence
    foreach ($cmd in $TaskConfig.commands) {
        if (-not (Invoke-TaskCommand -Command $cmd -TaskName $TaskName)) {
            $success = $false
            break  # Stop on first failure
        }
    }

    if ($success) {
        Write-MasterLog "=== Task Complete: $TaskName ===" "INFO" $TaskName
        $StateData.last_runs[$TaskName] = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    } else {
        Write-MasterLog "=== Task Failed: $TaskName ===" "ERROR" $TaskName
    }

    return $success
}

# === Main Scheduler Loop ===
function Start-MasterScheduler {
    param([switch]$Continuous = $true)

    Write-Host "`n" -NoNewline
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host "  Master Scheduler - Unified Rhythm Orchestration" -ForegroundColor Yellow
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host ""

    Write-MasterLog "Master Scheduler Started" "INFO"

    # Load previous state
    $existingState = Load-State
    $stateData = @{
        last_runs = $(if ($existingState.ContainsKey("last_runs")) { $existingState.last_runs } else { @{} })
        started_at = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    }

    $cycleCount = 0
    $isFirstCycle = $true

    while ($Continuous) {
        $cycleCount++
        $now = Get-Date

        # Check which tasks should run this cycle
        $tasksToRun = @()
        foreach ($taskName in $TaskDefinitions.Keys) {
            $taskConfig = $TaskDefinitions[$taskName]
            $lastRun = if ($stateData.last_runs.ContainsKey($taskName)) {
                [datetime]::ParseExact($stateData.last_runs[$taskName], "yyyy-MM-dd HH:mm:ss", $null)
            } else {
                $null
            }

            if (Should-RunTask -TaskName $taskName -IntervalMinutes $taskConfig.interval_minutes -LastRun $lastRun -ScheduledTime $taskConfig.scheduled_time) {
                $tasksToRun += $taskName
            }
        }

        # Execute scheduled tasks
        if ($tasksToRun.Count -gt 0) {
            Write-Host "`n[Cycle $cycleCount @ $($now.ToString('HH:mm:ss'))] Tasks scheduled: $($tasksToRun -join ', ')" -ForegroundColor Cyan

            # On first cycle, sort tasks by dependency order (execute dependencies first)
            if ($isFirstCycle) {
                $sortedTasks = @()
                $processed = @()

                function Add-TasksInOrder {
                    param([string]$task)
                    if ($processed -contains $task) { return }
                    if ($task -notin $tasksToRun) { return }

                    # Add dependencies first
                    foreach ($dep in $TaskDefinitions[$task].depends_on) {
                        Add-TasksInOrder -task $dep
                    }

                    $sortedTasks += $task
                    $processed += $task
                }

                foreach ($task in $tasksToRun) {
                    Add-TasksInOrder -task $task
                }

                $tasksToRun = $sortedTasks
                $isFirstCycle = $false
            }

            foreach ($taskName in $tasksToRun) {
                Invoke-Task -TaskName $taskName -TaskConfig $TaskDefinitions[$taskName] -StateData $stateData
            }

            # Save state after execution
            Save-State -State $stateData
        }

        # Display next check
        $nextCheck = $now.AddSeconds($CheckIntervalSeconds)
        Write-Host "Next check: $($nextCheck.ToString('HH:mm:ss'))" -ForegroundColor Gray

        # Wait before next cycle
        Start-Sleep -Seconds $CheckIntervalSeconds
    }
}

# === Scheduled Task Registration ===
function Register-MasterScheduler {
    Write-Host "`n[Registering Master Scheduler as Windows Scheduled Task]" -ForegroundColor Yellow

    $taskName = "AGI_Master_Scheduler"
    $scriptPath = $MyInvocation.MyCommand.Path

    # Check if already exists
    $existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "  Task already registered. Unregistering old version..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
    }

    # Create trigger (every 5 minutes)
    $trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Days 365) -Once -At (Get-Date)

    # Create action
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`""

    # Create task settings
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable

    # Register task
    try {
        Register-ScheduledTask -TaskName $taskName -Trigger $trigger -Action $action -Settings $settings -Force -ErrorAction Stop | Out-Null
        Write-Host "  ✓ Master Scheduler registered successfully" -ForegroundColor Green
        Write-Host "    Task Name: $taskName" -ForegroundColor Gray
        Write-Host "    Run Interval: Every 5 minutes" -ForegroundColor Gray
        Write-Host "    Status: Ready to start" -ForegroundColor Gray
    } catch {
        Write-Host "  ✗ Registration failed: $_" -ForegroundColor Red
        Write-Host "`n  To register manually, run this in Administrator PowerShell:" -ForegroundColor Yellow
        Write-Host "  Register-ScheduledTask -TaskName '$taskName' -Action `$action -Trigger `$trigger" -ForegroundColor Gray
    }
}

# === Display Configuration ===
function Show-Configuration {
    Write-Host "`nScheduled Tasks:" -ForegroundColor Cyan

    $TaskDefinitions.GetEnumerator() | ForEach-Object {
        $task = $_.Value
        $interval = if ($task.scheduled_time) { "Daily @ $($task.scheduled_time)" } else { "Every $($task.interval_minutes) min" }
        Write-Host "  • $($_.Key): $interval" -ForegroundColor Yellow

        if ($task.depends_on.Count -gt 0) {
            Write-Host "    ├─ Depends on: $($task.depends_on -join ', ')" -ForegroundColor Gray
        }

        foreach ($cmd in $task.commands) {
            Write-Host "    ├─ $($cmd.name)" -ForegroundColor Gray
        }
    }

    Write-Host "`nLog file: $MasterLogFile" -ForegroundColor Green
    Write-Host "State file: $StateFile" -ForegroundColor Green
}

# === Main Entry Point ===
if ($DryRun) {
    Write-Host "`n🔍 DRY RUN MODE - No scripts will be executed" -ForegroundColor Yellow
}

Show-Configuration
Write-Host ""

if ($InstallSchedule) {
    Register-MasterScheduler
} else {
    Write-Host "`nStarting Master Scheduler (Continuous Mode)..." -ForegroundColor Cyan
    Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray

    Start-MasterScheduler -Continuous $true
}

Write-Host ""
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""
