param(
    [int]$Tail = 200,
    [switch]$Follow
)

$LogFile = Join-Path (Resolve-Path "$PSScriptRoot\..\").Path "logs\inbox_watcher.log"
if (-not (Test-Path $LogFile)) {
    Write-Host "Log file not found: $LogFile"
    exit 0
}

if ($Follow) {
    Get-Content -Path $LogFile -Tail $Tail -Wait
}
else {
    Get-Content -Path $LogFile -Tail $Tail
}
