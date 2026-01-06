# System Health Check Script
# Checks all ION/Core systems in one command

param(
    [switch]$Detailed,
    [string]$OutputJson,
    [string]$OutputMarkdown,
    [object]$FastHealthGate
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot



$ErrorActionPreference = 'Continue'

# Ensure UTF-8 console/output to prevent mojibake in Korean logs/output
try { chcp 65001 > $null 2> $null } catch {}
try {
    [Console]::InputEncoding = New-Object System.Text.UTF8Encoding($false)
    [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
    $OutputEncoding = New-Object System.Text.UTF8Encoding($false)
    $PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'
}
catch {}



$results = @{
    Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Summary   = @{
        TotalChecks = 0
        Passed      = 0
        Warnings    = 0
        Failed      = 0
    }
    Checks    = @{}
}

function Write-CheckHeader {
    param([string]$Title)
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  $Title" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
}

function Write-CheckResult {
    param(
        [string]$Name,
        [string]$Status,
        [string]$Message,
        [hashtable]$Details = @{}
    )
    
    $results.Summary.TotalChecks++
    $color = switch ($Status) {
        "OK" { "Green"; $results.Summary.Passed++ }
        "WARNING" { "Yellow"; $results.Summary.Warnings++ }
        "ERROR" { "Red"; $results.Summary.Failed++ }
    }
    
    Write-Host "[$Status] " -ForegroundColor $color -NoNewline
    Write-Host "$Name : $Message"
    
    $results.Checks[$Name] = @{
        Status  = $Status
        Message = $Message
        Details = $Details
    }
}

Write-CheckHeader "1/7 - LM Studio Status"

try {
    $port8080 = Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue
    $script:lmStudioOnline = $false
    if (-not $port8080) {
        Write-CheckResult "LM Studio Port" "WARNING" "Port 8080 not listening (LM Studio not running)"
    }
    else {
        Write-CheckResult "LM Studio Port" "OK" "Port 8080 active (PID $($port8080[0].OwningProcess))"
        $script:lmStudioOnline = $true
    }
    
    if ($script:lmStudioOnline) {
        $modelsUri = "http://localhost:8080/v1/models"
        $modelsResponse = Invoke-RestMethod -Uri $modelsUri -Method Get -TimeoutSec 5 -ErrorAction Stop
        $modelCount = $modelsResponse.data.Count
        
        if ($modelCount -eq 0) {
            Write-CheckResult "LM Studio Models" "ERROR" "No models loaded"
        }
        else {
            $loadedModel = $modelsResponse.data[0].id
            Write-CheckResult "LM Studio Models" "OK" "$modelCount model(s) available: $loadedModel"
            
            $chatUri = "http://localhost:8080/v1/chat/completions"
            $testBody = @{
                model      = $loadedModel
                messages   = @(
                    @{ role = "user"; content = "Hello" }
                )
                max_tokens = 20
            } | ConvertTo-Json -Depth 10
            
            $start = Get-Date
            $chatResponse = Invoke-RestMethod -Uri $chatUri -Method Post -Body $testBody -ContentType "application/json" -TimeoutSec 10 -ErrorAction Stop
            $latency = [int]((Get-Date) - $start).TotalMilliseconds
            
            if ($latency -lt 5000) {
                Write-CheckResult "LM Studio Inference" "OK" "Response in ${latency}ms"
            }
            else {
                Write-CheckResult "LM Studio Inference" "WARNING" "Slow response: ${latency}ms"
            }
        }
    }
    else {
        Write-CheckResult "LM Studio Models" "WARNING" "LM Studio offline, skipped"
    }
}
catch {
    Write-CheckResult "LM Studio" "WARNING" "Check skipped or failed: $_"
}

Write-CheckHeader "2/7 - Core Gateway Status"

try {
    $CoreUri = "https://Core-gateway-x4qvsargwa-uc.a.run.app/chat"
    $CoreBody = @{ message = "test" } | ConvertTo-Json
    
    $start = Get-Date
    $CoreResponse = Invoke-RestMethod -Uri $CoreUri -Method Post -Body $CoreBody -ContentType "application/json" -TimeoutSec 10 -ErrorAction Stop
    $latency = [int]((Get-Date) - $start).TotalMilliseconds
    
    if ($latency -lt 500) {
        Write-CheckResult "Core Gateway" "OK" "Response in ${latency}ms"
    }
    elseif ($latency -lt 1000) {
        Write-CheckResult "Core Gateway" "WARNING" "Elevated latency: ${latency}ms"
    }
    else {
        Write-CheckResult "Core Gateway" "WARNING" "High latency: ${latency}ms"
    }
}
catch {
    Write-CheckResult "Core Gateway" "ERROR" "Failed: $_"
}

Write-CheckHeader "3/7 - Cloud AI API Status"

try {
    $cloudUri = "https://ion-api-64076350717.us-central1.run.app/chat"
    $cloudBody = @{ message = "test" } | ConvertTo-Json
    
    $start = Get-Date
    $cloudResponse = Invoke-RestMethod -Uri $cloudUri -Method Post -Body $cloudBody -ContentType "application/json" -TimeoutSec 10 -ErrorAction Stop
    $latency = [int]((Get-Date) - $start).TotalMilliseconds
    
    if ($latency -lt 1000) {
        Write-CheckResult "Cloud AI API" "OK" "Response in ${latency}ms"
    }
    else {
        Write-CheckResult "Cloud AI API" "WARNING" "Elevated latency: ${latency}ms"
    }
}
catch {
    Write-CheckResult "Cloud AI API" "ERROR" "Failed: $_"
}

Write-CheckHeader "4/7 - AGI Pipeline Test"

try {
    $originalLocation = Get-Location
    Set-Location "$WorkspaceRoot"
    
    if (-not (Test-Path "fdo_agi_repo\.venv\Scripts\python.exe")) {
        Write-CheckResult "AGI Pipeline" "ERROR" "Virtual environment not found"
    }
    else {
        $pytestFile = "tests\test_fdo_agi_self_correction.py"
        if (Test-Path $pytestFile) {
            # Run pytest with a timeout to avoid hanging this check
            $job = Start-Job -ScriptBlock { & "fdo_agi_repo\.venv\Scripts\python.exe" -m pytest -q "tests\test_fdo_agi_self_correction.py" 2>&1 | Out-String }
            $completed = Wait-Job -Job $job -Timeout 45
            if (-not $completed) {
                Try { Stop-Job -Job $job -Force -ErrorAction SilentlyContinue } Catch {}
                Write-CheckResult "AGI Pipeline" "WARNING" "Tests timed out after 45s"
            }
            else {
                $testOutput = Receive-Job -Job $job | Out-String
                if ($testOutput -match '(\d+) passed.*?(\d+\.?\d*)s') {
                    $testCount = $matches[1]
                    $testTime = $matches[2]
                    Write-CheckResult "AGI Pipeline" "OK" "$testCount test(s) passed in ${testTime}s"
                }
                elseif ($testOutput -match '(failed|error)') {
                    Write-CheckResult "AGI Pipeline" "ERROR" "Tests failed (pytest)"
                }
                elseif ($testOutput.Trim().Length -gt 0) {
                    Write-CheckResult "AGI Pipeline" "OK" "Tests completed"
                }
                else {
                    Write-CheckResult "AGI Pipeline" "WARNING" "No output from pytest"
                }
            }
        }
        else {
            # Fallback health gate with explicit timeouts and JSON parsing
            # Use absolute path and pass into job to avoid module autoload/path issues
            $repoRoot = Get-Location
            $pyExe = Join-Path $repoRoot "fdo_agi_repo\.venv\Scripts\python.exe"
            if (-not (Test-Path -LiteralPath $pyExe)) { $pyExe = 'python' }
            $pyScript = Join-Path $repoRoot "fdo_agi_repo\scripts\check_health.py"
            if (-not (Test-Path -LiteralPath $pyScript)) {
                Write-CheckResult "AGI Pipeline" "ERROR" "Health script not found at $pyScript"
            }
            else {
                $tempOut = [IO.Path]::Combine([IO.Path]::GetTempPath(), "agi_health_" + [guid]::NewGuid().ToString() + ".json")
                # Determine whether to use fast mode (default to true for reliability unless explicitly disabled)
                $useFast = $true
                if ($PSBoundParameters.ContainsKey('FastHealthGate')) {
                    $val = $FastHealthGate
                    if ($null -eq $val) {
                        $useFast = $true
                    }
                    elseif ($val -is [bool]) {
                        $useFast = [bool]$val
                    }
                    else {
                        $s = ([string]$val).Trim()
                        $sLower = $s.ToLowerInvariant()
                        if ($sLower -in @('false', '0', '$false')) { $useFast = $false }
                        elseif ($sLower -in @('true', '1', '$true')) { $useFast = $true }
                        else {
                            try { $useFast = [System.Convert]::ToBoolean($s) } catch { $useFast = $true }
                        }
                    }
                }
                $job = Start-Job -ScriptBlock {
                    param($py, $script, $outPath, $fast)
                    try {
                        $env:PYTHONIOENCODING = 'utf-8'
                        $args = @('--json-only', '--max-duration', '8', '--hard-timeout', '8')
                        if ($fast) { $args = @('--json-only', '--fast', '--max-duration', '8', '--hard-timeout', '8') }
                        $output = & $py $script @args 2>$null
                        [IO.File]::WriteAllText($outPath, [string]$output, [Text.Encoding]::UTF8)
                    }
                    catch {
                        [IO.File]::WriteAllText($outPath, "", [Text.Encoding]::UTF8)
                    }
                } -ArgumentList $pyExe, $pyScript, $tempOut, $useFast
                $completed = Wait-Job -Job $job -Timeout 12
            }
            if (-not $completed) {
                Try { Stop-Job -Job $job -Force -ErrorAction SilentlyContinue } Catch {}
                Write-CheckResult "AGI Pipeline" "WARNING" "Health gate timed out after 12s"
            }
            else {
                # Read JSON output captured by the job (stdout only)
                $agiHealthRaw = if ($tempOut -and (Test-Path -LiteralPath $tempOut)) { Get-Content -LiteralPath $tempOut -Raw } else { '' }
                $json = $agiHealthRaw
                if (-not $json) {
                    Write-CheckResult "AGI Pipeline" "WARNING" "No JSON returned from health gate"
                }
                else {
                    try {
                        $obj = $json | ConvertFrom-Json -ErrorAction Stop
                        if ($obj.healthy -eq $true) {
                            Write-CheckResult "AGI Pipeline" "OK" "AGI Health Gate PASS"
                        }
                        else {
                            $reason = if ($obj.reason) { $obj.reason } else { 'AGI Health Gate failed' }
                            $status = "ERROR"
                            if ($reason -match '(exceed|exceeded|timeout|timed out)') { $status = "WARNING" }
                            Write-CheckResult "AGI Pipeline" $status $reason
                        }
                    }
                    catch {
                        Write-CheckResult "AGI Pipeline" "WARNING" "Invalid JSON from health gate"
                    }
                }
                # Cleanup temp file
                if ($tempOut -and (Test-Path -LiteralPath $tempOut)) { Remove-Item -LiteralPath $tempOut -Force -ErrorAction SilentlyContinue }
            }
        }
    }
    Set-Location $originalLocation
}
catch {
    Write-CheckResult "AGI Pipeline" "ERROR" "Failed: $_"
    if ($originalLocation) {
        Set-Location $originalLocation
    }
}

Write-CheckHeader "5/7 - Process Monitoring"

try {
    $lmProcesses = Get-Process | Where-Object { $_.ProcessName -match 'lmstudio|llama' } -ErrorAction SilentlyContinue
    if ($lmProcesses) {
        $totalMemoryMB = ($lmProcesses | Measure-Object -Property WorkingSet64 -Sum).Sum / 1MB
        $processCount = $lmProcesses.Count
        
        if ($totalMemoryMB -lt 20000) {
            Write-CheckResult "LM Studio Memory" "OK" "$processCount process(es), $([int]$totalMemoryMB)MB total"
        }
        elseif ($totalMemoryMB -lt 30000) {
            Write-CheckResult "LM Studio Memory" "WARNING" "High usage: $processCount process(es), $([int]$totalMemoryMB)MB"
        }
        else {
            Write-CheckResult "LM Studio Memory" "ERROR" "Excessive usage: $([int]$totalMemoryMB)MB"
        }
    }
    else {
        Write-CheckResult "LM Studio Processes" "WARNING" "No LM Studio processes found"
    }
    
    $pythonProcesses = Get-Process python -ErrorAction SilentlyContinue
    if ($pythonProcesses) {
        $pythonCount = $pythonProcesses.Count
        Write-CheckResult "Python Processes" "OK" "$pythonCount process(es) running"
    }
    else {
        Write-CheckResult "Python Processes" "OK" "No active Python processes"
    }
}
catch {
    Write-CheckResult "Process Monitoring" "ERROR" "Failed: $_"
}

Write-CheckHeader "6/7 - Scheduler Tasks"

try {
    $ionTasks = Get-ScheduledTask | Where-Object { $_.TaskName -match 'Ion|Core|Monitor' } -ErrorAction SilentlyContinue
    
    if (-not $ionTasks) {
        Write-CheckResult "Scheduler Tasks" "WARNING" "No ION tasks found"
    }
    else {
        $readyTasks = ($ionTasks | Where-Object { $_.State -eq 'Ready' }).Count
        $runningTasks = ($ionTasks | Where-Object { $_.State -eq 'Running' }).Count
        $totalTasks = $ionTasks.Count
        
        Write-CheckResult "Scheduler Tasks" "OK" "$totalTasks task(s): $readyTasks Ready, $runningTasks Running"
    }
}
catch {
    Write-CheckResult "Scheduler Tasks" "ERROR" "Failed: $_"
}

Write-CheckHeader "7/8 - Luon Watcher Status"

try {
    $luonProcess = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
        $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)" -ErrorAction SilentlyContinue).CommandLine
        $cmdLine -match 'luon|start_luon_watch'
    }
    
    if ($luonProcess) {
        Write-CheckResult "Luon Watcher" "OK" "Running (PID $($luonProcess[0].Id))"
    }
    else {
        $luonTask = Get-ScheduledTask | Where-Object { $_.TaskName -match 'Luon' } -ErrorAction SilentlyContinue
        if ($luonTask) {
            Write-CheckResult "Luon Watcher" "WARNING" "Scheduled task exists but not running"
        }
        else {
            Write-CheckResult "Luon Watcher" "WARNING" "Not running (optional component)"
        }
    }
}
catch {
    Write-CheckResult "Luon Watcher" "WARNING" "Could not determine status: $_"
}

Write-CheckHeader "8/8 - VS Code Settings.json Validation"

try {
    $settingsPath = "$env:APPDATA\Code\User\settings.json"
    
    if (-not (Test-Path $settingsPath)) {
        Write-CheckResult "Settings.json" "ERROR" "File not found at $settingsPath"
    }
    else {
        # Get file info
        $fileInfo = Get-Item $settingsPath
        $fileSizeKB = [math]::Round($fileInfo.Length / 1KB, 1)
        
        # Run Python JSON validation
        $validatorScript = "$WorkspaceRoot\scripts\validate_settings_json.py"
        
        if (-not (Test-Path $validatorScript)) {
            # Create validator on-the-fly if missing
            Write-Host "  Creating validator script..." -ForegroundColor Yellow
            $validatorCode = @'
import json
import sys
from pathlib import Path

settings_path = Path.home() / "AppData" / "Roaming" / "Code" / "User" / "settings.json"

try:
    with open(settings_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Count terminal history entries
    history_count = 0
    if 'terminal.integrated.shellIntegration.commandHistory' in data:
        history_count = len(data['terminal.integrated.shellIntegration.commandHistory'])
    
    print(f"OK|{history_count}")
    sys.exit(0)
except json.JSONDecodeError as e:
    print(f"ERROR|JSON parse error at line {e.lineno}: {e.msg}")
    sys.exit(1)
except Exception as e:
    print(f"ERROR|{str(e)}")
    sys.exit(2)
'@
            $validatorCode | Out-File $validatorScript -Encoding UTF8
        }
        
        # Run validation
        $pythonExe = "python"
        if (Test-Path "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe") {
            $pythonExe = "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe"
        }
        
        $validationOutput = & $pythonExe $validatorScript 2>&1 | Out-String
        
        if ($LASTEXITCODE -eq 0) {
            $parts = $validationOutput.Trim() -split '\|'
            $historyCount = $parts[1]
            Write-CheckResult "Settings.json" "OK" "Valid JSON, ${fileSizeKB}KB, $historyCount commands"
        }
        else {
            $errorMsg = ($validationOutput.Trim() -split '\|')[1]
            Write-CheckResult "Settings.json" "ERROR" $errorMsg
            
            # Auto-fix attempt
            Write-Host "  Attempting auto-fix..." -ForegroundColor Yellow
            
            $backupPath = "$settingsPath.backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
            Copy-Item $settingsPath $backupPath -Force
            Write-Host "  Backup created: $backupPath" -ForegroundColor Cyan
            
            $fixScript = "$WorkspaceRoot\scripts\fix_settings_duplicates.py"
            if (Test-Path $fixScript) {
                & $pythonExe $fixScript
                
                # Re-validate
                $revalidationOutput = & $pythonExe $validatorScript 2>&1 | Out-String
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "  ??Auto-fix successful!" -ForegroundColor Green
                }
                else {
                    Write-Host "  ??Auto-fix failed. Manual intervention required." -ForegroundColor Red
                }
            }
        }
    }
}
catch {
    Write-CheckResult "Settings.json" "ERROR" "Validation failed: $_"
}

Write-Host ""
Write-CheckHeader "System Health Summary"

$passRate = [math]::Round(($results.Summary.Passed / $results.Summary.TotalChecks) * 100, 1)

Write-Host "Total Checks : " -NoNewline
Write-Host $results.Summary.TotalChecks -ForegroundColor Cyan

Write-Host "Passed       : " -NoNewline
Write-Host $results.Summary.Passed -ForegroundColor Green

Write-Host "Warnings     : " -NoNewline
Write-Host $results.Summary.Warnings -ForegroundColor Yellow

Write-Host "Failed       : " -NoNewline
Write-Host $results.Summary.Failed -ForegroundColor Red

Write-Host "Pass Rate    : " -NoNewline
if ($passRate -ge 90) {
    Write-Host "${passRate}% EXCELLENT" -ForegroundColor Green
}
elseif ($passRate -ge 70) {
    Write-Host "${passRate}% ACCEPTABLE" -ForegroundColor Yellow
}
else {
    Write-Host "${passRate}% NEEDS ATTENTION" -ForegroundColor Red
}

Write-Host ""
Write-Host "Overall Status: " -NoNewline
$overallStatus = ""
if ($results.Summary.Failed -eq 0 -and $results.Summary.Warnings -eq 0) {
    $overallStatus = "ALL SYSTEMS OPERATIONAL"
    Write-Host $overallStatus -ForegroundColor Green
}
elseif ($results.Summary.Failed -eq 0) {
    $overallStatus = "OPERATIONAL WITH WARNINGS"
    Write-Host $overallStatus -ForegroundColor Yellow
}
else {
    $overallStatus = "CRITICAL ISSUES DETECTED"
    Write-Host $overallStatus -ForegroundColor Red
}

# Enrich results before optional outputs
$results.Summary.PassRate = $passRate
$results.Summary.StatusText = $overallStatus

$outputMessages = @()

if ($OutputJson) {
    $results | ConvertTo-Json -Depth 10 | Out-File $OutputJson -Encoding UTF8
    $outputMessages += "Results saved to: $OutputJson"
}

if ($OutputMarkdown) {
    try {
        $sb = New-Object System.Text.StringBuilder
        $null = $sb.AppendLine("# System Health Check")
        $null = $sb.AppendLine("")
        $null = $sb.AppendLine("- Timestamp: ``$($results.Timestamp)``")
        $null = $sb.AppendLine("- Total Checks: $($results.Summary.TotalChecks)")
        $null = $sb.AppendLine("- Passed: $($results.Summary.Passed)")
        $null = $sb.AppendLine("- Warnings: $($results.Summary.Warnings)")
        $null = $sb.AppendLine("- Failed: $($results.Summary.Failed)")
        $null = $sb.AppendLine("- Pass Rate: $passRate%")
        $null = $sb.AppendLine("- Overall Status: **$overallStatus**")
        $null = $sb.AppendLine("")
        $null = $sb.AppendLine("## Checks")
        $statusEmoji = @{ OK = "✅"; WARNING = "⚠️"; ERROR = "❌" }
        foreach ($k in ($results.Checks.Keys | Sort-Object)) {
            $c = $results.Checks[$k]
            $emoji = if ($statusEmoji.ContainsKey($c.Status)) { $statusEmoji[$c.Status] } else { "" }
            $null = $sb.AppendLine("- $emoji **$k** — $($c.Status): $($c.Message)")
        }
        [IO.File]::WriteAllText($OutputMarkdown, $sb.ToString(), [Text.UTF8Encoding]::new($false))
        $outputMessages += "Markdown saved to: $OutputMarkdown"
    }
    catch {
        Write-Warning "Failed to save markdown: $($_.Exception.Message)"
    }
}

if ($outputMessages.Count -gt 0) {
    Write-Host ""
    foreach ($msg in $outputMessages) {
        Write-Host $msg -ForegroundColor Cyan
    }
}

if ($Detailed) {
    Write-Host ""
    Write-CheckHeader "Running Detailed Benchmarks"
    
    Write-Host "Executing LM Studio performance test..." -ForegroundColor Yellow
    if ($script:lmStudioOnline) {
        & "$PSScriptRoot\test_lm_studio_performance.ps1" -Warmup -MaxTokens 64
    }
    else {
        Write-Host "  Skipping LM Studio performance test (offline)." -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "Executing Core vs LM Studio comparison..." -ForegroundColor Yellow
    & "$PSScriptRoot\compare_performance.ps1" -Warmup -Iterations 5 -MaxTokens 64
}

Write-Host ""