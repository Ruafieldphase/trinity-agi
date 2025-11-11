# Quick Orchestrator Status Check
param(
    [switch]$Detailed
)

$ErrorActionPreference = 'Continue'

Write-Host "`n=== Quick Orchestrator Check ===" -ForegroundColor Cyan
Write-Host "Time: $(Get-Date -Format 'HH:mm:ss')`n" -ForegroundColor Gray

# 1. Process Check
Write-Host "1. Process:" -ForegroundColor White
$procCandidates = Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
Where-Object { $_.CommandLine -like '*full_stack_orchestrator.py*' } |
Sort-Object CreationDate -Descending |
Select-Object -First 3 @{
    Name       = 'ProcessId'
    Expression = { $_.ProcessId }
}, @{
    Name       = 'StartTime'
    Expression = { $_.CreationDate }
}, @{
    Name       = 'CommandLine'
    Expression = { $_.CommandLine }
}

if ($procCandidates) {
    $procCandidates | Format-Table -AutoSize
}
else {
    Write-Host "  Orchestrator process not detected" -ForegroundColor Red
}

# 2. State File
Write-Host "2. State:" -ForegroundColor White
$stateFile = "C:\workspace\agi\outputs\full_stack_orchestrator_state.json"
if (Test-Path $stateFile) {
    $state = Get-Content $stateFile | ConvertFrom-Json
    Write-Host "  Learning cycles: $($state.state.learning_cycles)" -ForegroundColor Cyan
    Write-Host "  Events processed: $($state.state.events_processed)" -ForegroundColor Cyan
    Write-Host "  Last optimization: $($state.state.last_optimization)" -ForegroundColor Gray
    Write-Host "  Saved: $($state.saved_at)" -ForegroundColor Gray
}
else {
    Write-Host "  State file not found" -ForegroundColor Red
}

# 3. Log Files
Write-Host "`n3. Recent Logs:" -ForegroundColor White
$stdout = "C:\workspace\agi\outputs\fullstack_24h_stdout.log"
$stderr = "C:\workspace\agi\outputs\fullstack_24h_stderr.log"

if (Test-Path $stdout) {
    $lines = (Get-Content $stdout -Tail 5 | Measure-Object -Line).Lines
    Write-Host "  stdout: $lines lines (last 5)" -ForegroundColor Gray
    if ($Detailed) {
        Get-Content $stdout -Tail 5 | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }
    }
}
else {
    Write-Host "  stdout: not found" -ForegroundColor Yellow
}

if (Test-Path $stderr) {
    $lastError = Get-Content $stderr -Tail 1
    if ($lastError -and $lastError.Trim()) {
        Write-Host "  stderr: has output (check for errors)" -ForegroundColor Yellow
        if ($Detailed) {
            Get-Content $stderr -Tail 10 | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkYellow }
        }
    }
    else {
        Write-Host "  stderr: empty (good)" -ForegroundColor Green
    }
}
else {
    Write-Host "  stderr: not found" -ForegroundColor Yellow
}

# 4. Progress Tracking
$now = Get-Date
$startTime = [DateTime]::Parse($state.state.started_at)
$elapsedMin = [Math]::Round(($now - $startTime).TotalMinutes, 1)
$expectedCycles = [Math]::Floor($elapsedMin / 5)

Write-Host "`n4. Progress:" -ForegroundColor White
Write-Host "  Elapsed: $elapsedMin minutes" -ForegroundColor Gray
Write-Host "  Expected cycles: ~$expectedCycles" -ForegroundColor Gray
Write-Host "  Actual cycles: $($state.state.learning_cycles)" -ForegroundColor $(if ($state.state.learning_cycles -ge $expectedCycles) { 'Green' }else { 'Yellow' })
Write-Host "  Events/cycle: $([Math]::Round($state.state.events_processed / $state.state.learning_cycles, 1))" -ForegroundColor Cyan

if ($state.state.learning_cycles -ge $expectedCycles) {
    Write-Host "`n✅ ON TRACK" -ForegroundColor Green
}
else {
    Write-Host "`n⚠️  BEHIND SCHEDULE" -ForegroundColor Yellow
}

Write-Host ""
