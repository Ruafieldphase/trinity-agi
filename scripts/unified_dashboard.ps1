# ?합 모니?링 ??보??# AGI (fdo_agi_repo) + Core (LLM_Unified) ?스???합 모니?링

param(
    [int]$Hours = 1,
    [switch]$Json
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot



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

# AGI ?스???태 ?인
Write-ColorLine "`n============================================================" "Cyan"
Write-ColorLine "[START] ?합 모니?링 ??보?? "Cyan"
Write-ColorLine "============================================================`n" "Cyan"

$agiStatus = @{
    healthy = $false
    metrics = @{}
    error   = $null
}

try {
    # AGI Python ??보???행
    $agiRoot = "$WorkspaceRoot\fdo_agi_repo"
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

# AGI ?스??출력
Write-ColorLine "[System 1] AGI Orchestrator (fdo_agi_repo)" "Yellow"
if ($agiStatus.healthy) {
    Write-ColorLine "   Status: " -NoNewline
    Write-ColorLine "??HEALTHY" "Green"
    
    $m = $agiStatus.metrics
    $p = $agiStatus.policy
    
    Write-ColorLine "   Metrics (최근 $($p.recent_hours)?간):"
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
    
    if ($agiStatus.health_checks.core_ok) {
        Write-ColorLine "      ??Core Gateway: ??Online" "Green"
    }
    else {
        Write-ColorLine "      ??Core Gateway: ??Offline" "Red"
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

# Core ?스???태 ?인
Write-ColorLine "[System 2] Core Multi-Channel Gateway" "Yellow"

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

# Core Gateway
$gateway = Get-ChannelStatus -Name "Core Gateway" -Url "https://Core-gateway-x4qvsargwa-uc.a.run.app/chat" -Body @{
    message = "ping"
} -TimeoutSec 5

Write-ColorLine "`n   [Channel 3] Core Gateway:"
if ($gateway.Status -eq "Online") {
    $msg = "      ??Status: ??Online (" + $gateway.ResponseTime + " ms)"
    Write-ColorLine $msg "Green"
}
else {
    Write-ColorLine "      ??Status: ??Offline" "Red"
}

# ?체 ?태 ?약
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

# JSON 출력 (?택)
if ($Json) {
    $output = @{
        timestamp   = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
        all_healthy = $allHealthy
        agi         = $agiStatus
        Core       = @{
            local_llm = @{
                health = $localHealth
                chat   = $localChat
            }
            cloud_ai  = $cloudAi
            gateway   = $gateway
        }
    }
    
    $jsonPath = "$WorkspaceRoot\outputs\unified_dashboard_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    $output | ConvertTo-Json -Depth 10 | Out-File -Encoding utf8 -FilePath $jsonPath
    Write-ColorLine "JSON report saved: $jsonPath" "Cyan"
}