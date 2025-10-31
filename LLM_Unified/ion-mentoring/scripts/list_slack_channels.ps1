#Requires -Version 5.1
<#
.SYNOPSIS
    List Slack channels that bot can access
#>

$ErrorActionPreference = "Stop"

Write-Host "=== Slack Channel List ===" -ForegroundColor Cyan
Write-Host ""

$token = $env:SLACK_BOT_TOKEN

if (-not $token) {
    Write-Host "ERROR: SLACK_BOT_TOKEN not set" -ForegroundColor Red
    exit 1
}

Write-Host "Getting channels..." -ForegroundColor Cyan

$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type"  = "application/json"
}

try {
    # Get public channels
    Write-Host "`n1. Public Channels:" -ForegroundColor Yellow
    $response = Invoke-RestMethod -Uri "https://slack.com/api/conversations.list?types=public_channel" -Method Get -Headers $headers
    
    if ($response.ok) {
        foreach ($channel in $response.channels) {
            $isMember = if ($channel.is_member) { "[OK] Member" } else { "[WARN]  Not member" }
            Write-Host "  - $($channel.name) (ID: $($channel.id)) $isMember" -ForegroundColor $(if ($channel.is_member) { "Green" } else { "Gray" })
        }
    }
    else {
        Write-Host "  Error: $($response.error)" -ForegroundColor Red
    }
    
    # Get private channels (if bot is member)
    Write-Host "`n2. Private Channels (if member):" -ForegroundColor Yellow
    $response = Invoke-RestMethod -Uri "https://slack.com/api/conversations.list?types=private_channel" -Method Get -Headers $headers
    
    if ($response.ok -and $response.channels.Count -gt 0) {
        foreach ($channel in $response.channels) {
            Write-Host "  - $($channel.name) (ID: $($channel.id)) [OK] Member" -ForegroundColor Green
        }
    }
    else {
        Write-Host "  (None or no access)" -ForegroundColor Gray
    }
    
    # Get DMs
    Write-Host "`n3. Direct Messages:" -ForegroundColor Yellow
    $response = Invoke-RestMethod -Uri "https://slack.com/api/conversations.list?types=im" -Method Get -Headers $headers
    
    if ($response.ok -and $response.channels.Count -gt 0) {
        Write-Host "  Found $($response.channels.Count) DM channels" -ForegroundColor Green
    }
    else {
        Write-Host "  (None)" -ForegroundColor Gray
    }
    
    Write-Host "`n" -NoNewline
    Write-Host "[INFO] Tip: " -ForegroundColor Cyan -NoNewline
    Write-Host "Use channel ID (e.g., C01234567) instead of #channel-name for better reliability"
    Write-Host "      Or invite bot to channel: " -NoNewline
    Write-Host "/invite @YourBotName" -ForegroundColor Yellow
    Write-Host ""
}
catch {
    Write-Host "ERROR: $_" -ForegroundColor Red
    exit 1
}
