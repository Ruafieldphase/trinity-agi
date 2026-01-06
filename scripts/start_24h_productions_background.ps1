<#
.SYNOPSIS
    24h Production을 백그라운드 PowerShell Job으로 시작 (재시작 안전)

.DESCRIPTION
    다음 Production을 백그라운드 Job으로 시작합니다:
    1. Core 24h Feedback System
    2. Trinity Autopoietic Cycle
    3. Unified Real-Time Dashboard
    
    VS Code 재시작 시 자동으로 복구됩니다.

.PARAMETER Force
    기존 Job 종료 후 재시작

.EXAMPLE
    .\start_24h_productions_background.ps1
    
.EXAMPLE
    .\start_24h_productions_background.ps1 -Force
#>

[CmdletBinding()]
param(
    [switch]$Force
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = 'Stop'

$JobNames = @(
    "AGI_Core_24h"
    "AGI_Trinity_24h"
    "AGI_Dashboard_24h"
)

function Stop-ExistingJobs {
    Write-Host "`n🛑 기존 Job 정리 중...`n" -ForegroundColor Yellow
    
    foreach ($jobName in $JobNames) {
        $job = Get-Job -Name $jobName -ErrorAction SilentlyContinue
        if ($job) {
            Stop-Job -Name $jobName -ErrorAction SilentlyContinue
            Remove-Job -Name $jobName -Force -ErrorAction SilentlyContinue
            Write-Host "   ✅ $jobName 종료" -ForegroundColor Green
        }
    }
}

function Start-CoreJob {
    Write-Host "1️⃣  Core 24h Production 시작..." -ForegroundColor Yellow
    
    $job = Start-Job -Name $JobNames[0] -ScriptBlock {
        param($Root)
        Set-Location "$Root\fdo_agi_repo"
        $pythonExe = "$Root\fdo_agi_repo\.venv\Scripts\python.exe"
        & $pythonExe 'scripts\start_24h_monitoring.py' --interval 5
    } -ArgumentList $WorkspaceRoot
    
    Write-Host "   ✅ Job ID: $($job.Id)" -ForegroundColor Green
    Write-Host "   📊 로그: fdo_agi_repo\outputs\fullstack_24h_monitoring.jsonl" -ForegroundColor Gray
}

function Start-TrinityJob {
    Write-Host "`n2️⃣  Trinity Autopoietic Cycle 시작..." -ForegroundColor Yellow
    
    $job = Start-Job -Name $JobNames[1] -ScriptBlock {
        param($Root)
        Set-Location $Root
        & "$Root\scripts\autopoietic_trinity_cycle.ps1" -Hours 24
    } -ArgumentList $WorkspaceRoot
    
    Write-Host "   ✅ Job ID: $($job.Id)" -ForegroundColor Green
    Write-Host "   📊 로그: outputs\trinity_cycle_24h_*.md" -ForegroundColor Gray
}

function Start-DashboardJob {
    Write-Host "`n3️⃣  Unified Dashboard 시작..." -ForegroundColor Yellow
    
    $job = Start-Job -Name $JobNames[2] -ScriptBlock {
        param($Root)
        Set-Location $Root
        
        # 대시보드는 무한 루프
        while ($true) {
            & "$Root\scripts\unified_realtime_dashboard.ps1" -RefreshSeconds 10 -Once
            Start-Sleep -Seconds 10
        }
    } -ArgumentList $WorkspaceRoot
    
    Write-Host "   ✅ Job ID: $($job.Id)" -ForegroundColor Green
    Write-Host "   📊 로그: outputs\unified_dashboard_latest.txt" -ForegroundColor Gray
}

function Show-JobStatus {
    Write-Host "`n╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║  24h Production - 백그라운드 Job 상태                        ║" -ForegroundColor Cyan
    Write-Host "╚══════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan
    
    foreach ($jobName in $JobNames) {
        $job = Get-Job -Name $jobName -ErrorAction SilentlyContinue
        
        if ($job) {
            $icon = switch ($job.State) {
                "Running" { "🟢" }
                "Completed" { "✅" }
                "Failed" { "❌" }
                default { "⚠️" }
            }
            
            Write-Host "$icon $jobName" -ForegroundColor White
            Write-Host "   상태: $($job.State)" -ForegroundColor Gray
            Write-Host "   Job ID: $($job.Id)" -ForegroundColor Gray
        } else {
            Write-Host "⚠️  $jobName - 실행 안 됨" -ForegroundColor Yellow
        }
        Write-Host ""
    }
    
    Write-Host "💡 Job 확인 명령어:" -ForegroundColor Cyan
    Write-Host "   Get-Job | Where-Object { `$_.Name -like 'AGI_*' }" -ForegroundColor Gray
    Write-Host ""
}

# Main
Write-Host "`n╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  24h Production - 백그라운드 Job 시작                        ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

if ($Force) {
    Stop-ExistingJobs
}

# 기존 Job 확인
$existingJobs = Get-Job | Where-Object { $_.Name -like 'AGI_*' }
if ($existingJobs -and -not $Force) {
    Write-Host "⚠️  이미 실행 중인 Job이 있습니다:" -ForegroundColor Yellow
    $existingJobs | Format-Table Name, State, Id -AutoSize
    Write-Host "`n기존 Job을 종료하고 재시작하려면 -Force 옵션을 사용하세요.`n" -ForegroundColor Cyan
    exit 0
}

# Job 시작
Start-CoreJob
Start-Sleep -Seconds 2

Start-TrinityJob
Start-Sleep -Seconds 2

Start-DashboardJob

Write-Host "`n✨ 모든 Production Job 시작 완료!" -ForegroundColor Green
Write-Host ""

Show-JobStatus

Write-Host "📌 중요 사항:" -ForegroundColor Yellow
Write-Host "   - PowerShell 창을 닫으면 Job도 종료됩니다" -ForegroundColor White
Write-Host "   - VS Code 터미널은 열어두는 것이 안전합니다" -ForegroundColor White
Write-Host "   - VS Code 재시작 시 자동으로 복구됩니다 (runOn: folderOpen)" -ForegroundColor White
Write-Host ""