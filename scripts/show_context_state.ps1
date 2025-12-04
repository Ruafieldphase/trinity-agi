# Show Context State - ASCII safe for PowerShell 5.1
param([switch]$Verbose)

$ErrorActionPreference = "Continue"
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot

Write-Host "`n====================================" -ForegroundColor Cyan
Write-Host "     Context State Dashboard" -ForegroundColor Cyan
Write-Host "====================================`n" -ForegroundColor Cyan

# 1. Latest Handover
Write-Host "[ Latest Handover ]" -ForegroundColor Yellow
$handoverPath = Join-Path $WorkspaceRoot "session_memory\handovers\latest_handover.json"
if (Test-Path $handoverPath) {
    try {
        $handover = Get-Content $handoverPath -Raw | ConvertFrom-Json
        Write-Host "  Session ID:  $($handover.session_id)" -ForegroundColor White
        Write-Host "  Task:        $($handover.task_description)" -ForegroundColor White
        Write-Host "  Progress:    $($handover.current_progress)" -ForegroundColor White
        Write-Host "  [OK] Handover available" -ForegroundColor Green
    }
    catch {
        Write-Host "  [WARN] Failed to parse" -ForegroundColor Yellow
    }
}
else {
    Write-Host "  [MISSING] No handover found" -ForegroundColor Red
}

# 2. Agent Handoff Document
Write-Host "`n[ Agent Handoff Document ]" -ForegroundColor Yellow
$handoffPath = Join-Path $WorkspaceRoot "docs\AGENT_HANDOFF.md"
if (Test-Path $handoffPath) {
    Write-Host "  [OK] Document exists" -ForegroundColor Green
}
else {
    Write-Host "  [MISSING] No AGENT_HANDOFF.md" -ForegroundColor Red
}

# 3. Auto Resume State
Write-Host "`n[ Auto Resume State ]" -ForegroundColor Yellow
$statePath = Join-Path $WorkspaceRoot "outputs\auto_resume_state.json"
if (Test-Path $statePath) {
    try {
        $state = Get-Content $statePath -Raw | ConvertFrom-Json
        $lastRun = [DateTime]::Parse($state.last_run)
        $minAgo = [int]((Get-Date) - $lastRun).TotalMinutes
        Write-Host "  Last Run: $($lastRun.ToString('yyyy-MM-dd HH:mm:ss')) ($minAgo min ago)" -ForegroundColor White
        Write-Host "  [OK] State file exists" -ForegroundColor Green
    }
    catch {
        Write-Host "  [WARN] Failed to parse" -ForegroundColor Yellow
    }
}
else {
    Write-Host "  [MISSING] Never run" -ForegroundColor Red
}

# 4. Task Queue Server
Write-Host "`n[ Task Queue Server ]" -ForegroundColor Yellow
try {
    Invoke-WebRequest -Uri "http://localhost:8091/api/health" -TimeoutSec 2 -ErrorAction Stop | Out-Null
    Write-Host "  [OK] ONLINE (port 8091)" -ForegroundColor Green
}
catch {
    Write-Host "  [OFFLINE]" -ForegroundColor Red
}

# Summary
Write-Host "`n====================================" -ForegroundColor Cyan
Write-Host "Summary:" -ForegroundColor White

$hasHandover = Test-Path $handoverPath
$hasHandoff = Test-Path $handoffPath
$hasAutoResume = Test-Path $statePath
$hasServer = $false
try { Invoke-WebRequest -Uri "http://localhost:8091/api/health" -TimeoutSec 1 -ErrorAction Stop | Out-Null; $hasServer = $true } catch {}

$readiness = 0
if ($hasHandover) { $readiness++ }
if ($hasHandoff) { $readiness++ }
if ($hasAutoResume) { $readiness++ }
if ($hasServer) { $readiness++ }

Write-Host "  Session Handover:  $(if ($hasHandover) { '[OK]' } else { '[MISSING]' })" -ForegroundColor $(if ($hasHandover) { "Green" } else { "Red" })
Write-Host "  Agent Handoff:     $(if ($hasHandoff) { '[OK]' } else { '[MISSING]' })" -ForegroundColor $(if ($hasHandoff) { "Green" } else { "Red" })
Write-Host "  Auto Resume:       $(if ($hasAutoResume) { '[OK]' } else { '[NOT RUN]' })" -ForegroundColor $(if ($hasAutoResume) { "Green" } else { "Yellow" })
Write-Host "  Task Queue:        $(if ($hasServer) { '[OK]' } else { '[OFFLINE]' })" -ForegroundColor $(if ($hasServer) { "Green" } else { "Red" })

Write-Host "`nOverall Readiness: $readiness/4" -ForegroundColor White

if ($readiness -lt 4) {
    Write-Host "`nRecommended Actions:" -ForegroundColor Cyan
    if (-not $hasServer) {
        Write-Host "  1. Start Task Queue: Task 'Comet-Gitko: Start Task Queue Server'" -ForegroundColor Yellow
    }
    if (-not $hasAutoResume) {
        Write-Host "  2. Run auto-resume: Task 'Context: Manual Resume'" -ForegroundColor Yellow
    }
}
Write-Host ""
