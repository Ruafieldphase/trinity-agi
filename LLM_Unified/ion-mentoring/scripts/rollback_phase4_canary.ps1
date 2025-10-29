<#
.SYNOPSIS
    Phase 4 Canary Rollback Script

.DESCRIPTION
    카나리 배포를 롤백하고 100% 레거시 트래픽으로 복귀하는 스크립트입니다.

.PARAMETER ProjectId
    Google Cloud 프로젝트 ID

.PARAMETER Region
    Cloud Run 리전 (기본값: us-central1)

.PARAMETER DeleteCanaryService
    카나리 서비스 완전 삭제 여부 (기본값: $true)

.EXAMPLE
    .\rollback_phase4_canary.ps1 -ProjectId "ion-mentoring-prod"

.NOTES
    Author: GitHub Copilot
    Date: 2025-10-18
    Version: 1.0.0
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,
    
    [Parameter(Mandatory = $false)]
    [string]$Region = "us-central1",
    
    [Parameter(Mandatory = $false)]
    [bool]$DeleteCanaryService = $true,

    [Parameter(Mandatory = $false)]
    [switch]$AutoApprove = $false
)

$ErrorActionPreference = "Stop"

$SERVICE_CANARY = "ion-api-canary"
$TIMESTAMP = Get-Date -Format "yyyyMMdd-HHmmss"

Write-Host "==================== Phase 4 Canary Rollback ====================" -ForegroundColor Red
Write-Host "Project ID: $ProjectId" -ForegroundColor Yellow
Write-Host "Region: $Region" -ForegroundColor Yellow
Write-Host "Delete Canary Service: $DeleteCanaryService" -ForegroundColor Yellow
Write-Host "====================================================================" -ForegroundColor Red
Write-Host ""

# 사용자 확인
if (-not $AutoApprove) {
    $confirmation = Read-Host "Are you sure you want to rollback the canary deployment? This action will route 100% traffic to legacy. (yes/no)"
    if ($confirmation -ne "yes") {
        Write-Host "Rollback cancelled by user." -ForegroundColor Green
        exit 0
    }
}
else {
    Write-Host "Auto-approve enabled: proceeding without interactive confirmation." -ForegroundColor Yellow
}

# Force non-interactive mode for gcloud
$env:CLOUDSDK_CORE_DISABLE_PROMPTS = '1'

Write-Host ""
Write-Host "Step 1: Stopping canary service..." -ForegroundColor Cyan

# 카나리 서비스 트래픽을 0%로 설정 (서비스 중지)
gcloud run services update $SERVICE_CANARY `
    --no-traffic `
    --region=$Region `
    --project=$ProjectId `
    --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to stop canary service traffic" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Canary service traffic stopped (0%)" -ForegroundColor Green

# 카나리 서비스 삭제 (선택적)
if ($DeleteCanaryService) {
    Write-Host ""
    Write-Host "Step 2: Deleting canary service..." -ForegroundColor Cyan
    
    gcloud run services delete $SERVICE_CANARY `
        --region=$Region `
        --project=$ProjectId `
        --quiet
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to delete canary service" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✓ Canary service deleted" -ForegroundColor Green
}
else {
    Write-Host ""
    Write-Host "Step 2: Keeping canary service (traffic = 0%)" -ForegroundColor Yellow
}

# 롤백 완료
Write-Host ""
Write-Host "====================================================================" -ForegroundColor Green
Write-Host "Rollback Completed Successfully!" -ForegroundColor Green
Write-Host "====================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "All traffic is now routed to LEGACY service (100%)" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "1. Monitor legacy service metrics for stability" -ForegroundColor White
Write-Host "2. Review rollback reason and logs" -ForegroundColor White
Write-Host "3. Create incident report (PHASE4_ROLLBACK_$TIMESTAMP.md)" -ForegroundColor White
Write-Host "4. Fix canary issues before next deployment" -ForegroundColor White
Write-Host ""
