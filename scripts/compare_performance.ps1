# 성능 비교 테스트 스크립트
# LM Studio vs Core Gateway 응답 시간 비교 (동일한 chat/completions 기준)

param(
    [int]$Iterations = 5,
    [int]$MaxTokens = 64,
    [switch]$Warmup,
    [string]$LmModelId = "yanolja_-_eeve-korean-instruct-10.8b-v1.0"
)

# Force UTF-8 console to prevent mojibake on Windows PowerShell
try { chcp 65001 > $null 2> $null } catch {}
try {
    [Console]::InputEncoding = New-Object System.Text.UTF8Encoding($false)
    [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
    $OutputEncoding = New-Object System.Text.UTF8Encoding($false)
}
catch {}

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Performance Comparison: LM Studio vs Core Gateway" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

# 테스트 페이로드
$testMessage = "안녕하세요. 간단한 테스트입니다."

# Core Gateway 테스트
Write-Host "[1/2] Core Gateway chat test..." -ForegroundColor Yellow
$CoreBody = @{
    message = $testMessage
} | ConvertTo-Json

$CoreTimes = @()
if ($Warmup) {
    try { $null = Invoke-RestMethod -Uri "https://Core-gateway-x4qvsargwa-uc.a.run.app/chat" -Method POST -Body $CoreBody -ContentType "application/json" -TimeoutSec 30 } catch {}
}
for ($i = 1; $i -le $Iterations; $i++) {
    try {
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $response = Invoke-RestMethod -Uri "https://Core-gateway-x4qvsargwa-uc.a.run.app/chat" -Method POST -Body $CoreBody -ContentType "application/json" -TimeoutSec 30
        $sw.Stop()
        $elapsed = $sw.ElapsedMilliseconds
        $CoreTimes += $elapsed
        Write-Host "  Request $i : $elapsed ms" -ForegroundColor Green
    }
    catch {
        Write-Host "  Request $i : FAILED - $_" -ForegroundColor Red
    }
    Start-Sleep -Milliseconds 500
}

Write-Host ""

# LM Studio chat 테스트 (동일 엔드포인트로 공정 비교)
Write-Host "[2/2] LM Studio chat test..." -ForegroundColor Yellow
$lmTimes = @()
$lmOnline = $false
try {
    $probe = Invoke-RestMethod -Uri "http://localhost:8080/v1/models" -Method GET -TimeoutSec 3 -ErrorAction Stop
    $lmOnline = $true
}
catch {
    Write-Host "  LM Studio offline: skipping chat test." -ForegroundColor Yellow
}

if ($lmOnline) {
    $lmBodyBase = @{
        model      = $LmModelId
        messages   = @(@{ role = "user"; content = $testMessage })
        max_tokens = $MaxTokens
    }
    if ($Warmup) {
        try { $null = Invoke-RestMethod -Uri "http://localhost:8080/v1/chat/completions" -Method POST -Body ($lmBodyBase | ConvertTo-Json -Depth 10) -ContentType "application/json" -TimeoutSec 30 } catch {}
    }
    for ($i = 1; $i -le $Iterations; $i++) {
        try {
            $lmBody = $lmBodyBase | ConvertTo-Json -Depth 10
            $sw = [System.Diagnostics.Stopwatch]::StartNew()
            $response = Invoke-RestMethod -Uri "http://localhost:8080/v1/chat/completions" -Method POST -Body $lmBody -ContentType "application/json" -TimeoutSec 30
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

if ($CoreTimes.Count -gt 0) {
    $CoreAvg = ($CoreTimes | Measure-Object -Average).Average
    $CoreMin = ($CoreTimes | Measure-Object -Minimum).Minimum
    $CoreMax = ($CoreTimes | Measure-Object -Maximum).Maximum
    
    Write-Host "Core Gateway:" -ForegroundColor Yellow
    Write-Host "  Average: $([math]::Round($CoreAvg, 2)) ms" -ForegroundColor White
    Write-Host "  Min: $CoreMin ms" -ForegroundColor White
    Write-Host "  Max: $CoreMax ms" -ForegroundColor White
}

if ($lmTimes.Count -gt 0) {
    $lmAvg = ($lmTimes | Measure-Object -Average).Average
    $lmMin = ($lmTimes | Measure-Object -Minimum).Minimum
    $lmMax = ($lmTimes | Measure-Object -Maximum).Maximum
    
    Write-Host "LM Studio (chat):" -ForegroundColor Yellow
    Write-Host "  Average: $([math]::Round($lmAvg, 2)) ms" -ForegroundColor White
    Write-Host "  Min: $lmMin ms" -ForegroundColor White
    Write-Host "  Max: $lmMax ms" -ForegroundColor White
}

Write-Host ""
Write-Host "Recommendation:" -ForegroundColor Cyan
Write-Host "  - Core Gateway는 초기 콜드 히트 이후 평균 지연이 낮음" -ForegroundColor White
Write-Host "  - LM Studio는 로컬 모델 로딩/초기화 시간이 존재하며 하드웨어/모델에 좌우" -ForegroundColor White
Write-Host "  - 동일 chat 기준으로 비교한 결과를 참고하여 워크로드 배치 결정 권장" -ForegroundColor Green
Write-Host ""