# 猷⑤찘 ?섏씠釉뚮━???쒖뒪???듯빀 ??쒕낫??
param(
    [switch]$Watch,
    [int]$RefreshSeconds = 5
)

$ErrorActionPreference = "Continue"

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
        Symbol       = "??
    }
    
    try {
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
        
        if ($Body.Count -gt 0) {
            $bodyJson = $Body | ConvertTo-Json -Compress
            $response = Invoke-RestMethod -Uri $Url -Method POST -Body $bodyJson -ContentType "application/json" -Headers $Headers -TimeoutSec $TimeoutSec -ErrorAction Stop
        }
        else {
            $response = Invoke-RestMethod -Uri $Url -Method GET -Headers $Headers -TimeoutSec $TimeoutSec -ErrorAction Stop
        }
        
        $stopwatch.Stop()
        
        $status.Status = "Online"
        $status.StatusCode = 200
        $status.ResponseTime = [math]::Round($stopwatch.Elapsed.TotalMilliseconds)
        $status.Color = "Green"
        $status.Symbol = "?윟"
        
    }
    catch {
        $stopwatch.Stop()
        $status.Status = "Offline"
        $status.StatusCode = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode.value__ } else { 0 }
        $status.ResponseTime = [math]::Round($stopwatch.Elapsed.TotalMilliseconds)
        $status.ErrorMessage = $_.Exception.Message
        $status.Color = "Red"
        $status.Symbol = "?뵶"
    }
    
    return $status
}

function Show-Dashboard {
    Clear-Host
    
    Write-Host ""
    Write-ColorLine "?붴븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븮" "Cyan"
    Write-ColorLine "??       猷⑤찘 ?섏씠釉뚮━???쒖뒪???듯빀 ??쒕낫??               ?? "Cyan"
    Write-ColorLine "?싢븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븴" "Cyan"
    Write-Host ""
    Write-ColorLine "?ㅼ틪 ?쒓컖: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" "Yellow"
    Write-Host ""
    
    # 濡쒖뺄 ?꾨줉???꾨줈?몄뒪 泥댄겕
    $proxyProcess = Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue
    $proxyRunning = $null -ne $proxyProcess
    
    Write-ColorLine "?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺" "DarkGray"
    Write-Host ""
    
    # 1. 濡쒖뺄 LLM ?꾨줉??
    Write-ColorLine "?뱧 梨꾨꼸 1: 濡쒖뺄 LLM ?꾨줉?? "White"
    Write-ColorLine "   ?붾뱶?ъ씤?? http://localhost:8080/v1/chat/completions" "DarkGray"
    
    if ($proxyRunning) {
        Write-ColorLine "   ?꾨줈?몄뒪: ?ㅽ뻾 以?(PID: $($proxyProcess.OwningProcess))" "DarkGreen"
        
        $localStatus = Get-ChannelStatus -Name "Local Proxy Health" -Url "http://localhost:8080/health"
        Write-Host "   ?곹깭: " -NoNewline
        Write-ColorLine "$($localStatus.Symbol) $($localStatus.Status)" $localStatus.Color
        Write-ColorLine "   ?묐떟?쒓컙: $($localStatus.ResponseTime)ms" "DarkGray"
        
        # ?ㅼ젣 梨꾪똿 ?뚯뒪??
        $chatTest = Get-ChannelStatus -Name "Local Proxy Chat" -Url "http://localhost:8080/v1/chat/completions" -Body @{
            model      = "lumen-gateway"
            messages   = @(
                @{role = "user"; content = "ping" }
            )
            max_tokens = 10
        } -TimeoutSec 15
        
        Write-Host "   梨꾪똿: " -NoNewline
        Write-ColorLine "$($chatTest.Symbol) $($chatTest.Status) ($($chatTest.ResponseTime)ms)" $chatTest.Color
    }
    else {
        Write-ColorLine "   ?꾨줈?몄뒪: ?좑툘  以묒??? "Yellow"
        Write-ColorLine "   ???쒖옉: .\scripts\quick_diagnose.ps1 -StartProxy" "DarkYellow"
    }
    
    Write-Host ""
    Write-ColorLine "?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺" "DarkGray"
    Write-Host ""
    
    # 2. Cloud AI (?대떎AI)
    Write-ColorLine "?뱧 梨꾨꼸 2: Cloud AI (?대떎AI)" "White"
    Write-ColorLine "   ?붾뱶?ъ씤?? https://ion-api-64076350717.us-central1.run.app/chat" "DarkGray"
    
    $cloudStatus = Get-ChannelStatus -Name "Cloud AI" -Url "https://ion-api-64076350717.us-central1.run.app/chat" -Body @{
        message = "ping"
    }
    
    Write-Host "   ?곹깭: " -NoNewline
    Write-ColorLine "$($cloudStatus.Symbol) $($cloudStatus.Status)" $cloudStatus.Color
    Write-ColorLine "   ?묐떟?쒓컙: $($cloudStatus.ResponseTime)ms" "DarkGray"
    
    if ($cloudStatus.StatusCode -ne 200) {
        Write-ColorLine "   ?ㅻ쪟: $($cloudStatus.ErrorMessage)" "Red"
    }
    
    Write-Host ""
    Write-ColorLine "?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺" "DarkGray"
    Write-Host ""
    
    # 3. Lumen Gateway
    Write-ColorLine "?뱧 梨꾨꼸 3: Lumen Gateway" "White"
    Write-ColorLine "   ?붾뱶?ъ씤?? https://lumen-gateway-x4qvsargwa-uc.a.run.app/chat" "DarkGray"
    
    $lumenStatus = Get-ChannelStatus -Name "Lumen Gateway" -Url "https://lumen-gateway-x4qvsargwa-uc.a.run.app/chat" -Body @{
        message = "ping"
    }
    
    Write-Host "   ?곹깭: " -NoNewline
    Write-ColorLine "$($lumenStatus.Symbol) $($lumenStatus.Status)" $lumenStatus.Color
    Write-ColorLine "   ?묐떟?쒓컙: $($lumenStatus.ResponseTime)ms" "DarkGray"
    
    if ($lumenStatus.StatusCode -ne 200) {
        Write-ColorLine "   ?ㅻ쪟: $($lumenStatus.ErrorMessage)" "Red"
    }
    
    Write-Host ""
    Write-ColorLine "?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺" "DarkGray"
    Write-Host ""
    
    # 醫낇빀 ?곹깭
    $allGreen = ($proxyRunning -and $localStatus.Status -eq "Online" -and $chatTest.Status -eq "Online" -and 
        $cloudStatus.Status -eq "Online" -and $lumenStatus.Status -eq "Online")
    
    Write-Host "?뱤 醫낇빀 ?곹깭: " -NoNewline
    if ($allGreen) {
        Write-ColorLine "?윟 ALL GREEN - 紐⑤뱺 ?쒖뒪???뺤긽" "Green"
    }
    else {
        Write-ColorLine "?좑툘  ?쇰? ?쒖뒪???먭? ?꾩슂" "Yellow"
    }
    
    Write-Host ""
    Write-ColorLine "?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺" "DarkGray"
    Write-Host ""
    
    # 鍮좊Ⅸ ?≪뀡
    Write-ColorLine "?뵩 鍮좊Ⅸ ?≪뀡:" "Cyan"
    Write-ColorLine "   [1] ?꾨줉???쒖옉:    .\scripts\quick_diagnose.ps1 -StartProxy" "White"
    Write-ColorLine "   [2] ?꾨줉??以묒?:    .\scripts\quick_diagnose.ps1 -StopProxy" "White"
    Write-ColorLine "   [3] ?꾩껜 吏꾨떒:      .\scripts\quick_diagnose.ps1" "White"
    Write-ColorLine "   [4] Python ?뚯뒪??  .\.venv\Scripts\python.exe .\test_lumen_connection.py" "White"
    
    Write-Host ""
    
    if ($Watch) {
        Write-ColorLine "?깍툘  $RefreshSeconds 珥????덈줈怨좎묠... (Ctrl+C濡?醫낅즺)" "DarkYellow"
    }
}

# 硫붿씤 ?ㅽ뻾
if ($Watch) {
    while ($true) {
        Show-Dashboard
        Start-Sleep -Seconds $RefreshSeconds
    }
}
else {
    Show-Dashboard
}
