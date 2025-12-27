#Requires -Version 5.1
<#
.SYNOPSIS
    Smart Metabolic Cleaner: Targeted Apoptosis for AGI Zombies
    Identifies and removes duplicate AGI processes, keeping only the youngest (healthiest).
#>

param(
    [switch]$DryRun
)

$ErrorActionPreference = "Continue"

function Kill-ZombieProcess {
    param(
        [string]$ScriptPattern,
        [string]$DisplayName
    )
    
    # Get processes matching the pattern in CommandLine
    $procs = Get-CimInstance Win32_Process | Where-Object { 
        $_.CommandLine -and $_.CommandLine -like "*$ScriptPattern*" 
    } | Sort-Object CreationDate -Descending 
    # Sorting Descending means Index 0 is the NEWEST (Youngest)

    if (-not $procs) {
        return
    }

    $count = ($procs | Measure-Object).Count
    if ($count -le 1) {
        Write-Host "  ✅ $DisplayName : Healthy ($count active)" -ForegroundColor Green
        return
    }

    # Keep the youngest (Index 0), Kill the rest (Index 1..)
    $youngest = $procs[0]
    $zombies = $procs | Select-Object -Skip 1

    Write-Host "  🧹 $DisplayName : Cleanup needed. Keeping PID $($youngest.ProcessId) (Newest)." -ForegroundColor Yellow
    
    foreach ($zombie in $zombies) {
        $pidToKill = $zombie.ProcessId
        
        if ($DryRun) {
            Write-Host "    [DRY-RUN] Would kill Zombie PID $pidToKill (Created: $($zombie.CreationDate))" -ForegroundColor Gray
            continue
        }

        Write-Host "    🔪 Targeting Zombie PID $pidToKill..." -NoNewline
        
        # Try Method 1: PowerShell Stop-Process
        try {
            Stop-Process -Id $pidToKill -Force -ErrorAction Stop
            Write-Host " [KILLED via PS]" -ForegroundColor Green
            continue
        }
        catch {
            # Method 1 Failed (Access Denied?)
        }

        # Try Method 2: Taskkill (Force)
        try {
            $null = taskkill /F /PID $pidToKill 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host " [KILLED via TaskKill]" -ForegroundColor Green
            }
            else {
                Write-Host " [FAILED] Access Denied / Rigid Zombie" -ForegroundColor Red
            }
        }
        catch {
            Write-Host " [FAILED] Error invoking taskkill" -ForegroundColor Red
        }
    }
}

Write-Host "[Metabolic Cleanup] Scanning for waste..." -ForegroundColor Cyan

# 1. Clean Brain Clones
Kill-ZombieProcess -ScriptPattern "rhythm_think.py" -DisplayName "Brain (RhythmThink)"

# 2. Clean Heartbeat Clones
Kill-ZombieProcess -ScriptPattern "heartbeat_loop.py" -DisplayName "Heart (Heartbeat)"

# 3. Clean Aura Clones
Kill-ZombieProcess -ScriptPattern "aura_controller.py" -DisplayName "Aura (Controller)"

# 4. Clean Immune System Clones (Self-Regulation)
Kill-ZombieProcess -ScriptPattern "launch_immune_system.py" -DisplayName "Immune System"

Write-Host "[Metabolic Cleanup] Complete." -ForegroundColor Cyan
