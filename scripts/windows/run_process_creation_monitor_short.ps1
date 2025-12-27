param(
    [int]$DurationSec = 6
)

$ErrorActionPreference = 'Continue'
$scriptPath = Join-Path (Split-Path -Parent $PSScriptRoot) 'windows\monitor_process_creation.ps1'

if (-not (Test-Path $scriptPath)) {
    Write-Host "Missing: $scriptPath" -ForegroundColor Yellow
    exit 1
}

try {
    $job = Start-Job -ScriptBlock { & $using:scriptPath }
    Start-Sleep -Seconds $DurationSec
    Stop-Job $job
    Receive-Job $job -ErrorAction SilentlyContinue | Out-Null
    Remove-Job $job -Force
}
catch {
    try {
        if ($job) { Stop-Job $job -ErrorAction SilentlyContinue }
    } catch { }
    try {
        if ($job) { Remove-Job $job -Force -ErrorAction SilentlyContinue }
    } catch { }
    exit 1
}
