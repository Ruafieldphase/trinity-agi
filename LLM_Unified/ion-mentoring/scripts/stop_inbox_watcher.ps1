param(
    [string]$TaskName = "IonInboxWatcher"
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

Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue | Out-Null
Write-Host "Scheduled task '$TaskName' stopped."
