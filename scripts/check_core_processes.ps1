#requires -Version 5.1
Param(
    [switch]$SummaryOnly,
    [string]$OutJson,
    [int]$WarnCpuPercent = 90,
    [int]$WarnMinAvailMB = 512,
    [int]$MinWorkers = 1,
    [switch]$RequireWatchdog
)

$ErrorActionPreference = 'SilentlyContinue'

function Get-HostMetrics {
    try {
        # Take two samples for a more stable CPU reading
        $cpuSample = (Get-Counter -Counter '\\Processor(_Total)\\% Processor Time' -SampleInterval 1 -MaxSamples 2).CounterSamples | Select-Object -Last 1
        $cpu = [math]::Round($cpuSample.CookedValue, 1)
    }
    catch { $cpu = $null }

    try {
        $mem = (Get-Counter -Counter '\\Memory\\Available MBytes').CounterSamples[0].CookedValue
        $mem = [math]::Round($mem, 0)
    }
    catch { $mem = $null }

    return [pscustomobject]@{
        cpu_percent_total = $cpu
        mem_available_mb  = $mem
        timestamp         = (Get-Date).ToString('yyyy-MM-dd HH:mm:ssK')
    }
}

function Get-ProcMatches {
    param(
        [string[]]$Patterns
    )
    $list = @()
    # Iterate processes via CIM to get CommandLine reliably on PS 5.1
    try {
        $cims = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue
    }
    catch { $cims = @() }
    foreach ($p in $cims) {
        $cmd = $p.CommandLine
        if (-not $cmd) { continue }
        foreach ($pat in $Patterns) {
            if ($cmd -like $pat) {
                # Attach perf info from matching process id
                $proc = Get-Process -Id $p.ProcessId -ErrorAction SilentlyContinue
                $wsMB = if ($proc) { [math]::Round(($proc.WorkingSet64 / 1MB), 2) } else { $null }
                $cpu = if ($proc) { $proc.CPU } else { $null }
                $name = if ($proc) { $proc.ProcessName } else { $p.Name }
                $list += [pscustomobject]@{
                    pid         = $p.ProcessId
                    name        = $name
                    cpu_seconds = $cpu
                    ws_mb       = $wsMB
                    commandLine = ($cmd -replace '\s+', ' ').Trim()
                }
                break
            }
        }
    }
    return $list
}

# Identify core agents
$rpaPatterns = @('*integrations\\rpa_worker.py*', '*rpa_worker.py*')
$watchdogPatterns = @('*task_watchdog.py*', '*self_healing_watchdog.ps1*')
$monitorPatterns = @('*worker_monitor*', '*monitoring_daemon.py*', '*metrics_collector*')

$rpa = Get-ProcMatches -Patterns $rpaPatterns
$watchdogs = Get-ProcMatches -Patterns $watchdogPatterns
$monitors = Get-ProcMatches -Patterns $monitorPatterns

$host = Get-HostMetrics

$result = [pscustomobject]@{
    host       = $host
    processes  = if ($SummaryOnly) { $null } else {
        [pscustomobject]@{
            rpa_workers = $rpa
            watchdogs   = $watchdogs
            monitors    = $monitors
        }
    }
    counts     = [pscustomobject]@{
        rpa_workers = $rpa.Count
        watchdogs   = $watchdogs.Count
        monitors    = $monitors.Count
    }
    thresholds = [pscustomobject]@{
        warn_cpu_percent  = $WarnCpuPercent
        warn_min_avail_mb = $WarnMinAvailMB
        min_workers       = $MinWorkers
        require_watchdog  = [bool]$RequireWatchdog
    }
    status     = 'ok'
    issues     = @()
}

# Evaluate status
if ($null -ne $host.cpu_percent_total -and $host.cpu_percent_total -ge $WarnCpuPercent) {
    $result.issues += "High CPU: $($host.cpu_percent_total)% >= $WarnCpuPercent%"
}
if ($null -ne $host.mem_available_mb -and $host.mem_available_mb -le $WarnMinAvailMB) {
    $result.issues += "Low free memory: $($host.mem_available_mb) MB <= $WarnMinAvailMB MB"
}
if ($rpa.Count -lt $MinWorkers) { $result.issues += "Not enough RPA workers: $($rpa.Count) < $MinWorkers" }
if ($RequireWatchdog -and $watchdogs.Count -lt 1) { $result.issues += 'Watchdog not running' }

if ($result.issues.Count -gt 0) { $result.status = 'degraded' }

# Output
$json = $result | ConvertTo-Json -Depth 6
if ($OutJson) {
    try {
        $outDir = Split-Path -Parent $OutJson
        if ($outDir -and !(Test-Path -LiteralPath $outDir)) { New-Item -Path $outDir -ItemType Directory -Force | Out-Null }
        $json | Out-File -LiteralPath $OutJson -Encoding UTF8
        Write-Host "Saved: $OutJson" -ForegroundColor Green
    }
    catch {
        Write-Warning ("Failed to write {0}: {1}" -f $OutJson, $_)
    }
}

$json

if ($result.status -eq 'ok') { exit 0 } else { exit 2 }
