# AI-to-AI Communication Hub
# Enables AI agents to send notifications and coordinate actions

param(
    [Parameter(Mandatory)]
    [ValidateSet('send', 'receive', 'broadcast', 'query')]
    [string]$Action,
    
    [string]$SourceAgent = "Unknown",
    [string]$TargetAgent = "all",
    [string]$Message = "",
    [hashtable]$Data = @{},
    [ValidateSet('INFO', 'WARNING', 'CRITICAL', 'SUCCESS')]
    [string]$Priority = "INFO",
    [switch]$Json
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$outputDir = Join-Path (Split-Path -Parent $scriptDir) "outputs"
$commsDir = Join-Path $outputDir "ai_comms"
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"

# Ensure communications directory exists
if (-not (Test-Path $commsDir)) {
    New-Item -ItemType Directory -Path $commsDir -Force | Out-Null
}

function Send-AgentMessage {
    param($source, $target, $message, $data, $priority)
    
    $msg = @{
        Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Source    = $source
        Target    = $target
        Priority  = $priority
        Message   = $message
        Data      = $data
        MessageId = [guid]::NewGuid().ToString()
    }
    
    # Write to communication log
    $logFile = Join-Path $commsDir "agent_comms_$(Get-Date -Format 'yyyy-MM-dd').jsonl"
    $msg | ConvertTo-Json -Compress | Add-Content -Path $logFile -Encoding UTF8
    
    # If critical, also create alert file
    if ($priority -eq "CRITICAL") {
        $alertFile = Join-Path $commsDir "alert_$timestamp.json"
        $msg | ConvertTo-Json -Depth 5 | Out-File -FilePath $alertFile -Encoding UTF8
    }
    
    return $msg
}

function Receive-AgentMessages {
    param($targetAgent, $sinceMinutes = 60)
    
    $cutoffTime = (Get-Date).AddMinutes(-$sinceMinutes)
    $messages = @()
    
    $logFiles = Get-ChildItem -Path $commsDir -Filter "agent_comms_*.jsonl" -ErrorAction SilentlyContinue
    
    foreach ($logFile in $logFiles) {
        $lines = Get-Content $logFile.FullName -ErrorAction SilentlyContinue
        foreach ($line in $lines) {
            try {
                $msg = $line | ConvertFrom-Json
                $msgTime = [datetime]::ParseExact($msg.Timestamp, "yyyy-MM-dd HH:mm:ss", $null)
                
                if ($msgTime -gt $cutoffTime -and 
                    ($msg.Target -eq $targetAgent -or $msg.Target -eq "all")) {
                    $messages += $msg
                }
            }
            catch {
                # Skip malformed messages
            }
        }
    }
    
    return $messages | Sort-Object Timestamp -Descending
}

function Get-AgentStatus {
    $status = @{
        Timestamp       = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        MessagesLast24h = 0
        CriticalAlerts  = 0
        ActiveAgents    = @()
        RecentMessages  = @()
    }
    
    $messages = Receive-AgentMessages -targetAgent "all" -sinceMinutes 1440
    $status.MessagesLast24h = $messages.Count
    $status.CriticalAlerts = ($messages | Where-Object { $_.Priority -eq "CRITICAL" }).Count
    $status.ActiveAgents = $messages.Source | Select-Object -Unique
    $status.RecentMessages = $messages | Select-Object -First 10
    
    return $status
}

# Execute action
switch ($Action) {
    "send" {
        if (-not $Message) {
            Write-Host "ERROR: -Message required for send action" -ForegroundColor Red
            exit 1
        }
        
        Write-Host "Sending message from $SourceAgent to $TargetAgent..." -ForegroundColor Cyan
        $result = Send-AgentMessage -source $SourceAgent -target $TargetAgent `
            -message $Message -data $Data -priority $Priority
        
        if ($Json) {
            $result | ConvertTo-Json -Depth 5
        }
        else {
            Write-Host "  Message ID: $($result.MessageId)" -ForegroundColor Green
            Write-Host "  Priority: $($result.Priority)" -ForegroundColor $(
                switch ($Priority) {
                    "CRITICAL" { "Red" }
                    "WARNING" { "Yellow" }
                    "SUCCESS" { "Green" }
                    default { "Cyan" }
                }
            )
            Write-Host "  Status: Delivered" -ForegroundColor Green
        }
    }
    
    "receive" {
        Write-Host "Checking messages for $SourceAgent..." -ForegroundColor Cyan
        $messages = Receive-AgentMessages -targetAgent $SourceAgent -sinceMinutes 60
        
        if ($Json) {
            $messages | ConvertTo-Json -Depth 5
        }
        else {
            Write-Host "  Found $($messages.Count) message(s) in last hour" -ForegroundColor Green
            foreach ($msg in $messages | Select-Object -First 5) {
                Write-Host "`n  [$($msg.Priority)] From: $($msg.Source)" -ForegroundColor Cyan
                Write-Host "  Time: $($msg.Timestamp)" -ForegroundColor Gray
                Write-Host "  Message: $($msg.Message)" -ForegroundColor White
            }
        }
    }
    
    "broadcast" {
        if (-not $Message) {
            Write-Host "ERROR: -Message required for broadcast action" -ForegroundColor Red
            exit 1
        }
        
        Write-Host "Broadcasting from $SourceAgent to all agents..." -ForegroundColor Cyan
        $result = Send-AgentMessage -source $SourceAgent -target "all" `
            -message $Message -data $Data -priority $Priority
        
        Write-Host "  Broadcast ID: $($result.MessageId)" -ForegroundColor Green
        Write-Host "  Status: Sent to all agents" -ForegroundColor Green
    }
    
    "query" {
        Write-Host "Querying AI communication hub status..." -ForegroundColor Cyan
        $status = Get-AgentStatus
        
        if ($Json) {
            $status | ConvertTo-Json -Depth 5
        }
        else {
            Write-Host "`n  === AI Communication Hub Status ===" -ForegroundColor Cyan
            Write-Host "  Messages (24h): $($status.MessagesLast24h)" -ForegroundColor White
            Write-Host "  Critical Alerts: $($status.CriticalAlerts)" -ForegroundColor $(if ($status.CriticalAlerts -gt 0) { "Red" } else { "Green" })
            Write-Host "  Active Agents: $($status.ActiveAgents.Count)" -ForegroundColor White
            
            if ($status.ActiveAgents.Count -gt 0) {
                Write-Host "`n  Active Agents:" -ForegroundColor Cyan
                foreach ($agent in $status.ActiveAgents) {
                    Write-Host "    - $agent" -ForegroundColor Gray
                }
            }
            
            if ($status.RecentMessages.Count -gt 0) {
                Write-Host "`n  Recent Messages:" -ForegroundColor Cyan
                foreach ($msg in $status.RecentMessages | Select-Object -First 3) {
                    Write-Host "    [$($msg.Priority)] $($msg.Source) -> $($msg.Target): $($msg.Message)" -ForegroundColor Gray
                }
            }
        }
    }
}

Write-Host ""