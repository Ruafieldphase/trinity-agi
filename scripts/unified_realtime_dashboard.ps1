# 🎯 AGI System - Unified Real-Time Dashboard

<#
.SYNOPSIS
    통합 실시간 대시보드 - Lumen, Trinity, Original Data 모니터링

.DESCRIPTION
    3가지 핵심 Production을 실시간으로 모니터링합니다:
    1. Lumen 24h Production (5분 사이클)
    2. Trinity Autopoietic Cycle (24시간 실행)
    3. Original Data Index (10,000 files)

.PARAMETER RefreshSeconds
    갱신 간격 (기본: 10초)

.EXAMPLE
    .\unified_realtime_dashboard.ps1
    
.EXAMPLE
    .\unified_realtime_dashboard.ps1 -RefreshSeconds 5
#>

[CmdletBinding()]
param(
    [int]$RefreshSeconds = 10,
    [switch]$Once
)

$ErrorActionPreference = 'SilentlyContinue'

function Get-LumenStatus {
    $logFile = "C:\workspace\agi\fdo_agi_repo\outputs\lumen_production_24h_stable.jsonl"
    
    if (-not (Test-Path $logFile)) {
        return @{
            Status     = "⚠️  NOT RUNNING"
            Cycles     = "N/A"
            Progress   = "N/A"
            LastUpdate = "N/A"
        }
    }
    
    $lines = @(Get-Content $logFile)
    $totalCycles = 288
    $currentCycle = $lines.Count
    $progress = [math]::Round(($currentCycle / $totalCycles) * 100, 1)
    
    $lastMod = (Get-Item $logFile).LastWriteTime
    $elapsed = ((Get-Date) - $lastMod).TotalSeconds
    
    if ($elapsed -lt 360) {
        # 6분 이내
        $status = "🟢 RUNNING"
    }
    elseif ($elapsed -lt 900) {
        # 15분 이내
        $status = "🟡 SLOW"
    }
    else {
        $status = "🔴 STALLED"
    }
    
    return @{
        Status         = $status
        Cycles         = "$currentCycle / $totalCycles"
        Progress       = "$progress%"
        LastUpdate     = $lastMod.ToString('HH:mm:ss')
        ElapsedSeconds = [int]$elapsed
    }
}

function Get-TrinityStatus {
    # Trinity는 새 터미널에서 실행 중이므로 출력 파일로 상태 확인
    $reportFile = "C:\workspace\agi\outputs\trinity\autopoietic_trinity_integration_latest.md"
    
    if (Test-Path $reportFile) {
        $lastMod = (Get-Item $reportFile).LastWriteTime
        return @{
            Status     = "✅ COMPLETED"
            LastUpdate = $lastMod.ToString('HH:mm:ss')
        }
    }
    else {
        return @{
            Status     = "🟢 RUNNING"
            LastUpdate = "In progress..."
        }
    }
}

function Get-OriginalDataStatus {
    $indexFile = "C:\workspace\agi\outputs\original_data_index.json"
    
    if (-not (Test-Path $indexFile)) {
        return @{
            Status     = "⚠️  NO INDEX"
            Files      = "N/A"
            LastUpdate = "N/A"
        }
    }
    
    $index = Get-Content $indexFile | ConvertFrom-Json
    $lastMod = (Get-Item $indexFile).LastWriteTime
    
    return @{
        Status     = "✅ INDEXED"
        Files      = $index.files.Count
        LastUpdate = $lastMod.ToString('HH:mm:ss')
    }
}

# 메인 루프
Clear-Host
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  AGI System - Unified Real-Time Dashboard                   ║" -ForegroundColor Cyan
Write-Host "║  Press Ctrl+C to stop                                        ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

$iteration = 0
while ($true) {
    $iteration++
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    # 화면 지우기 (첫 반복 제외)
    if ($iteration -gt 1) {
        Clear-Host
        Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
        Write-Host "║  AGI System - Unified Real-Time Dashboard                   ║" -ForegroundColor Cyan
        Write-Host "║  Press Ctrl+C to stop                                        ║" -ForegroundColor Cyan
        Write-Host "╚══════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan
    }
    
    Write-Host "📊 Update #$iteration - $timestamp (Refresh: ${RefreshSeconds}s)`n" -ForegroundColor Yellow
    
    # Lumen 상태
    $lumen = Get-LumenStatus
    Write-Host "🌟 Lumen Feedback System (24h Production)" -ForegroundColor Magenta
    Write-Host "   Status:      $($lumen.Status)" -ForegroundColor White
    Write-Host "   Cycles:      $($lumen.Cycles)" -ForegroundColor White
    Write-Host "   Progress:    $($lumen.Progress)" -ForegroundColor White
    Write-Host "   Last Update: $($lumen.LastUpdate)" -ForegroundColor Gray
    if ($lumen.ElapsedSeconds) {
        Write-Host "   Elapsed:     $($lumen.ElapsedSeconds)s" -ForegroundColor Gray
    }
    Write-Host ""
    
    # Trinity 상태
    $trinity = Get-TrinityStatus
    Write-Host "🔄 Trinity Autopoietic Cycle (24h)" -ForegroundColor Green
    Write-Host "   Status:      $($trinity.Status)" -ForegroundColor White
    Write-Host "   Last Update: $($trinity.LastUpdate)" -ForegroundColor Gray
    Write-Host ""
    
    # Original Data 상태
    $originalData = Get-OriginalDataStatus
    Write-Host "📚 Original Data Index" -ForegroundColor Blue
    Write-Host "   Status:      $($originalData.Status)" -ForegroundColor White
    Write-Host "   Total Files: $($originalData.Files)" -ForegroundColor White
    Write-Host "   Last Update: $($originalData.LastUpdate)" -ForegroundColor Gray
    Write-Host ""
    
    # 전체 시스템 상태
    $allGreen = ($lumen.Status -match "RUNNING|COMPLETED") -and 
    ($trinity.Status -match "RUNNING|COMPLETED") -and 
    ($originalData.Status -eq "✅ INDEXED")
    
    if ($allGreen) {
        Write-Host "✅ System Status: ALL SYSTEMS OPERATIONAL" -ForegroundColor Green
    }
    else {
        Write-Host "⚠️  System Status: ATTENTION REQUIRED" -ForegroundColor Yellow
    }
    
    # -Once 옵션: 1회만 실행
    if ($Once) {
        Write-Host "`n─────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
        Write-Host "Dashboard snapshot complete (Once mode)" -ForegroundColor Gray
        break
    }
    
    Write-Host "`n─────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
    Write-Host "Next refresh in ${RefreshSeconds} seconds..." -ForegroundColor DarkGray
    
    Start-Sleep -Seconds $RefreshSeconds
}
