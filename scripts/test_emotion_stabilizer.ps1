#Requires -Version 5.1
<#
.SYNOPSIS
    Emotion Stabilizer 시나리오 테스트

.DESCRIPTION
    다양한 Fear 레벨을 시뮬레이션하여 Stabilizer 동작 테스트

.PARAMETER Scenario
    테스트 시나리오:
    - stable: Fear=0.3 (정상)
    - elevated: Fear=0.5 (Micro-Reset)
    - high: Fear=0.7 (Active Cooldown)
    - critical: Fear=0.9 (Deep Maintenance)

.PARAMETER DryRun
    Dry-run 모드

.EXAMPLE
    .\test_emotion_stabilizer.ps1 -Scenario elevated
    # Fear=0.5 시나리오 테스트
#>

param(
    [ValidateSet("stable", "elevated", "high", "critical")]
    [string]$Scenario = "stable",
    [switch]$DryRun
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
$CoreStatePath = Join-Path $WorkspaceRoot "fdo_agi_repo\memory\core_state.json"
$BackupPath = "$CoreStatePath.backup"

# Scenario configurations
$scenarios = @{
    stable   = @{
        fear        = 0.3
        joy         = 0.8
        trust       = 0.8
        description = "정상 상태 (안정화 불필요)"
    }
    elevated = @{
        fear        = 0.5
        joy         = 0.6
        trust       = 0.7
        description = "상승 상태 (Micro-Reset 권장)"
    }
    high     = @{
        fear        = 0.7
        joy         = 0.4
        trust       = 0.6
        description = "높은 Fear (Active Cooldown 권장)"
    }
    critical = @{
        fear        = 0.9
        joy         = 0.2
        trust       = 0.4
        description = "위험 상태 (Deep Maintenance 필요)"
    }
}

$config = $scenarios[$Scenario]

Write-Host "🧪 Testing Emotion Stabilizer: $Scenario scenario" -ForegroundColor Cyan
Write-Host "   Fear: $($config.fear)" -ForegroundColor Gray
Write-Host "   Joy: $($config.joy)" -ForegroundColor Gray
Write-Host "   Trust: $($config.trust)" -ForegroundColor Gray
Write-Host "   Description: $($config.description)" -ForegroundColor Gray
Write-Host ""

# Backup current state
if (Test-Path $CoreStatePath) {
    Write-Host "📦 Backing up current Core state..." -ForegroundColor Yellow
    Copy-Item $CoreStatePath $BackupPath -Force
}

# Create test state
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$testState = @{
    emotion       = @{
        fear  = $config.fear
        joy   = $config.joy
        trust = $config.trust
    }
    timestamp     = $timestamp
    test_scenario = $Scenario
} | ConvertTo-Json -Depth 10

Write-Host "✏️  Writing test Core state..." -ForegroundColor Yellow
$testState | Out-File -FilePath $CoreStatePath -Encoding utf8 -Force

# Run stabilizer
Write-Host ""
Write-Host "🚀 Running Emotion-Triggered Stabilizer..." -ForegroundColor Cyan
Write-Host ""

$stabilizerScript = Join-Path $WorkspaceRoot "scripts\start_emotion_stabilizer.ps1"
& $stabilizerScript -Once -DryRun

# Restore backup
Write-Host ""
if (Test-Path $BackupPath) {
    Write-Host "🔄 Restoring original Core state..." -ForegroundColor Yellow
    Move-Item $BackupPath $CoreStatePath -Force
}
else {
    Write-Host "⚠️  No backup found to restore" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✅ Test completed" -ForegroundColor Green