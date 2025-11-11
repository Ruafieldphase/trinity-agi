<#
.SYNOPSIS
    Flow Observer 데몬 내부 루프

.DESCRIPTION
    백그라운드에서 지속적으로 Flow 상태를 모니터링합니다.
#>

param(
    [int]$IntervalSeconds = 300,
    [string]$PythonPath = "python"
)

$ErrorActionPreference = 'Continue'
$workspaceRoot = Split-Path -Parent $PSScriptRoot
$logPath = Join-Path $workspaceRoot "outputs\flow_observer_daemon.log"
$observerScript = Join-Path $workspaceRoot "fdo_agi_repo\copilot\flow_observer_integration.py"
$telemetryScript = Join-Path $PSScriptRoot "observe_desktop_telemetry.ps1"

# 로그 디렉토리 생성
$logDir = Split-Path $logPath -Parent
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

function Write-DaemonLog {
    param([string]$Message, [string]$Level = "INFO")
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logLine = "[$timestamp] [$Level] $Message"
    
    # 콘솔과 파일 모두 출력
    Write-Host $logLine
    Add-Content -Path $logPath -Value $logLine -Encoding UTF8
}

Write-DaemonLog "🚀 Flow Observer Daemon started" "INFO"
Write-DaemonLog "   Interval: $IntervalSeconds seconds" "INFO"
Write-DaemonLog "   Python: $PythonPath" "INFO"

# 텔레메트리 백그라운드 시작
Write-DaemonLog "📡 Starting telemetry collector..." "INFO"
$telemetryJob = Start-Job -ScriptBlock {
    param($Script, $Root)
    Set-Location $Root
    & $Script -IntervalSeconds 5 -Continuous
} -ArgumentList $telemetryScript, $workspaceRoot -Name "FlowTelemetry"

if ($telemetryJob) {
    Write-DaemonLog "✅ Telemetry collector started (Job ID: $($telemetryJob.Id))" "INFO"
}
else {
    Write-DaemonLog "❌ Failed to start telemetry collector" "ERROR"
}

# 메인 루프
$iteration = 0
$lastPerspective = $null

try {
    while ($true) {
        $iteration++
        Write-DaemonLog "🔄 Analysis iteration #$iteration" "INFO"
        
        # Flow Observer 실행
        try {
            $result = & $PythonPath $observerScript 2>&1
            
            # 출력 파싱 (간단한 패턴 매칭)
            $stateMatch = $result | Select-String -Pattern "State: (\w+)"
            $confidenceMatch = $result | Select-String -Pattern "Confidence: ([\d.]+)"
            $perspectiveMatch = $result | Select-String -Pattern "Perspective: (\w+)"
            $fearMatch = $result | Select-String -Pattern "Fear Level: ([\d.]+)"
            
            if ($stateMatch) {
                $state = $stateMatch.Matches[0].Groups[1].Value
                $confidence = if ($confidenceMatch) { $confidenceMatch.Matches[0].Groups[1].Value } else { "?" }
                
                Write-DaemonLog "📊 Flow State: $state (confidence: $confidence)" "INFO"
                
                # Perspective 변경 감지
                if ($perspectiveMatch) {
                    $perspective = $perspectiveMatch.Matches[0].Groups[1].Value
                    
                    if ($lastPerspective -and $lastPerspective -ne $perspective) {
                        Write-DaemonLog "🔄 Perspective switched: $lastPerspective → $perspective" "ALERT"
                        
                        # Toast 알림 (Windows 10/11)
                        $notifTitle = "Perspective Switch"
                        $notifMessage = "Switched to $perspective mode"
                        
                        # PowerShell 7+ Toast (간단 버전)
                        if ($PSVersionTable.PSVersion.Major -ge 7) {
                            Write-Host "🔔 ${notifTitle}: $notifMessage" -ForegroundColor Yellow
                        }
                    }
                    
                    $lastPerspective = $perspective
                }
                
                # 정체 상태 감지
                if ($state -eq 'stagnation') {
                    if ($fearMatch) {
                        $fearLevel = $fearMatch.Matches[0].Groups[1].Value
                        Write-DaemonLog "⚠️ STAGNATION detected (fear level: $fearLevel)" "ALERT"
                        
                        if ([double]$fearLevel -gt 0.5) {
                            Write-DaemonLog "🚨 High fear level - perspective switch recommended!" "ALERT"
                        }
                    }
                    else {
                        Write-DaemonLog "⚠️ STAGNATION detected" "ALERT"
                    }
                }
                
                # ADHD 패턴 감지
                if ($state -like '*adhd*') {
                    Write-DaemonLog "✨ ADHD flow pattern detected" "INFO"
                }
                
            }
            else {
                Write-DaemonLog "⚠️ Could not parse flow state" "WARN"
            }
            
        }
        catch {
            Write-DaemonLog "❌ Error running flow observer: $_" "ERROR"
        }
        
        # 대기
        Write-DaemonLog "⏳ Waiting $IntervalSeconds seconds..." "INFO"
        Start-Sleep -Seconds $IntervalSeconds
    }
    
}
catch {
    Write-DaemonLog "❌ Fatal error in daemon loop: $_" "ERROR"
    
}
finally {
    # 정리
    Write-DaemonLog "🛑 Daemon stopping..." "INFO"
    
    if ($telemetryJob) {
        Write-DaemonLog "   Stopping telemetry collector..." "INFO"
        Stop-Job -Id $telemetryJob.Id -ErrorAction SilentlyContinue
        Remove-Job -Id $telemetryJob.Id -ErrorAction SilentlyContinue
    }
    
    Write-DaemonLog "✅ Daemon stopped" "INFO"
}
