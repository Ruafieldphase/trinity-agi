#!/usr/bin/env pwsh
<#
.SYNOPSIS
    자율 목표 시스템 대시보드 생성 및 오픈

.DESCRIPTION
    goal_tracker.json과 autonomous_goals_latest.json을 분석하여
    HTML 대시보드를 생성하고 브라우저에서 오픈합니다.

.PARAMETER OpenBrowser
    생성 후 브라우저로 자동 오픈

.PARAMETER Watch
    30초마다 자동 재생성 (Ctrl+C로 중지)

.EXAMPLE
    .\generate_autonomous_goal_dashboard.ps1
    
.EXAMPLE
    .\generate_autonomous_goal_dashboard.ps1 -OpenBrowser
    
.EXAMPLE
    .\generate_autonomous_goal_dashboard.ps1 -Watch
#>

param(
    [switch]$OpenBrowser,
    [switch]$Watch,
    [int]$WatchInterval = 30
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Stop"
$WorkspaceRoot = Split-Path $PSScriptRoot -Parent
$PythonScript = Join-Path $PSScriptRoot "generate_autonomous_goal_dashboard.py"
$OutputHtml = Join-Path (Join-Path $WorkspaceRoot "outputs") "autonomous_goal_dashboard_latest.html"

# Python 경로 찾기
$PythonExe = Join-Path $WorkspaceRoot "fdo_agi_repo\.venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    $PythonExe = "python"
}

function Generate-Dashboard {
    Write-Host "🎯 대시보드 생성 중..." -ForegroundColor Cyan
    
    try {
        & $PythonExe $PythonScript
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ 대시보드 생성 실패 (exit code: $LASTEXITCODE)" -ForegroundColor Red
            return $false
        }
        
        Write-Host "✅ 대시보드 생성 완료!" -ForegroundColor Green
        Write-Host "   📄 $OutputHtml" -ForegroundColor Gray
        return $true
        
    }
    catch {
        Write-Host "❌ 오류: $_" -ForegroundColor Red
        return $false
    }
}

# 메인 실행
if ($Watch) {
    Write-Host "🔄 Watch 모드: ${WatchInterval}초마다 자동 재생성 (Ctrl+C로 중지)" -ForegroundColor Yellow
    Write-Host ""
    
    while ($true) {
        $success = Generate-Dashboard
        
        if ($success -and (Test-Path $OutputHtml)) {
            Write-Host "   ⏰ 다음 업데이트: $(Get-Date).AddSeconds($WatchInterval).ToString('HH:mm:ss')" -ForegroundColor Gray
        }
        
        Write-Host ""
        Start-Sleep -Seconds $WatchInterval
    }
}
else {
    # 한 번만 생성
    $success = Generate-Dashboard
    
    if ($success -and $OpenBrowser -and (Test-Path $OutputHtml)) {
        Write-Host ""
        Write-Host "🌐 브라우저에서 대시보드 오픈 중..." -ForegroundColor Cyan
        Start-Process $OutputHtml
    }
}

exit 0