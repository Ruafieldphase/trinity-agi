param(
    [string]$ConfigPath = "${PSScriptRoot}\..\config\autonomic_monitors.json",
    [switch]$DryRun,
    [int]$Interval = 5,
    [switch]$KillExisting
)

$ErrorActionPreference = 'Stop'

function Get-PythonPath {
    $candidates = @(
        "$PSScriptRoot/../LLM_Unified/.venv/Scripts/python.exe",
        "$PSScriptRoot/../fdo_agi_repo/.venv/Scripts/python.exe"
    )
    foreach ($p in $candidates) { if (Test-Path -LiteralPath $p) { return (Resolve-Path $p).Path } }
    return 'python'
}

# Kill existing job if requested
if ($KillExisting) {
    Get-Job -Name 'NerveCenter' -ErrorAction SilentlyContinue | Remove-Job -Force -ErrorAction SilentlyContinue
    # Fallback: kill process by command line match
    Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*autonomic\\nerve_center.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
}

$py = Get-PythonPath
$script = Resolve-Path "$PSScriptRoot/../fdo_agi_repo/autonomic/nerve_center.py"

$argsList = @('--config', (Resolve-Path $ConfigPath).Path, '--interval', $Interval)
if ($DryRun) { $argsList += '--dry-run' }

$sb = {
    param($py, $script, $argsList)
    & $py $script @argsList
}

$job = Start-Job -Name 'NerveCenter' -ScriptBlock $sb -ArgumentList @($py, $script, $argsList)
Write-Host "Nerve Center started (Job: $($job.Id))" -ForegroundColor Green
