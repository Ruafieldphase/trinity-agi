#>

param(
    [switch]$Register,
    [switch]$Unregister,
    [switch]$Status,
    [string]$Time = "03:00",
    [switch]$SendEmail,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$TaskName = "AutoDreamPipeline"
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot

# Helper: Check if running as admin
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Helper: Check if action requires admin
function Test-RequiresAdmin {
    param([switch]$Register, [switch]$Unregister)
    return ($Register -or $Unregister)
}

# Helper: Get Python executable path
function Get-PythonPath {
    $venvPaths = @(
        "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe",
        "$WorkspaceRoot\LLM_Unified\.venv\Scripts\python.exe"
    )
    
    foreach ($path in $venvPaths) {
        if (Test-Path $path) {
            return $path
        }
    }
    
    # Fallback to system python
    $systemPython = Get-Command python -ErrorAction SilentlyContinue
    if ($systemPython) {
        return $systemPython.Source
    }
    
    throw "Python not found. Please install Python or create virtual environment."
}

# Helper: Create task action
function New-TaskAction {
    $pythonPath = Get-PythonPath
    $scriptPath = "$WorkspaceRoot\scripts\auto_dream_pipeline.py"
    
    if (-not (Test-Path $scriptPath)) {
        throw "Script not found: $scriptPath"
    }
    
    $psCommand = "& `"$pythonPath`" $arguments"
    
    Write-Host "Python: $pythonPath" -ForegroundColor Cyan
    Write-Host "Script: $scriptPath" -ForegroundColor Cyan
    Write-Host "Arguments: $arguments" -ForegroundColor Cyan
    
    return New-ScheduledTaskAction `
        -Execute 'powershell.exe' `
        -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command `"$psCommand`"" `
        -WorkingDirectory $WorkspaceRoot
}

# Helper: Create task trigger
function New-TaskTrigger {
    param([string]$Time)
    
    $timeParts = $Time.Split(':')
    if ($timeParts.Count -ne 2) {
        throw "Invalid time format. Use HH:MM (e.g., 03:00)"
    }
    
    $hour = [int]$timeParts[0]
    $minute = [int]$timeParts[1]
    
    Write-Host "Trigger: Daily at $($hour.ToString('00')):$($minute.ToString('00'))" -ForegroundColor Cyan
    
    return New-ScheduledTaskTrigger `
        -Daily `
        -At ([datetime]::Today.AddHours($hour).AddMinutes($minute))
}

# Helper: Create task principal (run with highest privileges)
function New-TaskPrincipal {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    
    Write-Host "User: $currentUser" -ForegroundColor Cyan
    
    return New-ScheduledTaskPrincipal `
        -UserId $currentUser `
        -LogonType S4U `
        -RunLevel Highest
}

# Helper: Create task settings
function New-TaskSettings {
    return New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable:$false `
        -ExecutionTimeLimit (New-TimeSpan -Hours 2) `
        -RestartCount 3 `
        -RestartInterval (New-TimeSpan -Minutes 10)
}

# Main: Register task
function Register-Task {
    param([string]$Time, [switch]$DryRun)
    
    Write-Host "`n=== Registering Auto Dream Pipeline Task ===" -ForegroundColor Green
    
    if (-not (Test-Administrator)) {
        Write-Host "ERROR: This script requires Administrator privileges" -ForegroundColor Red
        Write-Host "Please run PowerShell as Administrator" -ForegroundColor Yellow
        exit 1
    }
    
    try {
        # Check if task already exists
        $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($existingTask) {
            Write-Host "Task already exists. Unregistering first..." -ForegroundColor Yellow
            if (-not $DryRun) {
                Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
            }
            Write-Host "Existing task removed" -ForegroundColor Green
        }
        
        # Create task components
        Write-Host "`nCreating task components..." -ForegroundColor White
        $action = New-TaskAction
        $trigger = New-TaskTrigger -Time $Time
        $principal = New-TaskPrincipal
        $settings = New-TaskSettings
        
        # Create task
        $task = New-ScheduledTask `
            -Action $action `
            -Trigger $trigger `
            -Principal $principal `
            -Settings $settings `
            -Description "Automatic Dream Pipeline: Resonance → Dream → Glymphatic → Memory consolidation"
        
        if ($DryRun) {
            Write-Host "`n[DRY-RUN] Would register task:" -ForegroundColor Magenta
            Write-Host "  Name: $TaskName" -ForegroundColor Gray
            Write-Host "  Time: $Time" -ForegroundColor Gray
            Write-Host "  User: $($principal.UserId)" -ForegroundColor Gray
            Write-Host "  Action: $($action.Execute) $($action.Arguments)" -ForegroundColor Gray
        }
        else {
            Register-ScheduledTask -TaskName $TaskName -InputObject $task | Out-Null
            Write-Host "`n✅ Task registered successfully!" -ForegroundColor Green
            Write-Host "   Name: $TaskName" -ForegroundColor White
            Write-Host "   Schedule: Daily at $Time" -ForegroundColor White
            Write-Host "   Next Run: $(Get-NextRunTime $Time)" -ForegroundColor Cyan
        }
        
    }
    catch {
        Write-Host "`nERROR: Failed to register task" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        exit 1
    }
}

# Main: Unregister task
function Unregister-Task {
    param([switch]$DryRun)
    
    Write-Host "`n=== Unregistering Auto Dream Pipeline Task ===" -ForegroundColor Yellow
    
    if (-not (Test-Administrator)) {
        Write-Host "ERROR: This script requires Administrator privileges" -ForegroundColor Red
        exit 1
    }
    
    try {
        $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if (-not $existingTask) {
            Write-Host "Task not found: $TaskName" -ForegroundColor Yellow
            return
        }
        
        if ($DryRun) {
            Write-Host "[DRY-RUN] Would unregister task: $TaskName" -ForegroundColor Magenta
        }
        else {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
            Write-Host "✅ Task unregistered successfully" -ForegroundColor Green
        }
        
    }
    catch {
        Write-Host "ERROR: Failed to unregister task" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        exit 1
    }
}

# Main: Check status
function Get-TaskStatus {
    Write-Host "`n=== Auto Dream Pipeline Task Status ===" -ForegroundColor Cyan
    
    try {
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        
        if (-not $task) {
            Write-Host "❌ Task not registered" -ForegroundColor Red
            Write-Host "`nTo register, run:" -ForegroundColor Yellow
            Write-Host "  .\register_auto_dream_pipeline_task.ps1 -Register -Time `"03:00`"" -ForegroundColor White
            return
        }
        
        $info = Get-ScheduledTaskInfo -TaskName $TaskName
        
        Write-Host "`n✅ Task is registered" -ForegroundColor Green
        Write-Host "`nTask Details:" -ForegroundColor White
        Write-Host "  Name: $TaskName" -ForegroundColor Gray
        Write-Host "  State: $($task.State)" -ForegroundColor $(if ($task.State -eq 'Ready') { 'Green' } else { 'Yellow' })
        Write-Host "  Last Run: $($info.LastRunTime)" -ForegroundColor Gray
        Write-Host "  Last Result: $($info.LastTaskResult) $(Get-TaskResultDescription $info.LastTaskResult)" -ForegroundColor Gray
        Write-Host "  Next Run: $($info.NextRunTime)" -ForegroundColor Cyan
        
        # Show trigger details
        $trigger = $task.Triggers[0]
        if ($trigger) {
            Write-Host "`nSchedule:" -ForegroundColor White
            Write-Host "  Type: Daily" -ForegroundColor Gray
            $startTime = [datetime]::Parse($trigger.StartBoundary)
            Write-Host "  Time: $($startTime.ToString('HH:mm'))" -ForegroundColor Gray
        }
        
        # Show action details
        $action = $task.Actions[0]
        if ($action) {
            Write-Host "`nAction:" -ForegroundColor White
            Write-Host "  Execute: $($action.Execute)" -ForegroundColor Gray
            Write-Host "  Arguments: $($action.Arguments)" -ForegroundColor Gray
        }
        
    }
    catch {
        Write-Host "ERROR: Failed to get task status" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        exit 1
    }
}

# Helper: Get next run time
function Get-NextRunTime {
    param([string]$Time)
    
    $timeParts = $Time.Split(':')
    $hour = [int]$timeParts[0]
    $minute = [int]$timeParts[1]
    
    $today = [datetime]::Today.AddHours($hour).AddMinutes($minute)
    $now = [datetime]::Now
    
    if ($today -gt $now) {
        return $today.ToString('yyyy-MM-dd HH:mm')
    }
    else {
        return $today.AddDays(1).ToString('yyyy-MM-dd HH:mm')
    }
}

# Helper: Get task result description
function Get-TaskResultDescription {
    param([int]$ResultCode)
    
    switch ($ResultCode) {
        0 { return "(Success)" }
        1 { return "(Incorrect function)" }
        267009 { return "(Task not yet run)" }
        default { return "" }
    }
}

# Main execution
try {
    # Check admin requirement
    if ((Test-RequiresAdmin -Register:$Register -Unregister:$Unregister) -and -not (Test-Administrator)) {
        Write-Host "`nERROR: This operation requires Administrator privileges" -ForegroundColor Red
        Write-Host "Please run PowerShell as Administrator" -ForegroundColor Yellow
        exit 1
    }
    
    if (-not $Register -and -not $Unregister -and -not $Status) {
        # Default to status if no action specified
        Get-TaskStatus
        exit 0
    }
    
    if ($Register) {
        Register-Task -Time $Time -DryRun:$DryRun
    }
    
    if ($Unregister) {
        Unregister-Task -DryRun:$DryRun
    }
    
    if ($Status) {
        Get-TaskStatus
    }
    
}
catch {
    Write-Host "`nFATAL ERROR" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor Gray
    exit 1
}
