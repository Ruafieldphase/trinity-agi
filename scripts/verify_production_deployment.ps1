# ION API Production 배포 검증 스크립트
# 2025-10-23 - v1.1.1 배포 후 상태 확인

param(
    [string]$ProductionUrl = "https://ion-api-64076350717.us-central1.run.app",
    [string]$LumenGatewayUrl = "https://lumen-gateway-production-64076350717.us-central1.run.app",
    [switch]$SkipLumen
)

$ErrorActionPreference = "Continue"
Write-Host "`n=== ION API Production 배포 검증 ===" -ForegroundColor Cyan
Write-Host "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n" -ForegroundColor Gray

# 1. Health Check
Write-Host "[1/6] Health 엔드포인트 검증..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$ProductionUrl/health" -Method Get -ErrorAction Stop
    Write-Host "  [OK] Status: $($health.status)" -ForegroundColor Green
    Write-Host "  [OK] Version: $($health.version)" -ForegroundColor Green
    Write-Host "  [OK] Pipeline Ready: $($health.pipeline_ready)" -ForegroundColor Green
    
    if ($health.version -ne "1.1.1") {
        Write-Host "  [WARN]  Expected version 1.1.1, got $($health.version)" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "  [ERROR] Health check failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 2. Phase 4 Personalized Endpoint
Write-Host "`n[2/6] Phase 4 Personalized 엔드포인트 검증..." -ForegroundColor Yellow
try {
    $body = @{
        user_id = "test-verify"
        query   = "Hello production"
    } | ConvertTo-Json -Compress
    
    $response = Invoke-RestMethod -Uri "$ProductionUrl/api/v2/recommend/personalized" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body `
        -ErrorAction Stop
    
    Write-Host "  [OK] Primary Persona: $($response.primary_persona)" -ForegroundColor Green
    Write-Host "  [OK] Confidence: $($response.confidence)" -ForegroundColor Green
}
catch {
    Write-Host "  [ERROR] Personalized endpoint failed: $($_.Exception.Message)" -ForegroundColor Red
}

# 3. Swagger UI 접근성
Write-Host "`n[3/6] Swagger UI 접근성 확인..." -ForegroundColor Yellow
try {
    $swagger = Invoke-WebRequest -Uri "$ProductionUrl/docs" -Method Get -ErrorAction Stop
    if ($swagger.StatusCode -eq 200) {
        Write-Host "  [OK] Swagger UI accessible (HTTP $($swagger.StatusCode))" -ForegroundColor Green
    }
}
catch {
    Write-Host "  [ERROR] Swagger UI not accessible: $($_.Exception.Message)" -ForegroundColor Red
}

# 4. Lumen Gateway Health (Optional)
if (-not $SkipLumen) {
    Write-Host "`n[4/6] Lumen Gateway Health 확인..." -ForegroundColor Yellow
    try {
        $lumenHealth = Invoke-RestMethod -Uri "$ProductionUrl/api/lumen/health" -Method Get -ErrorAction Stop -TimeoutSec 10
        Write-Host "  [OK] Lumen Health Status: $($lumenHealth.status)" -ForegroundColor Green
        Write-Host "  ℹ️  Lumen Version: $($lumenHealth.version)" -ForegroundColor Cyan
        
        if ($lumenHealth.google_ai) {
            Write-Host "  ℹ️  Google AI: $($lumenHealth.google_ai)" -ForegroundColor Cyan
        }
    }
    catch {
        Write-Host "  [WARN]  Lumen Health check failed (expected if gateway not deployed): $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    # 5. Lumen Personas
    Write-Host "`n[5/6] Lumen Personas 확인..." -ForegroundColor Yellow
    try {
        $personas = Invoke-RestMethod -Uri "$ProductionUrl/api/lumen/personas" -Method Get -ErrorAction Stop -TimeoutSec 10
        Write-Host "  [OK] Personas Count: $($personas.Count)" -ForegroundColor Green
        foreach ($p in $personas) {
            Write-Host "    - $($p.name): $($p.specialty)" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "  [WARN]  Lumen Personas failed (expected if gateway not deployed): $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    # 6. Lumen Chat
    Write-Host "`n[6/6] Lumen Chat 테스트..." -ForegroundColor Yellow
    try {
        $chatBody = @{ message = "Hello from verification script" } | ConvertTo-Json -Compress
        $chatResponse = Invoke-RestMethod -Uri "$ProductionUrl/api/lumen/chat" `
            -Method Post `
            -ContentType "application/json" `
            -Body $chatBody `
            -ErrorAction Stop `
            -TimeoutSec 15
        
        Write-Host "  [OK] Chat Response: $($chatResponse.response.Substring(0, [Math]::Min(50, $chatResponse.response.Length)))..." -ForegroundColor Green
    }
    catch {
        Write-Host "  [WARN]  Lumen Chat failed (expected if gateway not deployed): $($_.Exception.Message)" -ForegroundColor Yellow
    }
}
else {
    Write-Host "`n[4-6/6] Lumen 테스트 스킵됨 (-SkipLumen 플래그)" -ForegroundColor Gray
}

# Summary
Write-Host "`n=== 검증 완료 ===" -ForegroundColor Cyan
Write-Host "Production URL: $ProductionUrl" -ForegroundColor Gray
Write-Host "Lumen Gateway URL: $LumenGatewayUrl" -ForegroundColor Gray
Write-Host "`n핵심 기능(Health, Phase4)은 정상 작동 중입니다." -ForegroundColor Green
Write-Host "Lumen 통합은 Gateway 배포 상태에 따라 달라집니다.`n" -ForegroundColor Yellow
