# Save Performance Benchmark to JSON
# Runs performance tests and saves results with timestamps for trend analysis

param(
    [int]$Iterations = 5,
    [int]$MaxTokens = 64,
    [switch]$Warmup,
    [string]$OutJson = "$PSScriptRoot\..\outputs\performance_benchmark_log.jsonl",
    [switch]$Append,
    [switch]$RunAnalysis,
    [switch]$OptimizePolicy
)

$ErrorActionPreference = "Stop"
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Performance Benchmark Data Collector" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

# Optional: run trend analysis and policy optimization
if ($RunAnalysis) {
    try {
        $analyzer = Join-Path $PSScriptRoot 'analyze_performance_trends.ps1'
        if (Test-Path $analyzer) {
            Write-Host "→ Running trend analysis..." -ForegroundColor Cyan
            & $analyzer | Out-Null
            Write-Host "  ✓ Trend analysis complete" -ForegroundColor Green
        }
        else {
            Write-Host "  ⚠ analyze_performance_trends.ps1 not found" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "  ✗ Trend analysis failed: $_" -ForegroundColor Yellow
    }
}

if ($OptimizePolicy) {
    try {
        $optimizer = Join-Path $PSScriptRoot 'adaptive_routing_optimizer.ps1'
        if (Test-Path $optimizer) {
            Write-Host "→ Optimizing routing policy..." -ForegroundColor Cyan
            & $optimizer | Out-Null
            Write-Host "  ✓ Policy optimization complete" -ForegroundColor Green
        }
        else {
            Write-Host "  ⚠ adaptive_routing_optimizer.ps1 not found" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "  ✗ Policy optimization failed: $_" -ForegroundColor Yellow
    }
}

# Test message
$testMessage = "안녕하세요. 간단한 테스트입니다."

# Initialize result object
$result = @{
    timestamp = $timestamp
    config    = @{
        iterations = $Iterations
        max_tokens = $MaxTokens
        warmup     = $Warmup.IsPresent
    }
    lumen     = @{
        available    = $false
        times_ms     = @()
        avg_ms       = $null
        min_ms       = $null
        max_ms       = $null
        success_rate = 0
    }
    lm_studio = @{
        available      = $false
        times_ms       = @()
        avg_ms         = $null
        min_ms         = $null
        max_ms         = $null
        tokens_per_sec = $null
        success_rate   = 0
    }
}

# Test Lumen Gateway
Write-Host "[1/2] Testing Lumen Gateway..." -ForegroundColor Yellow
try {
    $lumenBody = @{ message = $testMessage } | ConvertTo-Json
    $lumenTimes = @()
    $lumenSuccess = 0
    
    if ($Warmup) {
        try { $null = Invoke-RestMethod -Uri "https://lumen-gateway-x4qvsargwa-uc.a.run.app/chat" -Method POST -Body $lumenBody -ContentType "application/json" -TimeoutSec 30 } catch {}
        Write-Host "  Warmup completed" -ForegroundColor DarkGray
    }
    
    for ($i = 1; $i -le $Iterations; $i++) {
        try {
            $sw = [System.Diagnostics.Stopwatch]::StartNew()
            $response = Invoke-RestMethod -Uri "https://lumen-gateway-x4qvsargwa-uc.a.run.app/chat" -Method POST -Body $lumenBody -ContentType "application/json" -TimeoutSec 30
            $sw.Stop()
            $elapsed = $sw.ElapsedMilliseconds
            $lumenTimes += $elapsed
            $lumenSuccess++
            Write-Host "  Request $i : $elapsed ms" -ForegroundColor Green
        }
        catch {
            Write-Host "  Request $i : FAILED" -ForegroundColor Red
        }
        Start-Sleep -Milliseconds 500
    }
    
    if ($lumenTimes.Count -gt 0) {
        $result.lumen.available = $true
        $result.lumen.times_ms = $lumenTimes
        $result.lumen.avg_ms = [math]::Round(($lumenTimes | Measure-Object -Average).Average, 2)
        $result.lumen.min_ms = ($lumenTimes | Measure-Object -Minimum).Minimum
        $result.lumen.max_ms = ($lumenTimes | Measure-Object -Maximum).Maximum
        $result.lumen.success_rate = [math]::Round($lumenSuccess / $Iterations, 2)
        Write-Host "  ✓ Lumen: Avg $($result.lumen.avg_ms)ms" -ForegroundColor Green
    }
}
catch {
    Write-Host "  ✗ Lumen unavailable: $_" -ForegroundColor Yellow
}

Write-Host ""

# Test LM Studio
Write-Host "[2/2] Testing LM Studio..." -ForegroundColor Yellow
try {
    $probe = Invoke-RestMethod -Uri "http://localhost:8080/v1/models" -Method GET -TimeoutSec 3 -ErrorAction Stop
    $lmTimes = @()
    $lmTokens = @()
    $lmSuccess = 0
    
    $lmBodyBase = @{
        model      = "yanolja_-_eeve-korean-instruct-10.8b-v1.0"
        messages   = @(@{ role = "user"; content = $testMessage })
        max_tokens = $MaxTokens
    }
    
    if ($Warmup) {
        try { $null = Invoke-RestMethod -Uri "http://localhost:8080/v1/chat/completions" -Method POST -Body ($lmBodyBase | ConvertTo-Json -Depth 10) -ContentType "application/json" -TimeoutSec 30 } catch {}
        Write-Host "  Warmup completed" -ForegroundColor DarkGray
    }
    
    for ($i = 1; $i -le $Iterations; $i++) {
        try {
            $lmBody = $lmBodyBase | ConvertTo-Json -Depth 10
            $sw = [System.Diagnostics.Stopwatch]::StartNew()
            $response = Invoke-RestMethod -Uri "http://localhost:8080/v1/chat/completions" -Method POST -Body $lmBody -ContentType "application/json" -TimeoutSec 30
            $sw.Stop()
            $elapsed = $sw.ElapsedMilliseconds
            $lmTimes += $elapsed
            $lmSuccess++
            
            $tokens = $null
            try { $tokens = $response.usage.total_tokens } catch {}
            if ($tokens -eq $null) {
                $tokens = [int]([math]::Ceiling($response.choices[0].message.content.Length / 4.0))
            }
            $lmTokens += $tokens
            
            Write-Host "  Request $i : $elapsed ms ($tokens tokens)" -ForegroundColor Green
        }
        catch {
            Write-Host "  Request $i : FAILED" -ForegroundColor Red
        }
        Start-Sleep -Milliseconds 500
    }
    
    if ($lmTimes.Count -gt 0) {
        $result.lm_studio.available = $true
        $result.lm_studio.times_ms = $lmTimes
        $result.lm_studio.avg_ms = [math]::Round(($lmTimes | Measure-Object -Average).Average, 2)
        $result.lm_studio.min_ms = ($lmTimes | Measure-Object -Minimum).Minimum
        $result.lm_studio.max_ms = ($lmTimes | Measure-Object -Maximum).Maximum
        $result.lm_studio.success_rate = [math]::Round($lmSuccess / $Iterations, 2)
        
        if ($lmTokens.Count -gt 0) {
            $avgTokens = ($lmTokens | Measure-Object -Average).Average
            $avgTimeSec = $result.lm_studio.avg_ms / 1000
            $result.lm_studio.tokens_per_sec = [math]::Round($avgTokens / $avgTimeSec, 2)
        }
        
        Write-Host "  ✓ LM Studio: Avg $($result.lm_studio.avg_ms)ms" -ForegroundColor Green
        if ($result.lm_studio.tokens_per_sec) {
            Write-Host "    Throughput: $($result.lm_studio.tokens_per_sec) tok/s" -ForegroundColor DarkGray
        }
    }
}
catch {
    Write-Host "  ✗ LM Studio unavailable: $_" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan

# Save to JSON
$outDir = Split-Path -Parent $OutJson
if (-not (Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}

$jsonLine = $result | ConvertTo-Json -Depth 10 -Compress
if ($Append -and (Test-Path $OutJson)) {
    Add-Content -Path $OutJson -Value $jsonLine -Encoding UTF8
    Write-Host "✓ Appended to $OutJson" -ForegroundColor Green
}
else {
    Set-Content -Path $OutJson -Value $jsonLine -Encoding UTF8
    Write-Host "✓ Saved to $OutJson" -ForegroundColor Green
}

# Print recommendation
Write-Host ""
Write-Host "Recommendation:" -ForegroundColor Cyan
if ($result.lumen.available -and $result.lm_studio.available) {
    if ($result.lumen.avg_ms -lt $result.lm_studio.avg_ms) {
        $diff = $result.lm_studio.avg_ms - $result.lumen.avg_ms
        Write-Host "  → Lumen is faster by ${diff}ms on average" -ForegroundColor Green
        Write-Host "    Use Lumen for latency-sensitive workloads" -ForegroundColor White
    }
    else {
        $diff = $result.lumen.avg_ms - $result.lm_studio.avg_ms
        Write-Host "  → LM Studio is faster by ${diff}ms on average" -ForegroundColor Green
        Write-Host "    Consider LM Studio for cost optimization" -ForegroundColor White
    }
}
elseif ($result.lumen.available) {
    Write-Host "  → Only Lumen available, use as primary" -ForegroundColor Yellow
}
elseif ($result.lm_studio.available) {
    Write-Host "  → Only LM Studio available, use as primary" -ForegroundColor Yellow
}
else {
    Write-Host "  → No inference backend available!" -ForegroundColor Red
    exit 1
}

Write-Host ""
