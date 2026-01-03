param(
    [int]$CheckIntervalSeconds = 60,
    [int]$StaleMinutes = 10,
    [string]$StartScript = "$PSScriptRoot\start_luon_watch.ps1",
    [int]$WatchIntervalSeconds = 15,
    [string]$LogDirectory = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\logs",
    [string]$LogPath = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\logs\luon_watch_keepalive.log",
    [int]$MaxIterations = 0
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Stop"
$LogDirectory = [System.IO.Path]::GetFullPath($LogDirectory)
if (-not (Test-Path $LogDirectory)) {
    New-Item -ItemType Directory -Path $LogDirectory | Out-Null
}

$LogPath = [System.IO.Path]::GetFullPath($LogPath)

function Write-KeepAliveLog {
    param([string]$Message)
    $timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    $line = "[{0}] {1}" -f $timestamp, $Message
    $line | Add-Content -Path $LogPath -Encoding UTF8
    Write-Host $line
}

function Get-WatchProcesses {
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
        Where-Object { $_.CommandLine -like "*luon_watch_loop_auto.py*" }
}

function Stop-WatchProcesses {
    param([System.Array]$Processes)
    if (-not $Processes) { return }
    foreach ($proc in $Processes) {
        try {
            Stop-Process -Id $proc.ProcessId -Force -ErrorAction Stop
        } catch {
            Write-KeepAliveLog "Failed to stop PID=$($proc.ProcessId): $_"
        }
    }
}

function Start-WatchProcess {
    try {
        & $StartScript -IntervalSeconds $WatchIntervalSeconds -KillExisting | Out-Null
        Write-KeepAliveLog "Started Luon watch via $StartScript"
    } catch {
        Write-KeepAliveLog "Failed to start Luon watch: $_"
    }
}

if ($MaxIterations -lt 0) { $MaxIterations = 0 }
$iteration = 0

while ($true) {
    if ($MaxIterations -gt 0 -and $iteration -ge $MaxIterations) { break }
    $iteration++

    try {
        $processes = Get-WatchProcesses
        if (-not $processes) {
            Write-KeepAliveLog "Luon watch process not found. Restarting..."
            Start-WatchProcess
        } else {
            $latestLog = Get-ChildItem -Path $LogDirectory -Filter "luon_watch_*.out.log" |
                Sort-Object LastWriteTime -Descending |
                Select-Object -First 1
            $threshold = (Get-Date).AddMinutes(-1 * $StaleMinutes)
            $needsRestart = $false

            if (-not $latestLog) {
                Write-KeepAliveLog "No luon_watch_*.out.log files found. Restarting..."
                $needsRestart = $true
            } elseif ($latestLog.LastWriteTime -lt $threshold) {
                Write-KeepAliveLog ("Latest log {0} older than threshold ({1}). Restarting..." -f $latestLog.Name, $latestLog.LastWriteTime)
                $needsRestart = $true
            }

            if ($needsRestart) {
                Stop-WatchProcesses -Processes $processes
                Start-WatchProcess
            }
        }
    } catch {
        Write-KeepAliveLog "Keepalive loop error: $_"
    }
    Start-Sleep -Seconds $CheckIntervalSeconds
}