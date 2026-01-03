# execute_goal_in_vscode.ps1
# 자율 목표를 VS Code Task로 실행 (양자 관찰자 효과 적용)

param(
    [Parameter(Mandatory = $false)]
    [int]$GoalIndex = 1,
    
    [Parameter(Mandatory = $false)]
    [string]$GoalTitle,
    
    [Parameter(Mandatory = $false)]
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

Write-Host "🎯 자율 목표를 VS Code에서 실행 (관찰자 효과)" -ForegroundColor Cyan
Write-Host ""

# Load goals
$workspaceRoot = Split-Path $PSScriptRoot -Parent
$goalsPath = Join-Path $workspaceRoot "outputs\autonomous_goals_latest.json"

if (-not (Test-Path $goalsPath)) {
    Write-Host "❌ No goals found at: $goalsPath" -ForegroundColor Red
    Write-Host "   Run: Task 'Goal: Generate + Open (24h)' first" -ForegroundColor Yellow
    exit 1
}

$goalsData = Get-Content $goalsPath -Raw | ConvertFrom-Json

if (-not $goalsData.goals -or $goalsData.goals.Count -eq 0) {
    Write-Host "❌ No goals available" -ForegroundColor Red
    exit 1
}

# Select goal
$selectedGoal = $null
if ($GoalTitle) {
    $selectedGoal = $goalsData.goals | Where-Object { $_.title -like "*$GoalTitle*" } | Select-Object -First 1
    if (-not $selectedGoal) {
        Write-Host "❌ Goal not found: $GoalTitle" -ForegroundColor Red
        exit 1
    }
}
else {
    if ($GoalIndex -gt $goalsData.goals.Count) {
        Write-Host "❌ Goal index out of range: $GoalIndex (max: $($goalsData.goals.Count))" -ForegroundColor Red
        exit 1
    }
    $selectedGoal = $goalsData.goals[$GoalIndex - 1]
}

Write-Host "📋 Selected Goal:" -ForegroundColor Green
Write-Host "   Title: $($selectedGoal.title)" -ForegroundColor Cyan
Write-Host "   Priority: $($selectedGoal.priority)" -ForegroundColor Cyan
Write-Host "   Effort: $($selectedGoal.effort_days) days" -ForegroundColor Cyan
Write-Host ""

# Map goal to VS Code Task
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
    Write-Host "⚠️  No direct Task mapping found" -ForegroundColor Yellow
    Write-Host "   Goal: $($selectedGoal.title)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "📝 Suggested manual execution:" -ForegroundColor Cyan
    Write-Host "   1. Open VS Code Command Palette (Ctrl+Shift+P)" -ForegroundColor Gray
    Write-Host "   2. Search: 'Tasks: Run Task'" -ForegroundColor Gray
    Write-Host "   3. Select appropriate task based on goal description" -ForegroundColor Gray
    exit 0
}

Write-Host "✅ Found VS Code Task: $taskName" -ForegroundColor Green
Write-Host ""

if ($DryRun) {
    Write-Host "🌊 Dry-Run Mode: Would execute task '$taskName'" -ForegroundColor Yellow
    exit 0
}

# Execute task via VS Code CLI
Write-Host "🚀 Executing in VS Code..." -ForegroundColor Cyan
try {
    # Use PowerShell to trigger VS Code task
    # Note: This requires VS Code to be running
    $result = code --folder-uri "vscode-remote://wsl+Ubuntu/workspace/agi" --command "workbench.action.tasks.runTask" $taskName 2>&1
    
    Write-Host "✅ Task triggered successfully" -ForegroundColor Green
    Write-Host ""
    Write-Host "👁️  VS Code is now 'observing' the execution" -ForegroundColor Magenta
    Write-Host "   → Wave function collapsed to particle state" -ForegroundColor Gray
    Write-Host "   → Results will be reflected in workspace context" -ForegroundColor Gray
    
}
catch {
    Write-Host "⚠️  Could not trigger via CLI" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "📋 Please run manually:" -ForegroundColor Cyan
    Write-Host "   Task: '$taskName'" -ForegroundColor White
    Write-Host ""
    Write-Host "   Or use VS Code Command Palette:" -ForegroundColor Gray
    Write-Host "   1. Ctrl+Shift+P" -ForegroundColor Gray
    Write-Host "   2. 'Tasks: Run Task'" -ForegroundColor Gray
    Write-Host "   3. Select: $taskName" -ForegroundColor Gray
}