# Policy-Based Routing: Auto-select Lumen vs LM Studio
# Routes requests based on latency thresholds and availability

param(
    [string]$Message = "테스트 메시지입니다.",
    [int]$MaxTokens = 64,
    [int]$LatencyThresholdMs = 2000,  # Switch to Lumen if LM Studio exceeds this
    [switch]$PreferLocal,  # Prefer LM Studio when both are comparable
    [string]$BenchmarkLog = "$PSScriptRoot\..\outputs\performance_benchmark_log.jsonl",
    [string]$PolicyFile = "$PSScriptRoot\..\outputs\routing_policy.json"
)
$ErrorActionPreference = "Stop"
try {
    [Console]::OutputEncoding = [System.Text.UTF8Encoding]::UTF8
    $OutputEncoding = New-Object System.Text.UTF8Encoding $false
}
catch {}
Write-Host ""

# Load routing policy
$policy = if (Test-Path $PolicyFile) {
    $p = Get-Content $PolicyFile | ConvertFrom-Json
    Write-Host "📋 Policy loaded: Primary=$($p.primary_backend), Threshold=$($p.latency_threshold_ms)ms" -ForegroundColor Green
    $p
}
else {
    Write-Host "⚠️  No policy file found, using defaults" -ForegroundColor Yellow
    @{
        primary_backend      = "lumen"
        fallback_backend     = "lm_studio"
        latency_threshold_ms = 2000
    }
}

# Apply policy threshold (overrides default parameter)
$LatencyThresholdMs = $policy.latency_threshold_ms

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Policy-Based Inference Routing" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

# Read latest benchmark if available
$lumenAvg = $null
$lmAvg = $null
$lmAvailable = $false
$lumenAvailable = $false

if (Test-Path $BenchmarkLog) {
    try {
        $latestBenchmark = Get-Content $BenchmarkLog -Tail 1 | ConvertFrom-Json
        if ($latestBenchmark.lumen.available) {
            $lumenAvg = $latestBenchmark.lumen.avg_ms
            $lumenAvailable = $true
            Write-Host "📊 Lumen recent average: ${lumenAvg}ms" -ForegroundColor Cyan
        }
        if ($latestBenchmark.lm_studio.available) {
            $lmAvg = $latestBenchmark.lm_studio.avg_ms
            $lmAvailable = $true
            Write-Host "📊 LM Studio recent average: ${lmAvg}ms" -ForegroundColor Cyan
        }
    }
    catch {
        Write-Host "⚠ Could not read benchmark log, probing live..." -ForegroundColor Yellow
    }
}

# Live probe if no benchmark data
if ($null -eq $lumenAvg) {
    Write-Host "🔍 Probing Lumen..." -ForegroundColor Yellow
    try {
        $body = @{ message = "ping" } | ConvertTo-Json
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $null = Invoke-RestMethod -Uri "https://lumen-gateway-x4qvsargwa-uc.a.run.app/chat" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 5
        $sw.Stop()
        $lumenAvg = $sw.ElapsedMilliseconds
        $lumenAvailable = $true
        Write-Host "  ✓ Lumen probe: ${lumenAvg}ms" -ForegroundColor Green
    }
    catch {
        Write-Host "  ✗ Lumen unavailable" -ForegroundColor Red
    }
}

if ($null -eq $lmAvg) {
    Write-Host "🔍 Probing LM Studio..." -ForegroundColor Yellow
    try {
        $null = Invoke-RestMethod -Uri "http://localhost:8080/v1/models" -Method GET -TimeoutSec 2 -ErrorAction Stop
        $body = @{
            model      = "yanolja_-_eeve-korean-instruct-10.8b-v1.0"
            messages   = @(@{ role = "user"; content = "ping" })
            max_tokens = 8
        } | ConvertTo-Json -Depth 10
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $null = Invoke-RestMethod -Uri "http://localhost:8080/v1/chat/completions" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 5
        $sw.Stop()
        $lmAvg = $sw.ElapsedMilliseconds
        $lmAvailable = $true
        Write-Host "  ✓ LM Studio probe: ${lmAvg}ms" -ForegroundColor Green
    }
    catch {
        Write-Host "  ✗ LM Studio unavailable" -ForegroundColor Red
    }
}

Write-Host ""

# Routing decision
$selectedBackend = $null
$reason = ""

if (-not $lumenAvailable -and -not $lmAvailable) {
    Write-Host "❌ ERROR: No inference backend available!" -ForegroundColor Red
    exit 1
}
elseif ($lumenAvailable -and -not $lmAvailable) {
    $selectedBackend = "Lumen"
    $reason = "LM Studio offline"
}
elseif ($lmAvailable -and -not $lumenAvailable) {
    $selectedBackend = "LM Studio"
    $reason = "Lumen offline"
}
else {
    # Both available: apply policy
    if ($lmAvg -gt $LatencyThresholdMs) {
        $selectedBackend = "Lumen"
        $reason = "LM Studio exceeds latency threshold (${lmAvg}ms > ${LatencyThresholdMs}ms)"
    }
    elseif ($PreferLocal) {
        $selectedBackend = "LM Studio"
        $reason = "PreferLocal policy (${lmAvg}ms within threshold)"
    }
    elseif ($lumenAvg -lt $lmAvg) {
        $selectedBackend = "Lumen"
        $reason = "Lower latency (${lumenAvg}ms vs ${lmAvg}ms)"
    }
    else {
        $selectedBackend = "LM Studio"
        $reason = "Comparable latency, prefer local"
    }
}

Write-Host "🎯 Selected Backend: $selectedBackend" -ForegroundColor Green
Write-Host "   Reason: $reason" -ForegroundColor DarkGray
Write-Host ""

# Execute request
Write-Host "📤 Sending request..." -ForegroundColor Yellow
$sw = [System.Diagnostics.Stopwatch]::StartNew()

try {
    if ($selectedBackend -eq "Lumen") {
        $body = @{ message = $Message } | ConvertTo-Json
        $response = Invoke-RestMethod -Uri "https://lumen-gateway-x4qvsargwa-uc.a.run.app/chat" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 30
        $content = $response.response
    }
    else {
        $body = @{
            model      = "yanolja_-_eeve-korean-instruct-10.8b-v1.0"
            messages   = @(@{ role = "user"; content = $Message })
            max_tokens = $MaxTokens
        } | ConvertTo-Json -Depth 10
        $response = Invoke-RestMethod -Uri "http://localhost:8080/v1/chat/completions" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 30
        $content = $response.choices[0].message.content
    }
    
    $sw.Stop()
    $elapsed = $sw.ElapsedMilliseconds
    
    Write-Host "✓ Response received in ${elapsed}ms" -ForegroundColor Green
    Write-Host ""
    Write-Host "Response:" -ForegroundColor Cyan
    Write-Host $content -ForegroundColor White
    Write-Host ""
    
    exit 0
}
catch {
    $sw.Stop()
    Write-Host "❌ Request failed after $($sw.ElapsedMilliseconds)ms: $_" -ForegroundColor Red
    exit 1
}
