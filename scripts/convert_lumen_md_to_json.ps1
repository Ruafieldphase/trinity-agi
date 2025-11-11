# convert_lumen_md_to_json.ps1
# 루멘 레이턴시 MD 파일을 JSON으로 변환

param(
    [Parameter(Mandatory = $false)]
    [string]$InputMd = "outputs\lumen_latency_latest.md",
    
    [Parameter(Mandatory = $false)]
    [string]$OutputJson = "outputs\lumen_latency_latest.json"
)

$ErrorActionPreference = 'Stop'

try {
    if (-not (Test-Path $InputMd)) {
        Write-Host "❌ Input file not found: $InputMd" -ForegroundColor Red
        exit 1
    }
    
    $content = Get-Content $InputMd -Raw -Encoding UTF8
    
    # 레이턴시 값 추출 (테이블 형식)
    $avgPattern = '\|\s*avg\s*\|\s*([0-9]+)\s*\|'
    $minPattern = '\|\s*min\s*\|\s*([0-9]+)\s*\|'
    $maxPattern = '\|\s*max\s*\|\s*([0-9]+)\s*\|'
    $p50Pattern = '\|\s*p50\s*\|\s*([0-9]+)\s*\|'
    $p90Pattern = '\|\s*p90\s*\|\s*([0-9]+)\s*\|'
    
    $avgMatch = [regex]::Match($content, $avgPattern)
    $minMatch = [regex]::Match($content, $minPattern)
    $maxMatch = [regex]::Match($content, $maxPattern)
    $p50Match = [regex]::Match($content, $p50Pattern)
    $p90Match = [regex]::Match($content, $p90Pattern)
    
    $avgLatency = if ($avgMatch.Success) { [double]$avgMatch.Groups[1].Value } else { 0.0 }
    $minLatency = if ($minMatch.Success) { [double]$minMatch.Groups[1].Value } else { 0.0 }
    $maxLatency = if ($maxMatch.Success) { [double]$maxMatch.Groups[1].Value } else { 0.0 }
    $p50Latency = if ($p50Match.Success) { [double]$p50Match.Groups[1].Value } else { 0.0 }
    $p90Latency = if ($p90Match.Success) { [double]$p90Match.Groups[1].Value } else { 0.0 }
    
    # 레코드 수와 상태
    $recordsPattern = 'Records:\s*(\d+)'
    $okPattern = 'OK:\s*(\d+)'
    $warnPattern = 'Warn:\s*(\d+)'
    
    $recordsMatch = [regex]::Match($content, $recordsPattern)
    $okMatch = [regex]::Match($content, $okPattern)
    $warnMatch = [regex]::Match($content, $warnPattern)
    
    $totalRecords = if ($recordsMatch.Success) { [int]$recordsMatch.Groups[1].Value } else { 0 }
    $okCount = if ($okMatch.Success) { [int]$okMatch.Groups[1].Value } else { 0 }
    $warnCount = if ($warnMatch.Success) { [int]$warnMatch.Groups[1].Value } else { 0 }
    
    $successRate = if ($totalRecords -gt 0) { [double]$okCount / [double]$totalRecords } else { 1.0 }
    
    # JSON 생성
    $jsonData = @{
        timestamp      = (Get-Date).ToUniversalTime().ToString("o")
        avg_latency_ms = $avgLatency
        min_latency_ms = $minLatency
        max_latency_ms = $maxLatency
        p50_latency_ms = $p50Latency
        p90_latency_ms = $p90Latency
        success_rate   = $successRate
        total_records  = $totalRecords
        ok_count       = $okCount
        warn_count     = $warnCount
        source         = $InputMd
        observations   = @(
            @{
                endpoint   = "/api/v2/recommend/personalized"
                latency_ms = $avgLatency
                success    = ($okCount -gt 0)
                timestamp  = (Get-Date).ToUniversalTime().ToString("o")
            }
        )
    }
    
    # JSON 저장 (BOM 없이)
    $jsonString = $jsonData | ConvertTo-Json -Depth 10
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($OutputJson, $jsonString, $utf8NoBom)
    
    Write-Host "✅ Converted MD to JSON: $OutputJson" -ForegroundColor Green
    Write-Host "   Average Latency: $avgLatency ms (p50: $p50Latency, p90: $p90Latency)" -ForegroundColor Cyan
    Write-Host "   Success Rate: $($successRate * 100)% ($okCount / $totalRecords)" -ForegroundColor Cyan
    
}
catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    exit 1
}
