#Requires -Version 5.1
<#
.SYNOPSIS
    Simple Slack notification test
#>

$ErrorActionPreference = "Stop"

Write-Host "=== Slack Simple Test ===" -ForegroundColor Cyan
Write-Host ""

# Check environment variables
Write-Host "Checking environment variables..." -ForegroundColor Cyan
$token = $env:SLACK_BOT_TOKEN
$channel = $env:SLACK_ALERT_CHANNEL

if (-not $token) {
    Write-Host "ERROR: SLACK_BOT_TOKEN not set" -ForegroundColor Red
    exit 1
}

if (-not $channel) {
    Write-Host "ERROR: SLACK_ALERT_CHANNEL not set" -ForegroundColor Red
    exit 1
}

Write-Host "  Token: $($token.Substring(0, 10))..." -ForegroundColor Green
Write-Host "  Channel: $channel" -ForegroundColor Green
Write-Host ""

# Simple Slack API test
Write-Host "Sending test message to Slack..." -ForegroundColor Cyan

$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type"  = "application/json; charset=utf-8"
}

$body = @{
    channel = $channel
    text    = "Test message from Slack notification system"
    blocks  = @(
        @{
            type = "header"
            text = @{
                type = "plain_text"
                text = "Slack Test Message"
            }
        },
        @{
            type = "section"
            text = @{
                type = "mrkdwn"
                text = "*This is a test message* from the Slack notification system.`n`nTime: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
            }
        }
    )
} | ConvertTo-Json -Depth 10 -Compress

try {
    $response = Invoke-RestMethod -Uri "https://slack.com/api/chat.postMessage" -Method Post -Headers $headers -Body $body
    
    if ($response.ok) {
        Write-Host "SUCCESS: Message sent to Slack!" -ForegroundColor Green
        Write-Host "  Channel: $($response.channel)" -ForegroundColor Gray
        Write-Host "  Timestamp: $($response.ts)" -ForegroundColor Gray
        Write-Host ""
        Write-Host "Check your Slack channel: $channel" -ForegroundColor Yellow
        exit 0
    }
    else {
        Write-Host "ERROR: $($response.error)" -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "ERROR: $_" -ForegroundColor Red
    exit 1
}
