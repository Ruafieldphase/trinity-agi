param(
    [string]$ProjectId = 'naeda-genesis',
    [string]$ChannelDisplayName = 'ION Team Alert Email'
)

$ErrorActionPreference = 'Stop'

function Get-AccessToken {
    $token = & gcloud auth print-access-token
    if (-not $token) { throw 'Failed to obtain access token via gcloud.' }
    return $token.Trim()
}

function Get-NotificationChannelByName([string]$projectId, [string]$displayName) {
    $uri = "https://monitoring.googleapis.com/v3/projects/$projectId/notificationChannels"
    $headers = @{ Authorization = "Bearer $(Get-AccessToken)" }
    $resp = Invoke-RestMethod -Method Get -Uri $uri -Headers $headers
    $match = $resp.notificationChannels | Where-Object { $_.displayName -eq $displayName }
    return $match
}

function Add-Channel-To-Policy([string]$policyName, [string]$channelFullName) {
    $base = "https://monitoring.googleapis.com/v3/$policyName"
    $headers = @{ Authorization = "Bearer $(Get-AccessToken)" }
    Write-Host "Fetching policy: $base"
    # Fetch policy
    $policy = Invoke-RestMethod -Method Get -Uri $base -Headers $headers
    if (-not ($policy.PSObject.Properties.Name -contains 'notificationChannels')) {
        $policy | Add-Member -NotePropertyName 'notificationChannels' -NotePropertyValue @() -Force
    }
    if ($policy.notificationChannels -notcontains $channelFullName) {
        $policy.notificationChannels += $channelFullName
        $body = $policy | ConvertTo-Json -Depth 32
        $uri = ($base + '?updateMask=notification_channels')
        Write-Host "Patching policy: $uri"
        $null = Invoke-RestMethod -Method Patch -Uri $uri -Headers $headers -ContentType 'application/json; charset=utf-8' -Body $body
        Write-Host "Attached channel to policy: $($policy.displayName)"
    }
    else {
        Write-Host "Channel already attached: $($policy.displayName)"
    }
}

try {
    $channel = Get-NotificationChannelByName -projectId $ProjectId -displayName $ChannelDisplayName
    if (-not $channel) {
        Write-Warning "Notification channel '$ChannelDisplayName' not found in project $ProjectId. Aborting."
        exit 2
    }
    $channelName = $channel.name

    # Target policy names
    $targetNames = @(
        'Lumen Gateway - High p95 Latency',
        'Lumen Gateway - High Error Rate'
    )

    # List policies and filter by names
    $listUri = "https://monitoring.googleapis.com/v3/projects/$ProjectId/alertPolicies"
    $headers = @{ Authorization = "Bearer $(Get-AccessToken)" }
    $resp = Invoke-RestMethod -Method Get -Uri $listUri -Headers $headers
    $policies = $resp.alertPolicies | Where-Object { $targetNames -contains $_.displayName }

    if (-not $policies) {
        Write-Warning "No matching alert policies found to update."
        exit 3
    }

    foreach ($p in $policies) {
        Add-Channel-To-Policy -policyName $p.name -channelFullName $channelName
    }

    Write-Host "Completed attaching notification channel to target policies."
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}
