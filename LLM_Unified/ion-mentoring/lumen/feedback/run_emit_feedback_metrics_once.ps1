param(
    [string]$ProjectId = "naeda-genesis",
    [string]$ServiceName = "lumen-gateway",
    [string]$BudgetUSD = "200.0",
    [string]$VenvPython = "${env:WORKSPACE_FOLDER}/LLM_Unified/.venv/Scripts/python.exe"
)

if (-not $env:WORKSPACE_FOLDER) {
    # Try to infer workspace root from this script path
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $repoRoot = Resolve-Path (Join-Path $scriptDir "..\..\..\..")
    $env:WORKSPACE_FOLDER = $repoRoot.Path
}

$pythonPath = $VenvPython
if (-not (Test-Path $pythonPath)) {
    $pythonPath = Join-Path $env:WORKSPACE_FOLDER "LLM_Unified/.venv/Scripts/python.exe"
}

$scriptPath = Join-Path $env:WORKSPACE_FOLDER "LLM_Unified/ion-mentoring/lumen/feedback/emit_feedback_metrics_once.py"

Write-Host "Running feedback metrics emitter once..." -ForegroundColor Cyan
Write-Host "  ProjectId   : $ProjectId"
Write-Host "  ServiceName : $ServiceName"
Write-Host "  BudgetUSD   : $BudgetUSD"
Write-Host "  Python      : $pythonPath"
Write-Host "  Script      : $scriptPath"

$env:GCP_PROJECT_ID = $ProjectId
$env:SERVICE_NAME = $ServiceName
$env:MONTHLY_BUDGET_USD = $BudgetUSD

& $pythonPath $scriptPath
$exitCode = $LASTEXITCODE
Write-Host "Emitter exit code: $exitCode" -ForegroundColor Yellow
exit 0
