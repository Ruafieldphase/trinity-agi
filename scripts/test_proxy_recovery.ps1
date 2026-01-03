# Core ?록???동복구 ?스???위??param(
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
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot

    Write-Host ""
    Write-Host "?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?? -ForegroundColor Cyan
    Write-Host "  TEST: $Title" -ForegroundColor Yellow
    Write-Host "?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?? -ForegroundColor Cyan
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
        Write-Host "  ?? $Message" -ForegroundColor DarkGray
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

# ?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═??# TEST 1: ?로?스 강제 종료 ???동 ?시??# ?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═??
function Test-ProcessKillRecovery {
    Write-TestHeader "?로?스 강제 종료 ???동 ?시??
    
    $results = @{
        InitialStart      = $false
        HealthCheckBefore = $false
        ProcessKill       = $false
        AutoRestart       = $false
        HealthCheckAfter  = $false
    }
    
    # 1. 초기 ?록???작
    Write-Host "[1/5] ?록??초기 ?작..." -ForegroundColor DarkGray
    & "$PSScriptRoot\quick_diagnose.ps1" -StartProxy *>$null
    Start-Sleep -Seconds 3
    
    $status = Get-ProxyStatus
    $results.InitialStart = $status.IsRunning
    Write-TestResult "?록??초기 ?작" $results.InitialStart "PID: $($status.PID)"
    
    if (-not $results.InitialStart) {
        return $results
    }
    
    # 2. ?스체크 (종료 ??
    Write-Host "[2/5] ?스체크 (종료 ??..." -ForegroundColor DarkGray
    $results.HealthCheckBefore = Test-ProxyHealth
    Write-TestResult "?스체크 (종료 ??" $results.HealthCheckBefore
    
    # 3. ?로?스 강제 종료
    Write-Host "[3/5] ?로?스 강제 종료..." -ForegroundColor DarkGray
    $beforePID = $status.PID
    $results.ProcessKill = Stop-ProxyProcess -TimeoutSeconds 10
    Write-TestResult "?로?스 강제 종료" $results.ProcessKill "?전 PID: $beforePID"
    
    Start-Sleep -Seconds 2
    
    # 4. ?동 ?시??(quick_diagnose ?행)
    Write-Host "[4/5] ?동 ?시???도..." -ForegroundColor DarkGray
    & "$PSScriptRoot\quick_diagnose.ps1" *>$null
    Start-Sleep -Seconds 3
    
    $newStatus = Get-ProxyStatus
    $results.AutoRestart = $newStatus.IsRunning
    Write-TestResult "?동 ?시?? $results.AutoRestart "??PID: $($newStatus.PID)"
    
    # 5. ?스체크 (?시????
    Write-Host "[5/5] ?스체크 (?시????..." -ForegroundColor DarkGray
    $results.HealthCheckAfter = Test-ProxyHealth
    Write-TestResult "?스체크 (?시????" $results.HealthCheckAfter
    
    # 종합 결과
    Write-Host ""
    $allPassed = $results.Values | ForEach-Object { $_ } | Where-Object { $_ -eq $false } | Measure-Object | Select-Object -ExpandProperty Count
    $overallPass = $allPassed -eq 0
    
    Write-TestResult "TEST 1 종합" $overallPass "$(5 - $allPassed)/5 ?계 ?공"
    
    return $results
}

# ?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═??# TEST 2: ?트 충돌 감? ?처리
# ?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═??
function Test-PortConflictHandling {
    Write-TestHeader "?트 충돌 감? ?처리"
    
    $results = @{
        CreateDummyServer = $false
        ConflictDetection = $false
        CleanupDummy      = $false
        NormalStart       = $false
    }
    
    # 1. ?? ?버??트 ?유
    Write-Host "[1/4] ?? ?버??트 8080 ?유..." -ForegroundColor DarkGray
    
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
    Write-TestResult "?? ?버 ?작" $results.CreateDummyServer "PID: $($portOccupied.OwningProcess)"
    
    # 2. 충돌 감? ?도
    Write-Host "[2/4] ?록???작 ?도 (충돌 ?상)..." -ForegroundColor DarkGray
    
    $startOutput = & "$PSScriptRoot\start_local_llm_proxy.ps1" 2>&1
    $conflictDetected = $startOutput -match "already in use|OSError|Address already in use"
    $results.ConflictDetection = $conflictDetected
    Write-TestResult "충돌 감?" $results.ConflictDetection
    
    # 3. ?? ?버 ?리
    Write-Host "[3/4] ?? ?버 ?리..." -ForegroundColor DarkGray
    Stop-Job -Job $dummyJob -ErrorAction SilentlyContinue
    Remove-Job -Job $dummyJob -Force -ErrorAction SilentlyContinue
    
    Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue | ForEach-Object {
        Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
    }
    
    Start-Sleep -Seconds 2
    $portCleared = $null -eq (Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue)
    $results.CleanupDummy = $portCleared
    Write-TestResult "?? ?버 ?리" $results.CleanupDummy
    
    # 4. ?상 ?작 ?인
    Write-Host "[4/4] ?록???상 ?작 ?인..." -ForegroundColor DarkGray
    & "$PSScriptRoot\quick_diagnose.ps1" -StartProxy *>$null
    Start-Sleep -Seconds 3
    
    $status = Get-ProxyStatus
    $results.NormalStart = $status.IsRunning -and (Test-ProxyHealth)
    Write-TestResult "?상 ?작" $results.NormalStart
    
    # 종합 결과
    Write-Host ""
    $allPassed = $results.Values | ForEach-Object { $_ } | Where-Object { $_ -eq $false } | Measure-Object | Select-Object -ExpandProperty Count
    $overallPass = $allPassed -eq 0
    
    Write-TestResult "TEST 2 종합" $overallPass "$(4 - $allPassed)/4 ?계 ?공"
    
    return $results
}

# ?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═??# TEST 3: venv 경로 검?# ?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═??
function Test-VenvValidation {
    Write-TestHeader "venv 경로 검?
    
    $results = @{
        VenvExists        = $false
        PythonExists      = $false
        FlaskInstalled    = $false
        RequestsInstalled = $false
    }
    
    $venvPath = "$WorkspaceRoot\LLM_Unified\.venv"
    $pythonExe = "$venvPath\Scripts\python.exe"
    
    # 1. venv ?렉?리 존재 ?인
    Write-Host "[1/4] venv ?렉?리 ?인..." -ForegroundColor DarkGray
    $results.VenvExists = Test-Path $venvPath
    Write-TestResult "venv ?렉?리" $results.VenvExists $venvPath
    
    # 2. Python ?행 ?일 ?인
    Write-Host "[2/4] Python ?행 ?일 ?인..." -ForegroundColor DarkGray
    $results.PythonExists = Test-Path $pythonExe
    Write-TestResult "Python ?행 ?일" $results.PythonExists $pythonExe
    
    if (-not $results.PythonExists) {
        return $results
    }
    
    # 3. Flask ?치 ?인
    Write-Host "[3/4] Flask ?치 ?인..." -ForegroundColor DarkGray
    $flaskCheck = & $pythonExe -c "import flask; print(flask.__version__)" 2>$null
    $results.FlaskInstalled = $LASTEXITCODE -eq 0
    Write-TestResult "Flask ?치" $results.FlaskInstalled "버전: $flaskCheck"
    
    # 4. requests ?치 ?인
    Write-Host "[4/4] requests ?치 ?인..." -ForegroundColor DarkGray
    $requestsCheck = & $pythonExe -c "import requests; print(requests.__version__)" 2>$null
    $results.RequestsInstalled = $LASTEXITCODE -eq 0
    Write-TestResult "requests ?치" $results.RequestsInstalled "버전: $requestsCheck"
    
    # 종합 결과
    Write-Host ""
    $allPassed = $results.Values | ForEach-Object { $_ } | Where-Object { $_ -eq $false } | Measure-Object | Select-Object -ExpandProperty Count
    $overallPass = $allPassed -eq 0
    
    Write-TestResult "TEST 3 종합" $overallPass "$(4 - $allPassed)/4 ?계 ?공"
    
    return $results
}

# ?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═??# TEST 4: ?록??기능 ?합 ?스??# ?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═??
function Test-ProxyFunctionality {
    Write-TestHeader "?록??기능 ?합 ?스??
    
    $results = @{
        HealthEndpoint = $false
        ChatEndpoint   = $false
        OpenAIFormat   = $false
        ResponseTime   = $false
    }
    
    # ?록???행 ?인
    $status = Get-ProxyStatus
    if (-not $status.IsRunning) {
        Write-Host "[WARN]  ?록?? ?행 중이지 ?습?다. ?작 ?.." -ForegroundColor Yellow
        & "$PSScriptRoot\quick_diagnose.ps1" -StartProxy *>$null
        Start-Sleep -Seconds 3
    }
    
    # 1. /health ?드?인??    Write-Host "[1/4] /health ?드?인???스??.." -ForegroundColor DarkGray
    try {
        $healthResponse = Invoke-RestMethod -Uri 'http://localhost:8080/health' -Method GET -TimeoutSec 5
        $results.HealthEndpoint = $healthResponse.status -eq "ok"
        Write-TestResult "/health ?드?인?? $results.HealthEndpoint "Status: $($healthResponse.status)"
    }
    catch {
        Write-TestResult "/health ?드?인?? $false $_.Exception.Message
    }
    
    # 2. /v1/chat/completions ?드?인??    Write-Host "[2/4] /v1/chat/completions ?드?인???스??.." -ForegroundColor DarkGray
    try {
        $chatBody = @{
            model      = "Core-gateway"
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
        Write-TestResult "/v1/chat/completions ?드?인?? $results.ChatEndpoint "?답?간: ${responseTime}ms"
        
        # 3. OpenAI ?맷 검?        Write-Host "[3/4] OpenAI ?답 ?맷 검?.." -ForegroundColor DarkGray
        $hasId = $null -ne $chatResponse.id
        $hasChoices = $null -ne $chatResponse.choices
        $hasUsage = $null -ne $chatResponse.usage
        $results.OpenAIFormat = $hasId -and $hasChoices -and $hasUsage
        Write-TestResult "OpenAI ?맷" $results.OpenAIFormat "id: $hasId, choices: $hasChoices, usage: $hasUsage"
        
        # 4. ?답 ?간 검?(< 10?
        Write-Host "[4/4] ?답 ?간 검?.." -ForegroundColor DarkGray
        $results.ResponseTime = $responseTime -lt 10000
        Write-TestResult "?답 ?간 (< 10s)" $results.ResponseTime "${responseTime}ms"
        
    }
    catch {
        Write-TestResult "/v1/chat/completions ?드?인?? $false $_.Exception.Message
        Write-TestResult "OpenAI ?맷" $false "?전 ?계 ?패"
        Write-TestResult "?답 ?간" $false "?전 ?계 ?패"
    }
    
    # 종합 결과
    Write-Host ""
    $allPassed = $results.Values | ForEach-Object { $_ } | Where-Object { $_ -eq $false } | Measure-Object | Select-Object -ExpandProperty Count
    $overallPass = $allPassed -eq 0
    
    Write-TestResult "TEST 4 종합" $overallPass "$(4 - $allPassed)/4 ?계 ?공"
    
    return $results
}

# ?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═??# 메인 ?행
# ?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═??
Write-Host ""
Write-Host "?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?╗" -ForegroundColor Cyan
Write-Host "??  Core ?록???동복구 ?스???위??                      ?? -ForegroundColor Cyan
Write-Host "?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "?작 ?각: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Yellow
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
    Write-Host "[WARN]  ?스?? ?택?? ?았?니??" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "?용 가?한 ?션:" -ForegroundColor Cyan
    Write-Host "  -TestProcessKill     : ?로?스 강제 종료 복구 ?스?? -ForegroundColor White
    Write-Host "  -TestPortConflict    : ?트 충돌 처리 ?스?? -ForegroundColor White
    Write-Host "  -TestVenvMissing     : venv 경로 검??스?? -ForegroundColor White
    Write-Host "  -TestAllScenarios    : 모든 ?스???행" -ForegroundColor White
    Write-Host ""
    Write-Host "?시:" -ForegroundColor Cyan
    Write-Host "  .\scripts\test_proxy_recovery.ps1 -TestAllScenarios" -ForegroundColor DarkGray
    Write-Host ""
    exit 0
}

# 최종 ?약
Write-Host ""
Write-Host "?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?? -ForegroundColor Cyan
Write-Host "  최종 ?약" -ForegroundColor Yellow
Write-Host "?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?═?? -ForegroundColor Cyan
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
Write-Host "?체: $passedTests/$totalTests ($overallPercentage%)" -ForegroundColor $(if ($passedTests -eq $totalTests) { "Green" } else { "Yellow" })

Write-Host ""
Write-Host "?료 ?각: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Yellow
Write-Host ""

# Exit code
if ($passedTests -eq $totalTests) {
    exit 0
}
else {
    exit 1
}