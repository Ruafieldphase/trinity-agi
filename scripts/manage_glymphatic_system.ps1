# Glymphatic System Integration for Master Orchestrator
# 마스터 오케스트레이터에 Glymphatic 시스템 추가

param(
    [switch]$Enable,
    [switch]$Disable,
    [switch]$Status
)

$ErrorActionPreference = "Continue"
$WorkspaceRoot = "$PSScriptRoot\.."
$GlymphaticPid = "$WorkspaceRoot\outputs\glymphatic_system.pid"

function Start-GlymphaticSystem {
    Write-Host "🌊 Starting Adaptive Glymphatic System..." -ForegroundColor Cyan
    
    $pythonExe = "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe"
    if (-not (Test-Path $pythonExe)) {
        $pythonExe = "python"
    }
    
    $scriptPath = "$WorkspaceRoot\fdo_agi_repo\orchestrator\adaptive_glymphatic_system.py"
    
    # outputs 디렉토리 확인
    $outputsDir = Split-Path $GlymphaticPid -Parent
    if (-not (Test-Path $outputsDir)) {
        Write-Host "  📁 Creating outputs directory..." -ForegroundColor Yellow
        New-Item -ItemType Directory -Path $outputsDir -Force | Out-Null
    }
    
    Write-Host "  🐍 Python: $pythonExe" -ForegroundColor Gray
    Write-Host "  📜 Script: $scriptPath" -ForegroundColor Gray
    Write-Host "  📝 PID File: $GlymphaticPid" -ForegroundColor Gray
    
    # Background 실행 (간단한 방법)
    $jobName = "AdaptiveGlymphatic"
    
    # 기존 Job 제거
    $existingJob = Get-Job -Name $jobName -ErrorAction SilentlyContinue
    if ($existingJob) {
        Write-Host "  ⚠️  Removing existing job..." -ForegroundColor Yellow
        $existingJob | Remove-Job -Force
    }
    
    # 새 Job 시작 (모듈로 실행)
    $job = Start-Job -Name $jobName -ScriptBlock {
        param($py, $repoDir)
        Set-Location $repoDir
        & $py -m orchestrator.adaptive_glymphatic_system
    } -ArgumentList $pythonExe, "$WorkspaceRoot\fdo_agi_repo"
    
    Start-Sleep -Seconds 2
    
    # Job ID 저장
    Write-Host "  💾 Saving Job ID: $($job.Id) to $GlymphaticPid" -ForegroundColor Gray
    $job.Id | Out-File -FilePath $GlymphaticPid -Encoding ASCII -Force
    
    # 검증
    if (Test-Path $GlymphaticPid) {
        Write-Host "  ✅ PID file created successfully" -ForegroundColor Green
    }
    else {
        Write-Host "  ❌ PID file creation FAILED" -ForegroundColor Red
    }
    
    Write-Host "  ✓ Glymphatic System started (Job ID: $($job.Id))" -ForegroundColor Green
    return $job.Id
}

function Stop-GlymphaticSystem {
    if (Test-Path $GlymphaticPid) {
        $jobId = Get-Content $GlymphaticPid
        Get-Job -Id $jobId -ErrorAction SilentlyContinue | Stop-Job -PassThru | Remove-Job
        Remove-Item $GlymphaticPid -Force -ErrorAction SilentlyContinue
        Write-Host "  ✓ Glymphatic System stopped" -ForegroundColor Yellow
    }
}

function Test-GlymphaticRunning {
    if (-not (Test-Path $GlymphaticPid)) {
        return $false
    }
    
    $jobId = Get-Content $GlymphaticPid
    $job = Get-Job -Id $jobId -ErrorAction SilentlyContinue
    
    if ($null -eq $job -or $job.State -notin @('Running', 'NotStarted')) {
        Remove-Item $GlymphaticPid -Force -ErrorAction SilentlyContinue
        return $false
    }
    
    return $true
}

# Main
if ($Status) {
    if (Test-GlymphaticRunning) {
        Write-Host "✅ Glymphatic System is RUNNING" -ForegroundColor Green
        $jobId = Get-Content $GlymphaticPid
        $job = Get-Job -Id $jobId
        Write-Host "   Job ID: $($job.Id)"
        Write-Host "   State: $($job.State)"
        Write-Host "   Started: $($job.PSBeginTime)"
    }
    else {
        Write-Host "⚠️  Glymphatic System is NOT running" -ForegroundColor Yellow
    }
}
elseif ($Enable) {
    if (Test-GlymphaticRunning) {
        Write-Host "⚠️  Glymphatic System already running" -ForegroundColor Yellow
    }
    else {
        Start-GlymphaticSystem
    }
}
elseif ($Disable) {
    Stop-GlymphaticSystem
}
else {
    Write-Host "Usage:"
    Write-Host "  -Enable   Start Glymphatic System"
    Write-Host "  -Disable  Stop Glymphatic System"
    Write-Host "  -Status   Check status"
}
