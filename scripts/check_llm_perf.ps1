# check_llm_perf.ps1 - Local LLM Performance Diagnostics (Simplified)
param(
    [switch]$Benchmark
)

Write-Host "=== Local LLM Performance Check ===" -ForegroundColor Cyan
Write-Host ""

# 1. Test Current Latency
Write-Host "[1/3] Testing current latency..." -ForegroundColor Yellow
$testPayload = @{
    model       = "local-model"
    prompt      = "Hello"
    max_tokens  = 10
    temperature = 0.7
} | ConvertTo-Json

try {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $response = Invoke-WebRequest -Uri "http://localhost:8080/v1/completions" `
        -Method POST -Body $testPayload -ContentType "application/json" `
        -TimeoutSec 30 -ErrorAction Stop
    $sw.Stop()
    $latency = $sw.ElapsedMilliseconds
    
    if ($latency -gt 2000) {
        Write-Host "  Current: ${latency}ms (WARNING: Very Slow)" -ForegroundColor Red
    }
    elseif ($latency -gt 1000) {
        Write-Host "  Current: ${latency}ms (Needs Optimization)" -ForegroundColor Yellow
    }
    else {
        Write-Host "  Current: ${latency}ms (Good)" -ForegroundColor Green
    }
}
catch {
    Write-Host "  ERROR: Cannot connect to LM Studio on port 8080" -ForegroundColor Red
    Write-Host "  Make sure LM Studio is running with API server enabled" -ForegroundColor Gray
    exit 1
}

# 2. Check LM Studio Process
Write-Host ""
Write-Host "[2/3] Checking LM Studio process..." -ForegroundColor Yellow
$process = Get-Process -Name "LM Studio" -ErrorAction SilentlyContinue
if ($process) {
    $cpu = [math]::Round($process.CPU, 2)
    $memMB = [math]::Round($process.WorkingSet64 / 1MB, 1)
    Write-Host "  Running: PID $($process.Id)" -ForegroundColor Green
    Write-Host "  CPU Time: ${cpu}s" -ForegroundColor Cyan
    Write-Host "  Memory: ${memMB}MB" -ForegroundColor Cyan
}
else {
    Write-Host "  LM Studio process not found" -ForegroundColor Yellow
}

# 3. System Resources
Write-Host ""
Write-Host "[3/3] Checking system resources..." -ForegroundColor Yellow
$os = Get-CimInstance Win32_OperatingSystem
$totalRAM = [math]::Round($os.TotalVisibleMemorySize / 1MB, 1)
$freeRAM = [math]::Round($os.FreePhysicalMemory / 1MB, 1)
$usedRAM = $totalRAM - $freeRAM

Write-Host "  RAM: ${usedRAM}GB / ${totalRAM}GB used" -ForegroundColor Cyan

$gpu = Get-CimInstance Win32_VideoController | Where-Object { $_.AdapterRAM -gt 0 }
if ($gpu) {
    Write-Host "  GPU: $($gpu.Name)" -ForegroundColor Cyan
}

# 4. Optimization Recommendations
Write-Host ""
Write-Host "=== Optimization Recommendations ===" -ForegroundColor Cyan
Write-Host ""

if ($latency -gt 2000) {
    Write-Host "[HIGH] Reduce Context Length:" -ForegroundColor Red
    Write-Host "  - Open LM Studio settings" -ForegroundColor Gray
    Write-Host "  - Set Context Length: 2048 (현재 4096일 경우)" -ForegroundColor Gray
    Write-Host "  - Expected gain: ~30% faster" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "[HIGH] Maximize GPU Offload:" -ForegroundColor Red
    Write-Host "  - Open LM Studio model settings" -ForegroundColor Gray
    Write-Host "  - Set GPU Layers: MAX (99 or ALL)" -ForegroundColor Gray
    Write-Host "  - Set Batch Size: 512" -ForegroundColor Gray
    Write-Host "  - Expected gain: ~40% faster" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "[MEDIUM] Try Smaller Model:" -ForegroundColor Yellow
    Write-Host "  - Current model might be too large (7B or 13B?)" -ForegroundColor Gray
    Write-Host "  - Try Q4_K_M or Q5_K_M quantization" -ForegroundColor Gray
    Write-Host "  - Or use smaller model (3B instead of 7B)" -ForegroundColor Gray
    Write-Host "  - Expected gain: ~50% faster (with quality trade-off)" -ForegroundColor Green
    Write-Host ""
}

if ($latency -gt 1000 -and $latency -le 2000) {
    Write-Host "[MEDIUM] Enable KV Cache Optimization:" -ForegroundColor Yellow
    Write-Host "  - Open LM Studio advanced settings" -ForegroundColor Gray
    Write-Host "  - Enable KV Cache with F16 or Q8" -ForegroundColor Gray
    Write-Host "  - Expected gain: ~25% faster on repeated queries" -ForegroundColor Green
    Write-Host ""
}

# Benchmark Mode
if ($Benchmark) {
    Write-Host ""
    Write-Host "=== Running Benchmark (5 tests) ===" -ForegroundColor Cyan
    $latencies = @()
    
    for ($i = 1; $i -le 5; $i++) {
        Write-Host "  Test $i/5..." -NoNewline
        try {
            $sw = [System.Diagnostics.Stopwatch]::StartNew()
            $null = Invoke-WebRequest -Uri "http://localhost:8080/v1/completions" `
                -Method POST -Body $testPayload -ContentType "application/json" `
                -TimeoutSec 30 -ErrorAction Stop
            $sw.Stop()
            $latencies += $sw.ElapsedMilliseconds
            Write-Host " $($sw.ElapsedMilliseconds)ms" -ForegroundColor Cyan
        }
        catch {
            Write-Host " FAILED" -ForegroundColor Red
        }
        Start-Sleep -Milliseconds 500
    }
    
    if ($latencies.Count -gt 0) {
        $avg = [math]::Round(($latencies | Measure-Object -Average).Average, 0)
        $min = ($latencies | Measure-Object -Minimum).Minimum
        $max = ($latencies | Measure-Object -Maximum).Maximum
        $variance = [math]::Round(($latencies | ForEach-Object { ($_ - $avg) * ($_ - $avg) } | Measure-Object -Average).Average, 0)
        
        Write-Host ""
        Write-Host "Benchmark Results:" -ForegroundColor Green
        Write-Host "  Average: ${avg}ms" -ForegroundColor Cyan
        Write-Host "  Min: ${min}ms" -ForegroundColor Cyan
        Write-Host "  Max: ${max}ms" -ForegroundColor Cyan
        Write-Host "  Variance: ${variance}" -ForegroundColor Cyan
    }
}

Write-Host ""
Write-Host "Check complete! Target: <1000ms (current: ${latency}ms)" -ForegroundColor $(if ($latency -lt 1000) { "Green" }else { "Yellow" })
