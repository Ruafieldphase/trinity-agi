# Start Slack Bot in background
# Usage: .\start_slack_bot.ps1

param(
    [switch]$KillExisting,
    [int]$Port = 8080
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$venvPython = Join-Path $repoRoot "LLM_Unified\.venv\Scripts\python.exe"
$botScript = Join-Path $PSScriptRoot "..\slack_bot_conversational.py"

# Check if bot token is set
if (-not $env:SLACK_BOT_TOKEN) {
    Write-Host "[WARN]  SLACK_BOT_TOKEN not set!" -ForegroundColor Yellow
    Write-Host "   Set it with: [Environment]::SetEnvironmentVariable('SLACK_BOT_TOKEN', 'xoxb-...', 'User')" -ForegroundColor Yellow
    exit 1
}

# Kill existing processes
if ($KillExisting) {
    Write-Host "[SEARCH] Checking for existing Slack bot processes..." -ForegroundColor Cyan
    $processes = Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*slack_bot_server.py*"
    }
    
    if ($processes) {
        Write-Host "🛑 Stopping $($processes.Count) existing process(es)..." -ForegroundColor Yellow
        $processes | Stop-Process -Force
        Start-Sleep -Seconds 2
    }
}

# Check if port is in use
$listener = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
if ($listener) {
    Write-Host "[WARN]  Port $Port is already in use!" -ForegroundColor Yellow
    Write-Host "   Use -KillExisting to stop existing processes" -ForegroundColor Yellow
    exit 1
}

# Start bot in background
Write-Host "[DEPLOY] Starting Ion Canary Slack Bot on port $Port..." -ForegroundColor Green

$startArgs = @{
    FilePath     = "powershell"
    ArgumentList = @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-Command",
        "cd '$repoRoot\LLM_Unified\.venv\Scripts'; .\Activate.ps1; cd '$PSScriptRoot'; & '$venvPython' '$botScript'"
    )
    WindowStyle  = "Hidden"
    PassThru     = $true
}

$process = Start-Process @startArgs

Start-Sleep -Seconds 3

# Verify bot is running
try {
    $response = Invoke-RestMethod -Uri "http://localhost:$Port/health" -TimeoutSec 5
    if ($response.status -eq "ok") {
        Write-Host "[OK] Slack bot started successfully!" -ForegroundColor Green
        Write-Host "   PID: $($process.Id)" -ForegroundColor Gray
        Write-Host "   Health: http://localhost:$Port/health" -ForegroundColor Gray
        Write-Host "   Bot Active: $($response.bot_active)" -ForegroundColor Gray
    }
}
catch {
    Write-Host "[ERROR] Failed to verify bot health check" -ForegroundColor Red
    Write-Host "   Error: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "[LOG] Next steps:" -ForegroundColor Cyan
Write-Host "   1. Set up ngrok: ngrok http $Port" -ForegroundColor Gray
Write-Host "   2. Configure Slack Event URL: https://your-ngrok-url/slack/events" -ForegroundColor Gray
Write-Host "   3. Test in Slack: @Ion Canary Bot status" -ForegroundColor Gray
