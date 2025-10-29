param(
    [string]$TaskName = "IonInboxWatcher",
    [switch]$Force
)

try {
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
}
catch {
    $existing = $null
}

if (-not $existing) {
    Write-Host "Scheduled task '$TaskName' not found."
    exit 0
}

if (-not $Force) {
    Write-Host "Use -Force to confirm removal of scheduled task '$TaskName'."
    exit 1
}

Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue | Out-Null
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false | Out-Null
Write-Host "Scheduled task '$TaskName' unregistered."
