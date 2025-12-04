<#
Resilient Reboot Recovery (one-shot orchestrator)

Purpose:
  - After Windows reboot/logon, run a small, idempotent chain to recover the AGI workspace flow.
  - Steps: optional delay -> ensure queue -> ensure single worker -> restore session -> post-reboot verify.

Usage examples (PowerShell 5.1 compatible):
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts/resilient_reboot_recovery.ps1 -DryRun -Verbose
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts/resilient_reboot_recovery.ps1 -DelaySeconds 90 -OpenReport

Outputs:
  - outputs/resilient_reboot_recovery_summary.json (aggregate summary)

Notes:
  - Safe, user-scope only; relies on existing scripts in this repo.
  - Idempotent: re-running is fine; internal scripts already debounce where needed.
#>

param(
    [switch]$DryRun,
    [switch]$Execute,           # explicit execute mode (alias to NOT DryRun)
    [int]$DelaySeconds = 60,
    [switch]$NoDelay,           # when set, override delay to 0
    [switch]$OpenReport,
    [switch]$Verbose,
    [switch]$ShowSummary,       # when set, emit condensed console summary at end
    [switch]$MarkdownReport,    # when set, also emit a markdown summary file
    [switch]$JsonSlim,          # when set, also emit a slim JSON (no steps array) file
    [switch]$AutoFix,           # when set, pass -AutoFix to post_reboot_verify
    [switch]$StartWatchdog,     # when set, ask post_reboot_verify to ensure watchdog
    [switch]$HealthGate,        # enable quick status strict SLO gate (quick_status_smoke)
    [string]$HealthGateProfile = 'ops-normal', # profile: ops-normal|latency-first|ops-tight
    [switch]$HealthGateTrend,   # enable trend stability check
    [switch]$HealthGateExplain, # emit one-line JSON summary when gate passes
    [switch]$SkipHealthGate,    # force skip even if -HealthGate provided
    [int]$MaxHealthGateLogEntries = 200, # retain last N entries in JSONL log
    # --- New control / safety parameters ---
    [switch]$FailOnError,       # return non-zero exit code if any step errors
    [switch]$SkipEnsureQueue,
    [switch]$SkipEnsureWorker,
    [switch]$SkipSessionRestore,
    [switch]$SkipPostVerify,
    [int]$MinFreeMemoryMB = 0,  # if >0 require at least this much free physical memory before running main steps
    [int]$RecentRunCooldownMinutes = 0, # if >0 and last run within this window, skip heavy steps (fast idempotence)
    [switch]$Quiet              # suppress non-error informational output
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$scripts = Join-Path $root 'scripts'
$outDir = Join-Path $root 'outputs'
if (-not (Test-Path -LiteralPath $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }

function Write-Info([string]$msg) { if ($Quiet) { return }; Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Ok([string]$msg) { if ($Quiet) { return }; Write-Host "[ OK ] $msg" -ForegroundColor Green }
function Write-Warn([string]$msg) { if ($Quiet) { return }; Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err([string]$msg) { Write-Host "[ERR ] $msg" -ForegroundColor Red }

if ($Execute) { $DryRun = $false }

# Normalize delay
if ($NoDelay) { $DelaySeconds = 0 }

$__start = [DateTime]::UtcNow
$summary = [ordered]@{
    schemaVersion    = 1
    timestamp        = (Get-Date -Format o)
    dryRun           = [bool]$DryRun
    runMode          = if ($DryRun) { 'dryrun' } else { 'execute' }
    delaySec         = [int]$DelaySeconds
    'noDelay'        = [bool]$NoDelay
    openReport       = [bool]$OpenReport
    showSummary      = [bool]$ShowSummary
    markdownReport   = [bool]$MarkdownReport
    autoFix          = [bool]$AutoFix
    startWatch       = [bool]$StartWatchdog
    failOnError      = [bool]$FailOnError
    skips            = [ordered]@{
        ensureQueue    = [bool]$SkipEnsureQueue
        ensureWorker   = [bool]$SkipEnsureWorker
        sessionRestore = [bool]$SkipSessionRestore
        postVerify     = [bool]$SkipPostVerify
    }
    memoryGate       = $null
    cooldown         = $null
    healthGate       = $null
    steps            = @()
    success          = $null
    errorCount       = 0
    errorList        = @()
    firstFailureStep = $null
    durationMs       = 0
    finalizedEarly   = $false
    finalizeReason   = $null
}

# Internal early finalize flag replaces legacy goto usage
$FinalizeNow = $false

function Add-Step([string]$name, [string]$status, [string]$detail = '', [int]$durationMs = 0) {
    $step = [ordered]@{ name = $name; status = $status; detail = $detail; durationMs = $durationMs }
    $summary.steps += $step
    if ($status -eq 'error') {
        $summary.errorCount = [int]$summary.errorCount + 1
        $summary.errorList += ([ordered]@{ step = $name; message = $detail })
        if (-not $summary.firstFailureStep) { $summary.firstFailureStep = $name }
    }
    if ($Verbose) { Write-Info "Recorded: $name => $status ($detail)" }
}

function Invoke-IfExists([string]$path, [hashtable]$callArgs, [string]$stepName) {
    if ($DryRun) {
        $argPreview = if ($callArgs) { ($callArgs.GetEnumerator() | ForEach-Object { "-$($_.Key) $($_.Value)" }) -join ' ' } else { '' }
        Add-Step $stepName 'dryrun' $argPreview 0; return
    }
    if (-not (Test-Path -LiteralPath $path)) { Write-Warn "Missing: $path"; Add-Step $stepName 'skipped' 'not found'; return }
    try {
        if ($Verbose) {
            $argPreview = if ($callArgs) { ($callArgs.GetEnumerator() | ForEach-Object { "-$($_.Key) $($_.Value)" }) -join ' ' } else { '' }
            Write-Info "Run $($stepName): $argPreview"
        }
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        if ($callArgs) { & $path @callArgs | Out-Null } else { & $path | Out-Null }
        $sw.Stop()
        Add-Step $stepName 'ok' '' ([int]$sw.ElapsedMilliseconds)
        Write-Ok $stepName
    }
    catch {
        $msg = $_.Exception.Message
        $sw.Stop() | Out-Null
        Write-Err "$stepName failed: $msg"
        Add-Step $stepName 'error' $msg ([int]$sw.ElapsedMilliseconds)
    }
}

Write-Host '=== Resilient Reboot Recovery ===' -ForegroundColor Magenta
Write-Info  "Workspace: $root"

# Collect basic system info (best-effort)
try {
    $os = Get-CimInstance -ClassName Win32_OperatingSystem -ErrorAction SilentlyContinue
    $cs = Get-CimInstance -ClassName Win32_ComputerSystem -ErrorAction SilentlyContinue
    $memTotalMB = $null; $memFreeMB = $null
    if ($os) {
        if ($os.TotalVisibleMemorySize) { $memTotalMB = [int]([double]$os.TotalVisibleMemorySize / 1024) }
        if ($os.FreePhysicalMemory) { $memFreeMB = [int]([double]$os.FreePhysicalMemory / 1024) }
    }
    $summary.system = [ordered]@{
        machineName  = $env:COMPUTERNAME
        osVersion    = if ($os) { "$($os.Caption) $($os.Version) (Build $($os.BuildNumber))" } else { $PSVersionTable.OS }
        psVersion    = $PSVersionTable.PSVersion.ToString()
        cpuCount     = [int][Environment]::ProcessorCount
        memoryMB     = [ordered]@{ total = $memTotalMB; free = $memFreeMB }
        model        = if ($cs) { $cs.Model } else { $null }
        manufacturer = if ($cs) { $cs.Manufacturer } else { $null }
    }
}
catch { }

# 0) Optional stabilization delay
if ($DelaySeconds -gt 0) {
    if ($DryRun) { Add-Step 'delay' 'dryrun' "$DelaySeconds s" }
    else {
        Write-Info "Waiting $DelaySeconds seconds for system stabilization..."
        Start-Sleep -Seconds $DelaySeconds
        Add-Step 'delay' 'ok' "$DelaySeconds s" (1000 * $DelaySeconds)
    }
}

# 0.5) Recent run cooldown check
$cooldownMarker = Join-Path $outDir 'resilient_reboot_last_run.json'
if ($RecentRunCooldownMinutes -gt 0 -and -not $DryRun) {
    $nowUtc = [DateTimeOffset]::UtcNow
    $skipForCooldown = $false
    $prevInfo = $null
    if (Test-Path -LiteralPath $cooldownMarker) {
        try { $prevInfo = Get-Content -LiteralPath $cooldownMarker -Raw | ConvertFrom-Json } catch { $prevInfo = $null }
        if ($prevInfo -and $prevInfo.timestampUtc) {
            try {
                # Parse with DateTimeOffset to respect embedded timezone/offset and normalize to UTC
                $prevUtc = [DateTimeOffset]::Parse($prevInfo.timestampUtc).ToUniversalTime()
                $mins = ($nowUtc - $prevUtc).TotalMinutes
                $mins = [math]::Round($mins, 2)
                if ($mins -lt $RecentRunCooldownMinutes) {
                    $skipForCooldown = $true
                    $summary.cooldown = [ordered]@{ enabled = $true; minutes = $RecentRunCooldownMinutes; lastRunMinutesAgo = $mins; skipped = $true }
                }
            }
            catch { }
        }
    }
    if (-not $skipForCooldown) {
        # When we have a previous timestamp but are outside the cooldown window, surface the delta if available
        $lastAgo = $null
        try {
            if ($prevInfo -and $prevInfo.timestampUtc) {
                $prevUtc2 = [DateTimeOffset]::Parse($prevInfo.timestampUtc).ToUniversalTime()
                $lastAgo = [math]::Round((($nowUtc - $prevUtc2).TotalMinutes), 2)
            }
        }
        catch { $lastAgo = $null }
        $cd = [ordered]@{ enabled = $true; minutes = $RecentRunCooldownMinutes; skipped = $false }
        if ($null -ne $lastAgo) { $cd['lastRunMinutesAgo'] = $lastAgo }
        $summary.cooldown = $cd
    }
    if ($skipForCooldown) {
        Add-Step 'cooldown_skip' 'skipped' "Recent run within $RecentRunCooldownMinutes min"
        # still update marker fresh timestamp to reflect invocation
        try { @{ timestampUtc = $nowUtc.ToString('o'); reason = 'cooldown-skip' } | ConvertTo-Json | Out-File -FilePath $cooldownMarker -Encoding UTF8 } catch { }
        $FinalizeNow = $true
        $summary.finalizedEarly = $true
        $summary.finalizeReason = 'cooldown_skip'
    }
}

# memory gate (pre-step)
if ($MinFreeMemoryMB -gt 0) {
    $freeMB = $null
    try { $freeMB = $summary.system.memoryMB.free } catch { }
    if ($null -ne $freeMB -and $freeMB -lt $MinFreeMemoryMB) {
        $detail = "free=${freeMB}MB < min=${MinFreeMemoryMB}MB"
        Add-Step 'memory_gate' 'error' $detail
        $summary.memoryGate = [ordered]@{ enabled = $true; freeMB = $freeMB; min = $MinFreeMemoryMB; passed = $false }
        if ($FailOnError) { $summary.success = $false; $FinalizeNow = $true }
        if (-not $FinalizeNow) { $FinalizeNow = $true; $summary.finalizedEarly = $true; $summary.finalizeReason = 'memory_gate_failed' }
    }
    else {
        Add-Step 'memory_gate' (if ($DryRun) { 'dryrun' } else { 'ok' }) "free=$freeMB MB threshold=$MinFreeMemoryMB"
        $summary.memoryGate = [ordered]@{ enabled = $true; freeMB = $freeMB; min = $MinFreeMemoryMB; passed = $true }
    }
}
elseif ($MinFreeMemoryMB -eq 0) {
    $summary.memoryGate = [ordered]@{ enabled = $false }
}

if (-not $FinalizeNow) {
    # 1) Ensure Task Queue Server (8091)
    if (-not $SkipEnsureQueue) {
        $ensureQueue = Join-Path $scripts 'ensure_task_queue_server.ps1'
        Invoke-IfExists $ensureQueue @{ Port = 8091 } 'ensure_task_queue_server'
    }
    else { Add-Step 'ensure_task_queue_server' 'skipped' 'SkipEnsureQueue' }

    # 2) Ensure single worker
    if (-not $SkipEnsureWorker) {
        $ensureWorker = Join-Path $scripts 'ensure_rpa_worker.ps1'
        Invoke-IfExists $ensureWorker @{ EnforceSingle = $true; MaxWorkers = 1 } 'ensure_single_worker'
    }
    else { Add-Step 'ensure_single_worker' 'skipped' 'SkipEnsureWorker' }

    # 3) Session continuity restore (optionally open report)
    if (-not $SkipSessionRestore) {
        $sessionRestore = Join-Path $scripts 'session_continuity_restore.ps1'
        $restoreCallArgs = @{}
        if ($OpenReport) { $restoreCallArgs['OpenReport'] = $true }
        Invoke-IfExists $sessionRestore $restoreCallArgs 'session_continuity_restore'
    }
    else { Add-Step 'session_continuity_restore' 'skipped' 'SkipSessionRestore' }

    # 4) Post-reboot verify aggregation
    if (-not $SkipPostVerify) {
        $postVerify = Join-Path $scripts 'post_reboot_verify.ps1'
        $pvCallArgs = @{}
        if ($AutoFix) { $pvCallArgs['AutoFix'] = $true }
        if ($StartWatchdog) { $pvCallArgs['StartWatchdog'] = $true }
        if ($OpenReport) { $pvCallArgs['OpenReport'] = $true }
        Invoke-IfExists $postVerify $pvCallArgs 'post_reboot_verify'
    }
    else { Add-Step 'post_reboot_verify' 'skipped' 'SkipPostVerify' }

    # 5) Optional quick status health gate (strict SLO & trend checks)
    if ($HealthGate -and -not $SkipHealthGate) {
        $gateStepName = 'quick_status_health_gate'
        $gateScript = Join-Path $scripts 'tests' | Join-Path -ChildPath 'quick_status_smoke.ps1'
        if ($DryRun) {
            Add-Step $gateStepName 'dryrun' "profile=$HealthGateProfile trend=$($HealthGateTrend) explain=$($HealthGateExplain)"
            $summary.healthGate = [ordered]@{
                enabled       = $true
                dryRun        = $true
                profile       = $HealthGateProfile
                trendCheck    = [bool]$HealthGateTrend
                explain       = [bool]$HealthGateExplain
                maxLogEntries = [int]$MaxHealthGateLogEntries
            }
        }
        else {
            if (-not (Test-Path -LiteralPath $gateScript)) {
                Write-Warn "Health gate script missing: $gateScript"
                Add-Step $gateStepName 'skipped' 'not found'
            }
            else {
                try {
                    $hgArgs = @{'Strict' = $true; 'Profile' = $HealthGateProfile }
                    if ($HealthGateTrend) { $hgArgs['CheckTrendStability'] = $true }
                    if ($HealthGateExplain) { $hgArgs['ExplainStrict'] = $true }
                    if ($Verbose) {
                        $argPreview = ($hgArgs.GetEnumerator() | ForEach-Object { "-$($_.Key) $($_.Value)" }) -join ' '
                        Write-Info "Running health gate: $argPreview"
                    }
                    $hgOutputLines = & $gateScript @hgArgs 2>&1
                    $exitCode = $LASTEXITCODE
                    $jsonLine = $null
                    if ($HealthGateExplain -and $exitCode -eq 0) {
                        # Try simple line-based extraction first
                        $jsonLine = ($hgOutputLines | Where-Object { $_ -match '^\s*\{' } | Select-Object -First 1)
                        # Fallback: regex search across full output (singleline, non-greedy)
                        if (-not $jsonLine -or $jsonLine.Trim().Length -eq 0) {
                            try {
                                $allText = ($hgOutputLines -join "`n")
                                $m = [regex]::Match($allText, '(?s)\{.*?\}')
                                if ($m.Success) { $jsonLine = $m.Value }
                            }
                            catch { }
                        }
                    }
                    if ($exitCode -eq 0) {
                        $detail = if ($null -ne $jsonLine -and $jsonLine.Trim().Length -gt 0) { 'json-summary' } else { 'pass' }
                        Add-Step $gateStepName 'ok' $detail
                        Write-Ok "Health gate passed (profile=$HealthGateProfile)"

                        # Persist JSON summary if available (Explain+pass)
                        $hgOutPath = $null
                        $jsonSaved = $false
                        $jsonObj = $null
                        $hgLog = $null
                        $logCount = $null
                        if ($HealthGateExplain -and $null -ne $jsonLine -and $jsonLine.Trim().Length -gt 0) {
                            try { $jsonObj = $jsonLine | ConvertFrom-Json } catch { $jsonObj = $null }
                            $hgOutPath = Join-Path $outDir 'resilient_reboot_healthgate_latest.json'
                            if ($null -ne $jsonObj) {
                                $jsonObj | ConvertTo-Json -Depth 6 | Out-File -FilePath $hgOutPath -Encoding UTF8
                                $jsonSaved = $true
                            }
                            else {
                                $jsonLine | Out-File -FilePath $hgOutPath -Encoding UTF8
                                $jsonSaved = $true
                            }
                            # append JSONL log with timestamp for trend analysis
                            try {
                                $hgLog = Join-Path $outDir 'resilient_reboot_healthgate_log.jsonl'
                                $summaryValue = $jsonObj
                                if ($null -eq $summaryValue) { $summaryValue = $jsonLine }
                                $logObj = [ordered]@{
                                    timestamp = (Get-Date).ToString('o')
                                    profile   = $HealthGateProfile
                                    exitCode  = $exitCode
                                    explain   = $true
                                    summary   = $summaryValue
                                }
                                # Normalize existing log (if previous entries were multi-line JSON, collapse them to single-line objects)
                                if (Test-Path -LiteralPath $hgLog) {
                                    try {
                                        $raw = Get-Content -LiteralPath $hgLog -Raw -ErrorAction SilentlyContinue
                                        if ($raw -match "\r?\n") {
                                            $jsonMatchList = [regex]::Matches($raw, '(?s)\{.*?\}')
                                            if ($jsonMatchList.Count -gt 0) {
                                                $normalized = @()
                                                foreach ($jm in $jsonMatchList) { $normalized += (($jm.Value -replace '\r?\n', ' ') -replace '\s{2,}', ' ' ).Trim() }
                                                if ($normalized.Count -gt 0) { $normalized | Set-Content -LiteralPath $hgLog -Encoding UTF8 }
                                            }
                                        }
                                    }
                                    catch { }
                                }
                                # Append new entry as single-line JSON (PowerShell 5.1 lacks -Compress on ConvertTo-Json)
                                $logLine = ($logObj | ConvertTo-Json -Depth 6) -replace '\r?\n', ' ' -replace '\s{2,}', ' ' ; $logLine = $logLine.Trim()
                                Add-Content -Path $hgLog -Value $logLine -Encoding UTF8
                                # rotation: keep last N entries (lines) if configured
                                if ($MaxHealthGateLogEntries -gt 0 -and (Test-Path -LiteralPath $hgLog)) {
                                    try {
                                        $tail = Get-Content -LiteralPath $hgLog -Tail $MaxHealthGateLogEntries -ErrorAction SilentlyContinue
                                        if ($tail) { $tail | Set-Content -LiteralPath $hgLog -Encoding UTF8 }
                                    }
                                    catch { }
                                }
                                # count retained entries
                                try {
                                    if (Test-Path -LiteralPath $hgLog) {
                                        $logCount = (Get-Content -LiteralPath $hgLog -ErrorAction SilentlyContinue).Count
                                    }
                                }
                                catch { $logCount = $null }
                            }
                            catch { }
                        }
                    }
                    else {
                        Add-Step $gateStepName 'error' "exit=$exitCode"
                        Write-Err "Health gate failed (exit=$exitCode profile=$HealthGateProfile)"
                    }
                    $summary.healthGate = [ordered]@{
                        enabled     = $true
                        profile     = $HealthGateProfile
                        trendCheck  = [bool]$HealthGateTrend
                        explain     = [bool]$HealthGateExplain
                        exitCode    = $exitCode
                        jsonSummary = $jsonLine
                        outputTail  = ($hgOutputLines | Select-Object -Last 6) -join "\n"
                    }
                    $summary.healthGate['maxLogEntries'] = [int]$MaxHealthGateLogEntries
                    if ($jsonSaved -and $hgOutPath) { $summary.healthGate['jsonFile'] = $hgOutPath }
                    if ($hgLog) { $summary.healthGate['logFile'] = $hgLog }
                    if ($null -ne $logCount) { $summary.healthGate['logEntries'] = [int]$logCount }
                }
                catch {
                    $msg = $_.Exception.Message
                    Write-Err "Health gate exception: $msg"
                    Add-Step $gateStepName 'error' $msg
                    $summary.healthGate = [ordered]@{ enabled = $true; profile = $HealthGateProfile; error = $msg }
                }
            }
        }
    }
    elseif ($HealthGate -and $SkipHealthGate) {
        Add-Step 'quick_status_health_gate' 'skipped' 'SkipHealthGate'
        $summary.healthGate = [ordered]@{ enabled = $true; skipped = $true; reason = 'SkipHealthGate'; maxLogEntries = [int]$MaxHealthGateLogEntries }
    }
    else {
        $summary.healthGate = [ordered]@{ enabled = $false; maxLogEntries = [int]$MaxHealthGateLogEntries }
    }
}

# Write summary (finalization phase)
$sumFile = Join-Path $outDir 'resilient_reboot_recovery_summary.json'
try {
    # Finalize run stats
    $hasNonDrySteps = $summary.steps | Where-Object { $_.status -ne 'dryrun' }
    if (-not $DryRun) { $summary.dryRun = $false } elseif ($hasNonDrySteps -and $hasNonDrySteps.Count -gt 0) { $summary.dryRun = $false } else { $summary.dryRun = $true }
    $summary.runMode = if ($summary.dryRun) { 'dryrun' } else { 'execute' }
    $summary.success = ($summary.errorCount -eq 0)
    $summary.durationMs = [int]([DateTime]::UtcNow - $__start).TotalMilliseconds
    # Back-compat alias: provide systemInfo alongside system (requested field name)
    if ($summary.Contains('system')) { $summary['systemInfo'] = $summary.system }

    # Enriched step statistics & aliases (lightweight derived data)
    try {
        $totalSteps = $summary.steps.Count
        $okCount = ($summary.steps | Where-Object { $_.status -eq 'ok' }).Count
        $dryCount = ($summary.steps | Where-Object { $_.status -eq 'dryrun' }).Count
        $skipCount = ($summary.steps | Where-Object { $_.status -eq 'skipped' }).Count
        $errCount = ($summary.steps | Where-Object { $_.status -eq 'error' }).Count
        $summary.stepStats = [ordered]@{
            total   = [int]$totalSteps
            ok      = [int]$okCount
            dryrun  = [int]$dryCount
            skipped = [int]$skipCount
            error   = [int]$errCount
        }
        $summary.errorSteps = ($summary.steps | Where-Object { $_.status -eq 'error' } | ForEach-Object { $_.name })
        $summary.executedSteps = ($summary.steps | Where-Object { $_.status -in @('ok', 'error') } | ForEach-Object { $_.name })
    }
    catch { }

    # HealthGate retention alias for quick-access at top-level (PS 5.1 OrderedDictionary uses .Contains())
    if ($summary.healthGate) {
        try {
            if ($summary.healthGate.Contains('logEntries')) {
                $summary.retainedHealthGateLogEntries = [int]$summary.healthGate.logEntries
            }
        }
        catch { }
    }

    # Reason annotation for final runMode (helps diagnostics if DryRun partially executed)
    if ($summary.dryRun) {
        $summary.lastRunModeReason = 'All steps reported dryrun; -DryRun active and no executed steps.'
    }
    else {
        if ($DryRun) {
            $summary.lastRunModeReason = 'DryRun requested but one or more steps executed (internal path required real run).'
        }
        else {
            $summary.lastRunModeReason = 'Normal execution path; DryRun not set.'
        }
    }

    $summary | ConvertTo-Json -Depth 6 | Out-File -FilePath $sumFile -Encoding UTF8
    Write-Ok "Summary saved: $sumFile"

    # Update cooldown/run marker unconditionally for idempotence and fast skip decisions on future invocations
    try {
        if (-not $cooldownMarker) { $cooldownMarker = Join-Path $outDir 'resilient_reboot_last_run.json' }
        $runMarker = [ordered]@{
            timestampUtc   = [DateTime]::UtcNow.ToString('o')
            success        = [bool]$summary.success
            errorCount     = [int]$summary.errorCount
            durationMs     = [int]$summary.durationMs
            dryRun         = [bool]$summary.dryRun
            runMode        = $summary.runMode
            firstFailure   = $summary.firstFailureStep
            failureReason  = $(if ($summary.firstFailureStep) { ($summary.errorList | Select-Object -First 1).message } else { $null })
            finalizedEarly = [bool]$summary.finalizedEarly
        }
        $runMarker | ConvertTo-Json -Depth 4 | Out-File -FilePath $cooldownMarker -Encoding UTF8
        if (-not $summary.cooldown) { $summary.cooldown = [ordered]@{} }
        $summary.cooldown['markerUpdated'] = $true
    }
    catch { Write-Warn "Failed to update cooldown marker: $($_.Exception.Message)" }
}
catch { Write-Err "Failed to save summary: $($_.Exception.Message)" }

if (-not $Quiet) { Write-Host '=== Recovery Complete ===' -ForegroundColor Magenta }
if ($ShowSummary) {
    try {
        $okSteps = ($summary.steps | Where-Object { $_.status -eq 'ok' }).Count
        $errSteps = ($summary.steps | Where-Object { $_.status -eq 'error' }).Count
        $skipSteps = ($summary.steps | Where-Object { $_.status -eq 'skipped' }).Count
        $drySteps = ($summary.steps | Where-Object { $_.status -eq 'dryrun' }).Count
        $gateStatus = if ($summary.healthGate -and $summary.healthGate.enabled) {
            if ($summary.healthGate.exitCode -eq 0 -and $summary.healthGate.exitCode -ne $null) { 'pass' } elseif ($summary.healthGate.exitCode -ne $null) { "fail(exit=$($summary.healthGate.exitCode))" } elseif ($summary.healthGate.skipped) { 'skipped' } else { 'n/a' }
        }
        else { 'disabled' }
        $memGate = if ($summary.memoryGate -and $summary.memoryGate.enabled) {
            if ($summary.memoryGate.passed) { 'pass' } else { 'fail' }
        }
        else { 'disabled' }
        $cooldownInfo = if ($summary.cooldown) {
            if ($summary.cooldown.skipped) { "skipped(last=$($summary.cooldown.lastRunMinutesAgo) min)" } elseif ($summary.cooldown.enabled) { "active(last=$($summary.cooldown.lastRunMinutesAgo) min)" } else { 'inactive' }
        }
        else { 'inactive' }
        if (-not $Quiet) { Write-Host "--- Condensed Summary ---" -ForegroundColor DarkCyan }
        Write-Host ("Mode       : {0}" -f $summary.runMode)
        Write-Host ("Success    : {0}" -f ($summary.success))
        Write-Host ("Errors     : {0}" -f ($summary.errorCount))
        if ($summary.firstFailureStep) { Write-Host ("FirstFail  : {0}" -f $summary.firstFailureStep) -ForegroundColor Yellow }
        Write-Host ("DurationMs : {0}" -f $summary.durationMs)
        Write-Host ("Steps(ok/err/skip/dry): {0}/{1}/{2}/{3}" -f $okSteps, $errSteps, $skipSteps, $drySteps)
        Write-Host ("MemoryGate : {0}" -f $memGate)
        Write-Host ("HealthGate : {0}" -f $gateStatus)
        Write-Host ("Cooldown   : {0}" -f $cooldownInfo)
        if ($summary.finalizedEarly) { Write-Host ("Finalized  : early ($($summary.finalizeReason))") }
        if ($summary.healthGate -and $summary.healthGate.jsonSummary -and $summary.healthGate.jsonSummary.Trim().Length -gt 0) {
            Write-Host "HealthGate JSON Summary:" -ForegroundColor Cyan
            Write-Host ($summary.healthGate.jsonSummary.Trim())
        }
        if (-not $Quiet) { Write-Host "--------------------------" -ForegroundColor DarkCyan }
    }
    catch { Write-Warn "Failed to emit condensed summary: $($_.Exception.Message)" }
}
function Write-MarkdownReport($summaryObj, $runMarkerObj) {
    $mdPath = Join-Path $outDir 'resilient_reboot_recovery_summary.md'
    $lines = @()
    $lines += '# Resilient Reboot Recovery Summary'
    $lines += ''
    $lines += "**Timestamp (local)**: $(Get-Date)"
    $lines += "**Timestamp (UTC)**: $($summaryObj.timestamp)"
    $lines += "**Mode**: $($summaryObj.runMode)  "
    $lines += "**DryRun**: $($summaryObj.dryRun)  "
    $lines += "**Success**: $($summaryObj.success)  "
    $lines += "**Errors**: $($summaryObj.errorCount)  "
    if ($summaryObj.firstFailureStep) { $lines += "**First Failure Step**: $($summaryObj.firstFailureStep)  " }
    if ($summaryObj.finalizedEarly) { $lines += "**Finalized Early**: true ($($summaryObj.finalizeReason))  " }
    $lines += "**Duration (ms)**: $($summaryObj.durationMs)  "
    $lines += ''
    $lines += '### Steps'
    foreach ($s in $summaryObj.steps) {
        $detailFmt = if ($s.detail -and $s.detail.Trim().Length -gt 0) { $s.detail } else { 'no detail' }
        $durFmt = if ($s.durationMs -ne $null) { "$($s.durationMs) ms" } else { '(n/a)' }
        $lines += "- **$($s.name)**: $($s.status) ($detailFmt) $durFmt"
    }
    $lines += ''
    $lines += '### Gates'
    if ($summaryObj.memoryGate) {
        $memEnabled = if ($summaryObj.memoryGate.enabled -ne $null) { $summaryObj.memoryGate.enabled } else { '(n/a)' }
        $memPassed = if ($summaryObj.memoryGate.Contains('passed')) { $summaryObj.memoryGate.passed } else { '(n/a)' }
        $memFree = if ($summaryObj.memoryGate.freeMB -ne $null) { $summaryObj.memoryGate.freeMB } else { '(n/a)' }
        $memMin = if ($summaryObj.memoryGate.min -ne $null) { $summaryObj.memoryGate.min } else { '(n/a)' }
        $lines += "- Memory Gate: enabled=$memEnabled passed=$memPassed freeMB=$memFree min=$memMin"
    }
    if ($summaryObj.healthGate) {
        $hgEnabled = if ($summaryObj.healthGate.enabled -ne $null) { $summaryObj.healthGate.enabled } else { '(n/a)' }
        $hgExit = if ($summaryObj.healthGate.exitCode -ne $null) { $summaryObj.healthGate.exitCode } else { '(n/a)' }
        $hgTrend = if ($summaryObj.healthGate.trendCheck -ne $null) { $summaryObj.healthGate.trendCheck } else { '(n/a)' }
        $hgProfile = if ($summaryObj.healthGate.profile) { $summaryObj.healthGate.profile } else { '(n/a)' }
        $lines += "- Health Gate: enabled=$hgEnabled exitCode=$hgExit trendCheck=$hgTrend profile=$hgProfile"
    }
    if ($summaryObj.cooldown) {
        $cdEnabled = if ($summaryObj.cooldown.enabled -ne $null) { $summaryObj.cooldown.enabled } else { '(n/a)' }
        $cdSkipped = if ($summaryObj.cooldown.skipped -ne $null) { $summaryObj.cooldown.skipped } else { '(n/a)' }
        $cdMinutes = if ($summaryObj.cooldown.minutes -ne $null) { $summaryObj.cooldown.minutes } else { '(n/a)' }
        $cdAgo = if ($summaryObj.cooldown.lastRunMinutesAgo -ne $null) { $summaryObj.cooldown.lastRunMinutesAgo } else { '(n/a)' }
        $lines += "- Cooldown: enabled=$cdEnabled skipped=$cdSkipped minutes=$cdMinutes lastRunMinutesAgo=$cdAgo"
    }
    $lines += ''
    $lines += '### Errors'
    if ($summaryObj.errorCount -gt 0) {
        foreach ($e in $summaryObj.errorList) { $lines += "- $($e.step): $($e.message)" }
    }
    else { $lines += '- (none)' }
    $lines += ''
    $lines += '### System'
    if ($summaryObj.system) {
        $lines += "- Machine: $($summaryObj.system.machineName)"
        $lines += "- OS: $($summaryObj.system.osVersion)"
        $lines += "- PSVersion: $($summaryObj.system.psVersion)"
        $lines += "- CPU Count: $($summaryObj.system.cpuCount)"
        if ($summaryObj.system.memoryMB) { $lines += "- Memory: total=$($summaryObj.system.memoryMB.total)MB free=$($summaryObj.system.memoryMB.free)MB" }
    }
    $lines += ''
    $lines += '### Marker'
    $lines += "- Run Mode: $(if ($runMarkerObj) { $runMarkerObj.runMode } else { '(n/a)' })"
    $lines += "- Finalized Early: $(if ($runMarkerObj) { $runMarkerObj.finalizedEarly } else { '(n/a)' })"
    if ($runMarkerObj -and $runMarkerObj.failureReason) { $lines += "- Failure Reason: $($runMarkerObj.failureReason)" }
    $lines -join "`n" | Out-File -FilePath $mdPath -Encoding UTF8
    Write-Ok "Markdown report generated: $mdPath"
}
if ($MarkdownReport) {
    try { Write-MarkdownReport -summaryObj $summary -runMarkerObj $runMarker } catch { Write-Warn "Failed to write markdown report: $($_.Exception.Message)" }
}
if ($JsonSlim) {
    try {
        $slimPath = Join-Path $outDir 'resilient_reboot_recovery_slim.json'
        $slim = [ordered]@{
            schemaVersion  = $summary.schemaVersion
            timestamp      = $summary.timestamp
            runMode        = $summary.runMode
            success        = $summary.success
            errorCount     = $summary.errorCount
            durationMs     = $summary.durationMs
            finalizedEarly = $summary.finalizedEarly
            finalizeReason = $summary.finalizeReason
            memoryGate     = $summary.memoryGate
            healthGate     = $(if ($summary.healthGate) { [ordered]@{ enabled = $summary.healthGate.enabled; exitCode = $summary.healthGate.exitCode } } else { $null })
            cooldown       = $summary.cooldown
            stepStats      = $summary.stepStats
        }
        $slim | ConvertTo-Json -Depth 5 | Out-File -FilePath $slimPath -Encoding UTF8
        Write-Ok "Slim JSON saved: $slimPath"
    }
    catch { Write-Warn "Failed to write slim JSON: $($_.Exception.Message)" }
}
if ($FailOnError -and -not $summary.success) { exit 1 } else { exit 0 }
