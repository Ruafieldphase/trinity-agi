# 🧠 Adaptive Glymphatic System - User-Friendly Control CLI
# Advanced control interface with natural language commands

param(
    [string]$Action = "help",
    [switch]$Force,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"
$WorkspaceRoot = Split-Path $PSScriptRoot -Parent
$StateFile = "$WorkspaceRoot\outputs\glymphatic_state.json"

# Colors
$C_TITLE = "Cyan"
$C_SUCCESS = "Green"
$C_WARNING = "Yellow"
$C_ERROR = "Red"
$C_INFO = "Gray"

function Get-PythonExe {
    $candidates = @(
        "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe",
        "$WorkspaceRoot\LLM_Unified\.venv\Scripts\python.exe",
        "python"
    )
    
    foreach ($py in $candidates) {
        if (Test-Path $py -ErrorAction SilentlyContinue) {
            return $py
        }
        if ($py -eq "python") {
            try {
                & $py --version 2>&1 | Out-Null
                return $py
            }
            catch {
                continue
            }
        }
    }
    
    throw "❌ Python not found"
}

function Get-GlymphaticStatus {
    $py = Get-PythonExe
    $script = "$WorkspaceRoot\fdo_agi_repo\orchestrator\adaptive_glymphatic_system.py"
    
    try {
        $result = & $py $script --status 2>&1 | Out-String
        
        if ($LASTEXITCODE -eq 0) {
            return @{
                Running = $true
                Output  = $result
            }
        }
        else {
            return @{
                Running = $false
                Output  = $result
            }
        }
    }
    catch {
        return @{
            Running = $false
            Output  = $_.Exception.Message
        }
    }
}

function Show-Status {
    Write-Host ""
    Write-Host "🧠 Adaptive Glymphatic System - Status" -ForegroundColor $C_TITLE
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor $C_INFO
    
    if (-not (Test-Path $StateFile)) {
        Write-Host "⚠️  No state file found" -ForegroundColor $C_WARNING
        Write-Host "   Run 'check' to initialize" -ForegroundColor $C_INFO
        return
    }
    
    $state = Get-Content $StateFile | ConvertFrom-Json
    $lastUpdate = [DateTime]::Parse($state.timestamp)
    $age = (Get-Date) - $lastUpdate
    
    Write-Host ""
    Write-Host "📊 Current State:" -ForegroundColor $C_INFO
    Write-Host "   Workload:  $([Math]::Round($state.workload_percent, 1))%" -ForegroundColor $(if ($state.workload_percent -gt 70) { $C_WARNING } else { $C_SUCCESS })
    Write-Host "   Fatigue:   $([Math]::Round($state.fatigue_percent, 1))%" -ForegroundColor $(if ($state.fatigue_percent -gt 50) { $C_WARNING } else { $C_SUCCESS })
    Write-Host "   Action:    $($state.action)" -ForegroundColor $C_INFO
    Write-Host "   Delay:     $($state.cleanup_delay_min) min" -ForegroundColor $C_INFO
    Write-Host "   Updated:   $($age.TotalMinutes.ToString("F1")) min ago" -ForegroundColor $C_INFO
    
    Write-Host ""
    Write-Host "💡 Recommendation:" -ForegroundColor $C_TITLE
    
    switch ($state.action) {
        "immediate" {
            Write-Host "   ⚠️  System needs cleanup NOW!" -ForegroundColor $C_WARNING
            Write-Host "   Run: glymphatic_control.ps1 cleanup" -ForegroundColor $C_INFO
        }
        "schedule_urgent" {
            Write-Host "   ⏰ Schedule cleanup soon (within $($state.cleanup_delay_min) min)" -ForegroundColor $C_WARNING
        }
        "schedule_default" {
            Write-Host "   ✅ System healthy, scheduled cleanup in $($state.cleanup_delay_min) min" -ForegroundColor $C_SUCCESS
        }
        "defer" {
            Write-Host "   😴 System optimal, cleanup deferred ($($state.cleanup_delay_min) min)" -ForegroundColor $C_SUCCESS
        }
        default {
            Write-Host "   ❓ Unknown action: $($state.action)" -ForegroundColor $C_WARNING
        }
    }
    
    Write-Host ""
}

function Invoke-SystemCheck {
    Write-Host ""
    Write-Host "🔍 Running Glymphatic System Check..." -ForegroundColor $C_TITLE
    Write-Host ""
    
    $py = Get-PythonExe
    
    if ($Verbose) {
        Write-Host "  🐍 Python: $py" -ForegroundColor $C_INFO
        Write-Host ""
    }
    
    # 간단한 체크 스크립트 실행
    $tempScript = "$env:TEMP\glymphatic_check.py"
    @"
import sys
import os
import json
os.chdir(r'$($WorkspaceRoot.Replace('\', '\\'))')
sys.path.insert(0, r'$($WorkspaceRoot.Replace('\', '\\'))\fdo_agi_repo')

from orchestrator.adaptive_glymphatic_system import AdaptiveGlymphaticSystem

system = AdaptiveGlymphaticSystem()
result = system.monitor_and_decide()

workload = result['workload']['workload_percent']
fatigue = result['fatigue']['fatigue_level']
action = result['decision']['action']
delay = result['decision']['delay_minutes']

print(f'📊 Workload: {workload:.1f}%')
print(f'😴 Fatigue: {fatigue:.1f}%')
print(f'🎯 Action: {action}')
print(f'⏰ Delay: {delay} min')

# 상태 파일 저장
state_file = r'$($StateFile.Replace('\', '\\'))'
os.makedirs(os.path.dirname(state_file), exist_ok=True)
with open(state_file, 'w') as f:
    json.dump({
        'timestamp': result['timestamp'],
        'workload_percent': workload,
        'fatigue_percent': fatigue,
        'action': action,
        'cleanup_delay_min': delay
    }, f, indent=2)
"@ | Out-File -FilePath $tempScript -Encoding UTF8
    
    & $py $tempScript
    $exitCode = $LASTEXITCODE
    Remove-Item $tempScript -ErrorAction SilentlyContinue
    
    if ($exitCode -eq 0) {
        Write-Host ""
        Write-Host "✅ System check PASSED" -ForegroundColor $C_SUCCESS
        Start-Sleep -Seconds 1
        Show-Status
    }
    else {
        Write-Host ""
        Write-Host "❌ System check FAILED" -ForegroundColor $C_ERROR
        exit 1
    }
}

function Invoke-Cleanup {
    param([switch]$DryRun)
    
    Write-Host ""
    Write-Host "🧹 Running Glymphatic Cleanup..." -ForegroundColor $C_TITLE
    Write-Host ""
    
    if ($DryRun) {
        Write-Host "   [DRY-RUN MODE]" -ForegroundColor $C_WARNING
    }
    
    $py = Get-PythonExe
    
    # Cleanup 스크립트 실행
    $cleanupCmd = @"
import sys
sys.path.insert(0, r'$WorkspaceRoot\fdo_agi_repo')
from orchestrator.adaptive_glymphatic_system import AdaptiveGlymphaticSystem

system = AdaptiveGlymphaticSystem(workspace_root=r'$WorkspaceRoot')
dry_run = $($DryRun.ToString().ToLower())
result = system.execute_cleanup(dry_run=dry_run)

if result:
    print('✅ Cleanup completed successfully')
    sys.exit(0)
else:
    print('❌ Cleanup failed')
    sys.exit(1)
"@
    
    $result = & $py -c $cleanupCmd 2>&1
    Write-Host $result
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Cleanup completed" -ForegroundColor $C_SUCCESS
        
        if (-not $DryRun) {
            Write-Host ""
            Write-Host "🔄 Running post-cleanup check..." -ForegroundColor $C_INFO
            Start-Sleep -Seconds 2
            Show-Status
        }
    }
    else {
        Write-Host ""
        Write-Host "❌ Cleanup failed" -ForegroundColor $C_ERROR
        exit 1
    }
}

function Show-Help {
    Write-Host ""
    Write-Host "🧠 Adaptive Glymphatic System - Control CLI" -ForegroundColor $C_TITLE
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor $C_INFO
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor $C_INFO
    Write-Host "  .\glymphatic_control.ps1 <action> [options]"
    Write-Host ""
    Write-Host "Actions:" -ForegroundColor $C_TITLE
    Write-Host "  status       Show current system status" -ForegroundColor $C_SUCCESS
    Write-Host "  check        Run full system check & update state" -ForegroundColor $C_SUCCESS
    Write-Host "  cleanup      Execute cleanup now" -ForegroundColor $C_WARNING
    Write-Host "  dry-run      Simulate cleanup (no actual changes)" -ForegroundColor $C_INFO
    Write-Host "  help         Show this help" -ForegroundColor $C_INFO
    Write-Host ""
    Write-Host "Options:" -ForegroundColor $C_TITLE
    Write-Host "  -Verbose     Show detailed output" -ForegroundColor $C_INFO
    Write-Host "  -Force       Skip confirmations" -ForegroundColor $C_WARNING
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor $C_TITLE
    Write-Host "  .\glymphatic_control.ps1 status" -ForegroundColor $C_INFO
    Write-Host "  .\glymphatic_control.ps1 check -Verbose" -ForegroundColor $C_INFO
    Write-Host "  .\glymphatic_control.ps1 cleanup -Force" -ForegroundColor $C_INFO
    Write-Host "  .\glymphatic_control.ps1 dry-run" -ForegroundColor $C_INFO
    Write-Host ""
}

# Main Router
switch ($Action.ToLower()) {
    "status" {
        Show-Status
    }
    "check" {
        Invoke-SystemCheck
    }
    "cleanup" {
        if (-not $Force) {
            $confirm = Read-Host "⚠️  Run cleanup now? (y/N)"
            if ($confirm -ne "y") {
                Write-Host "❌ Cancelled" -ForegroundColor $C_WARNING
                exit 0
            }
        }
        Invoke-Cleanup
    }
    "dry-run" {
        Invoke-Cleanup -DryRun
    }
    "help" {
        Show-Help
    }
    default {
        Write-Host "❌ Unknown action: $Action" -ForegroundColor $C_ERROR
        Write-Host ""
        Show-Help
        exit 1
    }
}

Write-Host ""
