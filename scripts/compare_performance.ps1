# 성능 비교 테스트 스크립트
# LM Studio vs Lumen Gateway 응답 시간 비교

# Force UTF-8 console to prevent mojibake on Windows PowerShell
try { chcp 65001 > $null 2> $null } catch {}
try {
    [Console]::InputEncoding = New-Object System.Text.UTF8Encoding($false)
    [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
    $OutputEncoding = New-Object System.Text.UTF8Encoding($false)
}
catch {}

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Performance Comparison: LM Studio vs Lumen Gateway" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

# 테스트 페이로드
$testMessage = "안녕하세요. 간단한 테스트입니다."

# Lumen Gateway 테스트
Write-Host "[1/2] Lumen Gateway test..." -ForegroundColor Yellow
$lumenBody = @{
    message = $testMessage
} | ConvertTo-Json

$lumenTimes = @()
for ($i = 1; $i -le 5; $i++) {
    try {
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $response = Invoke-RestMethod -Uri "https://lumen-gateway-x4qvsargwa-uc.a.run.app/chat" -Method POST -Body $lumenBody -ContentType "application/json" -TimeoutSec 30
        $sw.Stop()
        $elapsed = $sw.ElapsedMilliseconds
        $lumenTimes += $elapsed
        Write-Host "  Request $i : $elapsed ms" -ForegroundColor Green
    }
    catch {
        Write-Host "  Request $i : FAILED - $_" -ForegroundColor Red
    }
    Start-Sleep -Milliseconds 500
}

Write-Host ""

# LM Studio health check (model load status)
Write-Host "[2/2] LM Studio health check..." -ForegroundColor Yellow
$lmTimes = @()
$lmOnline = $false
try {
    $probe = Invoke-RestMethod -Uri "http://localhost:8080/v1/models" -Method GET -TimeoutSec 3 -ErrorAction Stop
    $lmOnline = $true
}
catch {
    Write-Host "  LM Studio offline: skipping health check." -ForegroundColor Yellow
}

if ($lmOnline) {
    for ($i = 1; $i -le 5; $i++) {
        try {
            $sw = [System.Diagnostics.Stopwatch]::StartNew()
            $response = Invoke-RestMethod -Uri "http://localhost:8080/v1/models" -Method GET -TimeoutSec 10
            $sw.Stop()
            $elapsed = $sw.ElapsedMilliseconds
            $lmTimes += $elapsed
            Write-Host "  Request $i : $elapsed ms" -ForegroundColor Green
        }
        catch {
            Write-Host "  Request $i : FAILED - $_" -ForegroundColor Red
        }
        Start-Sleep -Milliseconds 500
    }
}

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

if ($lumenTimes.Count -gt 0) {
    $lumenAvg = ($lumenTimes | Measure-Object -Average).Average
    $lumenMin = ($lumenTimes | Measure-Object -Minimum).Minimum
    $lumenMax = ($lumenTimes | Measure-Object -Maximum).Maximum
    
    Write-Host "Lumen Gateway:" -ForegroundColor Yellow
    Write-Host "  Average: $([math]::Round($lumenAvg, 2)) ms" -ForegroundColor White
    Write-Host "  Min: $lumenMin ms" -ForegroundColor White
    Write-Host "  Max: $lumenMax ms" -ForegroundColor White
}

if ($lmTimes.Count -gt 0) {
    $lmAvg = ($lmTimes | Measure-Object -Average).Average
    $lmMin = ($lmTimes | Measure-Object -Minimum).Minimum
    $lmMax = ($lmTimes | Measure-Object -Maximum).Maximum
    
    Write-Host "LM Studio (health check):" -ForegroundColor Yellow
    Write-Host "  Average: $([math]::Round($lmAvg, 2)) ms" -ForegroundColor White
    Write-Host "  Min: $lmMin ms" -ForegroundColor White
    Write-Host "  Max: $lmMax ms" -ForegroundColor White
}

Write-Host ""
Write-Host "Recommendation:" -ForegroundColor Cyan
Write-Host "  - Lumen Gateway is cloud-based, stable and fast" -ForegroundColor White
Write-Host "  - LM Studio requires local model loading and has slow cold starts" -ForegroundColor White
Write-Host "  - Currently recommend using Lumen Gateway" -ForegroundColor Green
Write-Host ""
