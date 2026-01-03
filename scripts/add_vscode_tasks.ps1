. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot

# Add VS Code Tasks for Daily AGI Operations

$ErrorActionPreference = "Stop"

$tasksFile = "$WorkspaceRoot\.vscode\tasks.json"

# New tasks to add
$newTasks = @'
,
        {
            "label": "AGI: Open All Dashboards",
            "type": "shell",
            "command": "powershell",
            "args": [
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                "${workspaceFolder}/scripts/open_monitoring_dashboard.ps1"
            ],
            "problemMatcher": [],
            "presentation": {
                "reveal": "always",
                "panel": "new"
            },
            "group": "none"
        },
        {
            "label": "AGI: Quick Health Check",
            "type": "shell",
            "command": "python",
            "args": [
                "${workspaceFolder}/fdo_agi_repo/scripts/check_health.py",
                "--fast",
                "--json-only"
            ],
            "problemMatcher": [],
            "presentation": {
                "reveal": "always",
                "panel": "new"
            },
            "group": "test"
        },
        {
            "label": "AGI: Run E2E Integration Test",
            "type": "shell",
            "command": "powershell",
            "args": [
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                "${workspaceFolder}/scripts/run_e2e_integration_test.ps1",
                "-SkipYouTube"
            ],
            "problemMatcher": [],
            "presentation": {
                "reveal": "always",
                "panel": "dedicated"
            },
            "group": "test"
        },
        {
            "label": "AGI: Analyze Latency Spikes",
            "type": "shell",
            "command": "powershell",
            "args": [
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                "${workspaceFolder}/scripts/analyze_latency_spikes.ps1",
                "-ExportReport"
            ],
            "problemMatcher": [],
            "presentation": {
                "reveal": "always",
                "panel": "new"
            },
            "group": "none"
        },
        {
            "label": "AGI: Check Local LLM Performance",
            "type": "shell",
            "command": "powershell",
            "args": [
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                "${workspaceFolder}/scripts/check_llm_perf.ps1",
                "-Benchmark"
            ],
            "problemMatcher": [],
            "presentation": {
                "reveal": "always",
                "panel": "new"
            },
            "group": "test"
        },
        {
            "label": "AGI: Start Local LLM Monitor",
            "type": "shell",
            "command": "powershell",
            "args": [
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                "${workspaceFolder}/scripts/auto_restart_local_llm.ps1",
                "-Continuous"
            ],
            "problemMatcher": [],
            "isBackground": true,
            "presentation": {
                "reveal": "always",
                "panel": "dedicated"
            },
            "group": "none"
        },
        {
            "label": "AGI: Optimize Routing Policy",
            "type": "shell",
            "command": "powershell",
            "args": [
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                "${workspaceFolder}/scripts/adaptive_routing_optimizer.ps1",
                "-Verbose"
            ],
            "problemMatcher": [],
            "presentation": {
                "reveal": "always",
                "panel": "new"
            },
            "group": "none"
        },
        {
            "label": "AGI: Analyze Replan Patterns",
            "type": "shell",
            "command": "python",
            "args": [
                "${workspaceFolder}/fdo_agi_repo/analysis/analyze_replan_patterns.py"
            ],
            "problemMatcher": [],
            "presentation": {
                "reveal": "always",
                "panel": "new"
            },
            "group": "none"
        },
        {
            "label": "AGI: Refresh Performance Dashboard",
            "type": "shell",
            "command": "powershell",
            "args": [
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                "${workspaceFolder}/scripts/generate_performance_dashboard.ps1",
                "-WriteLatest"
            ],
            "problemMatcher": [],
            "presentation": {
                "reveal": "always",
                "panel": "new"
            },
            "group": "build"
        },
        {
            "label": "AGI: Circuit Breaker Status",
            "type": "shell",
            "command": "python",
            "args": [
                "${workspaceFolder}/scripts/circuit_breaker_router.py",
                "--status"
            ],
            "problemMatcher": [],
            "presentation": {
                "reveal": "always",
                "panel": "new"
            },
            "group": "none"
        }
'@

Write-Host "`n" -NoNewline
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "  Adding VS Code Tasks for AGI Operations" -ForegroundColor Yellow
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $tasksFile)) {
    Write-Host "Error: tasks.json not found at $tasksFile" -ForegroundColor Red
    exit 1
}

Write-Host "Reading existing tasks.json..." -ForegroundColor Cyan

$content = Get-Content $tasksFile -Raw

# Check if tasks already exist
if ($content -match "AGI: Open All Dashboards") {
    Write-Host "AGI tasks already exist in tasks.json" -ForegroundColor Yellow
    Write-Host "Skipping addition to avoid duplicates" -ForegroundColor Yellow
    exit 0
}

# Find the last task closing brace before the final array closing
# We'll insert before the final closing brackets "]}"

$insertPosition = $content.LastIndexOf('    ]')

if ($insertPosition -eq -1) {
    Write-Host "Error: Could not find insertion point in tasks.json" -ForegroundColor Red
    exit 1
}

# Insert new tasks
$newContent = $content.Substring(0, $insertPosition) + $newTasks + "`n" + $content.Substring($insertPosition)

# Backup original
$backupFile = "$tasksFile.backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
Copy-Item $tasksFile $backupFile
Write-Host "Backup created: $backupFile" -ForegroundColor Green

# Write updated tasks
$newContent | Out-File -FilePath $tasksFile -Encoding UTF8 -NoNewline

Write-Host ""
Write-Host "✅ Added 10 new AGI operation tasks" -ForegroundColor Green
Write-Host ""
Write-Host "New tasks available:" -ForegroundColor Cyan
Write-Host "  • AGI: Open All Dashboards" -ForegroundColor White
Write-Host "  • AGI: Quick Health Check" -ForegroundColor White
Write-Host "  • AGI: Run E2E Integration Test" -ForegroundColor White
Write-Host "  • AGI: Analyze Latency Spikes" -ForegroundColor White
Write-Host "  • AGI: Check Local LLM Performance" -ForegroundColor White
Write-Host "  • AGI: Start Local LLM Monitor" -ForegroundColor White
Write-Host "  • AGI: Optimize Routing Policy" -ForegroundColor White
Write-Host "  • AGI: Analyze Replan Patterns" -ForegroundColor White
Write-Host "  • AGI: Refresh Performance Dashboard" -ForegroundColor White
Write-Host "  • AGI: Circuit Breaker Status" -ForegroundColor White
Write-Host ""
Write-Host "Access via: Ctrl+Shift+P → 'Tasks: Run Task' → Select task" -ForegroundColor Yellow
Write-Host ""
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""