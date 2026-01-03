param(
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

function Get-WorkspaceRoot {
    $here = $PSScriptRoot
    if (-not $here) { $here = Split-Path -Parent $MyInvocation.MyCommand.Path }
    return (Split-Path -Parent $here)
}

function Stop-ProcessesByPatterns {
    param([string[]]$Patterns)
    $stopped = @()
    try {
        $procs = Get-CimInstance Win32_Process | Where-Object {
            $cmd = $_.CommandLine
            $Patterns | ForEach-Object { if ($cmd -and ($cmd -like "*$_*")) { return $true } }
            return $false
        }
        foreach ($p in $procs) {
            try {
                if ($DryRun) {
                    Write-Host "[DryRun] Would stop PID=$($p.ProcessId) CMD=$($p.CommandLine)" -ForegroundColor Yellow
                }
                else {
                    Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop
                    $stopped += $p.ProcessId
                    Write-Host "Stopped PID=$($p.ProcessId): $($p.CommandLine)" -ForegroundColor Cyan
                }
            }
            catch {
                Write-Host "Failed to stop PID=$($p.ProcessId): $_" -ForegroundColor Red
            }
        }
    }
    catch {
        Write-Host "Process scan failed: $_" -ForegroundColor Red
    }
    return $stopped
}

$root = Get-WorkspaceRoot
Write-Host "Entering Sleep Mode (AI) — preparing maintenance window..." -ForegroundColor Cyan

# 1) Quiesce: stop background monitors/workers (safe subset)
$patterns = @(
    'task_watchdog.py',
    'worker_monitor_daemon.ps1',
    'worker_monitor_foreground.ps1',
    'cache_validation_monitor_daemon.ps1'
)
$stoppedPids = Stop-ProcessesByPatterns -Patterns $patterns

# 2) Run nightly maintenance bundle (best-effort, existing scripts only)
$steps = @(
    @{ name = 'daily_maintenance'; path = (Join-Path $root 'scripts/daily_monitoring_maintenance.ps1'); args = @() },
    @{ name = 'monitoring_report'; path = (Join-Path $root 'scripts/generate_monitoring_report.ps1'); args = @('-Hours', '24') },
    @{ name = 'rotate_snapshots'; path = (Join-Path $root 'scripts/rotate_status_snapshots.ps1'); args = @('-Zip') },
    @{ name = 'autopoietic_report'; path = (Join-Path $root 'scripts/generate_autopoietic_report.ps1'); args = @('-Hours', '24') },
    @{ name = 'backup_eod'; path = (Join-Path $root 'scripts/end_of_day_backup.ps1'); args = @('-Note', 'SleepMode') }
)
$results = @()
foreach ($s in $steps) {
    $exists = Test-Path -LiteralPath $s.path
    if (-not $exists) {
        Write-Host ("Skip {0}: not found -> {1}" -f $s.name, $s.path) -ForegroundColor DarkGray
        $results += [pscustomobject]@{ step = $s.name; ok = $false; skipped = $true }
        continue
    }
    if ($DryRun) {
        Write-Host "[DryRun] Would run: $($s.path) $($s.args -join ' ')" -ForegroundColor Yellow
        $results += [pscustomobject]@{ step = $s.name; ok = $true; dryrun = $true }
        continue
    }
    try {
        & $s.path @($s.args)
        if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) { throw "ExitCode=$LASTEXITCODE" }
        $results += [pscustomobject]@{ step = $s.name; ok = $true }
    }
    catch {
        Write-Host "Step failed: $($s.name) ($_ )" -ForegroundColor Red
        $results += [pscustomobject]@{ step = $s.name; ok = $false; error = "$_" }
    }
}

# 3) Summary
$summary = [pscustomobject]@{
    mode        = 'sleep-enter'
    dryRun      = [bool]$DryRun
    stoppedPids = $stoppedPids
    steps       = $results
    timestamp   = (Get-Date).ToString('s')
}
$summary | ConvertTo-Json -Depth 6 | Write-Output
exit 0