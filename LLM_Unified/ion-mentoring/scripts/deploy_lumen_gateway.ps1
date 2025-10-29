Param(
    [ValidateSet("staging", "production")]
    [string]$Environment = "staging",
    [string]$ProjectId = "naeda-genesis",
    [string]$Region = "us-central1"
)

$ErrorActionPreference = 'Stop'

function Write-Info($msg) { Write-Host "[INFO ] $msg" -ForegroundColor Cyan }
function Write-Ok($msg) { Write-Host "[ OK  ] $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "[WARN ] $msg" -ForegroundColor Yellow }
function Write-Err($msg) { Write-Host "[ERR  ] $msg" -ForegroundColor Red }

Write-Info "Checking gcloud authentication..."
try {
    $acct = (gcloud auth list --format="value(account)" --filter="status=ACTIVE")
    if (-not $acct) { throw "No active gcloud account found" }
    Write-Ok "Active account: $acct"
}
catch {
    Write-Err $_
    Write-Err "Run: gcloud auth login; gcloud config set project $ProjectId"
    exit 1
}

$serviceBase = "lumen-gateway"
$serviceName = if ($Environment -eq "production") { $serviceBase } else { "$serviceBase-staging" }

Write-Info "Building image with Cloud Build and deploying to Cloud Run ($Region)..."

$env:CLOUDSDK_CORE_DISABLE_PROMPTS = "1"

$tag = [DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss')
$image = "gcr.io/$ProjectId/${serviceBase}:$tag"

Write-Info "Submitting build: $image"
& gcloud builds submit `
    --project $ProjectId `
    --config cloudbuild.lumen.yaml `
    --substitutions _IMAGE=$image `
    --quiet 2>&1 | ForEach-Object { $_ }
if ($LASTEXITCODE -ne 0) { Write-Err "gcloud builds submit failed with exit code $LASTEXITCODE"; exit $LASTEXITCODE }

Write-Info "Deploying service: $serviceName"
$deployArgs = @(
    "run", "deploy", $serviceName,
    "--image", $image,
    "--project", $ProjectId,
    "--region", $Region,
    "--allow-unauthenticated",
    "--timeout", "60",
    "--set-secrets", "GOOGLE_AI_STUDIO_API_KEY=GOOGLE_AI_STUDIO_API_KEY:latest",
    "--quiet"
)
if ($Environment -eq "production") {
    $deployArgs += @("--set-env-vars", "ENVIRONMENT=production", "--min-instances", "1", "--max-instances", "20", "--memory", "1Gi", "--cpu", "2")
}
else {
    $deployArgs += @("--set-env-vars", "ENVIRONMENT=staging", "--min-instances", "0", "--max-instances", "5", "--memory", "512Mi", "--cpu", "1")
}

& gcloud @deployArgs 2>&1 | ForEach-Object { $_ }
if ($LASTEXITCODE -ne 0) { Write-Err "gcloud run deploy failed with exit code $LASTEXITCODE"; exit $LASTEXITCODE }

Write-Info "Fetching service URL..."
$serviceUrl = gcloud run services describe $serviceName --project $ProjectId --region $Region --format "value(status.url)"
if (-not $serviceUrl) { Write-Err "Failed to get service URL"; exit 1 }
Write-Ok "Service URL: $serviceUrl"

Write-Info "Health check..."
try {
    $code = (curl.exe -s -o NUL -w "%{http_code}" "$serviceUrl/health")
    if ($code -ne "200") { throw "Health check HTTP $code" }
    Write-Ok "Health: 200"
}
catch {
    Write-Err "Health check failed: $_"
    exit 1
}

Write-Ok "Deployment completed successfully."
Write-Host "URL: $serviceUrl" -ForegroundColor Green
