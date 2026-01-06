param(
    [string]$LogFile = (Join-Path $( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } ) \"outputs\worker_monitor.log\")
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = 'Stop'
try {
    $job = Get-Job -Name 'RPA_Worker_Monitor' -ErrorAction SilentlyContinue
    if ($job) {
        Write-Host ("Monitor job: {0} (State={1})" -f $job.Name, $job.State) -ForegroundColor Green
    }
    else {
        Write-Host 'Monitor job not running.' -ForegroundColor Yellow
    }
    if (Test-Path -LiteralPath $LogFile) {
        Write-Host ("Log tail: {0}" -f $LogFile) -ForegroundColor Cyan
        Get-Content -LiteralPath $LogFile -Tail 12
    }
    else {
        Write-Host "No log file yet: $LogFile" -ForegroundColor DarkYellow
    }
    exit 0
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}