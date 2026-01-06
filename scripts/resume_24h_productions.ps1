<#
.SYNOPSIS
    VS Code 재시작 시 24h Production 상태 확인 및 복구

.DESCRIPTION
    VS Code가 폴더를 열 때 자동 실행됩니다.
    1. 실행 중인 Production 확인
    2. 중단된 Production 자동 재개
    3. 로그 상태 복구

.PARAMETER Silent
    콘솔 출력 최소화

.EXAMPLE
    .\resume_24h_productions.ps1
    
.EXAMPLE
    .\resume_24h_productions.ps1 -Silent
#>

[CmdletBinding()]
param(
    [switch]$Silent
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = 'SilentlyContinue'


function Write-Info {
    param([string]$Message, [string]$Color = "White")
    if (-not $Silent) {
        Write-Host $Message -ForegroundColor $Color
    }
}

function Get-ProductionStatus {
    $status = @{
        Core     = $false
        Trinity   = $false
        Dashboard = $false
    }
    
    # Job 상태 확인
    $jobs = Get-Job | Where-Object { $_.Name -like 'AGI_*' }
    
    foreach ($job in $jobs) {
        if ($job.Name -eq 'AGI_Core_24h' -and $job.State -eq 'Running') {
            $status.Core = $true
        }
        if ($job.Name -eq 'AGI_Trinity_24h' -and $job.State -eq 'Running') {
            $status.Trinity = $true
        }
        if ($job.Name -eq 'AGI_Dashboard_24h' -and $job.State -eq 'Running') {
            $status.Dashboard = $true
        }
    }
    
    # 로그 파일로도 확인 (Job이 없을 때)
    if (-not $status.Core) {
        $CoreLog = "$WorkspaceRoot\fdo_agi_repo\outputs\core_production_24h_stable.jsonl"
        if (Test-Path $CoreLog) {
            $lastMod = (Get-Item $CoreLog).LastWriteTime
            $elapsed = ((Get-Date) - $lastMod).TotalMinutes
            if ($elapsed -lt 10) {
                # 10분 이내 업데이트
                $status.Core = $true
            }
        }
    }
    
    return $status
}

function Resume-Core {
    Write-Info "🌟 Core 24h Production 재시작..." "Yellow"
    
    # Job으로 시작
    $job = Start-Job -Name 'AGI_Core_24h' -ScriptBlock {
        param($Root)
        Set-Location $Root
        & "$Root\scripts\start_core_24h_stable.ps1"
    } -ArgumentList $WorkspaceRoot
    
    Write-Info "   ✅ Job ID: $($job.Id)" "Green"
}

function Resume-Trinity {
    Write-Info "🔄 Trinity Autopoietic Cycle 재시작..." "Yellow"
    
    # Job으로 시작
    $job = Start-Job -Name 'AGI_Trinity_24h' -ScriptBlock {
        param($Root)
        Set-Location $Root
        & "$Root\scripts\autopoietic_trinity_cycle.ps1" -Hours 24
    } -ArgumentList $WorkspaceRoot
    
    Write-Info "   ✅ Job ID: $($job.Id)" "Green"
}

function Resume-Dashboard {
    Write-Info "� Unified Dashboard 재시작..." "Yellow"
    
    # Job으로 시작
    $job = Start-Job -Name 'AGI_Dashboard_24h' -ScriptBlock {
        param($Root)
        Set-Location $Root
        
        # 대시보드는 무한 루프
        while ($true) {
            & "$Root\scripts\unified_realtime_dashboard.ps1" -RefreshSeconds 10 -Once
            Start-Sleep -Seconds 10
        }
    } -ArgumentList $WorkspaceRoot
    
    Write-Info "   ✅ Job ID: $($job.Id)" "Green"
}

# Main
Write-Info "`n╔══════════════════════════════════════════════════════════════╗" "Cyan"
Write-Info "║  VS Code 시작 - 24h Production 상태 확인                     ║" "Cyan"
Write-Info "╚══════════════════════════════════════════════════════════════╝`n" "Cyan"

$status = Get-ProductionStatus

Write-Info "현재 상태:" "White"
Write-Info "   Core:     $(if ($status.Core) { '🟢 Running' } else { '⚠️  Stopped' })" "White"
Write-Info "   Trinity:   $(if ($status.Trinity) { '🟢 Running' } else { '⚠️  Stopped' })" "White"
Write-Info "   Dashboard: $(if ($status.Dashboard) { '🟢 Running' } else { '⚠️  Stopped' })" "White"
Write-Info ""

# 복구 필요한 경우
$needRecovery = -not ($status.Core -and $status.Trinity -and $status.Dashboard)

if ($needRecovery) {
    Write-Info "🔧 복구 필요 - 자동 재시작 중...`n" "Yellow"
    
    if (-not $status.Core) {
        Resume-Core
    }
    
    if (-not $status.Trinity) {
        Resume-Trinity
    }
    
    if (-not $status.Dashboard) {
        Resume-Dashboard
    }
    
    Write-Info "`n✨ 모든 Production 복구 완료!" "Green"
}
else {
    Write-Info "✅ 모든 Production 정상 실행 중" "Green"
}

if (-not $Silent) {
    Write-Info "`n📊 실시간 상태는 Unified Dashboard에서 확인하세요." "Cyan"
    Write-Info ""
}