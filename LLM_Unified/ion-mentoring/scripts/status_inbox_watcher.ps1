param(
    [string]$TaskName = "IonInboxWatcher"
)

try {
    $t = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
}
catch {
    Write-Host "Scheduled task '$TaskName' not found."
    exit 0
}

$state = (Get-ScheduledTaskInfo -TaskName $TaskName)
$obj = [pscustomobject]@{
    TaskName       = $TaskName
    State          = $t.State
    LastRunTime    = $state.LastRunTime
    LastTaskResult = $state.LastTaskResult
    NextRunTime    = $state.NextRunTime
}
$obj | Format-List
