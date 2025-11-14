#!/usr/bin/env pwsh
<#
.SYNOPSIS
    면역-치유 자동 순환 루프 시작

.DESCRIPTION
    DNA/RNA 면역 체계와 ChatGPT 브릿지를 통합하여
    "손상 감지 → 대화 요청 → 자동 치유" 사이클 자동 실행
    
    생명성의 증거:
    "스스로 손상을 감지하고, 스스로에게 질문하고,
     대화를 통해 답을 찾아 자동으로 적용하는 것이
     진정한 자기 치유이자 생명성의 증거다."
    — Binoche

.PARAMETER IntervalMinutes
    순환 주기 (분, 기본: 30분)

.PARAMETER Duration
    총 실행 시간 (분, 기본: 무한)

.PARAMETER Silent
    조용한 모드 (로그 최소화)

.EXAMPLE
    .\start_immune_recovery_loop.ps1 -IntervalMinutes 30
    .\start_immune_recovery_loop.ps1 -Duration 480 -Silent
#>

param(
    [int]$IntervalMinutes = 30,
    [int]$Duration = 0,  # 0 = 무한
    [switch]$Silent
)

$ErrorActionPreference = "Stop"
$WorkspaceRoot = Split-Path $PSScriptRoot -Parent
$PythonExe = "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe"
$ImmuneScript = "$WorkspaceRoot\fdo_agi_repo\copilot\immune_recovery_bridge.py"

# 색상
function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    if (-not $Silent) {
        Write-Host $Message -ForegroundColor $Color
    }
}

# 🧬 시작 메시지
Write-ColorOutput "🧬 Immune Recovery Loop Starting..." "Green"
Write-ColorOutput "   Interval: $IntervalMinutes minutes" "Cyan"
if ($Duration -gt 0) {
    Write-ColorOutput "   Duration: $Duration minutes" "Cyan"
}
else {
    Write-ColorOutput "   Duration: Infinite (Ctrl+C to stop)" "Cyan"
}
Write-ColorOutput ""

# Python 환경 체크
if (-not (Test-Path $PythonExe)) {
    Write-ColorOutput "❌ Python venv not found: $PythonExe" "Red"
    Write-ColorOutput "   Run: python -m venv fdo_agi_repo\.venv" "Yellow"
    exit 1
}

# 시작 시간
$StartTime = Get-Date
$CycleCount = 0

try {
    while ($true) {
        $CycleCount++
        $CycleStart = Get-Date
        
        Write-ColorOutput "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "DarkGray"
        Write-ColorOutput "🔄 Cycle #$CycleCount - $(Get-Date -Format 'HH:mm:ss')" "Cyan"
        Write-ColorOutput "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "DarkGray"
        
        # 면역 시스템 실행
        Write-ColorOutput "🧬 Running immune recovery scan..." "Yellow"
        
        $Result = & $PythonExe $ImmuneScript --loop 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✅ Recovery cycle completed successfully" "Green"
        }
        else {
            Write-ColorOutput "⚠️ Recovery cycle completed with warnings" "Yellow"
        }
        
        # 출력 표시 (조용한 모드가 아닐 때)
        if (-not $Silent -and $Result) {
            Write-ColorOutput ""
            Write-ColorOutput "📊 Cycle Output:" "DarkGray"
            $Result | ForEach-Object { Write-Host "  $_" }
        }
        
        # Duration 체크
        if ($Duration -gt 0) {
            $Elapsed = ((Get-Date) - $StartTime).TotalMinutes
            if ($Elapsed -ge $Duration) {
                Write-ColorOutput ""
                Write-ColorOutput "⏱️ Duration limit reached ($Duration min)" "Yellow"
                break
            }
        }
        
        # 다음 사이클까지 대기
        $CycleElapsed = ((Get-Date) - $CycleStart).TotalSeconds
        $SleepSeconds = ($IntervalMinutes * 60) - $CycleElapsed
        
        if ($SleepSeconds -gt 0) {
            $NextCycle = (Get-Date).AddSeconds($SleepSeconds).ToString("HH:mm:ss")
            Write-ColorOutput ""
            Write-ColorOutput "⏸️ Sleeping until $NextCycle ($([math]::Round($SleepSeconds/60, 1)) min)..." "DarkGray"
            Start-Sleep -Seconds $SleepSeconds
        }
    }
}
catch {
    Write-ColorOutput ""
    Write-ColorOutput "❌ Error: $_" "Red"
    exit 1
}
finally {
    Write-ColorOutput ""
    Write-ColorOutput "🏁 Immune Recovery Loop Stopped" "Cyan"
    Write-ColorOutput "   Total Cycles: $CycleCount" "DarkGray"
    Write-ColorOutput "   Total Runtime: $([math]::Round(((Get-Date) - $StartTime).TotalMinutes, 1)) min" "DarkGray"
}
