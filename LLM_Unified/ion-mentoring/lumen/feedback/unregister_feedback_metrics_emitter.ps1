param(
    [string]$TaskName = "LumenFeedbackEmitter",
    [switch]$Force
)

try {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop
    Write-Host "Scheduled task '$TaskName' unregistered." -ForegroundColor Yellow
}
catch {
    if ($Force) {
        Write-Warning "Failed to unregister '$TaskName' (might not exist). Continuing due to -Force."
        exit 0
    }
    else {
        Write-Error $_
        exit 1
    }
}
