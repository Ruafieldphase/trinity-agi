# ë£¨ë©˜ ?„ë¡???ë™ë³µêµ¬ ?ŒìŠ¤???¤ìœ„??param(
    [switch]$TestPortConflict,
    [switch]$TestProcessKill,
    [switch]$TestVenvMissing,
    [switch]$TestFlaskMissing,
    [switch]$TestAllScenarios,
    [switch]$Verbose
)

$ErrorActionPreference = "Continue"

function Write-TestHeader {
    param([string]$Title)
    Write-Host ""
    Write-Host "?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?? -ForegroundColor Cyan
    Write-Host "  TEST: $Title" -ForegroundColor Yellow
    Write-Host "?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?? -ForegroundColor Cyan
    Write-Host ""
}

function Write-TestResult {
    param(
        [string]$TestName,
        [bool]$Passed,
        [string]$Message = ""
    )
    
    $symbol = if ($Passed) { "?? } else { "?? }
    $color = if ($Passed) { "Green" } else { "Red" }
    
    Write-Host "$symbol $TestName" -ForegroundColor $color
    if ($Message) {
        Write-Host "  ?”â? $Message" -ForegroundColor DarkGray
    }
}

function Get-ProxyStatus {
    $connection = Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue
    return @{
        IsRunning = $null -ne $connection
        PID       = if ($connection) { $connection.OwningProcess } else { $null }
    }
}

function Test-ProxyHealth {
    try {
        $response = Invoke-RestMethod -Uri 'http://localhost:8080/health' -Method GET -TimeoutSec 5 -ErrorAction Stop
        return $response.status -eq "ok"
    }
    catch {
        return $false
    }
}

function Stop-ProxyProcess {
    param([int]$TimeoutSeconds = 10)
    
    $status = Get-ProxyStatus
    if (-not $status.IsRunning) {
        return $true
    }
    
    try {
        Stop-Process -Id $status.PID -Force -ErrorAction Stop
        
        # Wait for port to be released
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
        while ($stopwatch.Elapsed.TotalSeconds -lt $TimeoutSeconds) {
            Start-Sleep -Milliseconds 500
            $newStatus = Get-ProxyStatus
            if (-not $newStatus.IsRunning) {
                return $true
            }
        }
        
        return $false
    }
    catch {
        return $false
    }
}

# ?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•??# TEST 1: ?„ë¡œ?¸ìŠ¤ ê°•ì œ ì¢…ë£Œ ???ë™ ?¬ì‹œ??# ?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•??
function Test-ProcessKillRecovery {
    Write-TestHeader "?„ë¡œ?¸ìŠ¤ ê°•ì œ ì¢…ë£Œ ???ë™ ?¬ì‹œ??
    
    $results = @{
        InitialStart      = $false
        HealthCheckBefore = $false
        ProcessKill       = $false
        AutoRestart       = $false
        HealthCheckAfter  = $false
    }
    
    # 1. ì´ˆê¸° ?„ë¡???œì‘
    Write-Host "[1/5] ?„ë¡??ì´ˆê¸° ?œì‘..." -ForegroundColor DarkGray
    & "$PSScriptRoot\quick_diagnose.ps1" -StartProxy *>$null
    Start-Sleep -Seconds 3
    
    $status = Get-ProxyStatus
    $results.InitialStart = $status.IsRunning
    Write-TestResult "?„ë¡??ì´ˆê¸° ?œì‘" $results.InitialStart "PID: $($status.PID)"
    
    if (-not $results.InitialStart) {
        return $results
    }
    
    # 2. ?¬ìŠ¤ì²´í¬ (ì¢…ë£Œ ??
    Write-Host "[2/5] ?¬ìŠ¤ì²´í¬ (ì¢…ë£Œ ??..." -ForegroundColor DarkGray
    $results.HealthCheckBefore = Test-ProxyHealth
    Write-TestResult "?¬ìŠ¤ì²´í¬ (ì¢…ë£Œ ??" $results.HealthCheckBefore
    
    # 3. ?„ë¡œ?¸ìŠ¤ ê°•ì œ ì¢…ë£Œ
    Write-Host "[3/5] ?„ë¡œ?¸ìŠ¤ ê°•ì œ ì¢…ë£Œ..." -ForegroundColor DarkGray
    $beforePID = $status.PID
    $results.ProcessKill = Stop-ProxyProcess -TimeoutSeconds 10
    Write-TestResult "?„ë¡œ?¸ìŠ¤ ê°•ì œ ì¢…ë£Œ" $results.ProcessKill "?´ì „ PID: $beforePID"
    
    Start-Sleep -Seconds 2
    
    # 4. ?ë™ ?¬ì‹œ??(quick_diagnose ?¤í–‰)
    Write-Host "[4/5] ?ë™ ?¬ì‹œ???œë„..." -ForegroundColor DarkGray
    & "$PSScriptRoot\quick_diagnose.ps1" *>$null
    Start-Sleep -Seconds 3
    
    $newStatus = Get-ProxyStatus
    $results.AutoRestart = $newStatus.IsRunning
    Write-TestResult "?ë™ ?¬ì‹œ?? $results.AutoRestart "??PID: $($newStatus.PID)"
    
    # 5. ?¬ìŠ¤ì²´í¬ (?¬ì‹œ????
    Write-Host "[5/5] ?¬ìŠ¤ì²´í¬ (?¬ì‹œ????..." -ForegroundColor DarkGray
    $results.HealthCheckAfter = Test-ProxyHealth
    Write-TestResult "?¬ìŠ¤ì²´í¬ (?¬ì‹œ????" $results.HealthCheckAfter
    
    # ì¢…í•© ê²°ê³¼
    Write-Host ""
    $allPassed = $results.Values | ForEach-Object { $_ } | Where-Object { $_ -eq $false } | Measure-Object | Select-Object -ExpandProperty Count
    $overallPass = $allPassed -eq 0
    
    Write-TestResult "TEST 1 ì¢…í•©" $overallPass "$(5 - $allPassed)/5 ?¨ê³„ ?±ê³µ"
    
    return $results
}

# ?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•??# TEST 2: ?¬íŠ¸ ì¶©ëŒ ê°ì? ë°?ì²˜ë¦¬
# ?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•??
function Test-PortConflictHandling {
    Write-TestHeader "?¬íŠ¸ ì¶©ëŒ ê°ì? ë°?ì²˜ë¦¬"
    
    $results = @{
        CreateDummyServer = $false
        ConflictDetection = $false
        CleanupDummy      = $false
        NormalStart       = $false
    }
    
    # 1. ?”ë? ?œë²„ë¡??¬íŠ¸ ?ìœ 
    Write-Host "[1/4] ?”ë? ?œë²„ë¡??¬íŠ¸ 8080 ?ìœ ..." -ForegroundColor DarkGray
    
    # Stop existing proxy first
    Stop-ProxyProcess *>$null
    Start-Sleep -Seconds 2
    
    $dummyJob = Start-Job -ScriptBlock {
        $listener = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Any, 8080)
        $listener.Start()
        Write-Output "Dummy server started on port 8080"
        Start-Sleep -Seconds 30
        $listener.Stop()
    }
    
    Start-Sleep -Seconds 2
    $portOccupied = Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue
    $results.CreateDummyServer = $null -ne $portOccupied
    Write-TestResult "?”ë? ?œë²„ ?œì‘" $results.CreateDummyServer "PID: $($portOccupied.OwningProcess)"
    
    # 2. ì¶©ëŒ ê°ì? ?œë„
    Write-Host "[2/4] ?„ë¡???œì‘ ?œë„ (ì¶©ëŒ ?ˆìƒ)..." -ForegroundColor DarkGray
    
    $startOutput = & "$PSScriptRoot\start_local_llm_proxy.ps1" 2>&1
    $conflictDetected = $startOutput -match "already in use|OSError|Address already in use"
    $results.ConflictDetection = $conflictDetected
    Write-TestResult "ì¶©ëŒ ê°ì?" $results.ConflictDetection
    
    # 3. ?”ë? ?œë²„ ?•ë¦¬
    Write-Host "[3/4] ?”ë? ?œë²„ ?•ë¦¬..." -ForegroundColor DarkGray
    Stop-Job -Job $dummyJob -ErrorAction SilentlyContinue
    Remove-Job -Job $dummyJob -Force -ErrorAction SilentlyContinue
    
    Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue | ForEach-Object {
        Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
    }
    
    Start-Sleep -Seconds 2
    $portCleared = $null -eq (Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue)
    $results.CleanupDummy = $portCleared
    Write-TestResult "?”ë? ?œë²„ ?•ë¦¬" $results.CleanupDummy
    
    # 4. ?•ìƒ ?œì‘ ?•ì¸
    Write-Host "[4/4] ?„ë¡???•ìƒ ?œì‘ ?•ì¸..." -ForegroundColor DarkGray
    & "$PSScriptRoot\quick_diagnose.ps1" -StartProxy *>$null
    Start-Sleep -Seconds 3
    
    $status = Get-ProxyStatus
    $results.NormalStart = $status.IsRunning -and (Test-ProxyHealth)
    Write-TestResult "?•ìƒ ?œì‘" $results.NormalStart
    
    # ì¢…í•© ê²°ê³¼
    Write-Host ""
    $allPassed = $results.Values | ForEach-Object { $_ } | Where-Object { $_ -eq $false } | Measure-Object | Select-Object -ExpandProperty Count
    $overallPass = $allPassed -eq 0
    
    Write-TestResult "TEST 2 ì¢…í•©" $overallPass "$(4 - $allPassed)/4 ?¨ê³„ ?±ê³µ"
    
    return $results
}

# ?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•??# TEST 3: venv ê²½ë¡œ ê²€ì¦?# ?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•??
function Test-VenvValidation {
    Write-TestHeader "venv ê²½ë¡œ ê²€ì¦?
    
    $results = @{
        VenvExists        = $false
        PythonExists      = $false
        FlaskInstalled    = $false
        RequestsInstalled = $false
    }
    
    $venvPath = "C:\workspace\agi\LLM_Unified\.venv"
    $pythonExe = "$venvPath\Scripts\python.exe"
    
    # 1. venv ?”ë ‰? ë¦¬ ì¡´ì¬ ?•ì¸
    Write-Host "[1/4] venv ?”ë ‰? ë¦¬ ?•ì¸..." -ForegroundColor DarkGray
    $results.VenvExists = Test-Path $venvPath
    Write-TestResult "venv ?”ë ‰? ë¦¬" $results.VenvExists $venvPath
    
    # 2. Python ?¤í–‰ ?Œì¼ ?•ì¸
    Write-Host "[2/4] Python ?¤í–‰ ?Œì¼ ?•ì¸..." -ForegroundColor DarkGray
    $results.PythonExists = Test-Path $pythonExe
    Write-TestResult "Python ?¤í–‰ ?Œì¼" $results.PythonExists $pythonExe
    
    if (-not $results.PythonExists) {
        return $results
    }
    
    # 3. Flask ?¤ì¹˜ ?•ì¸
    Write-Host "[3/4] Flask ?¤ì¹˜ ?•ì¸..." -ForegroundColor DarkGray
    $flaskCheck = & $pythonExe -c "import flask; print(flask.__version__)" 2>$null
    $results.FlaskInstalled = $LASTEXITCODE -eq 0
    Write-TestResult "Flask ?¤ì¹˜" $results.FlaskInstalled "ë²„ì „: $flaskCheck"
    
    # 4. requests ?¤ì¹˜ ?•ì¸
    Write-Host "[4/4] requests ?¤ì¹˜ ?•ì¸..." -ForegroundColor DarkGray
    $requestsCheck = & $pythonExe -c "import requests; print(requests.__version__)" 2>$null
    $results.RequestsInstalled = $LASTEXITCODE -eq 0
    Write-TestResult "requests ?¤ì¹˜" $results.RequestsInstalled "ë²„ì „: $requestsCheck"
    
    # ì¢…í•© ê²°ê³¼
    Write-Host ""
    $allPassed = $results.Values | ForEach-Object { $_ } | Where-Object { $_ -eq $false } | Measure-Object | Select-Object -ExpandProperty Count
    $overallPass = $allPassed -eq 0
    
    Write-TestResult "TEST 3 ì¢…í•©" $overallPass "$(4 - $allPassed)/4 ?¨ê³„ ?±ê³µ"
    
    return $results
}

# ?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•??# TEST 4: ?„ë¡??ê¸°ëŠ¥ ?µí•© ?ŒìŠ¤??# ?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•??
function Test-ProxyFunctionality {
    Write-TestHeader "?„ë¡??ê¸°ëŠ¥ ?µí•© ?ŒìŠ¤??
    
    $results = @{
        HealthEndpoint = $false
        ChatEndpoint   = $false
        OpenAIFormat   = $false
        ResponseTime   = $false
    }
    
    # ?„ë¡???¤í–‰ ?•ì¸
    $status = Get-ProxyStatus
    if (-not $status.IsRunning) {
        Write-Host "[WARN]  ?„ë¡?œê? ?¤í–‰ ì¤‘ì´ì§€ ?ŠìŠµ?ˆë‹¤. ?œì‘ ì¤?.." -ForegroundColor Yellow
        & "$PSScriptRoot\quick_diagnose.ps1" -StartProxy *>$null
        Start-Sleep -Seconds 3
    }
    
    # 1. /health ?”ë“œ?¬ì¸??    Write-Host "[1/4] /health ?”ë“œ?¬ì¸???ŒìŠ¤??.." -ForegroundColor DarkGray
    try {
        $healthResponse = Invoke-RestMethod -Uri 'http://localhost:8080/health' -Method GET -TimeoutSec 5
        $results.HealthEndpoint = $healthResponse.status -eq "ok"
        Write-TestResult "/health ?”ë“œ?¬ì¸?? $results.HealthEndpoint "Status: $($healthResponse.status)"
    }
    catch {
        Write-TestResult "/health ?”ë“œ?¬ì¸?? $false $_.Exception.Message
    }
    
    # 2. /v1/chat/completions ?”ë“œ?¬ì¸??    Write-Host "[2/4] /v1/chat/completions ?”ë“œ?¬ì¸???ŒìŠ¤??.." -ForegroundColor DarkGray
    try {
        $chatBody = @{
            model      = "lumen-gateway"
            messages   = @(
                @{role = "user"; content = "ping" }
            )
            max_tokens = 10
        } | ConvertTo-Json
        
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
        $chatResponse = Invoke-RestMethod -Uri 'http://localhost:8080/v1/chat/completions' `
            -Method POST `
            -Body $chatBody `
            -ContentType "application/json" `
            -TimeoutSec 15
        $stopwatch.Stop()
        
        $results.ChatEndpoint = $chatResponse.choices.Count -gt 0
        $responseTime = [math]::Round($stopwatch.Elapsed.TotalMilliseconds)
        Write-TestResult "/v1/chat/completions ?”ë“œ?¬ì¸?? $results.ChatEndpoint "?‘ë‹µ?œê°„: ${responseTime}ms"
        
        # 3. OpenAI ?¬ë§· ê²€ì¦?        Write-Host "[3/4] OpenAI ?‘ë‹µ ?¬ë§· ê²€ì¦?.." -ForegroundColor DarkGray
        $hasId = $null -ne $chatResponse.id
        $hasChoices = $null -ne $chatResponse.choices
        $hasUsage = $null -ne $chatResponse.usage
        $results.OpenAIFormat = $hasId -and $hasChoices -and $hasUsage
        Write-TestResult "OpenAI ?¬ë§·" $results.OpenAIFormat "id: $hasId, choices: $hasChoices, usage: $hasUsage"
        
        # 4. ?‘ë‹µ ?œê°„ ê²€ì¦?(< 10ì´?
        Write-Host "[4/4] ?‘ë‹µ ?œê°„ ê²€ì¦?.." -ForegroundColor DarkGray
        $results.ResponseTime = $responseTime -lt 10000
        Write-TestResult "?‘ë‹µ ?œê°„ (< 10s)" $results.ResponseTime "${responseTime}ms"
        
    }
    catch {
        Write-TestResult "/v1/chat/completions ?”ë“œ?¬ì¸?? $false $_.Exception.Message
        Write-TestResult "OpenAI ?¬ë§·" $false "?´ì „ ?¨ê³„ ?¤íŒ¨"
        Write-TestResult "?‘ë‹µ ?œê°„" $false "?´ì „ ?¨ê³„ ?¤íŒ¨"
    }
    
    # ì¢…í•© ê²°ê³¼
    Write-Host ""
    $allPassed = $results.Values | ForEach-Object { $_ } | Where-Object { $_ -eq $false } | Measure-Object | Select-Object -ExpandProperty Count
    $overallPass = $allPassed -eq 0
    
    Write-TestResult "TEST 4 ì¢…í•©" $overallPass "$(4 - $allPassed)/4 ?¨ê³„ ?±ê³µ"
    
    return $results
}

# ?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•??# ë©”ì¸ ?¤í–‰
# ?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•??
Write-Host ""
Write-Host "?”â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•—" -ForegroundColor Cyan
Write-Host "??  ë£¨ë©˜ ?„ë¡???ë™ë³µêµ¬ ?ŒìŠ¤???¤ìœ„??                      ?? -ForegroundColor Cyan
Write-Host "?šâ•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•" -ForegroundColor Cyan
Write-Host ""
Write-Host "?œì‘ ?œê°: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Yellow
Write-Host ""

$allResults = @{}

if ($TestProcessKill -or $TestAllScenarios) {
    $allResults["ProcessKill"] = Test-ProcessKillRecovery
}

if ($TestPortConflict -or $TestAllScenarios) {
    $allResults["PortConflict"] = Test-PortConflictHandling
}

if ($TestVenvMissing -or $TestAllScenarios) {
    $allResults["VenvValidation"] = Test-VenvValidation
}

if ($TestAllScenarios) {
    $allResults["Functionality"] = Test-ProxyFunctionality
}

# No tests selected
if ($allResults.Count -eq 0) {
    Write-Host "[WARN]  ?ŒìŠ¤?¸ê? ? íƒ?˜ì? ?Šì•˜?µë‹ˆ??" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "?¬ìš© ê°€?¥í•œ ?µì…˜:" -ForegroundColor Cyan
    Write-Host "  -TestProcessKill     : ?„ë¡œ?¸ìŠ¤ ê°•ì œ ì¢…ë£Œ ë³µêµ¬ ?ŒìŠ¤?? -ForegroundColor White
    Write-Host "  -TestPortConflict    : ?¬íŠ¸ ì¶©ëŒ ì²˜ë¦¬ ?ŒìŠ¤?? -ForegroundColor White
    Write-Host "  -TestVenvMissing     : venv ê²½ë¡œ ê²€ì¦??ŒìŠ¤?? -ForegroundColor White
    Write-Host "  -TestAllScenarios    : ëª¨ë“  ?ŒìŠ¤???¤í–‰" -ForegroundColor White
    Write-Host ""
    Write-Host "?ˆì‹œ:" -ForegroundColor Cyan
    Write-Host "  .\scripts\test_proxy_recovery.ps1 -TestAllScenarios" -ForegroundColor DarkGray
    Write-Host ""
    exit 0
}

# ìµœì¢… ?”ì•½
Write-Host ""
Write-Host "?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?? -ForegroundColor Cyan
Write-Host "  ìµœì¢… ?”ì•½" -ForegroundColor Yellow
Write-Host "?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?? -ForegroundColor Cyan
Write-Host ""

$totalTests = 0
$passedTests = 0

foreach ($testName in $allResults.Keys) {
    $testResults = $allResults[$testName]
    $testTotal = $testResults.Values.Count
    $testPassed = ($testResults.Values | Where-Object { $_ -eq $true }).Count
    
    $totalTests += $testTotal
    $passedTests += $testPassed
    
    $percentage = [math]::Round(($testPassed / $testTotal) * 100)
    $symbol = if ($testPassed -eq $testTotal) { "?? } else { "[WARN]" }
    $color = if ($testPassed -eq $testTotal) { "Green" } else { "Yellow" }
    
    Write-Host "$symbol $testName : $testPassed/$testTotal ($percentage%)" -ForegroundColor $color
}

Write-Host ""
$overallPercentage = [math]::Round(($passedTests / $totalTests) * 100)
Write-Host "?„ì²´: $passedTests/$totalTests ($overallPercentage%)" -ForegroundColor $(if ($passedTests -eq $totalTests) { "Green" } else { "Yellow" })

Write-Host ""
Write-Host "?„ë£Œ ?œê°: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Yellow
Write-Host ""

# Exit code
if ($passedTests -eq $totalTests) {
    exit 0
}
else {
    exit 1
}
