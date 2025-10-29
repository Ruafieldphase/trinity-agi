<#
.SYNOPSIS
  Send a Slack notification via webhook.
.DESCRIPTION
  Posts a simple text message or structured blocks to Slack.
  Reads webhook URL from environment variable ION_SLACK_WEBHOOK_URL or accepts it via parameter.
.EXAMPLE
  .\send_slack_notification.ps1 -Message "Canary 100% deployed successfully" -Emoji ":rocket:"
  .\send_slack_notification.ps1 -WebhookUrl "https://hooks.slack.com/..." -Message "Test"
#>
param(
    [string]$WebhookUrl = "",
    [Parameter(Mandatory = $true)]
    [string]$Message,
    [string]$Emoji = ":information_source:",
    [string]$Username = "Ion Canary Bot"
)

$ErrorActionPreference = "Stop"

# Resolve webhook URL
if ([string]::IsNullOrWhiteSpace($WebhookUrl)) {
    $WebhookUrl = [Environment]::GetEnvironmentVariable("ION_SLACK_WEBHOOK_URL", "User")
    if (-not $WebhookUrl) {
        $WebhookUrl = [Environment]::GetEnvironmentVariable("ION_SLACK_WEBHOOK_URL", "Machine")
    }
}

if ([string]::IsNullOrWhiteSpace($WebhookUrl)) {
    Write-Warning "No Slack webhook URL provided. Set ION_SLACK_WEBHOOK_URL env var or pass -WebhookUrl."
    exit 0  # Silent skip if not configured
}

# Build payload
$payload = @{
    text     = "$Emoji $Message"
    username = $Username
} | ConvertTo-Json -Depth 5

try {
    Invoke-RestMethod -Uri $WebhookUrl -Method POST -Body $payload -ContentType "application/json; charset=utf-8" -TimeoutSec 10 | Out-Null
    Write-Host "[Slack] Message sent: $Message"
}
catch {
    Write-Warning "[Slack] Failed to send: $($_.Exception.Message)"
}
