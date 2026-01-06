# AGI Session Start Script
# UTF-8 BOM encoding to prevent emoji issues

param(
    [switch]$Silent,
    [switch]$JustCheck
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Stop"

# Color functions
function Write-Header { param($Text) Write-Host "`n[AGI] $Text" -ForegroundColor Cyan }
function Write-Success { param($Text) Write-Host "[OK] $Text" -ForegroundColor Green }
function Write-Warning { param($Text) Write-Host "[WARN] $Text" -ForegroundColor Yellow }
function Write-Error { param($Text) Write-Host "[ERROR] $Text" -ForegroundColor Red }
function Write-Info { param($Text) Write-Host "[INFO] $Text" -ForegroundColor Blue }

# Workspace root
$WorkspaceRoot = Split-Path $PSScriptRoot -Parent
$FdoAgiRepo = Join-Path $WorkspaceRoot "fdo_agi_repo"
$MasterPlan = Join-Path $WorkspaceRoot "깃코_AGI_구축_마스터플랜_2025-10-25.md"
$QuickStart = Join-Path $WorkspaceRoot "깃코_AGI_빠른시작_2025-10-25.md"

# Get current phase
function Get-CurrentPhase {
    $StateFile = Join-Path $WorkspaceRoot ".agi_work_state.json"
    
    if (Test-Path $StateFile) {
        $State = Get-Content $StateFile -Raw | ConvertFrom-Json
        return $State
    }
    
    # Default: Phase 1
    return @{
        current_phase    = 1
        phase_1_complete = $false
        phase_2_complete = $false
        phase_3_complete = $false
        phase_4_complete = $false
        last_session     = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        focus_streak     = 0
        distractions     = 0
    }
}

# Save state
function Save-WorkState {
    param($State)
    
    $StateFile = Join-Path $WorkspaceRoot ".agi_work_state.json"
    $State | ConvertTo-Json -Depth 10 | Set-Content $StateFile -Encoding UTF8
}

# Main logic
try {
    if (-not $Silent) {
        Clear-Host
        # Restore Codex Session
        Write-Header "Checking Codex Session..."
        $LastSessionId = python (Join-Path $PSScriptRoot "get_last_codex_session.py")
        if ($LASTEXITCODE -eq 0 -and $LastSessionId) {
            $env:CODEX_SESSION_ID = $LastSessionId.Trim()
            Write-Success "Restored Codex Session: $env:CODEX_SESSION_ID"
        }
        else {
            Write-Warning "No active Codex session found. A new one will be created."
        }
        Write-Host @"
================================================================
                AGI Construction Session Start
  "Building a system where AGI thinks and improves itself"
================================================================
"@ -ForegroundColor Cyan
    }

    # Check current state
    $State = Get-CurrentPhase
    
    Write-Header "Current Work Status"
    Write-Host "  Last Session: $($State.last_session)" -ForegroundColor Yellow
    Write-Host "  Focus Streak: $($State.focus_streak) sessions" -ForegroundColor Green
    Write-Host "  Distractions: $($State.distractions) times" -ForegroundColor $(if ($State.distractions -gt 5) { "Red" } else { "Yellow" })
    
    Write-Header "Phase Progress"
    
    # Phase status
    $Phase1Status = if ($State.phase_1_complete) { "[DONE]" } else { "[CURRENT]" }
    $Phase2Status = if ($State.phase_2_complete) { "[DONE]" } elseif ($State.current_phase -eq 2) { "[CURRENT]" } else { "[PENDING]" }
    $Phase3Status = if ($State.phase_3_complete) { "[DONE]" } elseif ($State.current_phase -eq 3) { "[CURRENT]" } else { "[PENDING]" }
    $Phase4Status = if ($State.phase_4_complete) { "[DONE]" } elseif ($State.current_phase -eq 4) { "[CURRENT]" } else { "[PENDING]" }
    
    Write-Host "  $Phase1Status Phase 1: Execute Test"
    Write-Host "  $Phase2Status Phase 2: LLM Backend Connection"
    Write-Host "  $Phase3Status Phase 3: Autonomous Learning Loop"
    Write-Host "  $Phase4Status Phase 4: Meta-Cognition"
    
    # AGI Score
    $AGIScore = 31.4
    if ($State.phase_1_complete) { $AGIScore = 35.0 }
    if ($State.phase_2_complete) { $AGIScore = 50.0 }
    if ($State.phase_3_complete) { $AGIScore = 65.0 }
    if ($State.phase_4_complete) { $AGIScore = 75.0 }
    
    Write-Host "`n  AGI Score: $AGIScore%" -ForegroundColor $(if ($AGIScore -ge 65) { "Green" } elseif ($AGIScore -ge 50) { "Yellow" } else { "Red" })
    
    # Next action
    Write-Header "Next Action"
    
    if (-not $State.phase_1_complete) {
        Write-Host @"
  
  Phase 1: fdo_agi_repo Execute Test
  
  Command:
    cd $WorkspaceRoot\fdo_agi_repo
    python -m scripts.run_task --title "demo" --goal "AGI self-correction loop explanation"
  
  Expected:
    [OK] Pipeline executes (echo responses only)
    [ERROR] Import/dependency issues -> fix immediately
  
"@
    }
    elseif (-not $State.phase_2_complete) {
        Write-Host @"
  
  Phase 2: LLM Backend Connection
  
  Files to edit:
    - $WorkspaceRoot\fdo_agi_repo\personas\thesis.py
    - $WorkspaceRoot\fdo_agi_repo\personas\antithesis.py
    - $WorkspaceRoot\fdo_agi_repo\personas\synthesis.py
  
  Task:
    - Add Gemini 1.5 Pro API call
    - Remove echo placeholder
    - Return real LLM responses
  
"@
    }
    
    # Quick actions
    Write-Header "Quick Actions"
    Write-Host "  [1] Open Quick Start Guide (Recommended)"
    Write-Host "  [2] Open Master Plan"
    Write-Host "  [3] Open fdo_agi_repo"
    Write-Host "  [4] Run Phase 1 (Auto)"
    Write-Host "  [Q] Quit"
    
    if (-not $JustCheck -and -not $Silent) {
        Write-Host "`nChoice: " -NoNewline -ForegroundColor Yellow
        $Choice = Read-Host
        
        switch ($Choice.ToUpper()) {
            "1" {
                if (Test-Path $QuickStart) {
                    code $QuickStart
                    Write-Success "Quick Start Guide opened!"
                }
            }
            "2" {
                if (Test-Path $MasterPlan) {
                    code $MasterPlan
                    Write-Success "Master Plan opened!"
                }
            }
            "3" {
                if (Test-Path $FdoAgiRepo) {
                    code $FdoAgiRepo
                    Write-Success "fdo_agi_repo opened!"
                }
            }
            "4" {
                Write-Info "Starting Phase 1 auto-execution..."
                Set-Location $FdoAgiRepo
                
                $VenvPath = Join-Path $FdoAgiRepo ".venv"
                if (-not (Test-Path $VenvPath)) {
                    Write-Warning "venv not found. Creating..."
                    python -m venv .venv
                }
                
                Write-Info "Running: python -m scripts.run_task..."
                
                & "$VenvPath\Scripts\python.exe" -m scripts.run_task --title "demo" --goal "AGI self-correction loop explanation"
                
                if ($LASTEXITCODE -eq 0) {
                    Write-Success "Phase 1 Complete!"
                    $State.phase_1_complete = $true
                    $State.current_phase = 2
                    $State.focus_streak++
                    Save-WorkState $State
                }
                else {
                    Write-Error "Error occurred. Check logs."
                }
            }
            "Q" {
                Write-Info "Exiting."
            }
            default {
                Write-Warning "Invalid choice."
            }
        }
    }
    
    # Update last session time
    $State.last_session = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Save-WorkState $State
    
    Write-Host ""
    Write-Host "[TIP] Stay focused! Does this task directly help AGI think and improve itself?" -ForegroundColor Gray
    Write-Host ""
    
}
catch {
    Write-Error "Error: $_"
    Write-Host $_.ScriptStackTrace -ForegroundColor Red
    exit 1
}