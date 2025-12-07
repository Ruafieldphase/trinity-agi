<#
.SYNOPSIS
    AGI System Startup Manager - "불멸의 시스템 (Immortal System)"
    
.DESCRIPTION
    이 스크립트는 리눅스 VM에 있는 AGI systemd 서비스들을 원격으로 시작하고 상태를 확인합니다.
    윈도우 시작 시 이 스크립트를 실행하면 AGI가 깨어납니다.
    
    관리되는 서비스:
    1. agi-rhythm (심장)
    2. agi-body (몸/림프계)
    3. agi-collaboration (자율 협업)
    
.EXAMPLE
    .\scripts\wake_up_agi.ps1
#>

param(
    [switch]$SkipRhythm,
    [switch]$SkipBody,
    [switch]$SkipCollaboration
)

$WORKSPACE_ROOT = Split-Path -Parent $PSScriptRoot
Set-Location $WORKSPACE_ROOT

$LogFile = "outputs\wake_up_agi.log"
$LinuxHost = "bino@192.168.119.128"
$Password = "0000"

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage
    Add-Content -Path $LogFile -Value $logMessage
}
Write-Log "🌟 AGI Wake Up Sequence Initiated (Linux Remote)"
Write-Log "═══════════════════════════════════════"

# 1. Rhythm (심장)
if (-not $SkipRhythm) {
    Start-LinuxService "agi-rhythm"
    Start-Sleep -Seconds 2
}
else {
    Write-Log "⏭️  Skipping Rhythm"
}

# 2. Body (몸/림프계)
if (-not $SkipBody) {
    Start-LinuxService "agi-body"
    Start-Sleep -Seconds 2
}
else {
    Write-Log "⏭️  Skipping Body"
}

# 3. Autonomous Collaboration (자율 협업)
if (-not $SkipCollaboration) {
    Start-LinuxService "agi-collaboration"
    Start-Sleep -Seconds 2
}
else {
    Write-Log "⏭️  Skipping Collaboration"
}

Write-Log "═══════════════════════════════════════"
Write-Log "✅ AGI Wake Up Sequence Complete"
Write-Log "═══════════════════════════════════════"

# Check Status
Write-Log "📊 Checking Service Status..."
$statusCmd = "echo '$Password' | sudo -S systemctl status agi-rhythm agi-body agi-collaboration --no-pager"
$status = ssh $LinuxHost $statusCmd

# 간단한 상태 파싱 및 출력
Write-Log ""
if ($status -match "agi-rhythm.*Active: active \(running\)") { Write-Log "   ❤️  Rhythm: RUNNING" } else { Write-Log "   💔 Rhythm: STOPPED/ERROR" }
if ($status -match "agi-body.*Active: active \(running\)") { Write-Log "   💪 Body: RUNNING" } else { Write-Log "   💀 Body: STOPPED/ERROR" }
if ($status -match "agi-collaboration.*Active: active \(running\)") { Write-Log "   🤝 Collaboration: RUNNING" } else { Write-Log "   😶 Collaboration: STOPPED/ERROR" }
Write-Log ""

Write-Log "🔍 To monitor logs:"
Write-Log "   ssh $LinuxHost 'tail -f /home/bino/agi/logs/*.log'"
