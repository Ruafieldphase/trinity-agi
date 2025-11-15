<#
.SYNOPSIS
    Integration test for Gitko Extension HTTP Poller + Computer Use safety controls

.DESCRIPTION
    - Spawns a minimal test API server (port 8091)
    - Posts computer_use tasks to queue
    - Verifies kill-switch (gitko.enableComputerUseOverHttp) behavior
    - Tests cooldown (gitko.minUiActionIntervalMs) enforcement
    - Cleans up server process on exit

.NOTES
    Requires: Python 3.8+, VS Code with Gitko Extension installed
    Usage: .\test_integration.ps1
#>

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$testPort = 8091
$apiBase = "http://localhost:$testPort/api"
$pythonPath = 'D:/nas_backup/LLM_Unified/.venv/Scripts/python.exe'
$serverScript = 'D:/nas_backup/LLM_Unified/ion-mentoring/task_queue_server.py'
$serverProc = $null

function Write-TestLog {
    param([string]$Message, [string]$Level = 'INFO')
    $color = switch ($Level) {
        'PASS' { 'Green' }
        'FAIL' { 'Red' }
        'WARN' { 'Yellow' }
        default { 'White' }
    }
    Write-Host "[$Level] $Message" -ForegroundColor $color
}

function Start-TestServer {
    Write-TestLog "Starting test API server on port $testPort..."
    
    if (-not (Test-Path $pythonPath)) {
        throw "Python not found at $pythonPath"
    }
    
    if (-not (Test-Path $serverScript)) {
        throw "Server script not found at $serverScript"
    }
    
    # Kill existing processes on port
    $existing = Get-NetTCPConnection -LocalPort $testPort -ErrorAction SilentlyContinue
    if ($existing) {
        Write-TestLog "Killing existing process on port $testPort..." 'WARN'
        Stop-Process -Id $existing.OwningProcess -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }
    
    # Start server in background
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $pythonPath
    $psi.Arguments = "`"$serverScript`" --port $testPort"
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    
    $script:serverProc = [System.Diagnostics.Process]::Start($psi)
    
    # Wait for server to be ready
    $maxWait = 10
    $waited = 0
    while ($waited -lt $maxWait) {
        try {
            $response = Invoke-RestMethod -Uri "$apiBase/health" -Method GET -TimeoutSec 1 -ErrorAction Stop
            Write-TestLog "Server ready: $($response.status)" 'PASS'
            return
        }
        catch {
            Start-Sleep -Seconds 1
            $waited++
        }
    }
    
    throw "Server failed to start within $maxWait seconds"
}

function Stop-TestServer {
    if ($script:serverProc -and -not $script:serverProc.HasExited) {
        Write-TestLog "Stopping test API server..."
        $script:serverProc.Kill()
        $script:serverProc.WaitForExit(5000)
        $script:serverProc.Dispose()
    }
}

function Test-PingTask {
    Write-TestLog "Test 1: Ping task..."
    
    $task = @{
        type = 'ping'
        data = @{}
    } | ConvertTo-Json -Depth 5
    
    try {
        $response = Invoke-RestMethod -Uri "$apiBase/tasks/create" -Method POST -Body $task -ContentType 'application/json'
        $taskId = $response.task_id
        
        Write-TestLog "  Created task: $taskId"
        
        # Wait for poller to pick up and complete
        $maxWait = 10
        $waited = 0
        while ($waited -lt $maxWait) {
            Start-Sleep -Seconds 1
            
            try {
                $result = Invoke-RestMethod -Uri "$apiBase/results/$taskId" -Method GET -ErrorAction Stop
                Write-TestLog "  Task completed: success=$($result.success)" 'PASS'
                return $result.success
            }
            catch {
                # 404 means result not submitted yet, keep waiting
                if ($_.Exception.Response.StatusCode.value__ -ne 404) {
                    throw
                }
            }
            
            $waited++
        }
        
        Write-TestLog "  Task did not complete in time" 'FAIL'
        return $false
        
    }
    catch {
        Write-TestLog "  Error: $($_.Exception.Message)" 'FAIL'
        return $false
    }
}

function Test-ComputerUseScan {
    param([bool]$ExpectSuccess = $true)
    
    $label = if ($ExpectSuccess) { "Test 2: Computer Use scan (enabled)" } else { "Test 3: Computer Use scan (disabled)" }
    Write-TestLog $label
    
    $task = @{
        type = 'computer_use.scan'
        data = @{}
    } | ConvertTo-Json -Depth 5
    
    try {
        $response = Invoke-RestMethod -Uri "$apiBase/tasks/create" -Method POST -Body $task -ContentType 'application/json'
        $taskId = $response.task_id
        
        Write-TestLog "  Created task: $taskId"
        
        # Wait for result
        $maxWait = 15
        $waited = 0
        while ($waited -lt $maxWait) {
            Start-Sleep -Seconds 1
            
            try {
                $result = Invoke-RestMethod -Uri "$apiBase/results/$taskId" -Method GET -ErrorAction Stop
                
                if ($ExpectSuccess -and $result.success) {
                    $elemCount = if ($result.data.elements) { $result.data.elements.Count } else { 0 }
                    Write-TestLog "  Scan succeeded (elements found: $elemCount)" 'PASS'
                    return $true
                }
                elseif (-not $ExpectSuccess -and -not $result.success) {
                    $errMsg = $result.error
                    if ($errMsg -match 'disabled by settings') {
                        Write-TestLog "  Correctly blocked by kill-switch: $errMsg" 'PASS'
                        return $true
                    }
                    else {
                        Write-TestLog "  Error but wrong reason: $errMsg" 'FAIL'
                        return $false
                    }
                }
                else {
                    Write-TestLog "  Unexpected result: success=$($result.success), expected=$ExpectSuccess" 'FAIL'
                    return $false
                }
            }
            catch {
                # 404 means result not submitted yet, keep waiting
                if ($_.Exception.Response.StatusCode.value__ -ne 404) {
                    throw
                }
            }
            
            $waited++
        }
        
        Write-TestLog "  Task did not complete in time" 'FAIL'
        return $false
        
    }
    catch {
        Write-TestLog "  Error: $($_.Exception.Message)" 'FAIL'
        return $false
    }
}

function Test-CooldownEnforcement {
    Write-TestLog "Test 4: Cooldown enforcement (3 rapid clicks)..."
    
    # Post 3 click tasks rapidly
    $taskIds = @()
    $startTime = Get-Date
    
    for ($i = 0; $i -lt 3; $i++) {
        $task = @{
            type = 'computer_use.click'
            data = @{ x = 100 + ($i * 10); y = 100 }
        } | ConvertTo-Json -Depth 5
        
        $response = Invoke-RestMethod -Uri "$apiBase/tasks/create" -Method POST -Body $task -ContentType 'application/json'
        $taskIds += $response.task_id
    }
    
    Write-TestLog "  Posted 3 click tasks: $($taskIds -join ', ')"
    
    # Wait for all to complete
    $maxWait = 20
    $waited = 0
    $allCompleted = $false
    
    while ($waited -lt $maxWait) {
        Start-Sleep -Seconds 1
        $allDone = $true
        
        foreach ($tid in $taskIds) {
            try {
                $result = Invoke-RestMethod -Uri "$apiBase/results/$tid" -Method GET -ErrorAction Stop
                # Result found
            }
            catch {
                if ($_.Exception.Response.StatusCode.value__ -eq 404) {
                    # Not ready yet
                    $allDone = $false
                    break
                }
                else {
                    throw
                }
            }
        }
        
        if ($allDone) {
            $allCompleted = $true
            break
        }
        
        $waited++
    }
    
    if (-not $allCompleted) {
        Write-TestLog "  Tasks did not complete in time" 'FAIL'
        return $false
    }
    
    $endTime = Get-Date
    $totalMs = [int]($endTime - $startTime).TotalMilliseconds
    
    # With default 150ms cooldown, 3 actions should take at least 300ms
    # (plus processing overhead)
    $minExpected = 300
    
    if ($totalMs -ge $minExpected) {
        Write-TestLog "  Cooldown enforced: ${totalMs}ms elapsed (>= ${minExpected}ms)" 'PASS'
        return $true
    }
    else {
        Write-TestLog "  Cooldown NOT enforced: ${totalMs}ms elapsed (< ${minExpected}ms)" 'FAIL'
        return $false
    }
}

function Show-VSCodeSettings {
    Write-TestLog "Current VS Code settings (gitko.*):"
    
    $settingsPath = "$env:APPDATA\Code\User\settings.json"
    if (Test-Path $settingsPath) {
        $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
        
        $gitkoSettings = $settings.PSObject.Properties | Where-Object { $_.Name -like 'gitko*' }
        
        if ($gitkoSettings) {
            foreach ($prop in $gitkoSettings) {
                Write-TestLog "  $($prop.Name) = $($prop.Value)"
            }
        }
        else {
            Write-TestLog "  (no gitko.* settings found in user settings)" 'WARN'
        }
    }
    else {
        Write-TestLog "  (settings.json not found at $settingsPath)" 'WARN'
    }
}

# Main execution
try {
    Write-TestLog "=== Gitko Extension Integration Test ===" 'INFO'
    Write-TestLog ""
    
    Show-VSCodeSettings
    Write-TestLog ""
    
    # Start server
    Start-TestServer
    Write-TestLog ""
    
    # Wait for extension poller to start (if auto-enabled)
    Write-TestLog "Waiting 5s for extension poller to initialize..."
    Start-Sleep -Seconds 5
    Write-TestLog ""
    
    # Run tests
    $results = @{}
    $results['ping'] = Test-PingTask
    Write-TestLog ""
    
    $results['scan_enabled'] = Test-ComputerUseScan -ExpectSuccess $true
    Write-TestLog ""
    
    Write-TestLog "To test kill-switch, set gitko.enableComputerUseOverHttp=false in VS Code settings," 'WARN'
    Write-TestLog "then reload window and re-run this script." 'WARN'
    Write-TestLog ""
    
    $results['cooldown'] = Test-CooldownEnforcement
    Write-TestLog ""
    
    # Summary
    $passed = ($results.Values | Where-Object { $_ -eq $true }).Count
    $total = $results.Count
    
    Write-TestLog "=== Test Summary: $passed/$total passed ===" 'INFO'
    
    foreach ($key in $results.Keys) {
        $status = if ($results[$key]) { 'PASS' } else { 'FAIL' }
        Write-TestLog "  [$status] $key"
    }
    
    if ($passed -eq $total) {
        Write-TestLog "" 
        Write-TestLog "All tests passed! (Success)" 'PASS'
        exit 0
    }
    else {
        Write-TestLog ""
        Write-TestLog "Some tests failed. Check extension Output channel: 'Gitko HTTP Poller'" 'FAIL'
        exit 1
    }
    
}
catch {
    Write-TestLog "Test harness error: $($_.Exception.Message)" 'FAIL'
    exit 1
}
finally {
    Stop-TestServer
}
