#Requires -Version 5.1
<#
.SYNOPSIS
    깃코 슬랙 봇을 백그라운드로 실행합니다.

.DESCRIPTION
    Python 봇 서버와 localtunnel을 함께 시작하고, 
    로그를 파일로 저장하며, 자동 재시작 기능을 제공합니다.

.PARAMETER KillExisting
    기존 실행 중인 봇을 종료하고 새로 시작합니다.

.PARAMETER StopOnly
    봇을 종료만 하고 새로 시작하지 않습니다.

.PARAMETER LogDir
    로그 파일을 저장할 디렉토리 경로 (기본값: outputs/logs)

.EXAMPLE
    .\start_gitco_bot.ps1
    # 봇을 백그라운드로 시작

.EXAMPLE
    .\start_gitco_bot.ps1 -KillExisting
    # 기존 봇을 종료하고 재시작

.EXAMPLE
    .\start_gitco_bot.ps1 -StopOnly
    # 봇만 종료
#>

[CmdletBinding()]
param(
    [switch]$KillExisting,
    [switch]$StopOnly,
    [string]$LogDir = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# =============================================================================
# Configuration
# =============================================================================

$WORKSPACE_ROOT = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$PYTHON_VENV = Join-Path $WORKSPACE_ROOT "LLM_Unified\.venv\Scripts\python.exe"
$BOT_SCRIPT = Join-Path $WORKSPACE_ROOT "LLM_Unified\ion-mentoring\slack_bot_v2.py"
$OUTPUTS_DIR = Join-Path $WORKSPACE_ROOT "LLM_Unified\ion-mentoring\outputs"

if ([string]::IsNullOrEmpty($LogDir)) {
    $LogDir = Join-Path $OUTPUTS_DIR "logs"
}

# 로그 디렉토리 생성
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

$TIMESTAMP = Get-Date -Format "yyyyMMdd_HHmmss"
$BOT_LOG = Join-Path $LogDir "gitco_bot_$TIMESTAMP.log"
$TUNNEL_LOG = Join-Path $LogDir "localtunnel_$TIMESTAMP.log"
$STATE_FILE = Join-Path $OUTPUTS_DIR "gitco_bot_state.json"

# =============================================================================
# Functions
# =============================================================================

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    Write-Host $logMessage
    Add-Content -Path $BOT_LOG -Value $logMessage -ErrorAction SilentlyContinue
}

function Get-GitcoBotProcesses {
    $botProcesses = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
        $_.Path -like "*LLM_Unified*" -and 
        $_.CommandLine -like "*slack_bot*"
    }
    
    $tunnelProcesses = Get-Process node -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*localtunnel*"
    }
    
    return @{
        Bot    = $botProcesses
        Tunnel = $tunnelProcesses
    }
}

function Stop-GitcoBotProcesses {
    Write-Log "🛑 기존 깃코 봇 프로세스 종료 중..."
    
    $processes = Get-GitcoBotProcesses
    
    $stopped = 0
    
    if ($processes.Bot) {
        foreach ($proc in $processes.Bot) {
            try {
                Write-Log "  종료: Python Bot (PID: $($proc.Id))"
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
                $stopped++
            }
            catch {
                Write-Log "  경고: PID $($proc.Id) 종료 실패" "WARN"
            }
        }
    }
    
    if ($processes.Tunnel) {
        foreach ($proc in $processes.Tunnel) {
            try {
                Write-Log "  종료: Localtunnel (PID: $($proc.Id))"
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
                $stopped++
            }
            catch {
                Write-Log "  경고: PID $($proc.Id) 종료 실패" "WARN"
            }
        }
    }
    
    if ($stopped -eq 0) {
        Write-Log "실행 중인 봇이 없습니다."
    }
    else {
        Write-Log "[OK] $stopped 개 프로세스 종료 완료"
        Start-Sleep -Seconds 2
    }
}

function Start-GitcoBot {
    Write-Log "[BOT] 깃코 봇 서버 시작 중..."
    
    # SLACK_BOT_TOKEN 확인
    $slackToken = [Environment]::GetEnvironmentVariable("SLACK_BOT_TOKEN", "User")
    if ([string]::IsNullOrEmpty($slackToken)) {
        Write-Log "[WARN]  SLACK_BOT_TOKEN 환경 변수가 설정되지 않았습니다!" "ERROR"
        Write-Log "설정 방법: [Environment]::SetEnvironmentVariable('SLACK_BOT_TOKEN', 'xoxb-...', 'User')" "ERROR"
        return $null
    }
    
    # Python 봇 시작
    $botStartInfo = New-Object System.Diagnostics.ProcessStartInfo
    $botStartInfo.FileName = $PYTHON_VENV
    $botStartInfo.Arguments = "`"$BOT_SCRIPT`""
    $botStartInfo.UseShellExecute = $false
    $botStartInfo.RedirectStandardOutput = $true
    $botStartInfo.RedirectStandardError = $true
    $botStartInfo.CreateNoWindow = $true
    $botStartInfo.EnvironmentVariables["SLACK_BOT_TOKEN"] = $slackToken
    
    $botProcess = [System.Diagnostics.Process]::Start($botStartInfo)
    
    if ($botProcess) {
        Write-Log "[OK] 봇 서버 시작됨 (PID: $($botProcess.Id))"
        
        # 로그 리다이렉션
        $null = Register-ObjectEvent -InputObject $botProcess -EventName OutputDataReceived -Action {
            if ($EventArgs.Data) {
                Add-Content -Path $using:BOT_LOG -Value $EventArgs.Data
            }
        }
        
        $null = Register-ObjectEvent -InputObject $botProcess -EventName ErrorDataReceived -Action {
            if ($EventArgs.Data) {
                Add-Content -Path $using:BOT_LOG -Value "[ERROR] $($EventArgs.Data)"
            }
        }
        
        $botProcess.BeginOutputReadLine()
        $botProcess.BeginErrorReadLine()
        
        # 서버 시작 대기
        Write-Log "[WAIT] 서버 시작 대기 중 (5초)..."
        Start-Sleep -Seconds 5
        
        # 헬스 체크
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8080/health" -TimeoutSec 5 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-Log "[OK] 봇 서버 헬스 체크 성공"
            }
        }
        catch {
            Write-Log "[WARN]  봇 서버 헬스 체크 실패 - 로그를 확인하세요" "WARN"
        }
        
        return $botProcess.Id
    }
    else {
        Write-Log "[ERROR] 봇 서버 시작 실패" "ERROR"
        return $null
    }
}

function Start-LocalTunnel {
    Write-Log "[WEB] Localtunnel 시작 중..."
    
    $tunnelStartInfo = New-Object System.Diagnostics.ProcessStartInfo
    $tunnelStartInfo.FileName = "npx"
    $tunnelStartInfo.Arguments = "localtunnel --port 8080"
    $tunnelStartInfo.UseShellExecute = $false
    $tunnelStartInfo.RedirectStandardOutput = $true
    $tunnelStartInfo.RedirectStandardError = $true
    $tunnelStartInfo.CreateNoWindow = $true
    
    $tunnelProcess = [System.Diagnostics.Process]::Start($tunnelStartInfo)
    
    if ($tunnelProcess) {
        Write-Log "[OK] Localtunnel 시작됨 (PID: $($tunnelProcess.Id))"
        
        # 로그 리다이렉션 및 URL 추출
        $tunnelUrl = $null
        $null = Register-ObjectEvent -InputObject $tunnelProcess -EventName OutputDataReceived -Action {
            if ($EventArgs.Data) {
                $data = $EventArgs.Data
                Add-Content -Path $using:TUNNEL_LOG -Value $data
                
                # URL 추출
                if ($data -match "your url is: (https://[^\s]+)") {
                    $script:tunnelUrl = $Matches[1]
                    Write-Host "[WEB] Public URL: $($Matches[1])" -ForegroundColor Green
                }
            }
        }
        
        $null = Register-ObjectEvent -InputObject $tunnelProcess -EventName ErrorDataReceived -Action {
            if ($EventArgs.Data) {
                Add-Content -Path $using:TUNNEL_LOG -Value "[ERROR] $($EventArgs.Data)"
            }
        }
        
        $tunnelProcess.BeginOutputReadLine()
        $tunnelProcess.BeginErrorReadLine()
        
        # URL 생성 대기
        Write-Log "[WAIT] Public URL 생성 대기 중 (10초)..."
        Start-Sleep -Seconds 10
        
        # URL 추출 시도
        if (Test-Path $TUNNEL_LOG) {
            $logContent = Get-Content $TUNNEL_LOG -Raw
            if ($logContent -match "your url is: (https://[^\s]+)") {
                $tunnelUrl = $Matches[1]
                Write-Log "[WEB] Public URL: $tunnelUrl"
            }
        }
        
        return @{
            Pid = $tunnelProcess.Id
            Url = $tunnelUrl
        }
    }
    else {
        Write-Log "[ERROR] Localtunnel 시작 실패" "ERROR"
        return $null
    }
}

function Save-BotState {
    param(
        [int]$BotPid,
        [int]$TunnelPid,
        [string]$TunnelUrl
    )
    
    $state = @{
        bot_pid    = $BotPid
        tunnel_pid = $TunnelPid
        tunnel_url = $TunnelUrl
        started_at = (Get-Date).ToString("o")
        log_dir    = $LogDir
        bot_log    = $BOT_LOG
        tunnel_log = $TUNNEL_LOG
    }
    
    $state | ConvertTo-Json | Set-Content $STATE_FILE -Encoding UTF8
    Write-Log "💾 상태 파일 저장: $STATE_FILE"
}

# =============================================================================
# Main
# =============================================================================

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║         깃코 슬랙 봇 - 백그라운드 런처                    ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# 기존 프로세스 종료
if ($KillExisting -or $StopOnly) {
    Stop-GitcoBotProcesses
}

if ($StopOnly) {
    Write-Log "🛑 종료 완료"
    exit 0
}

# 봇 시작
Write-Log "[DEPLOY] 깃코 봇 시작 중..."
Write-Log "📂 로그 디렉토리: $LogDir"

$botPid = Start-GitcoBot
if (-not $botPid) {
    Write-Log "[ERROR] 봇 시작 실패" "ERROR"
    exit 1
}

# Localtunnel 시작
$tunnelInfo = Start-LocalTunnel
if (-not $tunnelInfo) {
    Write-Log "[ERROR] Localtunnel 시작 실패" "ERROR"
    Write-Log "봇 서버만 실행 중입니다. 수동으로 터널을 설정하세요." "WARN"
}

# 상태 저장
Save-BotState -BotPid $botPid -TunnelPid $tunnelInfo.Pid -TunnelUrl $tunnelInfo.Url

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                    [OK] 시작 완료!                          ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "[METRICS] 상태 정보:" -ForegroundColor Yellow
Write-Host "  • 봇 PID: $botPid" -ForegroundColor White
Write-Host "  • Tunnel PID: $($tunnelInfo.Pid)" -ForegroundColor White
if ($tunnelInfo.Url) {
    Write-Host "  • Public URL: $($tunnelInfo.Url)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "[LOG] Slack Event Subscriptions URL에 설정하세요:" -ForegroundColor Yellow
    Write-Host "   $($tunnelInfo.Url)/slack/events" -ForegroundColor Green
}
Write-Host ""
Write-Host "📄 로그 파일:" -ForegroundColor Yellow
Write-Host "  • 봇: $BOT_LOG" -ForegroundColor White
Write-Host "  • 터널: $TUNNEL_LOG" -ForegroundColor White
Write-Host ""
Write-Host "[CONFIG] 관리 명령어:" -ForegroundColor Yellow
Write-Host "  • 재시작: .\start_gitco_bot.ps1 -KillExisting" -ForegroundColor White
Write-Host "  • 종료: .\start_gitco_bot.ps1 -StopOnly" -ForegroundColor White
Write-Host "  • 상태 확인: Get-Content '$STATE_FILE' | ConvertFrom-Json" -ForegroundColor White
Write-Host ""

Write-Log "[SUCCESS] 깃코 봇이 백그라운드에서 실행 중입니다!"
