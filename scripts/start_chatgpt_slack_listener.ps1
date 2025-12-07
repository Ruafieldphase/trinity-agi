# Start ChatGPT Slack Input Listener (Body Interface)
# This script starts the Body's Slack Interface in the background

$pythonPath = "python"
$scriptPath = "C:\workspace\agi\body\slack_interface.py"
$workingDir = "C:\workspace\agi"

Write-Host "Starting AGI Body (Slack Interface)..." -ForegroundColor Cyan

# Check if script exists
if (-not (Test-Path $scriptPath)) {
    Write-Host "Error: slack_interface.py not found at $scriptPath" -ForegroundColor Red
    exit 1
}

# Check if config is set up
$configPath = "C:\workspace\agi\config\slack_config.json"
if (Test-Path $configPath) {
    $config = Get-Content $configPath | ConvertFrom-Json
    if ($config.CHATGPT_SLACK_ENABLED -eq $false) {
        Write-Host "Warning: CHATGPT_SLACK_ENABLED is false in config" -ForegroundColor Yellow
        Write-Host "Please update slack_config.json with ChatGPT workspace tokens" -ForegroundColor Yellow
        exit 1
    }
}

# Start the listener process in background
Start-Process -FilePath $pythonPath `
    -ArgumentList $scriptPath `
    -WindowStyle Hidden `
    -WorkingDirectory $workingDir

Write-Host "✓ AGI Body (Slack Interface) started in background" -ForegroundColor Green
Write-Host "Check C:\workspace\agi\outputs\slack_interface.log for logs" -ForegroundColor Gray
