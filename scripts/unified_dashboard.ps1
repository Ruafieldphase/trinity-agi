# ?µÌï© Î™®Îãà?∞ÎßÅ ?Ä?úÎ≥¥??# AGI (fdo_agi_repo) + Lumen (LLM_Unified) ?úÏä§???µÌï© Î™®Îãà?∞ÎßÅ

param(
    [int]$Hours = 1,
    [switch]$Json
)

$ErrorActionPreference = "Stop"
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Write-ColorLine {
    param(
        [string]$Text,
        [string]$Color = "White",
        [switch]$NoNewline
    )
    if ($NoNewline) {
        Write-Host $Text -ForegroundColor $Color -NoNewline
    }
    else {
        Write-Host $Text -ForegroundColor $Color
    }
}

function Get-ChannelStatus {
    param(
        [string]$Name,
        [string]$Url,
        [hashtable]$Body = $null,
        [int]$TimeoutSec = 10
    )
    
    $start = Get-Date
    try {
        $params = @{
            Uri         = $Url
            Method      = if ($Body) { "POST" } else { "GET" }
            TimeoutSec  = $TimeoutSec
            ErrorAction = "Stop"
        }
        
        if ($Body) {
            $params.Body = ($Body | ConvertTo-Json -Compress)
            $params.ContentType = "application/json; charset=utf-8"
        }
        
        $response = Invoke-RestMethod @params
        $elapsed = ((Get-Date) - $start).TotalMilliseconds
        
        return @{
            Name         = $Name
            Status       = "Online"
            ResponseTime = [int]$elapsed
            Response     = $response
        }
    }
    catch {
        $elapsed = ((Get-Date) - $start).TotalMilliseconds
        return @{
            Name         = $Name
            Status       = "Offline"
            ResponseTime = [int]$elapsed
            Error        = $_.Exception.Message
        }
    }
}

# AGI ?úÏä§???ÅÌÉú ?ïÏù∏
Write-ColorLine "`n============================================================" "Cyan"
Write-ColorLine "[START] ?µÌï© Î™®Îãà?∞ÎßÅ ?Ä?úÎ≥¥?? "Cyan"
Write-ColorLine "============================================================`n" "Cyan"

$agiStatus = @{
    healthy = $false
    metrics = @{}
    error   = $null
}

try {
    # AGI Python ?Ä?úÎ≥¥???§Ìñâ
    $agiRoot = "C:\workspace\agi\fdo_agi_repo"
    $pythonExe = if (Test-Path "$agiRoot\.venv\Scripts\python.exe") {
        "$agiRoot\.venv\Scripts\python.exe"
    }
    else {
        "python"
    }
    
    Push-Location $agiRoot
    $dashboardOutput = & $pythonExe "scripts\ops_dashboard.py" "--json" 2>&1
    Pop-Location
    
    if ($LASTEXITCODE -eq 0) {
        $agiData = $dashboardOutput | ConvertFrom-Json
        $agiStatus.healthy = $agiData.healthy
        $agiStatus.metrics = $agiData.metrics
        $agiStatus.policy = $agiData.policy
        $agiStatus.health_checks = $agiData.health_checks
    }
}
catch {
    $agiStatus.error = $_.Exception.Message
}

# AGI ?úÏä§??Ï∂úÎ†•
Write-ColorLine "[System 1] AGI Orchestrator (fdo_agi_repo)" "Yellow"
if ($agiStatus.healthy) {
    Write-ColorLine "   Status: " -NoNewline
    Write-ColorLine "??HEALTHY" "Green"
    
    $m = $agiStatus.metrics
    $p = $agiStatus.policy
    
    Write-ColorLine "   Metrics (ÏµúÍ∑º $($p.recent_hours)?úÍ∞Ñ):"
    Write-ColorLine "      ??Confidence: $([math]::Round($m.avg_confidence, 3)) (samples: $($p.samples.confidence))" "White"
    Write-ColorLine "      ??Quality:    $([math]::Round($m.avg_quality, 3)) (samples: $($p.samples.quality))" "White"
    Write-ColorLine "      ??2nd Pass:   $([math]::Round($m.second_pass_rate, 3)) ($($m.second_pass_count)/$($m.total_tasks))" "White"
    
    Write-ColorLine "   Services:"
    if ($agiStatus.health_checks.proxy_ok) {
        Write-ColorLine "      ??Local Proxy:   ??Port $($p.resolved_proxy_port)" "Green"
    }
    else {
        Write-ColorLine "      ??Local Proxy:   ??Offline" "Red"
    }
    
    if ($agiStatus.health_checks.lumen_ok) {
        Write-ColorLine "      ??Lumen Gateway: ??Online" "Green"
    }
    else {
        Write-ColorLine "      ??Lumen Gateway: ??Offline" "Red"
    }
}
else {
    Write-ColorLine "   Status: " -NoNewline
    Write-ColorLine "??UNHEALTHY" "Red"
    if ($agiStatus.error) {
        Write-ColorLine "   Error: $($agiStatus.error)" "Red"
    }
}

Write-ColorLine "`n------------------------------------------------------------`n"

# Lumen ?úÏä§???ÅÌÉú ?ïÏù∏
Write-ColorLine "[System 2] Lumen Multi-Channel Gateway" "Yellow"

# Local LLM (LM Studio)
$localHealth = Get-ChannelStatus -Name "Local Health" -Url "http://localhost:8080/v1/models" -TimeoutSec 3
$localChat = Get-ChannelStatus -Name "Local Chat" -Url "http://localhost:8080/v1/chat/completions" -Body @{
    model      = "yanolja_-_eeve-korean-instruct-10.8b-v1.0"
    messages   = @(@{role = "user"; content = "ping" })
    max_tokens = 10
}

Write-ColorLine "   [Channel 1] Local LLM (LM Studio):"
if ($localHealth.Status -eq "Online") {
    $msg = "      ??Health: ??Online (" + $localHealth.ResponseTime + " ms)"
    Write-ColorLine $msg "Green"
}
else {
    Write-ColorLine "      ??Health: ??Offline" "Red"
}

if ($localChat.Status -eq "Online") {
    $msg = "      ??Chat:   ??Online (" + $localChat.ResponseTime + " ms)"
    Write-ColorLine $msg "Green"
}
else {
    Write-ColorLine "      ??Chat:   ??Offline" "Red"
}

# Cloud AI
$cloudAi = Get-ChannelStatus -Name "Cloud AI" -Url "https://ion-api-64076350717.us-central1.run.app/chat" -Body @{
    message = "ping"
} -TimeoutSec 5

Write-ColorLine "`n   [Channel 2] Cloud AI (ion-api):"
if ($cloudAi.Status -eq "Online") {
    $msg = "      ??Status: ??Online (" + $cloudAi.ResponseTime + " ms)"
    Write-ColorLine $msg "Green"
}
else {
    Write-ColorLine "      ??Status: ??Offline" "Red"
}

# Lumen Gateway
$gateway = Get-ChannelStatus -Name "Lumen Gateway" -Url "https://lumen-gateway-x4qvsargwa-uc.a.run.app/chat" -Body @{
    message = "ping"
} -TimeoutSec 5

Write-ColorLine "`n   [Channel 3] Lumen Gateway:"
if ($gateway.Status -eq "Online") {
    $msg = "      ??Status: ??Online (" + $gateway.ResponseTime + " ms)"
    Write-ColorLine $msg "Green"
}
else {
    Write-ColorLine "      ??Status: ??Offline" "Red"
}

# ?ÑÏ≤¥ ?ÅÌÉú ?îÏïΩ
Write-ColorLine "`n============================================================" "Cyan"

$allHealthy = $agiStatus.healthy -and 
$localHealth.Status -eq "Online" -and 
$localChat.Status -eq "Online" -and 
$cloudAi.Status -eq "Online" -and 
$gateway.Status -eq "Online"

if ($allHealthy) {
    Write-ColorLine "Summary: ??ALL SYSTEMS OPERATIONAL" "Green"
}
else {
    Write-ColorLine "Summary: ??SOME SYSTEMS DEGRADED" "Yellow"
}

Write-ColorLine "============================================================`n" "Cyan"

# JSON Ï∂úÎ†• (?†ÌÉù)
if ($Json) {
    $output = @{
        timestamp   = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
        all_healthy = $allHealthy
        agi         = $agiStatus
        lumen       = @{
            local_llm = @{
                health = $localHealth
                chat   = $localChat
            }
            cloud_ai  = $cloudAi
            gateway   = $gateway
        }
    }
    
    $jsonPath = "C:\workspace\agi\outputs\unified_dashboard_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    $output | ConvertTo-Json -Depth 10 | Out-File -Encoding utf8 -FilePath $jsonPath
    Write-ColorLine "JSON report saved: $jsonPath" "Cyan"
}
