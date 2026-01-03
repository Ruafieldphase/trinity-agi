#Requires -Version 5.1
<#
.SYNOPSIS
    Phase 9 풀스택 스모크 검증 자동화 스크립트.

.DESCRIPTION
    아래 순서로 핵심 검증 스텝을 실행해 Phase 9 E2E 테스트가 ALL GREEN 상태인지 확인합니다.
      1) BQI/YouTube 산출물 동기화 및 정규화
      2) Full-Stack Orchestrator 테스트 모드 실행 (상태 파일 생성)
      3) 실시간 피드백 루프 단일 사이클 실행
      4) Phase 9 E2E 통합 테스트 실행

    성공 시 `outputs/phase9_e2e_test_report.json`이 최신 상태로 갱신됩니다.

.PARAMETER OpenReport
    실행 완료 후 E2E 리포트를 VS Code(또는 기본 뷰어)에서 연다.
#>

param(
    [switch]$OpenReport
)

$ErrorActionPreference = 'Stop'

function Invoke-Step {
    param (
        [Parameter(Mandatory)]
        [string]$Label,
        [Parameter(Mandatory)]
        [scriptblock]$Action
    )

    Write-Host ""
    Write-Host "▶ $Label" -ForegroundColor Cyan
    & $Action
    if ($LASTEXITCODE -ne 0) {
        throw "Step '$Label' failed with exit code $LASTEXITCODE."
    }
    Write-Host "✓ Completed: $Label" -ForegroundColor Green
}

$workspaceRoot = Split-Path -Parent $PSScriptRoot
$python = (Get-Command python -ErrorAction Stop).Source
Push-Location $workspaceRoot

try {
    Write-Host "=== Phase 9 Smoke Verification ===" -ForegroundColor Yellow
    Write-Host ("Workspace: {0}" -f $workspaceRoot) -ForegroundColor Gray

    Invoke-Step -Label "Sync BQI / YouTube artifacts" -Action {
        & $python scripts/sync_bqi_models.py
    }

    Invoke-Step -Label "Run Full-Stack Orchestrator (test mode)" -Action {
        & $python fdo_agi_repo/orchestrator/full_stack_orchestrator.py --mode test
    }

    Invoke-Step -Label "Run realtime feedback loop cycle" -Action {
        & $python fdo_agi_repo/scripts/run_realtime_feedback_cycle.py
    }

    Invoke-Step -Label "Execute Phase 9 E2E test" -Action {
        & $python fdo_agi_repo/scripts/test_fullstack_integration_e2e.py
    }

    Write-Host ""
    Write-Host "🎉 Phase 9 smoke verification completed successfully." -ForegroundColor Green
    Write-Host "    Report: outputs/phase9_e2e_test_report.json" -ForegroundColor Gray
}
finally {
    Pop-Location
}

if ($OpenReport) {
    $reportPath = Join-Path $workspaceRoot "outputs\phase9_e2e_test_report.json"
    if (Test-Path $reportPath) {
        $codeCmd = Get-Command code -ErrorAction SilentlyContinue
        if ($null -ne $codeCmd) {
            Write-Host "Opening report in VS Code..." -ForegroundColor Gray
            Start-Process $codeCmd.Source -ArgumentList "`"$reportPath`""
        }
        else {
            Write-Host "Opening report with default viewer..." -ForegroundColor Gray
            Start-Process $reportPath
        }
    }
    else {
        Write-Warning "Report not found at $reportPath"
    }
}