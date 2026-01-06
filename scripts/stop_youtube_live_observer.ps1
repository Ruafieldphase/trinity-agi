param(
    [string]$OutDir = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\telemetry",
    [switch]$Quiet
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = 'Stop'
$OutDir = [IO.Path]::GetFullPath($OutDir)
$pidFile = Join-Path $OutDir 'youtube_live_observer.pid'

function Write-Info($msg, $color = 'Gray') {
    if (-not $Quiet) { Write-Host $msg -ForegroundColor $color }
}

# Find processes by CommandLine signature
try {
    $procs = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
            $_.CommandLine -and ($_.CommandLine -match 'observe_youtube_live\.ps1')
        })
}
catch { $procs = @() }

if ($procs.Count -eq 0) {
    Write-Info "[yt-observer] No live observer processes found (nothing to stop)." 'Yellow'
}
else {
    foreach ($p in $procs) {
        try {
            Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop
            Write-Info "[yt-observer] Stopped PID $($p.ProcessId)" 'Green'
        }
        catch {
            Write-Info ("[yt-observer] Failed to stop PID {0}: {1}" -f $p.ProcessId, $_.Exception.Message) 'Red'
        }
    }
}

if (Test-Path -LiteralPath $pidFile) {
    try { Remove-Item -LiteralPath $pidFile -Force -ErrorAction Stop; Write-Info "[yt-observer] PID file removed: $pidFile" 'DarkGray' } catch {}
}

exit 0