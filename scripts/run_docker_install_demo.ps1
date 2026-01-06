# run_docker_install_demo.ps1
# Phase 2.5 Week 2 Day 8-9: Docker Desktop Auto-Installation Demo

param(
    [string]$Url = "https://www.youtube.com/watch?v=kqtD5dpn9C8",
    [switch]$DryRun,
    [switch]$Verbose,
    [switch]$NoOpen
)

$ErrorActionPreference = "Stop"
$rootDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

# Banner
Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  Docker Desktop Auto-Installation Demo" -ForegroundColor Green
Write-Host "  Phase 2.5 Week 2 Day 8-9" -ForegroundColor Gray
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Target URL: $Url" -ForegroundColor Cyan
if ($DryRun) {
    Write-Host "Mode: DRY RUN (Simulation Only)" -ForegroundColor Yellow
}
Write-Host ""

# Check Task Queue Server
Write-Host "Checking Task Queue Server..." -ForegroundColor Yellow
try {
    $null = Invoke-RestMethod -Uri "http://127.0.0.1:8091/api/health" -TimeoutSec 2
    Write-Host "  Task Queue Server: ONLINE" -ForegroundColor Green
}
catch {
    Write-Host "  Task Queue Server: OFFLINE" -ForegroundColor Red
    Write-Host "  Please start the server first" -ForegroundColor Yellow
    exit 1
}

# Check Python
$pythonPath = "$rootDir\fdo_agi_repo\.venv\Scripts\python.exe"
if (-not (Test-Path $pythonPath)) {
    Write-Host "  Python not found: $pythonPath" -ForegroundColor Red
    exit 1
}
Write-Host "  Python: OK" -ForegroundColor Green

# Check E2E Pipeline
$pipelinePath = "$rootDir\fdo_agi_repo\rpa\e2e_pipeline.py"
if (-not (Test-Path $pipelinePath)) {
    Write-Host "  E2E Pipeline not found: $pipelinePath" -ForegroundColor Red
    exit 1
}
Write-Host "  E2E Pipeline: OK" -ForegroundColor Green
Write-Host ""

# Prepare output directory
$outputDir = "$rootDir\outputs\e2e_integration"
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

# Build Python command
$pythonArgs = @("-m", "rpa.e2e_pipeline", "--url", $Url)
if ($DryRun) { $pythonArgs += "--dry-run" }
if ($Verbose) { $pythonArgs += "--verbose" }

# Execute
Write-Host "Running E2E Pipeline..." -ForegroundColor Cyan
Write-Host ""

# Change to fdo_agi_repo directory for proper module resolution
Push-Location "$rootDir\fdo_agi_repo"
try {
    & $pythonPath $pythonArgs
    $exitCode = $LASTEXITCODE
}
finally {
    Pop-Location
}

Write-Host ""
if ($exitCode -eq 0) {
    Write-Host "E2E Pipeline completed successfully" -ForegroundColor Green
}
else {
    Write-Host "E2E Pipeline failed (exit code: $exitCode)" -ForegroundColor Red
    exit $exitCode
}

Write-Host ""

# Find result
Write-Host "Looking for result files..." -ForegroundColor Yellow

$jsonFiles = Get-ChildItem -Path $outputDir -Filter "e2e_result_*.json" -File -ErrorAction SilentlyContinue |
Sort-Object LastWriteTime -Descending

if ($jsonFiles -and $jsonFiles.Count -gt 0) {
    $latestJson = $jsonFiles[0]
    Write-Host "  Latest result: $($latestJson.Name)" -ForegroundColor Green
    
    try {
        $result = Get-Content $latestJson.FullName -Raw | ConvertFrom-Json
        
        Write-Host ""
        Write-Host "====================================================================" -ForegroundColor Cyan
        Write-Host "  Result Summary" -ForegroundColor Green
        Write-Host "====================================================================" -ForegroundColor Cyan
        Write-Host ""
        
        $statusColor = if ($result.success) { "Green" } else { "Red" }
        $statusText = if ($result.success) { "SUCCESS" } else { "FAILED" }
        
        Write-Host "Status: $statusText" -ForegroundColor $statusColor
        Write-Host "Steps: $($result.steps_executed) / $($result.steps_total)" -ForegroundColor White
        Write-Host "Duration: $([math]::Round($result.duration_seconds, 2))s" -ForegroundColor White
        
        if ($result.error_message) {
            Write-Host "Error: $($result.error_message)" -ForegroundColor Yellow
        }
        
        Write-Host ""
        Write-Host "====================================================================" -ForegroundColor Cyan
        
        if (-not $NoOpen) {
            Write-Host ""
            Write-Host "Opening result in VS Code..." -ForegroundColor Cyan
            Start-Process "code" -ArgumentList $latestJson.FullName
        }
    }
    catch {
        Write-Host "  Failed to parse JSON: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}
else {
    Write-Host "  No result files found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  Demo Complete" -ForegroundColor Green
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""

exit 0