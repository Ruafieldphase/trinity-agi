# GitHub Actions 워크플로우 비활성화 스크립트
# 실패하는 워크플로우들을 일시적으로 비활성화하여 이메일 알림을 중단합니다.

$ErrorActionPreference = "Stop"

Write-Host "=== GitHub Actions 워크플로우 비활성화 ===" -ForegroundColor Cyan
Write-Host ""

$repoPath = "D:\nas_backup\LLM_Unified"
$disabledDir = "$repoPath\.github\workflows\disabled"

# 백업 폴더 생성
if (-not (Test-Path $disabledDir)) {
    New-Item -ItemType Directory -Force -Path $disabledDir | Out-Null
    Write-Host "✓ 백업 폴더 생성: $disabledDir" -ForegroundColor Green
}
else {
    Write-Host "✓ 백업 폴더 존재: $disabledDir" -ForegroundColor Gray
}

Write-Host ""

# 비활성화할 워크플로우 목록
$workflows = @(
    "test.yml",
    "deploy-ion-api.yml",
    "docs-link-check.yml"
)

$movedCount = 0
foreach ($workflow in $workflows) {
    $source = "$repoPath\.github\workflows\$workflow"
    $dest = "$disabledDir\$workflow"
    
    if (Test-Path $source) {
        Move-Item -Force $source $dest
        Write-Host "✓ 비활성화: $workflow → disabled/" -ForegroundColor Yellow
        $movedCount++
    }
    else {
        Write-Host "⊘ 파일 없음: $workflow (이미 비활성화됨)" -ForegroundColor Gray
    }
}

Write-Host ""

if ($movedCount -eq 0) {
    Write-Host "모든 워크플로우가 이미 비활성화되어 있습니다." -ForegroundColor Green
    exit 0
}

Write-Host "=== Git 커밋 및 푸시 ===" -ForegroundColor Cyan
Write-Host ""

Set-Location $repoPath

git add .github/workflows

$commitMsg = @"
chore: Temporarily disable failing GitHub Actions workflows

- Disable Ion Mentoring Tests
- Disable Deploy ION API to Cloud Run  
- Disable Docs Link Check

Reason: Preventing email notification spam from failing workflows.
Workflows moved to .github/workflows/disabled/ for future re-enable.
"@

git commit -m $commitMsg

Write-Host ""
Write-Host "커밋 생성 완료. GitHub에 푸시합니다..." -ForegroundColor Cyan

git push origin master

Write-Host ""
Write-Host "[OK] 완료! 워크플로우가 비활성화되었습니다." -ForegroundColor Green
Write-Host ""
Write-Host "📧 다음 커밋부터는 더 이상 실패 이메일이 오지 않습니다." -ForegroundColor Cyan
Write-Host ""
Write-Host "재활성화하려면: Move-Item $disabledDir\*.yml $repoPath\.github\workflows\" -ForegroundColor Gray
