# Auto-Restart Local LLM Monitoring Script
# Monitors Local LLM health and provides restart recommendations

param(
    [int]$CheckIntervalSeconds = 300,  # 5분마다 체크
    [int]$MaxRetries = 3,
    [switch]$AutoRestart,  # 자동 재시작 (주의!)
    [switch]$Continuous,   # 지속적 모니터링
    [string]$LogFile = "$PSScriptRoot\..\outputs\llm_health_monitor.log"
)

$ErrorActionPreference = "Continue"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    Write-Host $logMessage -ForegroundColor $(switch ($Level) {
        "ERROR" { "Red" }
        "WARN" { "Yellow" }
        "SUCCESS" { "Green" }
        default { "White" }
    })
    Add-Content -Path $LogFile -Value $logMessage -ErrorAction SilentlyContinue
}

function Test-LocalLLM {
    $testPayload = @{
        model       = "local-model"
        prompt      = "ping"
        max_tokens  = 5
        temperature = 0.7
    } | ConvertTo-Json

    try {
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $response = Invoke-WebRequest -Uri "http://localhost:8080/v1/completions" `
            -Method POST -Body $testPayload -ContentType "application/json" `
            -TimeoutSec 10 -ErrorAction Stop
        $sw.Stop()

        return @{
            Status = "ONLINE"
            Latency = $sw.ElapsedMilliseconds
            StatusCode = $response.StatusCode
        }
    }
    catch {
        return @{
            Status = "OFFLINE"
            Error = $_.Exception.Message
            StatusCode = 0
        }
    }
}

function Get-LMStudioProcess {
    return Get-Process -Name "LM Studio" -ErrorAction SilentlyContinue
}

function Restart-LocalLLM {
    Write-Log "Attempting to restart Local LLM..." "WARN"

    # LM Studio 프로세스 확인
    $process = Get-LMStudioProcess

    if ($process) {
        Write-Log "Stopping LM Studio (PID: $($process.Id))..." "WARN"
        try {
            $process | Stop-Process -Force -ErrorAction Stop
            Start-Sleep -Seconds 5
            Write-Log "LM Studio stopped successfully" "SUCCESS"
        }
        catch {
            Write-Log "Failed to stop LM Studio: $_" "ERROR"
            return $false
        }
    }

    # LM Studio 실행 경로 찾기 (일반적인 경로들)
    $lmStudioPaths = @(
        "$env:LOCALAPPDATA\Programs\LM Studio\LM Studio.exe",
        "$env:ProgramFiles\LM Studio\LM Studio.exe",
        "C:\Program Files\LM Studio\LM Studio.exe"
    )

    $lmStudioPath = $lmStudioPaths | Where-Object { Test-Path $_ } | Select-Object -First 1

    if (-not $lmStudioPath) {
        Write-Log "LM Studio executable not found in common locations" "ERROR"
        Write-Log "Please start LM Studio manually" "WARN"
        return $false
    }

    Write-Log "Starting LM Studio from: $lmStudioPath" "INFO"
    try {
        Start-Process -FilePath $lmStudioPath -ErrorAction Stop
        Write-Log "LM Studio started. Waiting 30 seconds for initialization..." "INFO"
        Start-Sleep -Seconds 30

        # 재시작 후 health check
        $healthCheck = Test-LocalLLM
        if ($healthCheck.Status -eq "ONLINE") {
            Write-Log "LM Studio restarted successfully (latency: $($healthCheck.Latency)ms)" "SUCCESS"
            return $true
        }
        else {
            Write-Log "LM Studio started but API not responding. Manual intervention required." "WARN"
            return $false
        }
    }
    catch {
        Write-Log "Failed to start LM Studio: $_" "ERROR"
        return $false
    }
}

function Start-Monitoring {
    Write-Host "`n" -NoNewline
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host "  Local LLM Health Monitor" -ForegroundColor Yellow
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host ""
    Write-Log "Monitoring started (interval: ${CheckIntervalSeconds}s, auto-restart: $AutoRestart)" "INFO"
    Write-Host ""

    $consecutiveFailures = 0
    $iteration = 0

    do {
        $iteration++
        Write-Host "[Check $iteration] $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Cyan -NoNewline

        $health = Test-LocalLLM

        if ($health.Status -eq "ONLINE") {
            $consecutiveFailures = 0
            $color = if ($health.Latency -gt 2000) { "Yellow" } else { "Green" }
            Write-Host " - ONLINE ($($health.Latency)ms)" -ForegroundColor $color

            if ($health.Latency -gt 2000) {
                Write-Log "High latency detected: $($health.Latency)ms" "WARN"
            }
        }
        else {
            $consecutiveFailures++
            Write-Host " - OFFLINE (attempt $consecutiveFailures/$MaxRetries)" -ForegroundColor Red
            Write-Log "Health check failed: $($health.Error)" "ERROR"

            # 프로세스 상태 확인
            $process = Get-LMStudioProcess
            if ($process) {
                Write-Log "LM Studio process is running (PID: $($process.Id)) but not responding" "WARN"
            }
            else {
                Write-Log "LM Studio process not found" "ERROR"
            }

            # 재시작 로직
            if ($consecutiveFailures -ge $MaxRetries) {
                if ($AutoRestart) {
                    Write-Log "Max retries reached. Initiating auto-restart..." "WARN"
                    if (Restart-LocalLLM) {
                        $consecutiveFailures = 0
                        Write-Log "Auto-restart successful" "SUCCESS"
                    }
                    else {
                        Write-Log "Auto-restart failed. Manual intervention required!" "ERROR"
                    }
                }
                else {
                    Write-Host ""
                    Write-Host "⚠️  ALERT: Local LLM offline after $MaxRetries attempts" -ForegroundColor Red
                    Write-Host "Run with -AutoRestart to enable automatic recovery" -ForegroundColor Yellow
                    Write-Host "Or manually restart LM Studio" -ForegroundColor Yellow
                    Write-Host ""

                    if (-not $Continuous) {
                        break
                    }
                }
            }
        }

        if ($Continuous) {
            Start-Sleep -Seconds $CheckIntervalSeconds
        }

    } while ($Continuous)

    Write-Log "Monitoring stopped" "INFO"
}

# Main
Write-Host ""
Start-Monitoring
Write-Host ""
Write-Host "Monitor stopped. Check log: $LogFile" -ForegroundColor Cyan
