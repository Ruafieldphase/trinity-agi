# Resonance Simulator Smoke Test Runner
# 목적: 7일 위상 루프 기반 공명/에너지/엔트로피 동역학 시뮬레이션 검증

$ErrorActionPreference = "Stop"
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Resonance Simulator Smoke Test" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

try {
    # 1. Python 스크립트 실행
    Write-Host "[1/3] Running resonance simulator..." -ForegroundColor Yellow
    python scripts\resonance_simulator.py
    
    if ($LASTEXITCODE -ne 0) {
        throw "Simulator failed with exit code $LASTEXITCODE"
    }
    
    # 2. 결과 파일 확인
    Write-Host "`n[2/3] Verifying output..." -ForegroundColor Yellow
    $outputPath = "outputs\resonance_simulation_latest.json"
    
    if (-not (Test-Path $outputPath)) {
        throw "Output file not found: $outputPath"
    }
    
    $result = Get-Content $outputPath -Raw | ConvertFrom-Json
    
    Write-Host "  - Final resonance: $($result.final_state.resonance)" -ForegroundColor Gray
    Write-Host "  - Final entropy: $($result.final_state.entropy)" -ForegroundColor Gray
    Write-Host "  - Horizon crossings: $($result.final_state.horizon_crossings)" -ForegroundColor Gray
    Write-Host "  - History count: $($result.history_count)" -ForegroundColor Gray
    
    # 3. 기본 검증
    Write-Host "`n[3/3] Basic validation..." -ForegroundColor Yellow
    
    if ($result.history_count -lt 100) {
        throw "History count too low: $($result.history_count)"
    }
    
    if ($result.final_state.resonance -lt 0 -or $result.final_state.resonance -gt 1) {
        throw "Resonance out of range: $($result.final_state.resonance)"
    }
    
    Write-Host "  - History count: OK" -ForegroundColor Green
    Write-Host "  - Resonance range: OK" -ForegroundColor Green
    
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "PASS: All smoke tests passed" -ForegroundColor Green
    Write-Host "========================================`n" -ForegroundColor Green
    
    exit 0
    
}
catch {
    Write-Host "`n========================================" -ForegroundColor Red
    Write-Host "FAIL: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "========================================`n" -ForegroundColor Red
    exit 1
}