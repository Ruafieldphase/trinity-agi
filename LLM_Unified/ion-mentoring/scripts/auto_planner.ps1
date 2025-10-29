<#
SYNOPSIS
  Rule-based auto planner: generates and executes next TODOs after deployment flow.
  - Maintains outputs\auto_backlog.json
  - Generates tasks based on auto_canary_state.json
  - Executes up to -MaxTasksPerRun tasks per invocation
#>
param(
    [int]$MaxTasksPerRun = 1
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$workspaceRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)
$outputsDir = Join-Path $workspaceRoot "ion-mentoring\outputs"
if (-not (Test-Path $outputsDir)) { New-Item -ItemType Directory -Path $outputsDir | Out-Null }
$stateFile = Join-Path $outputsDir "auto_canary_state.json"
$backlogFile = Join-Path $outputsDir "auto_backlog.json"
$logFile = Join-Path $outputsDir "auto_canary_runner.log"

function Write-Log($msg, [string]$level = "INFO") {
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') [$level] [planner] $msg"
    Write-Host $line
    Add-Content -Path $logFile -Value $line
}

function Send-SlackNotification([string]$msg, [string]$emoji = ":information_source:") {
    try {
        & "$scriptDir\send_slack_notification.ps1" -Message $msg -Emoji $emoji -ErrorAction SilentlyContinue | Out-Null
    }
    catch { }
}

function Get-State() {
    if (Test-Path $stateFile) { try { return Get-Content $stateFile -Raw | ConvertFrom-Json } catch { } }
    return $null
}

function Get-Backlog() {
    if (Test-Path $backlogFile) { try { return Get-Content $backlogFile -Raw | ConvertFrom-Json } catch { } }
    return [pscustomobject]@{ tasks = @() }
}

function Save-Backlog($backlog) {
    ($backlog | ConvertTo-Json -Depth 6) | Set-Content -Path $backlogFile -Encoding UTF8
}

function New-Task([string]$title, [string]$command, [string[]]$taskArgs) {
    return [pscustomobject]@{
        id         = [guid]::NewGuid().ToString();
        title      = $title;
        command    = $command;
        args       = $taskArgs;
        status     = "pending";
        created_at = (Get-Date).ToString("o");
        last_run   = $null;
        retries    = 0
    }
}

function Update-Backlog($state, $backlog) {
    $phase = $null
    if ($null -ne $state) {
        try { $phase = $state.phase } catch { $phase = $null }
    }
    # Consider only active tasks (pending/running) for generation gating
    $active = @()
    if ($null -ne $backlog -and $null -ne $backlog.tasks) {
        $active = $backlog.tasks | Where-Object { $_.status -in @('pending', 'running') }
    }
    $allDone = ($null -eq $active -or $active.Count -eq 0)

    if ($allDone -or -not $backlog.tasks -or $backlog.tasks.Count -eq 0) {
        Write-Log "Backlog empty or all done; generating next tasks for phase '$phase'"
        $tasks = @()

        if ($phase -eq '100-monitoring') {
            # Mid-report and checks during 100% monitoring window
            # Use ASCII-safe filenames in outputs to avoid PS5.1 encoding/BOM issues with non-ASCII paths
            $midReport = Join-Path $outputsDir ("canary_100pct_interim_" + (Get-Date -Format 'yyyy-MM-dd') + ".md")
            if (-not (Test-Path $midReport)) {
                $tasks += New-Task "Generate 100% interim report" "powershell" @("-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
                    "Set-Content -Path `"$midReport`" -Value ('# 100% 중간 보고서`n`n- 생성시각: ' + (Get-Date).ToString('u') + '`n- 상태: 100% 모니터링 중') -Encoding UTF8")
            }
            $tasks += New-Task "Gentle probe (3, 2s)" (Join-Path $scriptDir 'rate_limit_probe.ps1') @('-RequestsPerSide', '3', '-DelayMsBetweenRequests', '2000', '-CanaryEndpointPath', '/health')
            $tasks += New-Task "Monitoring status check" (Join-Path $scriptDir 'check_monitoring_status.ps1') @()
        }
        elseif ($phase -eq 'done') {
            # Finalization tasks after completion
            # Use ASCII-safe filenames in outputs
            $finalReport = Join-Path $outputsDir ("canary_final_" + (Get-Date -Format 'yyyy-MM-dd') + ".md")
            if (-not (Test-Path $finalReport)) {
                $tasks += New-Task "Generate final deployment report" "powershell" @("-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
                    "Set-Content -Path `"$finalReport`" -Value ('# 최종 배포 보고서`n`n- 생성시각: ' + (Get-Date).ToString('u') + '`n- 결과: 완료') -Encoding UTF8")
            }
            $tasks += New-Task "Operations daily report (24h)" (Join-Path $scriptDir 'generate_daily_report.ps1') @('-Hours', '24')
            $tasks += New-Task "Summarize locust results (all)" (Join-Path $scriptDir 'summarize_locust_results.ps1') @('-InputGlob', (Join-Path $outputsDir '*.csv'))
            $tasks += New-Task "Cleanup old logs (7d, dryrun)" (Join-Path $scriptDir 'cleanup_old_logs.ps1') @('-KeepDays', '7', '-DryRun', '-Verbose')
        }
        else {
            # Default periodic health
            $tasks += New-Task "Default gentle probe" (Join-Path $scriptDir 'rate_limit_probe.ps1') @('-RequestsPerSide', '3', '-DelayMsBetweenRequests', '2000', '-CanaryEndpointPath', '/health')
        }

        $backlog.tasks = @($backlog.tasks + $tasks)
    }
}

function Invoke-Task($task) {
    try {
        # Idempotent skips for file-creating tasks
        if ($task.title -eq 'Generate 100% interim report') {
            $midReport = Join-Path $outputsDir ("canary_100pct_interim_" + (Get-Date -Format 'yyyy-MM-dd') + ".md")
            if (Test-Path $midReport) {
                Write-Log "Skip '$($task.title)' (exists: $midReport)"
                $task.status = 'completed'
                return
            }
        }
        if ($task.title -eq 'Generate final deployment report') {
            $finalReport = Join-Path $outputsDir ("canary_final_" + (Get-Date -Format 'yyyy-MM-dd') + ".md")
            if (Test-Path $finalReport) {
                Write-Log "Skip '$($task.title)' (exists: $finalReport)"
                $task.status = 'completed'
                return
            }
        }

        $task.status = 'running'
        $task.last_run = (Get-Date).ToString('o')
        $cmd = $task.command
        $taskArgs = $task.args
        Write-Log "Running task: $($task.title) => $cmd $($taskArgs -join ' ')"
        if ($cmd -ieq 'powershell') {
            $commonPS = @('-NoLogo', '-NonInteractive', '-WindowStyle', 'Hidden')
            & powershell @commonPS @taskArgs | Out-Null
        }
        elseif ((Test-Path $cmd) -and ($cmd.ToLower().EndsWith('.ps1'))) {
            & powershell -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File $cmd @taskArgs | Out-Null
        }
        else {
            & $cmd @taskArgs | Out-Null
        }
        $task.status = 'completed'
        Write-Log "Task completed: $($task.title)"
    }
    catch {
        $task.retries = ($task.retries + 1)
        $task.status = if ($task.retries -ge 3) { 'failed' } else { 'pending' }
        Write-Log "Task failed ($($task.retries)) : $($task.title) - $_" 'WARN'
    }
}

# Main
Write-Log "Auto planner start"
$state = Get-State
$phaseDbg = if ($state) { $state.phase } else { '<null>' }
$created = if ($state) { $state.created_at } else { '' }
$dummy = Write-Log ("State snapshot: phase=" + $phaseDbg)
$backlog = Get-Backlog
Update-Backlog -state $state -backlog $backlog

$executed = 0
foreach ($t in $backlog.tasks) {
    if ($executed -ge $MaxTasksPerRun) { break }
    if ($t.status -eq 'pending') {
        Invoke-Task -task $t
        $executed++
    }
}

Save-Backlog -backlog $backlog

$completedCount = @($backlog | Where-Object { $_.status -eq 'done' }).Count
$pendingCount = @($backlog | Where-Object { $_.status -eq 'pending' }).Count

Write-Log "Auto planner end (executed: $executed, completed: $completedCount, pending: $pendingCount)"

if ($executed -gt 0) {
    $tasks = ($backlog | Where-Object { $_.status -eq 'done' } | Select-Object -Last $executed | ForEach-Object { $_.name }) -join ', '
    Send-SlackNotification "🤖 Planner: $executed 개 작업 완료 ($tasks)" -emoji ":robot_face:"
}