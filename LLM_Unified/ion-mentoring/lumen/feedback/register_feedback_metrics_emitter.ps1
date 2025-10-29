param(
    [string]$TaskName = "LumenFeedbackEmitter",
    [int]$IntervalMinutes = 5,
    [switch]$Force,
    [string]$ProjectId = "naeda-genesis",
    [string]$ServiceName = "lumen-gateway",
    [string]$BudgetUSD = "200.0"
)

$wrapper = Join-Path $PSScriptRoot "run_emit_feedback_metrics_once.ps1"
if (-not (Test-Path $wrapper)) {
    Write-Error "Wrapper script not found: $wrapper"
    exit 1
}

if ($Force) {
    try { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue } catch {}
}

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$wrapper`" -ProjectId `"$ProjectId`" -ServiceName `"$ServiceName`" -BudgetUSD `"$BudgetUSD`""
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Force | Out-Null

Write-Host "Scheduled task '$TaskName' registered to run every $IntervalMinutes minute(s)." -ForegroundColor Green
