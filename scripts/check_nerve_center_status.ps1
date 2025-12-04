$ErrorActionPreference = 'Continue'

$job = Get-Job -Name 'NerveCenter' -ErrorAction SilentlyContinue | Select-Object -First 1
if ($job) {
    Write-Host "Nerve Center Job: $($job.State) (Id=$($job.Id))" -ForegroundColor Cyan
}
else {
    Write-Host "No Nerve Center job found." -ForegroundColor Yellow
}

# Check process existence
$procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*autonomic\\nerve_center.py*' }
if ($procs) {
    foreach ($p in $procs) { Write-Host "Process: PID=$($p.ProcessId) CMD=$($p.CommandLine)" -ForegroundColor Cyan }
}
else {
    Write-Host "No nerve_center.py process found." -ForegroundColor Yellow
}

# Show last status file
$ws = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$latest = Join-Path $ws 'outputs/nerve_center_status_latest.md'
if (Test-Path -LiteralPath $latest) { Write-Host "Last status: $latest" -ForegroundColor Green; Get-Content -Path $latest -Raw | Write-Output }
