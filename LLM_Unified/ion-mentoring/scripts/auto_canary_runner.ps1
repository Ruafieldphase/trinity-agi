
<#
SYNOPSIS
  Idempotent canary deployment auto-runner. Safe to run every few minutes.
  - Advances TODO pipeline based on time gates and state file
  - No prompts; logs to outputs/auto_canary_runner.log
  - Prevents system sleep while executing; designed for Scheduled Task with WakeToRun
  - Sends Slack notifications for deployment progress
#>
param(
    [string]$ProjectId = "naeda-genesis",
    [string]$CanaryHealthPath = "/health",
    [switch]$ForceAdvance,
    [int]$PlannerBurstMaxTasks = 3,
    [switch]$EnableSlackNotifications = $true
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$workspaceRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)
$outputsDir = Join-Path $workspaceRoot "ion-mentoring\outputs"
if (-not (Test-Path $outputsDir)) { New-Item -ItemType Directory -Path $outputsDir | Out-Null }
$logFile = Join-Path $outputsDir "auto_canary_runner.log"
$stateFile = Join-Path $outputsDir "auto_canary_state.json"
$lockFile = Join-Path $outputsDir "auto_canary_runner.lock"

# Slack 알림 모듈 로드
$SlackModulePath = Join-Path $scriptDir "SlackNotifications.ps1"
if ((Test-Path $SlackModulePath) -and $EnableSlackNotifications) {
    . $SlackModulePath
    Write-Verbose "Slack 알림 모듈 로드됨"
}
else {
    $EnableSlackNotifications = $false
}

function Log($msg, [string]$level = "INFO") {
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') [$level] $msg"
    Write-Host $line
    Add-Content -Path $logFile -Value $line
}

function Send-SlackNotification([string]$msg, [string]$emoji = ":information_source:") {
    if (-not $EnableSlackNotifications) { return }
    
    try {
        # 이모지 매핑
        $emojiMap = @{
            ":rocket:"             = "[DEPLOY]"
            ":white_check_mark:"   = "[OK]"
            ":x:"                  = "[ERROR]"
            ":checkered_flag:"     = "🏁"
            ":information_source:" = "ℹ️"
            ":warning:"            = "[WARN]"
        }
        
        $displayEmoji = if ($emojiMap.ContainsKey($emoji)) { $emojiMap[$emoji] } else { "" }
        
        Send-SlackMessage -Message $msg -Emoji $displayEmoji
    }
    catch {
        Log "Slack 알림 전송 실패: $_" "WARN"
    }
}

# Prevent sleep while running
try {
    Add-Type -Namespace Native -Name SleepUtil -MemberDefinition @"
    [System.Runtime.InteropServices.DllImport("kernel32.dll")]
    public static extern uint SetThreadExecutionState(uint esFlags);
"@
    # ES_CONTINUOUS(0x80000000) | ES_SYSTEM_REQUIRED(0x1)
    [Native.SleepUtil]::SetThreadExecutionState(0x80000001) | Out-Null
}
catch { }

function Save-State($state) {
    ($state | ConvertTo-Json -Depth 5) | Set-Content -Path $stateFile -Encoding UTF8
}

function Get-State() {
    if (Test-Path $stateFile) {
        try { return Get-Content $stateFile -Raw | ConvertFrom-Json } catch { }
    }
    # Default state assumes we've completed 50% immediate steps and are in monitoring if marker exists
    return [pscustomobject]@{
        phase       = "50-monitoring";
        monitor_end = (Get-Date).AddMinutes(60).ToString("o");
        project     = $ProjectId
    }
}

function Invoke-Probe([int]$count, [int]$delayMs) {
    & "$scriptDir\rate_limit_probe.ps1" -RequestsPerSide $count -DelayMsBetweenRequests $delayMs -CanaryEndpointPath $CanaryHealthPath | Out-Null
}

function Set-CanaryDeployment([int]$pct) {
    if ($EnableSlackNotifications) {
        Send-DeploymentStartAlert -Percentage $pct -Version "auto-canary"
    }
    
    $deployParams = @{
        ProjectId        = $ProjectId
        CanaryPercentage = $pct
    }
    
    if ($EnableSlackNotifications) {
        $deployParams.EnableSlackNotifications = $true
    }
    
    & "$scriptDir\deploy_phase4_canary.ps1" @deployParams | Out-Null
}

function Invoke-LogScan([string]$last) {
    & "$scriptDir\filter_logs_by_time.ps1" -Last $last -ShowSummary | Out-Null
}

function Invoke-LightLoadTest() {
    & "$scriptDir\run_all_load_tests.ps1" -ScenarioProfile "light" -OverrideRunTime "10s" | Out-Null
    & "$scriptDir\summarize_locust_results.ps1" | Out-Null
}

# Main
Log "Auto runner start"
# Simple lock to avoid overlapping runs
if (Test-Path $lockFile) {
    try {
        $age = (Get-Date) - (Get-Item $lockFile).LastWriteTime
        if ($age.TotalMinutes -lt 15) {
            Log "Another run appears active (lock present); exiting" "WARN"
            return
        }
    }
    catch { }
}
try { Set-Content -Path $lockFile -Value (Get-Date).ToString('o') -Encoding UTF8 } catch { }
$legacyOutputsDir = Join-Path $workspaceRoot "LLM_Unified\ion-mentoring\outputs"
if (Test-Path $legacyOutputsDir) {
    # Migrate legacy files if present from mistakenly nested path
    foreach ($f in @("auto_canary_runner.log", "auto_canary_state.json", "auto_backlog.json")) {
        $src = Join-Path $legacyOutputsDir $f
        $dst = Join-Path $outputsDir $f
        if ((Test-Path $src) -and -not (Test-Path $dst)) {
            try { Copy-Item -Path $src -Destination $dst -Force } catch { }
        }
    }
}
$state = Get-State
$now = Get-Date
$phase = $state.phase
$endTime = $null
if ($state.monitor_end) { try { $endTime = [datetime]::Parse($state.monitor_end) } catch { $endTime = $null } }
if ($ForceAdvance -and $phase -like "*-monitoring" -and $endTime -and $now -lt $endTime) {
    Log "ForceAdvance set; overriding monitor gate to now"
    $endTime = $now.AddSeconds(-1)
}

try {
    switch ($phase) {
        "50-monitoring" {
            if (-not $endTime -or $now -ge $endTime) {
                Log "50% monitoring gate passed; executing steps #11-15"
                Send-SlackNotification "[DEPLOY] Canary Runner: 50% → 100% 배포 시작" ":rocket:"
                try { Invoke-LogScan "1h"; Log "Log scan (1h) done" } catch { Log "Log scan failed: $_" "WARN" }
                try { Invoke-LightLoadTest; Log "Light load test + summarize done" } catch { Log "Load test failed: $_" "WARN" }
                # Optional: generate brief summary marker
                Set-Content -Path (Join-Path $outputsDir "50pct_summary_marker.txt") -Value (Get-Date).ToString('u')
                # Pre-check 100%
                try { Invoke-Probe -count 5 -delayMs 500; Log "Pre-check probe done" } catch { Log "Pre-check probe warn: $_" "WARN" }
                # Deploy 100%
                try { Set-CanaryDeployment -pct 100; Log "Deployed 100%" } catch { Log "Deploy 100% failed: $_" "ERROR"; Send-SlackNotification "🔴 Canary 100% 배포 실패: $_" ":x:"; throw }
                # Post probes
                try { Invoke-Probe -count 5 -delayMs 500; Invoke-Probe -count 10 -delayMs 1000; Invoke-Probe -count 25 -delayMs 500; Log "Post-deploy probes done" } catch { Log "Post-deploy probes warn: $_" "WARN" }
                # Set next monitoring 2h
                $state.phase = "100-monitoring"
                $state.monitor_end = (Get-Date).AddHours(2).ToString("o")
                Save-State $state
                Log "Entered 100-monitoring; end $($state.monitor_end)"
                Send-SlackNotification "[OK] Canary 100% 배포 완료. 2시간 모니터링 시작 → $(Get-Date -Date $state.monitor_end -Format 'HH:mm') 종료 예정" ":white_check_mark:"
            }
            else {
                $mins = [math]::Ceiling(($endTime - $now).TotalMinutes)
                Log "50% monitoring ongoing; $mins min left"
            }
        }
        "100-monitoring" {
            if (-not $endTime -or $now -ge $endTime) {
                Log "100% monitoring window ended; finalizing"
                Send-SlackNotification "🏁 Canary 100% 모니터링 종료. 최종 단계 실행 중..." ":checkered_flag:"
                try { Invoke-LogScan "2h"; Log "Log scan (2h) done" } catch { Log "Log scan (2h) failed: $_" "WARN" }
                $state.phase = "done"
                $state.completed_at = (Get-Date).ToString("o")
                Save-State $state
                Log "All stages completed"
                Send-SlackNotification "[SUCCESS] Canary 배포 전체 완료! Phase 4 종료 시각: $(Get-Date -Format 'HH:mm')" ":tada:"
            }
            else {
                $mins = [math]::Ceiling(($endTime - $now).TotalMinutes)
                Log "100% monitoring ongoing; $mins min left"
            }
        }
        default {
            Log "Unknown phase '$phase'; no action" "WARN"
        }
    }
}
finally {
    # planner and cleanup happen after phase handling
}

# Invoke auto planner to generate/execute next TODOs
try {
    & "$scriptDir\auto_planner.ps1" -MaxTasksPerRun $PlannerBurstMaxTasks | Out-Null
    Log "Auto planner executed"
}
catch {
    Log "Auto planner failed: $_" "WARN"
}

# Clear execution state (allow sleep again)
try { [Native.SleepUtil]::SetThreadExecutionState(0x80000000) | Out-Null } catch { }
Log "Auto runner end"
try { if (Test-Path $lockFile) { Remove-Item $lockFile -Force } } catch { }
