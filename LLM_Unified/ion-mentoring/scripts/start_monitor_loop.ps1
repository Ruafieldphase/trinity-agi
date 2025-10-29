param(
    [switch]$KillExisting,
    [switch]$StopOnly,
    [int]$IntervalSeconds = 1800,
    [int]$DurationMinutes = 1440,
    [switch]$IncludeRateLimitProbe,
    [switch]$Detach = $true,
    [switch]$IsChild
)

$ErrorActionPreference = 'Stop'

# Use Windows PowerShell host for child invocations
$psExe = 'powershell.exe'

function Stop-ExistingMonitorLoops {
    try {
        $thisScript = [IO.Path]::GetFileName($PSCommandPath)
        $procs = Get-CimInstance Win32_Process -Filter "Name = 'powershell.exe'" | Where-Object { $_.CommandLine -match [Regex]::Escape($thisScript) -and $_.ProcessId -ne $PID }
        foreach ($p in $procs) {
            Write-Host ("[monitor-loop] Stopping existing loop PID={0}" -f $p.ProcessId) -ForegroundColor Yellow
            Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
        }
    }
    catch {
        Write-Warning ("[monitor-loop] Failed to enumerate/stop existing loops: {0}" -f $_.Exception.Message)
    }
}

# Detach to a child process for robust backgrounding, unless explicitly disabled or already a child
if (-not $IsChild -and $Detach) {
    if ($KillExisting) { Stop-ExistingMonitorLoops }
    if ($StopOnly) { Write-Host "[monitor-loop] StopOnly requested; exiting after cleanup." -ForegroundColor Cyan; exit 0 }

    $argList = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "$PSCommandPath",
        '-IntervalSeconds', "$IntervalSeconds", '-DurationMinutes', "$DurationMinutes", '-IsChild')
    if ($IncludeRateLimitProbe) { $argList += '-IncludeRateLimitProbe' }

    try {
        Write-Host "[monitor-loop] Spawning detached child process..." -ForegroundColor Cyan
        Start-Process -FilePath $psExe -ArgumentList $argList -WindowStyle Hidden | Out-Null
        Write-Host "[monitor-loop] Child started; parent exiting (detached)." -ForegroundColor Green
        exit 0
    }
    catch {
        Write-Warning ("[monitor-loop] Detach failed: {0}. Falling back to in-process loop." -f $_.Exception.Message)
        # Fall-through to run loop inline
    }
}

if ($KillExisting) {
    Stop-ExistingMonitorLoops
    if ($StopOnly) {
        Write-Host "[monitor-loop] StopOnly requested; exiting after cleanup." -ForegroundColor Cyan
        exit 0
    }
}

# Paths
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$logsDirCandidate = Join-Path $PSScriptRoot '..\logs'
$resolved = Resolve-Path $logsDirCandidate -ErrorAction SilentlyContinue
if (-not $resolved) {
    New-Item -ItemType Directory -Force -Path $logsDirCandidate | Out-Null
    $resolved = Resolve-Path $logsDirCandidate
}
$logsDir = $resolved.Path
$timestamp = (Get-Date).ToString('yyyyMMdd_HHmmss')
$logFile = Join-Path $logsDir ("monitor_loop_" + $timestamp + ".log")

$checkScript = Join-Path $PSScriptRoot 'check_monitoring_status.ps1'
$rateProbeScript = Join-Path $PSScriptRoot 'rate_limit_probe.ps1'
$autoRemScript = Join-Path $PSScriptRoot 'auto_remediation.ps1'
if (-not (Test-Path $checkScript)) { Write-Error "check_monitoring_status.ps1 not found: $checkScript"; exit 1 }

function Invoke-ChildAndLog {
    param(
        [Parameter(Mandatory = $true)][string]$ScriptPath,
        [Parameter(Mandatory = $false)][string[]]$Args
    )
    $tmpOut = [System.IO.Path]::GetTempFileName()
    $tmpErr = [System.IO.Path]::GetTempFileName()
    try {
        # Ensure no nulls are passed to -ArgumentList
        $safeExtraArgs = @()
        if ($null -ne $Args) {
            foreach ($a in $Args) { if ($null -ne $a) { $safeExtraArgs += $a } }
        }
        $fullArgs = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $ScriptPath) + $safeExtraArgs
        $proc = Start-Process -FilePath $psExe -ArgumentList $fullArgs -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $tmpOut -RedirectStandardError $tmpErr
        if (Test-Path $tmpOut) {
            Get-Content -Path $tmpOut | Tee-Object -FilePath $logFile -Append | Out-Null
        }
        if (Test-Path $tmpErr) {
            # Mark stderr section for clarity
            Add-Content -Path $logFile -Value ("[{0}] [stderr] ---" -f (Get-Date).ToString('s'))
            Get-Content -Path $tmpErr | Tee-Object -FilePath $logFile -Append | Out-Null
        }
        return $proc.ExitCode
    }
    catch {
        Add-Content -Path $logFile -Value ("[{0}] Exception running {1}: {2}" -f (Get-Date).ToString('s'), [IO.Path]::GetFileName($ScriptPath), $_.Exception.Message)
        return 1
    }
    finally {
        if (Test-Path $tmpOut) { Remove-Item -Path $tmpOut -Force -ErrorAction SilentlyContinue }
        if (Test-Path $tmpErr) { Remove-Item -Path $tmpErr -Force -ErrorAction SilentlyContinue }
    }
}

$endTime = (Get-Date).AddMinutes($DurationMinutes)
Write-Host ("[monitor-loop] Starting; interval={0}s duration={1}m log={2}" -f $IntervalSeconds, $DurationMinutes, $logFile) -ForegroundColor Green

$iteration = 0
$failureStreak = 0
while ([DateTime]::Now -lt $endTime) {
    $iteration++
    $t0 = Get-Date
    try {
        Write-Host ("[monitor-loop] Iteration #{0} running checks..." -f $iteration) -ForegroundColor Cyan
        $statusJson = Join-Path $logsDir ("status_iter_${iteration}_" + (Get-Date).ToString('yyyyMMdd_HHmmss') + ".json")
        $code = Invoke-ChildAndLog -ScriptPath $checkScript -Args @('-ReturnExitCode', '-OutJson', $statusJson)
        if ($code -ne 0) {
            Add-Content -Path $logFile -Value ("[{0}] health check FAILED (exit {1}); statusJson={2}" -f (Get-Date).ToString('s'), $code, $statusJson)
            $failureStreak++
            # Auto remediation if available
            if (Test-Path $autoRemScript) {
                $dry = ($failureStreak -eq 1)
                $remArgs = @()
                if ($dry) { $remArgs += '-DryRun' }
                $remOut = Join-Path $logsDir ("auto_remediation_iter_${iteration}_" + (Get-Date).ToString('yyyyMMdd_HHmmss') + ".json")
                $remArgs += @('-OutJson', $remOut)
                Add-Content -Path $logFile -Value ("[{0}] invoking auto_remediation (dryRun={1}) -> {2}" -f (Get-Date).ToString('s'), $dry, $remOut)
                $rc = Invoke-ChildAndLog -ScriptPath $autoRemScript -Args $remArgs
                Add-Content -Path $logFile -Value ("[{0}] auto_remediation exit={1}" -f (Get-Date).ToString('s'), $rc)
                # Re-check after remediation attempt
                $statusJson2 = Join-Path $logsDir ("status_postfix_iter_${iteration}_" + (Get-Date).ToString('yyyyMMdd_HHmmss') + ".json")
                $code2 = Invoke-ChildAndLog -ScriptPath $checkScript -Args @('-ReturnExitCode', '-OutJson', $statusJson2)
                Add-Content -Path $logFile -Value ("[{0}] post-remediation health exit={1}; statusJson={2}" -f (Get-Date).ToString('s'), $code2, $statusJson2)
                if ($code2 -eq 0) { $failureStreak = 0 }
            }
        }
        else {
            # success resets streak
            if ($failureStreak -gt 0) { Add-Content -Path $logFile -Value ("[{0}] health OK -> reset failureStreak({1} -> 0)" -f (Get-Date).ToString('s'), $failureStreak) }
            $failureStreak = 0
        }
        if ($IncludeRateLimitProbe -and (Test-Path $rateProbeScript)) {
            # Safe probe defaults: gentle GET to health endpoints
            $probeJson = Join-Path $logsDir ("probe_iter_${iteration}_" + (Get-Date).ToString('yyyyMMdd_HHmmss') + ".json")
            $code2 = Invoke-ChildAndLog -ScriptPath $rateProbeScript -Args @(
                '-RequestsPerSide', '3',
                '-DelayMsBetweenRequests', '1000',
                '-Method', 'GET',
                '-CanaryEndpointPath', '/api/v2/health',
                '-LegacyEndpointPath', '/health',
                '-OutJson', $probeJson
            )
            if ($code2 -ne 0) {
                Add-Content -Path $logFile -Value ("[{0}] rate_limit_probe failed with exit {1}" -f (Get-Date).ToString('s'), $code2)
            }
            else {
                Add-Content -Path $logFile -Value ("[{0}] rate_limit_probe completed successfully -> {1}" -f (Get-Date).ToString('s'), $probeJson)
            }
        }
    }
    catch {
        Add-Content -Path $logFile -Value ("[{0}] Exception: {1}" -f (Get-Date).ToString('s'), $_.Exception.Message)
    }
    $t1 = Get-Date
    $elapsed = [int](($t1 - $t0).TotalSeconds)
    $sleep = [Math]::Max(0, $IntervalSeconds - $elapsed)
    if ($sleep -gt 0) {
        Write-Host ("[monitor-loop] Sleeping {0}s (elapsed {1}s)" -f $sleep, $elapsed) -ForegroundColor DarkGray
        Start-Sleep -Seconds $sleep
    }
}

Write-Host "[monitor-loop] Completed duration; exiting." -ForegroundColor Green
exit 0
