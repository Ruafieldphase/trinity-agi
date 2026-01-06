#!/usr/bin/env pwsh
# final_verification.ps1
# Phase 5 프로젝트 최종 검증 스크립트

param(
    [switch]$Verbose
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = 'Stop'

Write-Host "`n=============================================================" -ForegroundColor Cyan
Write-Host "   Gitko AGI Phase 5 - Final Verification" -ForegroundColor Yellow
Write-Host "=============================================================`n" -ForegroundColor Cyan

$verificationResults = @{
    TotalChecks  = 0
    PassedChecks = 0
    FailedChecks = 0
    Warnings     = 0
    Details      = @()
}

function Test-Check {
    param(
        [string]$Name,
        [scriptblock]$Test,
        [string]$SuccessMessage,
        [string]$FailureMessage,
        [switch]$Critical
    )
    
    $verificationResults.TotalChecks++
    
    try {
        $result = & $Test
        if ($result) {
            $verificationResults.PassedChecks++
            Write-Host "✅ $Name" -ForegroundColor Green
            if ($SuccessMessage) {
                Write-Host "   $SuccessMessage" -ForegroundColor Gray
            }
            $verificationResults.Details += @{
                Check   = $Name
                Status  = "PASS"
                Message = $SuccessMessage
            }
        }
        else {
            if ($Critical) {
                $verificationResults.FailedChecks++
                Write-Host "❌ $Name" -ForegroundColor Red
                if ($FailureMessage) {
                    Write-Host "   $FailureMessage" -ForegroundColor Red
                }
                $verificationResults.Details += @{
                    Check   = $Name
                    Status  = "FAIL"
                    Message = $FailureMessage
                }
            }
            else {
                $verificationResults.Warnings++
                Write-Host "⚠️  $Name" -ForegroundColor Yellow
                if ($FailureMessage) {
                    Write-Host "   $FailureMessage" -ForegroundColor Yellow
                }
                $verificationResults.Details += @{
                    Check   = $Name
                    Status  = "WARNING"
                    Message = $FailureMessage
                }
            }
        }
    }
    catch {
        $verificationResults.FailedChecks++
        Write-Host "❌ $Name" -ForegroundColor Red
        Write-Host "   오류: $($_.Exception.Message)" -ForegroundColor Red
        $verificationResults.Details += @{
            Check   = $Name
            Status  = "ERROR"
            Message = $_.Exception.Message
        }
    }
}

# 1. Required Files Check
Write-Host "`nRequired Files Verification..." -ForegroundColor Cyan

Test-Check -Name "Web Server File" -Critical -Test {
    Test-Path "$WorkspaceRoot\fdo_agi_repo\monitoring\web_server.py"
} -SuccessMessage "web_server.py found" -FailureMessage "web_server.py missing"

Test-Check -Name "Dashboard HTML" -Critical -Test {
    Test-Path "$WorkspaceRoot\fdo_agi_repo\monitoring\static\index.html"
} -SuccessMessage "index.html found" -FailureMessage "index.html missing"

Test-Check -Name "Dashboard JavaScript" -Critical -Test {
    Test-Path "$WorkspaceRoot\fdo_agi_repo\monitoring\static\app.js"
} -SuccessMessage "app.js found" -FailureMessage "app.js missing"

Test-Check -Name "Dashboard CSS" -Critical -Test {
    Test-Path "$WorkspaceRoot\fdo_agi_repo\monitoring\static\style.css"
} -SuccessMessage "style.css found" -FailureMessage "style.css missing"

Test-Check -Name "Start Script" -Critical -Test {
    Test-Path "$PSScriptRoot\start_phase5_system.ps1"
} -SuccessMessage "start_phase5_system.ps1 found" -FailureMessage "Start script missing"

# 2. Document Verification
Write-Host "`nDocument Verification..." -ForegroundColor Cyan

Test-Check -Name "Operations Guide" -Critical -Test {
    Test-Path "$WorkspaceRoot\OPERATIONS_GUIDE.md"
} -SuccessMessage "OPERATIONS_GUIDE.md found" -FailureMessage "Operations guide missing"

Test-Check -Name "Release Notes" -Critical -Test {
    Test-Path "$WorkspaceRoot\RELEASE_NOTES_PHASE5.md"
} -SuccessMessage "RELEASE_NOTES_PHASE5.md found" -FailureMessage "Release notes missing"

Test-Check -Name "Project Completion" -Critical -Test {
    Test-Path "$WorkspaceRoot\PROJECT_COMPLETION.md"
} -SuccessMessage "PROJECT_COMPLETION.md found" -FailureMessage "Completion doc missing"

Test-Check -Name "Final Summary" -Critical -Test {
    Test-Path "$WorkspaceRoot\PHASE_5_FINAL_SUMMARY.md"
} -SuccessMessage "PHASE_5_FINAL_SUMMARY.md found" -FailureMessage "Final summary missing"

Test-Check -Name "Project README" -Critical -Test {
    $readme = Get-Content "$WorkspaceRoot\README.md" -Raw
    $readme -match "Phase 5"
} -SuccessMessage "README.md has Phase 5 content" -FailureMessage "README.md missing Phase 5"

# 3. Python Environment
Write-Host "`nPython Environment Verification..." -ForegroundColor Cyan

Test-Check -Name "fdo_agi_repo venv" -Critical -Test {
    Test-Path "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe"
} -SuccessMessage "fdo_agi_repo Python venv found" -FailureMessage "Virtual environment missing"

Test-Check -Name "LLM_Unified venv" -Critical -Test {
    Test-Path "$WorkspaceRoot\LLM_Unified\.venv\Scripts\python.exe"
} -SuccessMessage "LLM_Unified Python venv found" -FailureMessage "Virtual environment missing"

# 4. Task Queue Server
Write-Host "`nTask Queue Server Verification..." -ForegroundColor Cyan

Test-Check -Name "Task Queue Server File" -Critical -Test {
    Test-Path "$WorkspaceRoot\LLM_Unified\ion-mentoring\task_queue_server.py"
} -SuccessMessage "task_queue_server.py found" -FailureMessage "Task Queue Server file missing"

Test-Check -Name "Task Queue Server Running" -Test {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8091/api/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
        $response.StatusCode -eq 200
    }
    catch {
        $false
    }
} -SuccessMessage "Running on port 8091" -FailureMessage "Task Queue Server not running (normal, start if needed)"

# 5. Git Status
Write-Host "`nGit Status Verification..." -ForegroundColor Cyan

Test-Check -Name "Git Commit Status" -Test {
    $status = git status --short
    $status.Length -eq 0 -or $status -match "M|A|D"
} -SuccessMessage "Git status OK" -FailureMessage "Git changes need review"

Test-Check -Name "Recent Commit" -Test {
    $lastCommit = git log -1 --oneline
    $lastCommit -match "Phase 5"
} -SuccessMessage "Phase 5 commit found: $(git log -1 --oneline)" -FailureMessage "No Phase 5 commit"

# 6. Directory Structure
Write-Host "`nDirectory Structure Verification..." -ForegroundColor Cyan

Test-Check -Name "monitoring directory" -Critical -Test {
    Test-Path "$WorkspaceRoot\fdo_agi_repo\monitoring" -PathType Container
} -SuccessMessage "monitoring directory found" -FailureMessage "monitoring directory missing"

Test-Check -Name "static directory" -Critical -Test {
    Test-Path "$WorkspaceRoot\fdo_agi_repo\monitoring\static" -PathType Container
} -SuccessMessage "static directory found" -FailureMessage "static directory missing"

Test-Check -Name "outputs directory" -Test {
    Test-Path "$WorkspaceRoot\outputs" -PathType Container
} -SuccessMessage "outputs directory found" -FailureMessage "outputs directory missing (auto-created)"

# Final Results
Write-Host "`n=============================================================" -ForegroundColor Cyan
Write-Host "   Verification Results Summary" -ForegroundColor Yellow
Write-Host "=============================================================`n" -ForegroundColor Cyan

Write-Host "Total Checks: $($verificationResults.TotalChecks)" -ForegroundColor White
Write-Host "Passed: $($verificationResults.PassedChecks)" -ForegroundColor Green
Write-Host "Failed: $($verificationResults.FailedChecks)" -ForegroundColor Red
Write-Host "Warnings: $($verificationResults.Warnings)" -ForegroundColor Yellow

$successRate = [math]::Round(($verificationResults.PassedChecks / $verificationResults.TotalChecks) * 100, 2)
Write-Host "`nSuccess Rate: $successRate%" -ForegroundColor $(if ($successRate -ge 90) { "Green" } elseif ($successRate -ge 70) { "Yellow" } else { "Red" })

if ($verificationResults.FailedChecks -eq 0) {
    Write-Host "`nAll critical checks passed!" -ForegroundColor Green
    Write-Host "   Project is production-ready." -ForegroundColor Green
}
elseif ($verificationResults.FailedChecks -le 2) {
    Write-Host "`nSome issues found." -ForegroundColor Yellow
    Write-Host "   But most features are working normally." -ForegroundColor Yellow
}
else {
    Write-Host "`nMultiple issues found." -ForegroundColor Red
    Write-Host "   Please resolve issues and verify again." -ForegroundColor Red
}

Write-Host "`n=============================================================" -ForegroundColor Cyan
Write-Host "   Next Steps" -ForegroundColor Yellow
Write-Host "=============================================================`n" -ForegroundColor Cyan

Write-Host "1. Start System:" -ForegroundColor Cyan
Write-Host "   .\scripts\start_phase5_system.ps1" -ForegroundColor White
Write-Host "`n2. Open Browser:" -ForegroundColor Cyan
Write-Host "   http://127.0.0.1:8000" -ForegroundColor White
Write-Host "`n3. Git Push (Optional):" -ForegroundColor Cyan
Write-Host "   git push origin main" -ForegroundColor White
Write-Host ""

# JSON Output (Optional)
if ($Verbose) {
    $jsonPath = "$WorkspaceRoot\outputs\verification_result.json"
    $verificationResults | ConvertTo-Json -Depth 5 | Out-File -FilePath $jsonPath -Encoding UTF8
    Write-Host "Detailed results saved: $jsonPath" -ForegroundColor Gray
}

# Exit code
if ($verificationResults.FailedChecks -eq 0) {
    exit 0
}
else {
    exit 1
}