# profile_feedback_script.ps1
# Python 스크립트 실행 시간 프로파일링

param(
    [Parameter(Mandatory = $false)]
    [string]$ProjectId = "naeda-genesis",
    
    [Parameter(Mandatory = $false)]
    [string]$ServiceName = "lumen-gateway",
    
    [Parameter(Mandatory = $false)]
    [double]$BudgetUSD = 200.0,
    
    [Parameter(Mandatory = $false)]
    [int]$Iterations = 3,
    
    [Parameter(Mandatory = $false)]
    [string]$OutFile = ""
)

$ErrorActionPreference = "Stop"

Write-Host "=== Feedback Script Profiler ===" -ForegroundColor Cyan
Write-Host "Iterations: $Iterations"
Write-Host "Project: $ProjectId"
Write-Host "Service: $ServiceName"
Write-Host ""

$scriptPath = "D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/emit_feedback_metrics_once.py"
$pythonPath = "D:/nas_backup/LLM_Unified/.venv/Scripts/python.exe"

if (-not (Test-Path $scriptPath)) {
    Write-Host "ERROR: Script not found: $scriptPath" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $pythonPath)) {
    Write-Host "ERROR: Python not found: $pythonPath" -ForegroundColor Red
    exit 1
}

# Set environment variables
$env:GCP_PROJECT_ID = $ProjectId
$env:SERVICE_NAME = $ServiceName
$env:MONTHLY_BUDGET_USD = $BudgetUSD.ToString()

$results = @()

for ($i = 1; $i -le $Iterations; $i++) {
    Write-Host "Run $i of $Iterations..." -ForegroundColor Yellow
    
    $startTime = Get-Date
    $startMem = (Get-Process -Id $PID).WorkingSet64
    
    try {
        $output = & $pythonPath $scriptPath 2>&1
        $exitCode = $LASTEXITCODE
        
        $endTime = Get-Date
        $duration = ($endTime - $startTime).TotalSeconds
        
        $success = ($exitCode -eq 0)
        $statusColor = if ($success) { "Green" } else { "Red" }
        $status = if ($success) { "SUCCESS" } else { "FAILED" }
        
        Write-Host "  $status in $([math]::Round($duration, 2))s (Exit: $exitCode)" -ForegroundColor $statusColor
        
        # Parse output for insights
        $hasFallback = $output -match "fallback"
        $hasOrchestrator = $output -match "Orchestrator"
        $hasImportError = $output -match "import.*(failed|error)"
        
        $mode = if ($hasOrchestrator -and -not $hasFallback) {
            "Full Orchestrator"
        }
        elseif ($hasFallback) {
            "Fallback Mode"
        }
        else {
            "Unknown"
        }
        
        Write-Host "    Mode: $mode" -ForegroundColor Cyan
        if ($hasImportError) {
            Write-Host "    Import Error Detected" -ForegroundColor Yellow
        }
        
        $results += [PSCustomObject]@{
            Iteration       = $i
            Success         = $success
            ExitCode        = $exitCode
            DurationSeconds = $duration
            Mode            = $mode
            HasFallback     = $hasFallback
            HasImportError  = $hasImportError
            StartTime       = $startTime
            Output          = $output -join "`n"
        }
        
    }
    catch {
        Write-Host "  ERROR: $($_.Exception.Message)" -ForegroundColor Red
        $results += [PSCustomObject]@{
            Iteration       = $i
            Success         = $false
            ExitCode        = -1
            DurationSeconds = 0
            Mode            = "Error"
            HasFallback     = $false
            HasImportError  = $true
            StartTime       = $startTime
            Output          = $_.Exception.Message
        }
    }
    
    if ($i -lt $Iterations) {
        Start-Sleep -Seconds 2
    }
}

Write-Host ""
Write-Host "=== Profiling Results ===" -ForegroundColor Cyan
Write-Host ""

# Summary statistics
$successCount = ($results | Where-Object { $_.Success }).Count
$failCount = $Iterations - $successCount
$avgDuration = ($results | Where-Object { $_.Success } | Measure-Object -Property DurationSeconds -Average).Average
$minDuration = ($results | Where-Object { $_.Success } | Measure-Object -Property DurationSeconds -Minimum).Minimum
$maxDuration = ($results | Where-Object { $_.Success } | Measure-Object -Property DurationSeconds -Maximum).Maximum

Write-Host "Success Rate: $successCount/$Iterations ($([math]::Round($successCount/$Iterations*100, 1))%)" -ForegroundColor $(if ($successCount -eq $Iterations) { "Green" } else { "Yellow" })
Write-Host ""

if ($successCount -gt 0) {
    Write-Host "Duration Statistics:" -ForegroundColor Yellow
    Write-Host "  Average: $([math]::Round($avgDuration, 2))s"
    Write-Host "  Minimum: $([math]::Round($minDuration, 2))s"
    Write-Host "  Maximum: $([math]::Round($maxDuration, 2))s"
    Write-Host ""
}

# Mode analysis
$modes = $results | Group-Object -Property Mode
Write-Host "Execution Modes:" -ForegroundColor Yellow
foreach ($mode in $modes) {
    Write-Host "  $($mode.Name): $($mode.Count) runs"
}
Write-Host ""

# Detailed results
Write-Host "Detailed Results:" -ForegroundColor Yellow
$results | Format-Table -Property Iteration, Success, ExitCode, @{
    Label      = "Duration"; 
    Expression = { [math]::Round($_.DurationSeconds, 2) }
}, Mode -AutoSize

# Recommendations
Write-Host ""
Write-Host "Recommendations:" -ForegroundColor Cyan

$avgDurationRounded = [math]::Round($avgDuration, 1)

if ($avgDuration -lt 10) {
    Write-Host "  ✓ Performance is excellent (<10s average)" -ForegroundColor Green
    Write-Host "    - 5-minute interval is appropriate"
    Write-Host "    - Current 4-minute timeout provides good safety margin"
}
elseif ($avgDuration -lt 60) {
    Write-Host "  ✓ Performance is good (<1m average)" -ForegroundColor Green
    Write-Host "    - 5-minute interval is appropriate"
    Write-Host "    - Current 4-minute timeout is adequate"
}
elseif ($avgDuration -lt 240) {
    Write-Host "  ! Performance is acceptable (1-4m average)" -ForegroundColor Yellow
    Write-Host "    - Consider increasing timeout to 5 minutes"
    Write-Host "    - Or optimize script performance"
}
else {
    Write-Host "  ! Performance needs improvement (>4m average)" -ForegroundColor Red
    Write-Host "    - Increase interval to 10 minutes"
    Write-Host "    - Set timeout to 8 minutes"
    Write-Host "    - Investigate performance bottlenecks"
}

$fallbackCount = ($results | Where-Object { $_.HasFallback }).Count
if ($fallbackCount -gt 0) {
    Write-Host ""
    Write-Host "  ! Running in Fallback Mode ($fallbackCount/$Iterations)" -ForegroundColor Yellow
    Write-Host "    - FeedbackOrchestrator import is failing"
    Write-Host "    - Check Python dependencies"
    Write-Host "    - Review import errors in output"
}

$importErrorCount = ($results | Where-Object { $_.HasImportError }).Count
if ($importErrorCount -gt 0) {
    Write-Host ""
    Write-Host "  ! Import errors detected ($importErrorCount/$Iterations)" -ForegroundColor Yellow
    Write-Host "    - Review Python virtual environment"
    Write-Host "    - Ensure all dependencies installed"
    Write-Host "    - Check PYTHONPATH settings"
}

# Save results
if ($OutFile) {
    $report = @{
        GeneratedAt     = Get-Date -Format "o"
        Configuration   = @{
            ProjectId   = $ProjectId
            ServiceName = $ServiceName
            BudgetUSD   = $BudgetUSD
            Iterations  = $Iterations
        }
        Summary         = @{
            SuccessCount       = $successCount
            FailCount          = $failCount
            SuccessRate        = $successCount / $Iterations
            AvgDurationSeconds = $avgDuration
            MinDurationSeconds = $minDuration
            MaxDurationSeconds = $maxDuration
        }
        Modes           = $modes | ForEach-Object { @{
                Name  = $_.Name
                Count = $_.Count
            } }
        DetailedResults = $results
    }
    
    $report | ConvertTo-Json -Depth 10 | Out-File -FilePath $OutFile -Encoding utf8
    Write-Host ""
    Write-Host "Report saved to: $OutFile" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== Profiling Complete ===" -ForegroundColor Cyan
