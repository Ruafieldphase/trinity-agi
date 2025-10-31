# A/B Testing Automation Script (PowerShell)

param(
    [int]$Iterations = 5,          # 각 설정당 실행 횟수
    [string]$ConfigA = "900",      # Config A 값
    [string]$ConfigB = "800",      # Config B 값
    [string]$TaskGoal = "AGI 자기교정 루프 설명 3문장"
)

$ErrorActionPreference = "Stop"

Write-Host "🔬 AGI A/B Testing Automation" -ForegroundColor Cyan

# 현재 디렉토리 확인
$MonitorDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $MonitorDir

Write-Host "📁 Monitor Directory: $MonitorDir" -ForegroundColor Gray
Write-Host "📁 Repo Root: $RepoRoot" -ForegroundColor Gray

# Python 가상환경 활성화 (있으면)
$VenvPath = Join-Path $RepoRoot ".venv"
if (Test-Path $VenvPath) {
    Write-Host "🐍 가상환경 활성화: $VenvPath" -ForegroundColor Yellow
    & "$VenvPath\Scripts\Activate.ps1"
} else {
    Write-Host "[WARN]  가상환경 없음. 시스템 Python 사용" -ForegroundColor Yellow
}

# 테스트 정보 출력
Write-Host ""
Write-Host "=" * 60 -ForegroundColor Green
Write-Host "🔬 A/B Test Configuration" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green
Write-Host ""
Write-Host "  테스트 변수: SYNTHESIS_SECTION_MAX_CHARS" -ForegroundColor Cyan
Write-Host "  Config A: $ConfigA" -ForegroundColor Cyan
Write-Host "  Config B: $ConfigB" -ForegroundColor Cyan
Write-Host "  Iterations: $Iterations (총 $($Iterations * 2)회 실행)" -ForegroundColor Cyan
Write-Host "  Task Goal: $TaskGoal" -ForegroundColor Cyan
Write-Host ""
Write-Host "  예상 소요 시간: $([math]::Round($Iterations * 2 * 2, 1)) 분" -ForegroundColor Yellow
Write-Host ""

# 확인 대기
$continue = Read-Host "계속하시겠습니까? (y/N)"
if ($continue -ne 'y' -and $continue -ne 'Y') {
    Write-Host "종료합니다." -ForegroundColor Red
    exit 0
}

# A/B 테스트 실행
Write-Host ""
Write-Host "[DEPLOY] Starting A/B Test..." -ForegroundColor Green
Write-Host ""

Set-Location $MonitorDir

# 환경변수를 직접 Python에 전달하는 대신, 커맨드라인으로 전달
$pythonScript = @"
import os
import sys
sys.path.insert(0, r'$MonitorDir')
from ab_tester import ABTester

tester = ABTester()

config_a = {'SYNTHESIS_SECTION_MAX_CHARS': '$ConfigA'}
config_b = {'SYNTHESIS_SECTION_MAX_CHARS': '$ConfigB'}

result = tester.run_ab_test(
    config_a,
    config_b,
    iterations=$Iterations,
    task_title='ab_test_synthesis',
    task_goal='$TaskGoal'
)

print('\n[OK] A/B Test completed!')
print(f'Results saved to: outputs/ab_test_*.json')
"@

python -c $pythonScript

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Green
Write-Host "[OK] A/B Test Completed" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green
Write-Host ""
Write-Host "[METRICS] 결과 확인:" -ForegroundColor Cyan
Write-Host "  - JSON: $RepoRoot\outputs\ab_test_*.json" -ForegroundColor Gray
Write-Host "  - 대시보드: http://localhost:5000 (실행 중이면)" -ForegroundColor Gray
Write-Host ""
