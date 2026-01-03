<#
Post-reboot consolidated verification script for Trinity (AGI + Monitoring + Queue + Watchdog).

Usage examples:
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts/post_reboot_verify.ps1
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts/post_reboot_verify.ps1 -AutoFix -StartWatchdog

Parameters:
    -AutoFix       : Pass through to system restart check to attempt automatic remediation.
    -StartWatchdog : If watchdog process not detected, start it (auto-recover enabled).
    -OpenReport    : Open session continuity markdown after restore.
    -Verbose       : More detailed progress output.

Outputs (written under outputs/):
    quick_status_latest.json (refreshed)
    post_reboot_verify_summary.json (aggregate results)

Safe: Only reads/writes inside workspace and starts standard processes already used.
#>
param(
    [switch]$AutoFix,
    [switch]$StartWatchdog,
    [switch]$OpenReport,
    [int]$TimeoutSec = 10,
    [switch]$Verbose
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Info($msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Ok($msg) { Write-Host "[ OK ] $msg" -ForegroundColor Green }
function Write-Err($msg) { Write-Host "[ERR ] $msg" -ForegroundColor Red }

Write-Host "=== Trinity Post-Reboot Verification ===" -ForegroundColor Magenta
Write-Info "Workspace root: $(Split-Path -Parent $PSScriptRoot)"

$summary = [ordered]@{
    timestamp     = (Get-Date).ToString('s')
    autoFix       = [bool]$AutoFix
    startWatchdog = [bool]$StartWatchdog
    steps         = @()
}

function Add-StepResult([string]$name, [string]$status, [string]$detail) {
    $summary.steps += [ordered]@{ name = $name; status = $status; detail = $detail }
    if ($Verbose) { Write-Info "Recorded: $name => $status" }
}

# Robust process query with CommandLine (fallback to CIM when needed)
function Get-ProcessByCommandLineLike {
    param(
        [Parameter(Mandatory)] [string]$Pattern
    )
    try {
        # Prefer CIM for reliable CommandLine access on Windows PowerShell 5.1
        $procs = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like $Pattern }
        return $procs
    }
    catch {
        # Fallback minimal (may not have CommandLine)
        return @()
    }
}

# Helper to safely invoke another ps1
function Invoke-ScriptIfExists {
    param(
        [Parameter(Mandatory)] [string]$Path,
        [string]$Arguments = '',
        [string]$StepName = (Split-Path -Leaf $Path)
    )
    if (-not (Test-Path -LiteralPath $Path)) {
        Write-Warn "Missing script: $Path"
        Add-StepResult $StepName 'skipped' 'not found'
        return
    }
    try {
        Write-Info "Running: $StepName $Arguments"
        $cmd = "& '$Path' $Arguments"
        Invoke-Expression $cmd | Out-Null
        Add-StepResult $StepName 'ok' $Arguments
        Write-Ok $StepName
    }
    catch {
        Write-Err "$StepName failed: $($_.Exception.Message)"
        Add-StepResult $StepName 'error' $($_.Exception.Message)
    }
}

$root = Split-Path -Parent $PSScriptRoot
$scripts = Join-Path $root 'scripts'
$fdoRepo = Join-Path $root 'fdo_agi_repo'
$outDir = Join-Path $root 'outputs'
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }

# 1. System after restart check
$sysCheck = Join-Path $scripts 'check_system_after_restart.ps1'
Invoke-ScriptIfExists -Path $sysCheck -Arguments ($(if ($AutoFix) { '-AutoFix' } else { '' })) -StepName 'check_system_after_restart'

# 2. Session continuity restore
$sessionRestore = Join-Path $scripts 'session_continuity_restore.ps1'
$restoreArgs = @()
if ($OpenReport) { $restoreArgs += '-OpenReport' }
Invoke-ScriptIfExists -Path $sessionRestore -Arguments ($restoreArgs -join ' ') -StepName 'session_continuity_restore'

# 3. Queue health
$queueHealth = Join-Path $scripts 'queue_health_check.ps1'
Invoke-ScriptIfExists -Path $queueHealth -StepName 'queue_health_check'

# 4. Quick status snapshot
$quickStatus = Join-Path $scripts 'quick_status.ps1'
if (Test-Path $quickStatus) {
    try {
        Write-Info 'Generating quick status JSON'
        & $quickStatus -OutJson (Join-Path $outDir 'quick_status_latest.json') | Out-Null
        Add-StepResult 'quick_status' 'ok' 'quick_status_latest.json updated'
        Write-Ok 'quick_status'
    }
    catch { Write-Err "quick_status failed: $($_.Exception.Message)"; Add-StepResult 'quick_status' 'error' $($_.Exception.Message) }
}
else {
    Write-Warn 'quick_status.ps1 not found'
    Add-StepResult 'quick_status' 'skipped' 'not found'
}

# 5. Ensure single worker
$ensureWorker = Join-Path $scripts 'ensure_rpa_worker.ps1'
Invoke-ScriptIfExists -Path $ensureWorker -Arguments '-EnforceSingle -MaxWorkers 1' -StepName 'ensure_single_worker'

# 6. Watchdog check & optional start
Write-Info 'Checking watchdog process'
$watchdog = Get-ProcessByCommandLineLike -Pattern '*task_watchdog.py*'
if ($watchdog -and $watchdog.Count -gt 0) {
    Add-StepResult 'watchdog' 'ok' 'already running'
    Write-Ok 'watchdog running'
}
else {
    Write-Warn 'watchdog not running'
    if ($StartWatchdog) {
        $watchdogScript = Join-Path $fdoRepo 'scripts/task_watchdog.py'
        if (Test-Path $watchdogScript) {
            $py = Join-Path $fdoRepo '.venv/Scripts/python.exe'
            if (-not (Test-Path $py)) { $py = 'python' }
            try {
                Write-Info 'Starting watchdog...'
                Start-Process -FilePath $py -ArgumentList "`"$watchdogScript`" --server http://127.0.0.1:8091 --interval 60 --auto-recover" -WindowStyle Hidden | Out-Null
                Start-Sleep -Seconds 2
                $running = Get-ProcessByCommandLineLike -Pattern '*task_watchdog.py*'
                if ($running -and $running.Count -gt 0) { Add-StepResult 'watchdog' 'started' 'watchdog launched'; Write-Ok 'watchdog started' } else { Add-StepResult 'watchdog' 'error' 'launch did not appear'; Write-Err 'watchdog launch not detected' }
            }
            catch { Add-StepResult 'watchdog' 'error' $($_.Exception.Message); Write-Err "watchdog start failed: $($_.Exception.Message)" }
        }
        else {
            Add-StepResult 'watchdog' 'skipped' 'script not found'; Write-Warn 'task_watchdog.py not found'
        }
    }
    else {
        Add-StepResult 'watchdog' 'missing' 'not running; StartWatchdog not specified'
    }
}

# 7. Aggregate summary file
$summaryFile = Join-Path $outDir 'post_reboot_verify_summary.json'
try {
    $summary | ConvertTo-Json -Depth 6 | Out-File -FilePath $summaryFile -Encoding UTF8
    Write-Ok "Summary saved: $summaryFile"
}
catch { Write-Err "Failed to write summary: $($_.Exception.Message)" }

Write-Host "=== Verification Complete ===" -ForegroundColor Magenta
if ($Verbose) { $summary }