<#
.SYNOPSIS
    Simplified canary deployment using Cloud Build (no Docker Desktop required)
    
.DESCRIPTION
    Directly uses gcloud builds submit for container builds, bypassing Docker Desktop.
    
.PARAMETER Percentage
    Canary traffic percentage (5, 10, 25, 50, 100)
    
.PARAMETER ProjectId
    GCP project ID (default: naeda-genesis)
    
.EXAMPLE
    .\simple_canary_deploy.ps1 -Percentage 5
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet(5, 10, 25, 50, 100)]
    [int]$Percentage,
    
    [string]$ProjectId = "naeda-genesis"
)

$ErrorActionPreference = "Stop"
$region = "us-central1"
$serviceName = "ion-api-canary"
$workDir = "D:\nas_backup\LLM_Unified\ion-mentoring"

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Simple Canary Deployment - $Percentage%" -ForegroundColor White
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Verify gcloud authentication
Write-Host "[1/4] Checking authentication..." -ForegroundColor Yellow
$account = gcloud auth list --filter=status:ACTIVE --format="value(account)"
Write-Host "  Authenticated as: $account" -ForegroundColor Green
Write-Host ""

# Step 2: Set project
Write-Host "[2/4] Setting project..." -ForegroundColor Yellow
gcloud config set project $ProjectId
Write-Host "  Project: $ProjectId" -ForegroundColor Green
Write-Host ""

# Step 3: Build and deploy with Cloud Build
Write-Host "[3/4] Building and deploying (this takes 3-5 minutes)..." -ForegroundColor Yellow
Write-Host "  Using gcloud builds submit (no Docker Desktop needed)" -ForegroundColor Gray
Write-Host ""

Set-Location -Path $workDir

# Deploy canary service
gcloud run deploy $serviceName `
    --source . `
    --region $region `
    --project $ProjectId `
    --platform managed `
    --allow-unauthenticated `
    --memory 2Gi `
    --cpu 2 `
    --timeout 300 `
    --max-instances 10 `
    --min-instances 1 `
    --set-env-vars "CANARY_ENABLED=true,CANARY_PERCENTAGE=$Percentage" `
    --tag "canary-$Percentage-percent"

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Deployment failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "  Deployed successfully!" -ForegroundColor Green
Write-Host ""

# Step 4: Get service URL
Write-Host "[4/4] Verifying deployment..." -ForegroundColor Yellow
$url = gcloud run services describe $serviceName --region $region --project $ProjectId --format="value(status.url)"
Write-Host "  Service URL: $url" -ForegroundColor Green

# Test health endpoint
Write-Host ""
Write-Host "Testing health endpoint..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$url/health" -Method GET -TimeoutSec 10
    Write-Host "  Status: $($health.status)" -ForegroundColor Green
    Write-Host "  Version: $($health.version)" -ForegroundColor Green
}
catch {
    Write-Host "  Warning: Health check failed (service may still be starting)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Deployment Complete!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Run health check: .\quick_health_check.ps1" -ForegroundColor Gray
Write-Host "  2. Monitor dashboard: .\system_dashboard.ps1" -ForegroundColor Gray
Write-Host "  3. Check metrics: Prometheus at http://localhost:9090" -ForegroundColor Gray
Write-Host ""
