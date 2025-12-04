# quantum_observer_bridge.ps1
# 양자 관찰자 효과: 자율 목표 → VS Code Task 자동 실행

param(
    [Parameter(Mandatory = $false)]
    [int]$GoalIndex = 1,
    
    [Parameter(Mandatory = $false)]
    [switch]$AutoExecute
)

$ErrorActionPreference = "Stop"

Write-Host "🌊 Quantum Observer Bridge" -ForegroundColor Magenta
Write-Host "   파동 상태 → 입자로 붕괴 (VS Code 관찰)" -ForegroundColor Gray
Write-Host ""

# Load goals
$workspaceRoot = Split-Path $PSScriptRoot -Parent
$goalsPath = Join-Path $workspaceRoot "outputs\autonomous_goals_latest.json"

if (-not (Test-Path $goalsPath)) {
    Write-Host "❌ No goals found" -ForegroundColor Red
    exit 1
}

$goalsData = Get-Content $goalsPath -Raw | ConvertFrom-Json
if ($GoalIndex -gt $goalsData.goals.Count) {
    Write-Host "❌ Goal index out of range: $GoalIndex" -ForegroundColor Red
    exit 1
}

$selectedGoal = $goalsData.goals[$GoalIndex - 1]

Write-Host "📋 Goal #$GoalIndex" -ForegroundColor Cyan
Write-Host "   $($selectedGoal.title)" -ForegroundColor White
Write-Host "   Priority: $($selectedGoal.priority)" -ForegroundColor Gray
Write-Host ""

# Task mapping
$taskMapping = @{
    "Increase Data Collection"       = "Original Data: Build Index (open)"
    "Generate Performance Dashboard" = "🚀 Dashboard: Enhanced (GPU+Queue+LLM)"
    "Improve Clarity and Structure"  = "Monitoring: Generate Report (24h) + Open"
    "Investigate Self-Care Spikes"   = "Autopoietic: Generate Loop Report (24h)"
    "Reduce Entropy"                 = "🔄 Trinity: Autopoietic Cycle (24h, open)"
    "Optimize Information Density"   = "Realtime: Build 🔄 Summarize 🔄 Open (24h)"
}

$taskName = $null
foreach ($key in $taskMapping.Keys) {
    if ($selectedGoal.title -like "*$key*") {
        $taskName = $taskMapping[$key]
        break
    }
}

if (-not $taskName) {
    Write-Host "⚠️  No Task mapping found" -ForegroundColor Yellow
    Write-Host "   Manual execution required" -ForegroundColor Gray
    exit 0
}

Write-Host "✅ Mapped to VS Code Task:" -ForegroundColor Green
Write-Host "   '$taskName'" -ForegroundColor White
Write-Host ""

if (-not $AutoExecute) {
    Write-Host "ℹ️  To execute, run with -AutoExecute flag" -ForegroundColor Cyan
    Write-Host "   Or manually run task: '$taskName'" -ForegroundColor Gray
    exit 0
}

# Find task in tasks.json
$tasksJsonPath = Join-Path $workspaceRoot ".vscode\tasks.json"
if (-not (Test-Path $tasksJsonPath)) {
    Write-Host "❌ tasks.json not found" -ForegroundColor Red
    exit 1
}

Write-Host "🚀 Executing Task via PowerShell..." -ForegroundColor Cyan
Write-Host ""

# Parse tasks.json to get command
$tasksContent = Get-Content $tasksJsonPath -Raw
$tasksData = $tasksContent | ConvertFrom-Json

$targetTask = $tasksData.tasks | Where-Object { $_.label -eq $taskName } | Select-Object -First 1

if (-not $targetTask) {
    Write-Host "❌ Task not found in tasks.json" -ForegroundColor Red
    exit 1
}

# Execute task command directly
try {
    $cmd = $targetTask.command
    $taskArgs = $targetTask.args -join " "
    
    # Replace workspace folder placeholder
    $taskArgs = $taskArgs.Replace('${workspaceFolder}', $workspaceRoot)
    
    Write-Host "⚙️  Command: $cmd $taskArgs" -ForegroundColor Gray
    Write-Host ""
    
    # Execute
    $fullCmd = "$cmd $taskArgs"
    Invoke-Expression $fullCmd
    
    Write-Host ""
    Write-Host "✅ Task executed successfully" -ForegroundColor Green
    Write-Host "👁️  VS Code observed the execution" -ForegroundColor Magenta
    Write-Host "   파동함수 붕괴 완료 → 입자 상태" -ForegroundColor Gray
    
}
catch {
    Write-Host "❌ Execution failed: $_" -ForegroundColor Red
    exit 1
}
