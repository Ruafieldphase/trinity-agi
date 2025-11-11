param(
    [switch]$Register,
    [switch]$Unregister,
    [switch]$Status,
    [int]$IntervalMinutes = 10,
    [switch]$RunNow
)

$ErrorActionPreference = 'Stop'
$taskName = 'AGI_FeedbackLoop'
$ws = Split-Path -Parent $PSCommandPath
$root = Split-Path -Parent $ws
$scriptPy = Join-Path $root 'fdo_agi_repo\scripts\rune\feedback_loop_once.py'
$wrapper = Join-Path $ws 'run_feedback_loop_once.ps1'

function New-FeedbackLoopWrapper {
    param([string]$WrapperPath)
    $venv1 = Join-Path $root 'LLM_Unified\.venv\Scripts\python.exe'
    $venv2 = Join-Path $root 'fdo_agi_repo\.venv\Scripts\python.exe'
    $script = $scriptPy
    $content = @'
# Auto-generated. Do not edit.
param()
$py = "__VENV1__"
if (-not (Test-Path -LiteralPath $py)) { $py = "__VENV2__" }
if (-not (Test-Path -LiteralPath $py)) { $py = 'python' }
& $py "__SCRIPT__" | Write-Output
'@
    $content = $content.Replace('__VENV1__', $venv1).Replace('__VENV2__', $venv2).Replace('__SCRIPT__', $script)
    Set-Content -LiteralPath $WrapperPath -Value $content -Encoding UTF8 -Force
}

if ($Register) {
    New-FeedbackLoopWrapper -WrapperPath $wrapper
    $exists = $null
    $queryExit = 1
    try {
        $exists = schtasks /Query /TN $taskName /FO LIST /V 2>$null | Out-String
        $queryExit = $LASTEXITCODE
    }
    catch {
        $queryExit = 1
        $exists = $null
    }
    if ($queryExit -eq 0 -and $exists) {
        Write-Host "Task '$taskName' already exists. Updating..." -ForegroundColor Yellow
        schtasks /Delete /TN $taskName /F | Out-Null
    }
    $cmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$wrapper`""
    schtasks /Create /SC MINUTE /MO $IntervalMinutes /TN $taskName /TR "$cmd" /RL LIMITED /F | Out-Null
    Write-Host "Registered '$taskName' to run every $IntervalMinutes minute(s)." -ForegroundColor Green
    if ($RunNow) {
        Write-Host "Running once now..." -ForegroundColor Cyan
        powershell -NoProfile -ExecutionPolicy Bypass -File $wrapper
    }
    exit 0
}

if ($Unregister) {
    schtasks /Delete /TN $taskName /F | Out-Null
    Write-Host "Unregistered '$taskName'." -ForegroundColor Green
    exit 0
}

if ($Status) {
    schtasks /Query /TN $taskName /FO LIST /V
    exit 0
}

Write-Host "Usage: .\\register_feedback_loop_task.ps1 -Register [-IntervalMinutes 10] [-RunNow] | -Unregister | -Status" -ForegroundColor Yellow
exit 1
