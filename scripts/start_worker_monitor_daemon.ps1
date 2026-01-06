param(
    [string]$Server = 'http://127.0.0.1:8091',
    [int]$IntervalSeconds = 5,
    [switch]$KillExisting,
    [string]$LogFile = (Join-Path $( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } ) \"outputs\worker_monitor.log\")
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = 'Stop'
try {
    $repoRoot = $WorkspaceRoot
    $daemon = Join-Path $repoRoot 'scripts\worker_monitor_daemon.ps1'
    if (-not (Test-Path -LiteralPath $daemon)) { throw "daemon script not found: $daemon" }

    if ($KillExisting) {
        $procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine -like '*worker_monitor_daemon.ps1*' }
        if ($procs) {
            $pids = $procs | Select-Object -ExpandProperty ProcessId
            Write-Host ("Killing existing daemon(s): {0}" -f ($pids -join ',')) -ForegroundColor Yellow
            $pids | ForEach-Object { try { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue } catch {} }
        }
    }

    $procArgs = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "$daemon", '-Server', "$Server", '-IntervalSeconds', [string]$IntervalSeconds, '-LogFile', "$LogFile")
    Start-Process -FilePath 'powershell' -ArgumentList ($procArgs -join ' ') -WindowStyle Hidden | Out-Null
    Write-Host ("Daemon started. interval=${IntervalSeconds}s, log=$LogFile") -ForegroundColor Green
    exit 0
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}