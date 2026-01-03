# Core Hybrid System Dashboard (ASCII-safe)
param(
    [switch]$Watch,
    [int]$RefreshSeconds = 5,
    [switch]$FailOnDegraded,
    [switch]$FailOnWarn,
    [int]$WarnMs = 800,
    [int]$AlertMs = 1500,
    [switch]$SlackOnFailure,
    [string]$SlackChannel,
    [string]$OutJson,
    [string]$OutMarkdown
)

function Write-ColorLine {
    param(
        [string]$Text,
        [string]$Color = "White"
    )
    Write-Host $Text -ForegroundColor $Color
}

function Get-ChannelStatus {
    param(
        [string]$Name,
        [string]$Url,
        [hashtable]$Headers = @{},
        [hashtable]$Body = @{},
        [int]$TimeoutSec = 10
    )

    $status = @{
        Name         = $Name
        Url          = $Url
        Status       = "Unknown"
        StatusCode   = 0
        ResponseTime = 0
        ErrorMessage = ""
        Color        = "Gray"
        Symbol       = "O"
    }

    try {
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

        if ($Body.Count -gt 0) {
            $bodyJson = $Body | ConvertTo-Json -Compress
            $null = Invoke-RestMethod -Uri $Url -Method POST -Body $bodyJson -ContentType "application/json" -Headers $Headers -TimeoutSec $TimeoutSec -ErrorAction Stop
        }
        else {
            $null = Invoke-RestMethod -Uri $Url -Method GET -Headers $Headers -TimeoutSec $TimeoutSec -ErrorAction Stop
        }

        $stopwatch.Stop()

        $status.Status = "Online"
        $status.StatusCode = 200
        $status.ResponseTime = [math]::Round($stopwatch.Elapsed.TotalMilliseconds)
        $status.Color = "Green"
        $status.Symbol = "OK"
    }
    catch {
        $stopwatch.Stop()
        $status.Status = "Offline"
        $status.StatusCode = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode.value__ } else { 0 }
        $status.ResponseTime = [math]::Round($stopwatch.Elapsed.TotalMilliseconds)
        $status.ErrorMessage = $_.Exception.Message
        $status.Color = "Red"
        $status.Symbol = "ERR"
    }

    return $status
}

function Show-Dashboard {
    Clear-Host
    
    Write-Host ""
    Write-ColorLine "============================================================" "Cyan"
    Write-ColorLine " Core Hybrid System Dashboard" "Cyan"
    Write-ColorLine "============================================================" "Cyan"
    Write-Host ""
    $scanTime = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    Write-ColorLine "Scanned at: $scanTime" "Yellow"
    Write-Host ""
    
    # 로컬 프록시 프로세스 체크
    $proxyProcess = Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue
    $proxyRunning = $null -ne $proxyProcess
    
    Write-ColorLine "------------------------------------------------------------" "DarkGray"
    Write-Host ""
    
    # 1. 로컬 LLM 프록시
    Write-ColorLine "[Channel 1] Local LLM Proxy" "White"
    Write-ColorLine "   Endpoint: http://localhost:8080/v1/chat/completions" "DarkGray"
    
    if ($proxyRunning) {
        Write-ColorLine "   Process: Running (PID: $($proxyProcess.OwningProcess))" "DarkGreen"
        
        # LM Studio는 /health 대신 /v1/models로 헬스체크
        $localStatus = Get-ChannelStatus -Name "Local Proxy Health" -Url "http://localhost:8080/v1/models" -TimeoutSec 3
        Write-Host "   Status: " -NoNewline
        Write-ColorLine "$($localStatus.Symbol) $($localStatus.Status)" $localStatus.Color
        Write-ColorLine "   Response time: $($localStatus.ResponseTime) ms" "DarkGray"
        
        # 실제 채팅 테스트 (LM Studio 모델 사용)
        $chatTest = Get-ChannelStatus -Name "Local Proxy Chat" -Url "http://localhost:8080/v1/chat/completions" -Body @{
            model      = "yanolja_-_eeve-korean-instruct-10.8b-v1.0"
            messages   = @(
                @{role = "user"; content = "ping" }
            )
            max_tokens = 10
        } -TimeoutSec 15
        
        Write-Host "   Chat: " -NoNewline
        Write-ColorLine "$($chatTest.Symbol) $($chatTest.Status) ($($chatTest.ResponseTime) ms)" $chatTest.Color
    }
    else {
        Write-ColorLine "   Process: Stopped" "Yellow"
        Write-ColorLine "   -> Start: .\scripts\quick_diagnose.ps1 -StartProxy" "DarkYellow"
    }
    
    Write-Host ""
    Write-ColorLine "------------------------------------------------------------" "DarkGray"
    Write-Host ""
    
    # 2. Cloud AI (내다AI)
    Write-ColorLine "[Channel 2] Cloud AI" "White"
    Write-ColorLine "   Endpoint: https://ion-api-64076350717.us-central1.run.app/chat" "DarkGray"
    
    $cloudStatus = Get-ChannelStatus -Name "Cloud AI" -Url "https://ion-api-64076350717.us-central1.run.app/chat" -Body @{
        message = "ping"
    }
    
    Write-Host "   Status: " -NoNewline
    Write-ColorLine "$($cloudStatus.Symbol) $($cloudStatus.Status)" $cloudStatus.Color
    Write-ColorLine "   Response time: $($cloudStatus.ResponseTime) ms" "DarkGray"
    
    if ($cloudStatus.StatusCode -ne 200) {
        Write-ColorLine "   Error: $($cloudStatus.ErrorMessage)" "Red"
    }
    
    Write-Host ""
    Write-ColorLine "------------------------------------------------------------" "DarkGray"
    Write-Host ""
    
    # 3. Core Gateway
    Write-ColorLine "[Channel 3] Core Gateway" "White"
    Write-ColorLine "   Endpoint: https://Core-gateway-x4qvsargwa-uc.a.run.app/chat" "DarkGray"
    
    $CoreStatus = Get-ChannelStatus -Name "Core Gateway" -Url "https://Core-gateway-x4qvsargwa-uc.a.run.app/chat" -Body @{
        message = "ping"
    }
    
    Write-Host "   Status: " -NoNewline
    Write-ColorLine "$($CoreStatus.Symbol) $($CoreStatus.Status)" $CoreStatus.Color
    Write-ColorLine "   Response time: $($CoreStatus.ResponseTime) ms" "DarkGray"
    
    if ($CoreStatus.StatusCode -ne 200) {
        Write-ColorLine "   Error: $($CoreStatus.ErrorMessage)" "Red"
    }
    
    Write-Host ""
    Write-ColorLine "------------------------------------------------------------" "DarkGray"
    Write-Host ""
    
    # 종합 상태 및 성능 진단
    $issues = @()
    $warnings = @()

    # 로컬 상태 체크 (proxy 미동작 시 보호)
    # LM Studio는 초기화 시간으로 2-3초 소요가 정상
    $localHealthAlertMs = 4000  # LM Studio 전용 임계값 (4초)
    
    if (-not $proxyRunning) {
        $issues += "Local proxy process stopped"
    }
    elseif ($null -ne $localStatus) {
        if ($localStatus.Status -ne "Online") { $issues += "Local health offline ($($localStatus.StatusCode))" }
        elseif ($localStatus.ResponseTime -gt $localHealthAlertMs) { $issues += "ALERT: Local health latency $($localStatus.ResponseTime)ms" }
        elseif ($localStatus.ResponseTime -gt ($localHealthAlertMs * 0.75)) { $warnings += "WARN: Local health latency $($localStatus.ResponseTime)ms" }
    }
    if ($proxyRunning -and $null -ne $chatTest) {
        if ($chatTest.Status -ne "Online") { $issues += "Local chat offline ($($chatTest.StatusCode))" }
        elseif ($chatTest.ResponseTime -gt $AlertMs) { $issues += "ALERT: Local chat latency $($chatTest.ResponseTime)ms" }
        elseif ($chatTest.ResponseTime -gt $WarnMs) { $warnings += "WARN: Local chat latency $($chatTest.ResponseTime)ms" }
    }

    # 클라우드 상태 체크
    if ($cloudStatus.Status -ne "Online") { $issues += "Cloud AI offline ($($cloudStatus.StatusCode))" }
    elseif ($cloudStatus.ResponseTime -gt $AlertMs) { $issues += "ALERT: Cloud AI latency $($cloudStatus.ResponseTime)ms" }
    elseif ($cloudStatus.ResponseTime -gt $WarnMs) { $warnings += "WARN: Cloud AI latency $($cloudStatus.ResponseTime)ms" }

    if ($CoreStatus.Status -ne "Online") { $issues += "Core Gateway offline ($($CoreStatus.StatusCode))" }
    elseif ($CoreStatus.ResponseTime -gt $AlertMs) { $issues += "ALERT: Core Gateway latency $($CoreStatus.ResponseTime)ms" }
    elseif ($CoreStatus.ResponseTime -gt $WarnMs) { $warnings += "WARN: Core Gateway latency $($CoreStatus.ResponseTime)ms" }

    $hasAlerts = ($issues | Where-Object { $_ -like 'ALERT*' -or $_ -like '*offline*' }).Count -gt 0
    $hasWarns = $warnings.Count -gt 0

    $allGreen = (-not $hasAlerts -and -not $hasWarns)
    $isDegraded = $hasAlerts
    
    Write-Host "Summary: " -NoNewline
    if ($allGreen) {
        Write-ColorLine "ALL GREEN - all systems OK" "Green"
    }
    elseif ($isDegraded) {
        Write-ColorLine "ATTENTION - issues detected (see below)" "Yellow"
    }
    else {
        Write-ColorLine "WARNING - latency thresholds exceeded" "Yellow"
    }

    if ($isDegraded -or $hasWarns) {
        if ($isDegraded) {
            Write-ColorLine "Issues:" "Red"
            foreach ($i in $issues) { Write-ColorLine "   - $i" "Red" }
        }
        if ($hasWarns) {
            Write-ColorLine "Warnings:" "Yellow"
            foreach ($w in $warnings) { Write-ColorLine "   - $w" "Yellow" }
        }
    }
    
    Write-Host ""
    Write-ColorLine "------------------------------------------------------------" "DarkGray"
    Write-Host ""
    
    # 빠른 액션
    Write-ColorLine "Quick actions:" "Cyan"
    Write-ColorLine "   [1] Start proxy:    .\scripts\quick_diagnose.ps1 -StartProxy" "White"
    Write-ColorLine "   [2] Stop proxy:     .\scripts\quick_diagnose.ps1 -StopProxy" "White"
    Write-ColorLine "   [3] Full diagnose:  .\scripts\quick_diagnose.ps1" "White"
    Write-ColorLine "   [4] Python test:    .\.venv\Scripts\python.exe .\test_core_connection.py" "White"
    
    Write-Host ""
    
    if ($Watch) {
        Write-ColorLine "Refresh in $RefreshSeconds sec... (Ctrl+C to exit)" "DarkYellow"
    }
    $channels = @{
        LocalHealth  = $localStatus
        LocalChat    = $chatTest
        CloudAI      = $cloudStatus
        CoreGateway = $CoreStatus
    }

    return @{
        AllGreen   = $allGreen
        IsDegraded = $isDegraded
        HasWarns   = $hasWarns
        Issues     = $issues
        Warnings   = $warnings
        Timestamp  = $scanTime
        Thresholds = @{ WarnMs = $WarnMs; AlertMs = $AlertMs }
        Channels   = $channels
    }
}

# 메인 실행
if ($Watch) {
    while ($true) {
        $null = Show-Dashboard
        Start-Sleep -Seconds $RefreshSeconds
    }
}
else {
    $result = Show-Dashboard

    # 실패 시 슬랙 알림 (Webhook 기반 - PS 5.1 ASCII-safe)
    if ($SlackOnFailure -and ($result.IsDegraded -or (-not $result.AllGreen)) ) {
        $webhook = $env:SLACK_WEBHOOK_URL
        if ($null -ne $webhook -and $webhook.Trim().Length -gt 0) {
            try {
                $title = if ($result.IsDegraded) { "Core 대시보드 경고 (Degraded)" } else { "Core 대시보드 경고 (Latency)" }
                $msgLines = @()
                foreach ($i in $result.Issues) { $msgLines += "- $i" }
                foreach ($w in $result.Warnings) { $msgLines += "- $w" }
                $message = if ($msgLines.Count -gt 0) { ($msgLines -join "`n") } else { "세부 원인 없음" }

                $payload = @{
                    text       = "*$title*`n$message"
                    username   = "Core Dashboard"
                    icon_emoji = ":rotating_light:"
                }
                if ($SlackChannel -or $env:SLACK_ALERT_CHANNEL -or $env:SLACK_FALLBACK_CHANNEL) {
                    $payload.channel = if ($SlackChannel) { $SlackChannel } elseif ($env:SLACK_ALERT_CHANNEL) { $env:SLACK_ALERT_CHANNEL } else { $env:SLACK_FALLBACK_CHANNEL }
                }

                $json = ($payload | ConvertTo-Json -Compress)
                Invoke-RestMethod -Uri $webhook -Method POST -Body $json -ContentType "application/json" | Out-Null
            }
            catch {
                Write-Host "(Slack) Webhook send failed: $($_.Exception.Message)" -ForegroundColor Yellow
            }
        }
        else {
            Write-Host "(Slack) SLACK_WEBHOOK_URL not set; alert skipped." -ForegroundColor Yellow
        }
    }

    # JSON 내보내기 (요청 시)
    if ($OutJson -and $OutJson.Trim().Length -gt 0) {
        try {
            $export = @{
                Summary  = @{
                    AllGreen   = $result.AllGreen
                    IsDegraded = $result.IsDegraded
                    HasWarns   = $result.HasWarns
                    Issues     = $result.Issues
                    Warnings   = $result.Warnings
                    Timestamp  = $result.Timestamp
                    Thresholds = $result.Thresholds
                }
                Channels = $result.Channels
            }
            $json = $export | ConvertTo-Json -Depth 6 -Compress
            $outPath = (Resolve-Path -LiteralPath $OutJson -ErrorAction SilentlyContinue)
            if (-not $outPath) {
                $dir = Split-Path -Parent $OutJson
                if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
                $outPath = $OutJson
            }
            else { $outPath = $outPath.Path }
            [System.IO.File]::WriteAllText($outPath, $json, [System.Text.Encoding]::UTF8)
        }
        catch {
            Write-Host "(OutJson) write failed: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }

    # Markdown 내보내기 (요청 시)
    if ($OutMarkdown -and $OutMarkdown.Trim().Length -gt 0) {
        try {
            $lines = @()
            $lines += "# Core Dashboard Report"
            $lines += ""
            $lines += "Scanned: $($result.Timestamp)"
            $lines += "Thresholds: Warn=$($result.Thresholds.WarnMs) ms, Alert=$($result.Thresholds.AlertMs) ms"
            $lines += ""
            $summaryText = if ($result.AllGreen) { "ALL GREEN - all systems OK" } elseif ($result.IsDegraded) { "ATTENTION - issues detected" } else { "WARNING - latency thresholds exceeded" }
            $lines += "**Summary:** $summaryText"
            $lines += "- AllGreen: $($result.AllGreen)"
            $lines += "- Degraded: $($result.IsDegraded)"
            $lines += "- HasWarns: $($result.HasWarns)"
            $lines += ""
            $lines += "## Channels"
            foreach ($k in 'LocalHealth', 'LocalChat', 'CloudAI', 'CoreGateway') {
                $c = $result.Channels[$k]
                if ($null -ne $c) {
                    $lines += ('- {0}: Status={1}, Code={2}, Time={3} ms' -f $k, $c.Status, $c.StatusCode, $c.ResponseTime)
                }
            }
            if ($result.Issues.Count -gt 0) {
                $lines += ""
                $lines += "## Issues"
                foreach ($i in $result.Issues) { $lines += "- $i" }
            }
            if ($result.Warnings.Count -gt 0) {
                $lines += ""
                $lines += "## Warnings"
                foreach ($w in $result.Warnings) { $lines += "- $w" }
            }

            $md = $lines -join "`r`n"
            $mdPath = (Resolve-Path -LiteralPath $OutMarkdown -ErrorAction SilentlyContinue)
            if (-not $mdPath) {
                $dir = Split-Path -Parent $OutMarkdown
                if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
                $mdPath = $OutMarkdown
            }
            else { $mdPath = $mdPath.Path }
            [System.IO.File]::WriteAllText($mdPath, $md, [System.Text.Encoding]::UTF8)
        }
        catch {
            Write-Host "(OutMarkdown) write failed: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }

    if ($FailOnDegraded -and $result.IsDegraded) {
        exit 1
    }
    elseif ($FailOnWarn -and (-not $result.IsDegraded) -and $result.HasWarns) {
        exit 2
    }
}