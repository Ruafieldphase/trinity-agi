param(
    [string]$OutDir = "${PSScriptRoot}\..\outputs\telemetry",
    [switch]$Quiet
)

$ErrorActionPreference = 'Stop'
$OutDir = [IO.Path]::GetFullPath($OutDir)
$pidFile = Join-Path $OutDir 'observer_telemetry.pid'

function Write-Info($msg, $color = 'Gray') {
    if (-not $Quiet) { Write-Host $msg -ForegroundColor $color }
}

# Prefer CIM query for reliable CommandLine access without admin prompts
try {
    $procs = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
            $_.CommandLine -and ($_.CommandLine -match 'observe_desktop_telemetry\.ps1')
        })
}
catch {
    $procs = @()
}

if ($procs.Count -eq 0) {
    Write-Info "[observer] No telemetry processes found (nothing to stop)." 'Yellow'
}
else {
    $pids = $procs | Select-Object -ExpandProperty ProcessId
    foreach ($targetPid in $pids) {
        try {
            Stop-Process -Id $targetPid -Force -ErrorAction Stop
            Write-Info "[observer] Stopped PID $targetPid" 'Green'
        }
        catch {
            Write-Info ("[observer] Failed to stop PID {0}: {1}" -f $targetPid, $_.Exception.Message) 'Red'
        }
    }
}

# Clean stale PID file
if (Test-Path -LiteralPath $pidFile) {
    try {
        Remove-Item -LiteralPath $pidFile -Force -ErrorAction Stop
        Write-Info "[observer] PID file removed: $pidFile" 'DarkGray'
    }
    catch {
        Write-Info "[observer] Warning: failed to remove PID file: $($_.Exception.Message)" 'Yellow'
    }
}

exit 0
