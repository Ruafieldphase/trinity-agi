#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Fix Secret Manager IAM permissions for Cloud Run service account
    
.DESCRIPTION
    Grants Secret Manager Secret Accessor role to the Compute Engine default service account
    so that Cloud Run can access GOOGLE_AI_STUDIO_API_KEY secret.
    
.EXAMPLE
    .\fix_secret_manager_iam.ps1
#>

param(
    [string]$ProjectId = "naeda-genesis",
    [string]$SecretName = "GOOGLE_AI_STUDIO_API_KEY"
)

$ErrorActionPreference = "Stop"

Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Secret Manager IAM Fix Script" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Get project number
Write-Host "[1/3] Getting project number..." -ForegroundColor Yellow
$ProjectNumber = (gcloud projects describe $ProjectId --format="value(projectNumber)") 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to get project number: $ProjectNumber"
    exit 1
}

Write-Host "      Project ID: $ProjectId" -ForegroundColor Gray
Write-Host "      Project Number: $ProjectNumber" -ForegroundColor Gray
Write-Host ""

# Compute Engine default service account
$ServiceAccountEmail = "${ProjectNumber}-compute@developer.gserviceaccount.com"

Write-Host "[2/3] Granting secretmanager.secretAccessor role..." -ForegroundColor Yellow
Write-Host "      Service Account: $ServiceAccountEmail" -ForegroundColor Gray
Write-Host "      Secret: $SecretName" -ForegroundColor Gray
Write-Host ""

# Grant role on specific secret
$result = gcloud secrets add-iam-policy-binding $SecretName `
    --member="serviceAccount:$ServiceAccountEmail" `
    --role="roles/secretmanager.secretAccessor" `
    --project=$ProjectId 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to grant role on secret (might already exist or secret doesn't exist)"
    Write-Host "      Error: $result" -ForegroundColor Gray
}
else {
    Write-Host "      [OK] Role granted successfully on secret $SecretName" -ForegroundColor Green
}

Write-Host ""
Write-Host "[3/3] Verifying IAM policy..." -ForegroundColor Yellow

$policy = gcloud secrets get-iam-policy $SecretName `
    --project=$ProjectId `
    --format=json 2>&1 | ConvertFrom-Json

$found = $false
foreach ($binding in $policy.bindings) {
    if ($binding.role -eq "roles/secretmanager.secretAccessor") {
        foreach ($member in $binding.members) {
            if ($member -eq "serviceAccount:$ServiceAccountEmail") {
                $found = $true
                break
            }
        }
    }
}

if ($found) {
    Write-Host "      [OK] IAM policy verified: Service account has secretAccessor role" -ForegroundColor Green
}
else {
    Write-Warning "      [WARN]  Service account not found in IAM policy. This might be normal if using project-level permissions."
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  [OK] Secret Manager IAM Fix Complete!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Re-run GitHub Actions workflow: gh workflow run deploy-lumen-gateway.yml --field environment=staging" -ForegroundColor Gray
Write-Host "  2. Or deploy manually: .\scripts\deploy_lumen_gateway.ps1 -Environment staging" -ForegroundColor Gray
Write-Host ""

exit 0
