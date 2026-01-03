# execute_goal_via_task.ps1
# 자율 목표 → VS Code Task 직접 실행

param(
    [Parameter(Mandatory = $false)]
    [int]$GoalIndex = 1
)

$ErrorActionPreference = "Stop"

Write-Host "🎯 Autonomous Goal Executor" -ForegroundColor Cyan
Write-Host "   Goal #$GoalIndex → VS Code Task" -ForegroundColor Gray
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

Write-Host "📋 Selected Goal:" -ForegroundColor Cyan
Write-Host "   $($selectedGoal.title)" -ForegroundColor White
Write-Host "   Priority: $($selectedGoal.priority) | Feasibility: $($selectedGoal.feasibility)" -ForegroundColor Gray
Write-Host ""

# Task mapping (goal title keyword → Task label)
$taskMapping = @{
    "Data Collection"       = "Original Data: Build Index (open)"
    "Performance Dashboard" = "🚀 Dashboard: Enhanced (GPU+Queue+LLM)"
    "Clarity and Structure" = "Monitoring: Generate Report (24h) + Open"
    "Self-Care"             = "Autopoietic: Generate Loop Report (24h)"
    "Entropy"               = "🔄 Trinity: Autopoietic Cycle (24h, open)"
    "Information Density"   = "Realtime: Build 🔄 Summarize 🔄 Open (24h)"
}

$taskLabel = $null
foreach ($key in $taskMapping.Keys) {
    if ($selectedGoal.title -like "*$key*") {
        $taskLabel = $taskMapping[$key]
        break
    }
}

if (-not $taskLabel) {
    Write-Host "⚠️  No Task mapping found for this goal" -ForegroundColor Yellow
    Write-Host "   Goal: $($selectedGoal.title)" -ForegroundColor Gray
    Write-Host "   Manual execution required" -ForegroundColor Gray
    exit 0
}

Write-Host "✅ Mapped to Task:" -ForegroundColor Green
Write-Host "   '$taskLabel'" -ForegroundColor White
Write-Host ""
Write-Host "⚡ Executing Task..." -ForegroundColor Cyan

# Execute via VS Code CLI
try {
    code --command "workbench.action.tasks.runTask" "$taskLabel"
    Write-Host "✅ Task launched in VS Code" -ForegroundColor Green
    Write-Host "👁️  Observer effect: 파동 → 입자 붕괴 완료" -ForegroundColor Magenta
}
catch {
    Write-Host "❌ Failed to launch task: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 Fallback: Run task manually from Task menu:" -ForegroundColor Yellow
    Write-Host "   Terminal → Run Task → $taskLabel" -ForegroundColor Gray
    exit 1
}