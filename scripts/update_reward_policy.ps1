#!/usr/bin/env pwsh
<#
.SYNOPSIS
    보상 기반 행동 정책을 업데이트합니다 (기저핵 습관 강화)
    
.DESCRIPTION
    reward_signals.jsonl을 분석해 action_policy.json을 업데이트하고
    성공적인 패턴을 강화합니다.
    
.PARAMETER UpdateInterval
    정책 업데이트 주기 (시간)
    
.EXAMPLE
    .\update_reward_policy.ps1 -UpdateInterval 24
#>

param(
    [int]$UpdateInterval = 12
)

$ErrorActionPreference = "Stop"
$workspaceRoot = Split-Path -Parent $PSScriptRoot

# Python 경로 찾기
$pythonExe = Join-Path $workspaceRoot "fdo_agi_repo\.venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

Write-Host "🧠 Updating reward-based policy..." -ForegroundColor Cyan

try {
    & $pythonExe (Join-Path $workspaceRoot "scripts\reward_tracker.py") update-policy
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Policy updated successfully" -ForegroundColor Green
        
        # 정책 요약 출력
        $policyPath = Join-Path $workspaceRoot "fdo_agi_repo\memory\action_policy.json"
        if (Test-Path $policyPath) {
            $policy = Get-Content $policyPath -Raw | ConvertFrom-Json
            Write-Host "`n📊 Current Policy Summary:" -ForegroundColor Yellow
            Write-Host "  Goal Execution Patterns: $($policy.goal_execution.Count)"
            Write-Host "  Self-Care Patterns: $($policy.self_care.Count)"
            Write-Host "  Last Updated: $($policy.updated_at)"
        }
    }
    else {
        Write-Host "❌ Policy update failed (exit code: $LASTEXITCODE)" -ForegroundColor Red
        exit $LASTEXITCODE
    }
}
catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    exit 1
}
