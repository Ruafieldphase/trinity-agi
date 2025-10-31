#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Send test notification to verify Slack integration

.DESCRIPTION
  Sends formatted test messages to Slack webhook to validate notification setup

.PARAMETER WebhookUrl
  Slack incoming webhook URL

.PARAMETER TestType
  Type of test: 'simple', 'alert', 'dashboard' (default: simple)

.EXAMPLE
  ./test_slack_webhook.ps1 -WebhookUrl "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
  ./test_slack_webhook.ps1 -WebhookUrl "https://hooks.slack.com/..." -TestType alert
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$WebhookUrl,
  
    [ValidateSet("simple", "alert", "dashboard", "metrics")]
    [string]$TestType = "simple"
)

$ErrorActionPreference = "Stop"

Write-Host "=== Slack Webhook Test ===" -ForegroundColor Cyan
Write-Host "Test Type: $TestType" -ForegroundColor Gray
Write-Host ""

function Send-SlackMessage {
    param([hashtable]$payload)
  
    $json = $payload | ConvertTo-Json -Depth 10 -Compress
  
    try {
        $response = Invoke-RestMethod -Uri $WebhookUrl -Method Post -Body $json -ContentType "application/json"
        return $true
    }
    catch {
        Write-Host "Failed to send: $_" -ForegroundColor Red
        return $false
    }
}

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

switch ($TestType) {
    "simple" {
        Write-Host "Sending simple test message..." -ForegroundColor Yellow
        $payload = @{
            text   = ":wave: Lumen Monitoring Test - $timestamp"
            blocks = @(
                @{
                    type = "section"
                    text = @{
                        type = "mrkdwn"
                        text = "*Lumen Feedback Loop Monitoring*`n:white_check_mark: Slack integration test successful!"
                    }
                }
            )
        }
    }
  
    "alert" {
        Write-Host "Sending alert notification test..." -ForegroundColor Yellow
        $payload = @{
            text   = "[TEST ALERT] Cache Hit Rate Low"
            blocks = @(
                @{
                    type = "header"
                    text = @{
                        type = "plain_text"
                        text = ":warning: Alert: Cache Hit Rate Low"
                    }
                },
                @{
                    type   = "section"
                    fields = @(
                        @{
                            type = "mrkdwn"
                            text = "*Severity:*`nWarning"
                        },
                        @{
                            type = "mrkdwn"
                            text = "*Service:*`nlumen-gateway"
                        },
                        @{
                            type = "mrkdwn"
                            text = "*Metric:*`ncache_hit_rate"
                        },
                        @{
                            type = "mrkdwn"
                            text = "*Threshold:*`np50 < 0.50"
                        },
                        @{
                            type = "mrkdwn"
                            text = "*Current Value:*`n0.42 (p50)"
                        },
                        @{
                            type = "mrkdwn"
                            text = "*Time:*`n$timestamp"
                        }
                    )
                },
                @{
                    type     = "actions"
                    elements = @(
                        @{
                            type  = "button"
                            text  = @{
                                type = "plain_text"
                                text = "View Dashboard"
                            }
                            url   = "https://console.cloud.google.com/monitoring/dashboards/custom/71f2f32c-29a4-49e2-b3c5-d840984828a6?project=naeda-genesis"
                            style = "primary"
                        },
                        @{
                            type = "button"
                            text = @{
                                type = "plain_text"
                                text = "View Logs"
                            }
                            url  = "https://console.cloud.google.com/logs/query?project=naeda-genesis"
                        }
                    )
                },
                @{
                    type     = "context"
                    elements = @(
                        @{
                            type = "mrkdwn"
                            text = ":information_source: This is a *test alert*. No action required."
                        }
                    )
                }
            )
        }
    }
  
    "dashboard" {
        Write-Host "Sending dashboard summary..." -ForegroundColor Yellow
        $payload = @{
            text   = "Lumen Metrics Dashboard Summary"
            blocks = @(
                @{
                    type = "header"
                    text = @{
                        type = "plain_text"
                        text = ":chart_with_upwards_trend: Lumen Feedback Loop - Daily Summary"
                    }
                },
                @{
                    type = "section"
                    text = @{
                        type = "mrkdwn"
                        text = "*Performance Overview* ($timestamp)"
                    }
                },
                @{
                    type   = "section"
                    fields = @(
                        @{
                            type = "mrkdwn"
                            text = "*Cache Hit Rate:*`n:large_green_circle: 70%"
                        },
                        @{
                            type = "mrkdwn"
                            text = "*Memory Usage:*`n:large_green_circle: 65%"
                        },
                        @{
                            type = "mrkdwn"
                            text = "*Avg TTL:*`n:large_green_circle: 1200s"
                        },
                        @{
                            type = "mrkdwn"
                            text = "*Health Score:*`n:large_green_circle: 85/100"
                        }
                    )
                },
                @{
                    type = "divider"
                },
                @{
                    type = "section"
                    text = @{
                        type = "mrkdwn"
                        text = "*Status:* :white_check_mark: All systems operational`n*Alerts:* 0 active`n*Uptime:* 99.9%"
                    }
                },
                @{
                    type     = "actions"
                    elements = @(
                        @{
                            type  = "button"
                            text  = @{
                                type = "plain_text"
                                text = "Open Dashboard"
                            }
                            url   = "https://console.cloud.google.com/monitoring/dashboards/custom/71f2f32c-29a4-49e2-b3c5-d840984828a6?project=naeda-genesis"
                            style = "primary"
                        }
                    )
                }
            )
        }
    }
  
    "metrics" {
        Write-Host "Sending real-time metrics..." -ForegroundColor Yellow
    
        # Query actual metrics
        $logFilter = "jsonPayload.component=`"feedback_loop`""
        $logCmd = "gcloud logging read `"$logFilter`" --project=naeda-genesis --limit=1 --format=json --freshness=10m 2>&1"
        $logJson = cmd /c $logCmd
    
        $hitRate = 0.7
        $memUsage = 65
        $avgTTL = 1200
        $health = 85
    
        if ($LASTEXITCODE -eq 0) {
            $logEntries = $logJson | ConvertFrom-Json
            if ($logEntries.Count -gt 0) {
                $payload_data = $logEntries[0].jsonPayload
                $hitRate = $payload_data.cache_hit_rate
                $memUsage = $payload_data.cache_memory_usage_percent
                $avgTTL = $payload_data.cache_avg_ttl_seconds
                $health = $payload_data.unified_health_score
            }
        }
    
        $hitRatePercent = [Math]::Round($hitRate * 100, 1)
        $hitRateIcon = if ($hitRate -ge 0.7) { ":large_green_circle:" } elseif ($hitRate -ge 0.5) { ":large_yellow_circle:" } else { ":red_circle:" }
        $memIcon = if ($memUsage -le 75) { ":large_green_circle:" } elseif ($memUsage -le 90) { ":large_yellow_circle:" } else { ":red_circle:" }
        $ttlIcon = if ($avgTTL -ge 600) { ":large_green_circle:" } elseif ($avgTTL -ge 300) { ":large_yellow_circle:" } else { ":red_circle:" }
        $healthIcon = if ($health -ge 80) { ":large_green_circle:" } elseif ($health -ge 60) { ":large_yellow_circle:" } else { ":red_circle:" }
    
        $payload = @{
            text   = "Lumen Real-time Metrics"
            blocks = @(
                @{
                    type = "header"
                    text = @{
                        type = "plain_text"
                        text = ":chart_with_upwards_trend: Live Metrics - $timestamp"
                    }
                },
                @{
                    type   = "section"
                    fields = @(
                        @{
                            type = "mrkdwn"
                            text = "*Cache Hit Rate:*`n$hitRateIcon ${hitRatePercent}%"
                        },
                        @{
                            type = "mrkdwn"
                            text = "*Memory Usage:*`n$memIcon ${memUsage}%"
                        },
                        @{
                            type = "mrkdwn"
                            text = "*Avg TTL:*`n$ttlIcon ${avgTTL}s"
                        },
                        @{
                            type = "mrkdwn"
                            text = "*Health Score:*`n$healthIcon ${health}/100"
                        }
                    )
                }
            )
        }
    }
}

Write-Host "Sending to Slack..." -ForegroundColor Yellow
$success = Send-SlackMessage $payload

if ($success) {
    Write-Host "[OK] Message sent successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Check your Slack channel for the test message." -ForegroundColor Cyan
}
else {
    Write-Host "[ERROR] Failed to send message" -ForegroundColor Red
    exit 1
}
