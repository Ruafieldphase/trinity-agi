param(
    [string]$TaskName = "IonInboxWatcher",
    [string]$Agents = "all",
    [switch]$Force
)

$Script = Join-Path $PSScriptRoot "run_inbox_watcher.ps1"
if (-not (Test-Path $Script)) {
    Write-Error "run_inbox_watcher.ps1 not found: $Script"
    exit 1
}

try {
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
}
catch {
    $existing = $null
}

if ($existing -and -not $Force) {
    Write-Host "Scheduled task '$TaskName' already exists. Use -Force to recreate."
    exit 0
}

if ($existing -and $Force) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue | Out-Null
}

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$Script`" -Agents `"$Agents`""
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances Parallel -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Description "INBOX Watcher (agents=$Agents)" | Out-Null
Start-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue | Out-Null

Write-Host "Scheduled task '$TaskName' registered and started."
