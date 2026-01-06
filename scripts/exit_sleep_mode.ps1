param(
    [switch]$DryRun,
    [string]$OutJson,
    [string]$HistoryJsonl,
    [int]$LatencyWarnMs,
    [int]$LatencyCriticalMs
)

$ErrorActionPreference = 'Stop'

function Get-WorkspaceRoot {
    $here = $PSScriptRoot
    if (-not $here) { $here = Split-Path -Parent $MyInvocation.MyCommand.Path }
    return (Split-Path -Parent $here)
}

$root = Get-WorkspaceRoot
Write-Host "Exiting Sleep Mode (AI) — resuming background monitors..." -ForegroundColor Cyan

# 1) Start worker monitor (daemon) if script exists
$startWorkerMon = Join-Path $root 'scripts/start_worker_monitor_daemon.ps1'
if (Test-Path -LiteralPath $startWorkerMon) {
    if ($DryRun) {
        Write-Host "[DryRun] Would start: $startWorkerMon -KillExisting" -ForegroundColor Yellow
    }
    else {
        & $startWorkerMon -KillExisting
    }
}
else {
    Write-Host "Skip: start_worker_monitor_daemon.ps1 not found" -ForegroundColor DarkGray
}

# 2) Start cache validation monitor if available
$startCacheMon = Join-Path $root 'scripts/start_cache_validation_monitor.ps1'
if (Test-Path -LiteralPath $startCacheMon) {
    if ($DryRun) {
        Write-Host "[DryRun] Would start: $startCacheMon -KillExisting" -ForegroundColor Yellow
    }
    else {
        & $startCacheMon -KillExisting
    }
}
else {
    Write-Host "Skip: start_cache_validation_monitor.ps1 not found" -ForegroundColor DarkGray
}

# 3) Start Task Watchdog in background (replicates VS Code task behavior)
$py = Join-Path $root 'fdo_agi_repo/.venv/Scripts/python.exe'
$watchdog = Join-Path $root 'fdo_agi_repo/scripts/task_watchdog.py'
if (-not (Test-Path -LiteralPath $watchdog)) {
    Write-Host "Skip: task_watchdog.py not found" -ForegroundColor DarkGray
}
else {
    $exe = 'python'
    if (Test-Path -LiteralPath $py) { $exe = $py }
    $wdArgs = "`"$watchdog`" --server http://127.0.0.1:8091 --interval 60 --auto-recover"
    if ($DryRun) {
        Write-Host "[DryRun] Would start watchdog: $exe $wdArgs" -ForegroundColor Yellow
    }
    else {
        Start-Process -FilePath $exe -ArgumentList $wdArgs -WindowStyle Hidden | Out-Null
        Write-Host "Watchdog started" -ForegroundColor Green
    }
}

# 4) Core quick health probe (optional)
$CoreProbe = Join-Path $root 'scripts/core_quick_probe.ps1'
$CoreOk = $null
$CoreLatencyMs = $null
$CoreError = $null
if (Test-Path -LiteralPath $CoreProbe) {
    if ($DryRun) {
        Write-Host "[DryRun] Would run: $CoreProbe" -ForegroundColor Yellow
        $CoreOk = $true
    }
    else {
        try {
            $sw = [System.Diagnostics.Stopwatch]::StartNew()
            & $CoreProbe
            $sw.Stop()
            $CoreLatencyMs = [int64]$sw.Elapsed.TotalMilliseconds
            if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) { throw "Core probe exit $LASTEXITCODE" }
            $CoreOk = $true
            # Critical latency hook
            if (-not $DryRun -and $LatencyCriticalMs -and $CoreLatencyMs -ge [int64]$LatencyCriticalMs) {
                Write-Host ("Core latency {0} ms ≥ critical threshold {1} ms" -f $CoreLatencyMs, $LatencyCriticalMs) -ForegroundColor Red
                $quickStatus = Join-Path $root 'scripts/quick_status.ps1'
                if (Test-Path -LiteralPath $quickStatus) {
                    try {
                        & $quickStatus -AlertOnDegraded -LogJsonl
                    }
                    catch {
                        Write-Host "quick_status alert/log failed (critical): $_" -ForegroundColor DarkRed
                    }
                }
            }
        }
        catch {
            $CoreOk = $false
            Write-Host "Core probe failed: $_" -ForegroundColor Red
            $CoreError = ($_ | Out-String)
            # On failure, emit a quick degraded alert/log snapshot (best-effort)
            $quickStatus = Join-Path $root 'scripts/quick_status.ps1'
            if (Test-Path -LiteralPath $quickStatus) {
                try {
                    & $quickStatus -AlertOnDegraded -LogJsonl
                }
                catch {
                    Write-Host "quick_status alert/log failed: $_" -ForegroundColor DarkRed
                }
            }
        }
    }
}
else {
    Write-Host "Skip: core_quick_probe.ps1 not found" -ForegroundColor DarkGray
}

$summary = [pscustomobject]@{
    mode       = 'sleep-exit'
    dryRun     = [bool]$DryRun
    CoreProbe = $(
        if ($CoreOk -ne $null) {
            $obj = @{ ok = [bool]$CoreOk }
            if ($CoreLatencyMs -ne $null) { $obj.latencyMs = [int64]$CoreLatencyMs }
            if (-not $DryRun -and $CoreOk -eq $true -and $CoreLatencyMs -ne $null -and $LatencyWarnMs) {
                $obj.warn = [bool]([int64]$CoreLatencyMs -ge [int64]$LatencyWarnMs)
            }
            if (-not $DryRun -and $CoreOk -eq $true -and $CoreLatencyMs -ne $null -and $LatencyCriticalMs) {
                $obj.critical = [bool]([int64]$CoreLatencyMs -ge [int64]$LatencyCriticalMs)
            }
            if ($CoreError) {
                $trunc = $CoreError.Trim()
                if ($trunc.Length -gt 400) { $trunc = $trunc.Substring(0, 400) + '...' }
                $obj.error = $trunc
            }
            $obj
        }
        else { $null }
    )
    timestamp  = (Get-Date).ToString('s')
}
$summary | ConvertTo-Json -Depth 6 | Write-Output

# Optional latency warning message (non-dry-run)
if (-not $DryRun -and $CoreOk -eq $true -and $CoreLatencyMs -ne $null -and $LatencyWarnMs) {
    if ([int64]$CoreLatencyMs -ge [int64]$LatencyWarnMs) {
        Write-Host ("Core latency {0} ms ≥ warn threshold {1} ms" -f $CoreLatencyMs, $LatencyWarnMs) -ForegroundColor Yellow
    }
}

if ($OutJson -and $OutJson.Trim() -ne '') {
    try {
        $dir = Split-Path -Parent $OutJson
        if ($dir -and -not (Test-Path -LiteralPath $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
        $summary | ConvertTo-Json -Depth 6 | Out-File -FilePath $OutJson -Encoding UTF8 -Force
        Write-Host "Summary written to: $OutJson" -ForegroundColor DarkGreen
    }
    catch {
        Write-Host "Failed to write OutJson '$OutJson': $_" -ForegroundColor DarkRed
    }
}

# Optional: append a JSONL history record (only when not DryRun)
if (-not $DryRun -and $HistoryJsonl -and $HistoryJsonl.Trim() -ne '') {
    try {
        $dir2 = Split-Path -Parent $HistoryJsonl
        if ($dir2 -and -not (Test-Path -LiteralPath $dir2)) {
            New-Item -ItemType Directory -Path $dir2 -Force | Out-Null
        }
        $record = [pscustomobject]@{
            timestamp = (Get-Date).ToString('o')
            ok        = $(if ($CoreOk -eq $true) { $true } else { $false })
            latencyMs = $(if ($CoreLatencyMs -ne $null) { [int64]$CoreLatencyMs } else { $null })
            warn      = $(if ($LatencyWarnMs -and $CoreLatencyMs -ne $null -and $CoreOk -eq $true) { [bool]([int64]$CoreLatencyMs -ge [int64]$LatencyWarnMs) } else { $false })
            critical  = $(if ($LatencyCriticalMs -and $CoreLatencyMs -ne $null -and $CoreOk -eq $true) { [bool]([int64]$CoreLatencyMs -ge [int64]$LatencyCriticalMs) } else { $false })
        }
        # Use -Compress to output single-line JSON for proper JSONL format
        # Use UTF8NoBOM encoding (PowerShell 6+) or UTF8 with manual BOM removal
        $jsonLine = ($record | ConvertTo-Json -Depth 5 -Compress)
        # Append without BOM by using .NET StreamWriter
        $sw = New-Object System.IO.StreamWriter($HistoryJsonl, $true, [System.Text.UTF8Encoding]::new($false))
        $sw.WriteLine($jsonLine)
        $sw.Close()
        Write-Host "History appended to: $HistoryJsonl" -ForegroundColor DarkGreen
    }
    catch {
        Write-Host "Failed to append HistoryJsonl '$HistoryJsonl': $_" -ForegroundColor DarkRed
    }
}
exit 0