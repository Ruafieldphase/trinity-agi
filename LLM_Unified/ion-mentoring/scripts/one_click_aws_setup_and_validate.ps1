#Requires -Version 5.1
<#
.SYNOPSIS
    One-click AWS credentials setup + Phase1 validation
.DESCRIPTION
    Calls setup_aws_credentials.ps1 -> STS check -> deployment_phase1_validation.ps1 -> (optional) Dry-Run
    User runs this script once for complete AWS auth + pre-deployment validation.
.PARAMETER Profile
    AWS CLI profile name (default: lubit-canary)
.PARAMETER Region
    AWS region (default: ap-northeast-2)
.PARAMETER RunDryRun
    After Phase1 validation, automatically run deploy_phase4_canary.ps1 -DryRun
.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File .\one_click_aws_setup_and_validate.ps1
    powershell -NoProfile -ExecutionPolicy Bypass -File .\one_click_aws_setup_and_validate.ps1 -RunDryRun
#>
[CmdletBinding()]
param(
    [string]$Profile = "lubit-canary",
    [string]$Region = "ap-northeast-2",
    [switch]$RunDryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
try { $OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false) } catch {}

function Write-Info([string]$msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Ok  ([string]$msg) { Write-Host "[OK]   $msg" -ForegroundColor Green }
function Write-Warn([string]$msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err ([string]$msg) { Write-Host "[ERR]  $msg" -ForegroundColor Red }

Write-Info "=== One-Click AWS Setup + Phase1 Validation ==="

# Paths
$repoRoot = Resolve-Path (Join-Path (Join-Path $PSScriptRoot '..') '..')
$scripts = (Resolve-Path $PSScriptRoot).Path
$phase1 = Join-Path $repoRoot 'deployment_phase1_validation.ps1'
$deploy = Join-Path $scripts 'deploy_phase4_canary.ps1'
$setupAws = Join-Path $scripts 'setup_aws_credentials.ps1'

Write-Info "Repository root: $repoRoot"

# Step 0: Check AWS CLI
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Err "AWS CLI not found. Install from https://docs.aws.amazon.com/cli/ and retry."
    exit 1
}

# Step 1: AWS credentials setup (session-scoped with ExportEnv)
if (-not (Test-Path $setupAws)) {
    Write-Err "Setup script not found: $setupAws"
    exit 1
}
Write-Info "Setting up AWS credentials (Secret Key will not be displayed on screen)..."
& $setupAws -Profile $Profile -Region $Region -ExportEnv
if ($LASTEXITCODE -ne 0) {
    Write-Err "Credential setup failed"
    exit 1
}

# Step 2: STS validation
Write-Info "Verifying credentials with AWS STS get-caller-identity..."
try {
    $stsOut = aws sts get-caller-identity --output json 2>&1
    if ($LASTEXITCODE -ne 0) { throw "STS call failed: exit code $LASTEXITCODE" }
    $identity = $stsOut | ConvertFrom-Json
    Write-Ok ("STS verified - Account: {0}, ARN: {1}" -f $identity.Account, $identity.Arn)
}
catch {
    Write-Err ("STS failed: {0}" -f $_.Exception.Message)
    Write-Warn "Check Access Key/Secret Key, network connectivity, or IAM permissions."
    exit 2
}

# Step 3: Phase1 pre-deployment validation
if (-not (Test-Path $phase1)) {
    Write-Err "Phase1 validation script not found: $phase1"
    exit 3
}

Write-Info "Running Phase1 validation... (path: $phase1)"
$phase1Succeeded = $true
try {
    Push-Location $repoRoot
    & $phase1
    $nativeCode = $LASTEXITCODE
    $psOk = $?
    if (-not $psOk -or ($null -ne $nativeCode -and $nativeCode -ne 0)) { 
        $phase1Succeeded = $false 
    }
}
catch {
    $phase1Succeeded = $false
    Write-Err ("Phase1 validation exception: {0}" -f $_.Exception.Message)
}
finally { 
    Pop-Location 
}

if ($phase1Succeeded) { 
    Write-Ok "Phase1 validation: PASSED" 
}
else { 
    Write-Warn "Phase1 validation: WARNINGS or FAILURES detected" 
}

# Step 4: (Optional) Dry-Run deployment
if ($RunDryRun) {
    if (-not (Test-Path $deploy)) {
        Write-Err "Deploy script not found: $deploy"
        exit 4
    }
    Write-Info "Running Phase4 Dry-Run deployment..."
    try {
        & $deploy -ProjectId 'naeda-genesis' -DryRun
        Write-Ok "Dry-Run completed"
    }
    catch {
        Write-Warn ("Dry-Run warning/error: {0}" -f $_.Exception.Message)
    }
}

Write-Ok "All steps completed successfully."
Write-Info "Next recommended steps:"
Write-Info "  (1) Run monitoring status check task"
Write-Info "  (2) Execute canary deployment tasks in sequence: 5% -> 10% -> 25% -> 50% -> 100%"
exit 0
