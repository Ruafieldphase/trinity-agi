<#
.SYNOPSIS
    Autonomous Loop Executor
    자율적으로 작업을 계획하고 실행하는 루프

.DESCRIPTION
    작업 완료 후 자동으로 다음 작업을 선택하고 실행
    Phase 6+ Self-Continuing Agent

.PARAMETER MaxIterations
    최대 반복 횟수 (기본: 10)

.PARAMETER AutoApprove
    수동 작업도 자동 승인

.PARAMETER IntervalSeconds
    작업 간 대기 시간 (기본: 5)
#>

param(
    [int]$MaxIterations = 10,
    [switch]$AutoApprove,
    [int]$IntervalSeconds = 5
)

$ErrorActionPreference = "Stop"
$WorkspaceRoot = "C:\workspace\agi"
$PythonExe = "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe"
$PlannerScript = "$WorkspaceRoot\fdo_agi_repo\orchestrator\autonomous_work_planner.py"
$OutputDir = "$WorkspaceRoot\outputs"

# 색상 출력 헬퍼
function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Write-Banner {
    param([string]$Message)
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  $Message" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
}

# 작업 ID to 실행 명령 매핑
$WorkCommands = @{
    "monitor_24h"           = {
        Write-ColorOutput "🔍 Generating 24h monitoring report..." "Cyan"
        & "$WorkspaceRoot\scripts\generate_monitoring_report.ps1" -Hours 24 -ErrorAction Continue
    }
    "autopoietic_report"    = {
        Write-ColorOutput "🔄 Generating autopoietic loop report..." "Cyan"
        & "$WorkspaceRoot\scripts\generate_autopoietic_report.ps1" -Hours 24 -ErrorAction Continue
    }
    "phase6_optimization"   = {
        Write-ColorOutput "🎯 Running Phase 6 optimization..." "Yellow"
        Write-ColorOutput "   (User approval required in future implementation)" "Gray"
        # & "$WorkspaceRoot\fdo_agi_repo\scripts\run_bqi_learner.ps1" -Phase 6 -ErrorAction Continue
    }
    "layer23_activation"    = {
        Write-ColorOutput "🔒 Activating Layer 2 & 3 Monitoring..." "Yellow"
        Write-ColorOutput "   (Requires admin privileges - skipping for now)" "Gray"
    }
    "performance_dashboard" = {
        Write-ColorOutput "📊 Updating performance dashboard..." "Cyan"
        & "$WorkspaceRoot\scripts\generate_performance_dashboard.ps1" -WriteLatest -ExportJson -ErrorAction Continue
    }
    "system_health_check"   = {
        Write-ColorOutput "🏥 Running system health check..." "Cyan"
        & "$WorkspaceRoot\scripts\quick_status.ps1" -ErrorAction Continue
    }
}

# 메인 루프
Write-Banner "🤖 Autonomous Loop Executor Started"

Write-ColorOutput "⚙️  Configuration:" "Yellow"
Write-ColorOutput "   Max Iterations: $MaxIterations" "Gray"
Write-ColorOutput "   Auto-Approve: $AutoApprove" "Gray"
Write-ColorOutput "   Interval: $IntervalSeconds seconds" "Gray"
Write-Host ""

$iteration = 0
$completed = 0
$skipped = 0

while ($iteration -lt $MaxIterations) {
    $iteration++
    
    Write-ColorOutput "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "DarkGray"
    Write-ColorOutput "🔄 Iteration $iteration / $MaxIterations" "Magenta"
    Write-ColorOutput "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "DarkGray"
    Write-Host ""
    
    # 다음 작업 가져오기
    Write-ColorOutput "📋 Fetching next work item..." "Cyan"
    $nextWorkJson = & $PythonExe $PlannerScript next 2>&1 | Out-String
    
    # 파싱 (간단한 정규식)
    if ($nextWorkJson -match "ID:\s+(\S+)") {
        $workId = $matches[1]
        $nextWorkJson -match "Title:\s+(.+)" | Out-Null
        $workTitle = $matches[1]
        $nextWorkJson -match "Auto-Execute:\s+(\S+)" | Out-Null
        $autoExecute = $matches[1] -eq "True"
        $nextWorkJson -match "Estimated:\s+(\d+)m" | Out-Null
        $estimatedMinutes = $matches[1]
        
        Write-Host ""
        Write-ColorOutput "🎯 Next Work Item:" "Green"
        Write-ColorOutput "   ID: $workId" "White"
        Write-ColorOutput "   Title: $workTitle" "White"
        Write-ColorOutput "   Auto-Execute: $autoExecute" "$(if ($autoExecute) { 'Green' } else { 'Yellow' })"
        Write-ColorOutput "   Estimated: ~$estimatedMinutes minutes" "Gray"
        Write-Host ""
        
        # 실행 결정
        $shouldExecute = $false
        
        if ($autoExecute) {
            Write-ColorOutput "✅ Auto-executing in $IntervalSeconds seconds..." "Green"
            Start-Sleep -Seconds $IntervalSeconds
            $shouldExecute = $true
        }
        elseif ($AutoApprove) {
            Write-ColorOutput "⚡ Auto-approved by flag, executing in $IntervalSeconds seconds..." "Yellow"
            Start-Sleep -Seconds $IntervalSeconds
            $shouldExecute = $true
        }
        else {
            Write-ColorOutput "⏸️  Manual approval required - skipping for now" "Yellow"
            & $PythonExe $PlannerScript complete $workId "skipped_manual_approval_required" | Out-Null
            $skipped++
            Start-Sleep -Seconds 2
            continue
        }
        
        # 작업 실행
        if ($shouldExecute) {
            Write-ColorOutput "🚀 Executing: $workTitle" "Green"
            Write-Host ""
            
            # In-progress 표시는 Python 스크립트에서 지원하지 않으므로 생략
            # 향후 구현 시 추가
            
            try {
                $command = $WorkCommands[$workId]
                if ($command) {
                    & $command
                    $exitCode = $LASTEXITCODE
                    
                    if ($exitCode -eq 0 -or $null -eq $exitCode) {
                        Write-Host ""
                        Write-ColorOutput "✅ Work item completed successfully: $workId" "Green"
                        & $PythonExe $PlannerScript complete $workId "success" | Out-Null
                        $completed++
                    }
                    else {
                        Write-Host ""
                        Write-ColorOutput "⚠️  Work item failed with exit code $exitCode" "Yellow"
                        & $PythonExe $PlannerScript complete $workId "failed_exit_$exitCode" | Out-Null
                    }
                }
                else {
                    Write-ColorOutput "⚠️  No command mapping found for: $workId" "Yellow"
                    & $PythonExe $PlannerScript complete $workId "no_command_mapping" | Out-Null
                }
            }
            catch {
                Write-ColorOutput "❌ Error executing work item: $_" "Red"
                & $PythonExe $PlannerScript complete $workId "error_$($_.Exception.Message)" | Out-Null
            }
            
            Write-Host ""
            Write-ColorOutput "⏱️  Cooling down for $IntervalSeconds seconds..." "Gray"
            Start-Sleep -Seconds $IntervalSeconds
        }
    }
    elseif ($nextWorkJson -match "No pending work items") {
        Write-Host ""
        Write-ColorOutput "✅ All work items completed!" "Green"
        Write-Host ""
        break
    }
    else {
        Write-ColorOutput "⚠️  Unable to parse next work item" "Yellow"
        Write-ColorOutput $nextWorkJson "Gray"
        break
    }
}

# 최종 요약
Write-Banner "🎊 Autonomous Loop Completed"

Write-ColorOutput "📊 Summary:" "Cyan"
Write-ColorOutput "   Iterations: $iteration / $MaxIterations" "White"
Write-ColorOutput "   Completed: $completed" "Green"
Write-ColorOutput "   Skipped: $skipped" "Yellow"
Write-Host ""

# 최종 리포트 생성
Write-ColorOutput "📄 Generating final work plan report..." "Cyan"
& $PythonExe $PlannerScript | Out-Null

$reportPath = "$OutputDir\autonomous_work_plan.md"
if (Test-Path $reportPath) {
    Write-ColorOutput "📝 Report saved: $reportPath" "Green"
    Write-Host ""
    Write-ColorOutput "To view the report:" "Yellow"
    Write-ColorOutput "   code `"$reportPath`"" "Gray"
}

Write-Host ""
Write-ColorOutput "🎵 Autonomous loop finished naturally!" "Green"
Write-Host ""
