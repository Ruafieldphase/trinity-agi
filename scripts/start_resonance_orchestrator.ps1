# Start Trinity Resonance Orchestrator as background daemon
param(
    [int]$IntervalSeconds = 5,
    [int]$DurationSeconds = $null,
    [switch]$KillExisting
)

$ErrorActionPreference = 'Stop'
$workspace = "$PSScriptRoot\.."

# Kill existing if requested
if ($KillExisting) {
    Write-Host "🔍 Checking for existing Resonance Orchestrator..." -ForegroundColor Cyan
    Get-Process -Name 'python', 'pwsh', 'powershell' -ErrorAction SilentlyContinue | 
    Where-Object { $_.CommandLine -like '*resonance_orchestrator.py*' } | 
    ForEach-Object {
        Write-Host "⏹️ Stopping existing process: $($_.Id)" -ForegroundColor Yellow
        Stop-Process -Id $_.Id -Force
    }
    Start-Sleep -Seconds 2
}

# Find Python
$python = "$workspace\fdo_agi_repo\.venv\Scripts\python.exe"
if (!(Test-Path -LiteralPath $python)) {
    $python = "$workspace\LLM_Unified\.venv\Scripts\python.exe"
}
if (!(Test-Path -LiteralPath $python)) {
    $python = "python"
}

# Build command
$script = "$workspace\fdo_agi_repo\trinity\resonance_orchestrator.py"
$cmd = "& '$python' '$script' --interval $IntervalSeconds"
if ($DurationSeconds) {
    $cmd += " --duration $DurationSeconds"
}
$cmd += " --workspace '$workspace'"

Write-Host "🌀 Starting Trinity Resonance Orchestrator..." -ForegroundColor Green
Write-Host "📡 Interval: ${IntervalSeconds}s" -ForegroundColor Cyan
if ($DurationSeconds) {
    Write-Host "⏱️ Duration: ${DurationSeconds}s" -ForegroundColor Cyan
}
else {
    Write-Host "⏱️ Duration: Indefinite (press Ctrl+C to stop)" -ForegroundColor Cyan
}

# Start in background
Start-Process -FilePath $python -ArgumentList @(
    "$script",
    "--interval", "$IntervalSeconds",
    "--workspace", "$workspace"
) -WindowStyle Hidden -PassThru | Format-Table Id, ProcessName, StartTime

Write-Host "`n✅ Resonance Orchestrator started in background" -ForegroundColor Green
Write-Host "📊 Check status with: Get-Process python | Where-Object { `$_.CommandLine -like '*resonance_orchestrator*' }" -ForegroundColor Yellow
Write-Host "💾 State file: outputs\resonance_state.json" -ForegroundColor Cyan
Write-Host "📡 Events: outputs\events\" -ForegroundColor Cyan