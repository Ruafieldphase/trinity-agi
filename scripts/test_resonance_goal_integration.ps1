# Test Resonance + Goal Integration
param(
    [switch]$VerboseLog
)

$ErrorActionPreference = "Stop"
$ws = "c:\workspace\agi"

Write-Host "🔬 Testing Resonance + Goal Integration..." -ForegroundColor Cyan

# Step 1: Generate some rhythm events
Write-Host "`n1️⃣ Generating rhythm events..." -ForegroundColor Yellow
$py = "$ws\fdo_agi_repo\.venv\Scripts\python.exe"
if (!(Test-Path -LiteralPath $py)) { $py = "python" }

& $py "$ws\scripts\test_resonance_orchestrator.ps1" | Out-Null
Start-Sleep -Seconds 2

# Step 2: Generate autonomous goals
Write-Host "`n2️⃣ Generating autonomous goals..." -ForegroundColor Yellow
& $py "$ws\scripts\autonomous_goal_generator.py" --hours 24 | Out-Null

# Step 3: Execute goals with resonance
Write-Host "`n3️⃣ Executing goals with resonance oracle..." -ForegroundColor Yellow
& $py "$ws\scripts\autonomous_goal_executor.py" | Out-Null

# Step 4: Check goal tracker
Write-Host "`n4️⃣ Checking goal tracker..." -ForegroundColor Yellow
$tracker = Get-Content "$ws\fdo_agi_repo\memory\goal_tracker.json" | ConvertFrom-Json
Write-Host "   Total goals: $($tracker.goals.Count)" -ForegroundColor Green
Write-Host "   Active goals: $($tracker.goals | Where-Object { $_.status -eq 'in_progress' } | Measure-Object | Select-Object -ExpandProperty Count)" -ForegroundColor Green

# Step 5: Check event bus
Write-Host "`n5️⃣ Checking event bus..." -ForegroundColor Yellow
if (Test-Path "$ws\outputs\event_bus.jsonl") {
    $events = Get-Content "$ws\outputs\event_bus.jsonl" | ConvertFrom-Json
    Write-Host "   Total events: $($events.Count)" -ForegroundColor Green
    Write-Host "   Rhythm pulses: $($events | Where-Object { $_.topic -eq 'rhythm.pulse' } | Measure-Object | Select-Object -ExpandProperty Count)" -ForegroundColor Green
    Write-Host "   Flow updates: $($events | Where-Object { $_.topic -eq 'flow.update' } | Measure-Object | Select-Object -ExpandProperty Count)" -ForegroundColor Green
}

Write-Host "`n✅ Integration test complete!" -ForegroundColor Green
Write-Host "   Check outputs/autonomous_goals_latest.md for goal details" -ForegroundColor Cyan
Write-Host "   Check fdo_agi_repo/memory/goal_tracker.json for execution status" -ForegroundColor Cyan
