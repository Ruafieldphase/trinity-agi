param(
    [Parameter(Mandatory = $true)] [string]$ProjectId,
    [string]$EmailAddress = "",
    [string]$SlackWebhookUrl = "",
    [switch]$DryRun
)

# Header
Write-Host "`n[Lumen v1.7] Setting up Cloud Monitoring Notification Channels" -ForegroundColor Cyan

function Invoke-GCloud($argsArray) {
    $tmpOut = [System.IO.Path]::GetTempFileName()
    $cmdLine = "gcloud $($argsArray -join ' ') --project=$ProjectId"
    cmd /c "$cmdLine > `"$tmpOut`" 2>&1"
    $out = Get-Content -Path $tmpOut -Raw -ErrorAction SilentlyContinue
    Remove-Item $tmpOut -ErrorAction SilentlyContinue
    return $out
}

function Get-NotificationChannelByDisplayName([string]$displayName) {
    $json = Invoke-GCloud @("monitoring", "channels", "list", "--format=json")
    if (-not $json) { return $null }
    try {
        $arr = $json | ConvertFrom-Json
        foreach ($ch in $arr) {
            if ($ch.displayName -eq $displayName) { return $ch }
        }
    }
    catch {}
    return $null
}

function Ensure-NotificationChannel {
    param(
        [Parameter(Mandatory = $true)] [string]$DisplayName,
        [Parameter(Mandatory = $true)] [string]$Type,
        [Parameter(Mandatory = $true)] [hashtable]$Labels,
        [string]$Description = ""
    )

    Write-Host "`n[•] Ensuring notification channel: $DisplayName" -ForegroundColor Yellow
    $existing = Get-NotificationChannelByDisplayName -displayName $DisplayName

    $channelObj = [ordered]@{
        displayName = $DisplayName
        type        = $Type
        labels      = $Labels
        enabled     = $true
    }
    if ($Description) {
        $channelObj.description = $Description
    }

    if ($DryRun) {
        Write-Host "   - DryRun: Would apply channel below:" -ForegroundColor DarkGray
        $channelObj | ConvertTo-Json -Depth 10 | Write-Output
        return $null
    }

    $tmpChannel = [System.IO.Path]::GetTempFileName()
    try {
        if ($existing -and $existing.name) {
            $channelObj.name = $existing.name
            $channelObj | ConvertTo-Json -Depth 10 | Out-File -FilePath $tmpChannel -Encoding UTF8
            $out = Invoke-GCloud @("monitoring", "channels", "update", "$($existing.name)", "--channel-content-from-file=$tmpChannel")
            Write-Host "   - Updated: $($existing.name)" -ForegroundColor DarkGray
            return $existing.name
        }
        else {
            $channelObj | ConvertTo-Json -Depth 10 | Out-File -FilePath $tmpChannel -Encoding UTF8
            $out = Invoke-GCloud @("monitoring", "channels", "create", "--channel-content-from-file=$tmpChannel")
            # Parse created channel name from output
            if ($out -match 'name:\s*(.+)') {
                $createdName = $Matches[1].Trim()
                Write-Host "   - Created: $createdName" -ForegroundColor DarkGray
                return $createdName
            }
            Write-Host "   - Created: $DisplayName" -ForegroundColor DarkGray
            return $DisplayName
        }
    }
    finally {
        Remove-Item $tmpChannel -ErrorAction SilentlyContinue
    }
}

function Link-ChannelToPolicy {
    param(
        [Parameter(Mandatory = $true)] [string]$PolicyDisplayName,
        [Parameter(Mandatory = $true)] [string]$ChannelName
    )

    Write-Host "`n[•] Linking channel to policy: $PolicyDisplayName" -ForegroundColor Yellow

    $json = Invoke-GCloud @("monitoring", "policies", "list", "--format=json")
    if (-not $json) {
        Write-Host "   - Error: Could not list policies" -ForegroundColor Red
        return
    }

    try {
        $arr = $json | ConvertFrom-Json
        $policy = $null
        foreach ($p in $arr) {
            if ($p.displayName -eq $PolicyDisplayName) {
                $policy = $p
                break
            }
        }

        if (-not $policy) {
            Write-Host "   - Warning: Policy not found: $PolicyDisplayName" -ForegroundColor Yellow
            return
        }

        if ($DryRun) {
            Write-Host "   - DryRun: Would link $ChannelName to $($policy.name)" -ForegroundColor DarkGray
            return
        }

        # Add channel to notificationChannels array if not already present
        $channels = @($policy.notificationChannels)
        if ($channels -notcontains $ChannelName) {
            $channels += $ChannelName
        }
        $policy.notificationChannels = $channels

        $tmpPolicy = [System.IO.Path]::GetTempFileName()
        try {
            $policy | ConvertTo-Json -Depth 10 | Out-File -FilePath $tmpPolicy -Encoding UTF8
            $out = Invoke-GCloud @("monitoring", "policies", "update", "--policy-from-file=$tmpPolicy")
            Write-Host "   - Linked channel to policy" -ForegroundColor DarkGray
        }
        finally {
            Remove-Item $tmpPolicy -ErrorAction SilentlyContinue
        }
    }
    catch {
        Write-Host "   - Error linking channel: $_" -ForegroundColor Red
    }
}

# Create notification channels
$channelNames = @()

if ($EmailAddress) {
    Write-Host "`n==> Creating Email notification channel" -ForegroundColor Cyan
    $emailChannel = Ensure-NotificationChannel `
        -DisplayName "Lumen Alerts Email" `
        -Type "email" `
        -Labels @{ email_address = $EmailAddress } `
        -Description "Email notifications for Lumen feedback loop alerts"
    
    if ($emailChannel) {
        $channelNames += $emailChannel
    }
}

if ($SlackWebhookUrl) {
    Write-Host "`n==> Creating Slack notification channel" -ForegroundColor Cyan
    $slackChannel = Ensure-NotificationChannel `
        -DisplayName "Lumen Alerts Slack" `
        -Type "slack" `
        -Labels @{ url = $SlackWebhookUrl } `
        -Description "Slack notifications for Lumen feedback loop alerts"
    
    if ($slackChannel) {
        $channelNames += $slackChannel
    }
}

if ($channelNames.Count -eq 0) {
    Write-Host "`nNo notification channels specified. Use -EmailAddress or -SlackWebhookUrl" -ForegroundColor Yellow
    exit 0
}

if (-not $DryRun) {
    # Link channels to alert policies
    Write-Host "`n==> Linking channels to alert policies" -ForegroundColor Cyan
    $policies = @("Lumen: Cache Hit Rate Low", "Lumen: Memory Usage High", "Lumen: Unified Health Low")
    
    foreach ($policyName in $policies) {
        foreach ($channelName in $channelNames) {
            Link-ChannelToPolicy -PolicyDisplayName $policyName -ChannelName $channelName
        }
    }
}

Write-Host ("`n" + 'Notification channels setup complete for project: ' + $ProjectId) -ForegroundColor Green
