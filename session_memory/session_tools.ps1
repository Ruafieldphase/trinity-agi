# Session Memory PowerShell Wrappers
# Quick commands for session management

param(
    [Parameter(Position = 0)]
    [string]$Command = "help"
)

$ErrorActionPreference = "Stop"
$SessionMemoryDir = "$PSScriptRoot"
$PythonLogger = "$SessionMemoryDir\session_logger.py"
$PythonSearch = "$SessionMemoryDir\session_search.py"

function Show-Help {
    Write-Host @"

[SEARCH] Session Memory - Quick Commands

USAGE:
    .\session_tools.ps1 <command> [args]

COMMANDS:
    start <title>         - Start new session
    task <title>          - Add task to current session
    file <path>           - Track file/artifact
    end [score]           - End current session (score: 0.0-1.0)
    pause                 - Pause current session
    resume <id>           - Resume paused session
    
    search <query>        - Full-text search
    recent [N]            - Show N recent sessions (default: 10)
    details <id>          - Show session details
    active                - Show active sessions
    similar <id>          - Find similar sessions
    by-file <pattern>     - Find sessions by file
    
    export <id> <path>    - Export session to Markdown
    stats                 - Show statistics by persona

EXAMPLES:
    .\session_tools.ps1 start "BQI Phase 6 implementation"
    .\session_tools.ps1 task "Create online learner"
    .\session_tools.ps1 file "outputs/ensemble_weights.json"
    .\session_tools.ps1 end 0.9
    
    .\session_tools.ps1 search "BQI Phase 6"
    .\session_tools.ps1 recent 20
    .\session_tools.ps1 by-file "bqi_learner"

"@ -ForegroundColor Cyan
}

function Invoke-SessionCommand {
    param([string]$Cmd, [string[]]$Args)
    
    $pythonCmd = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } else { "py" }
    
    & $pythonCmd $Cmd @Args
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Command failed with exit code $LASTEXITCODE" -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

switch ($Command.ToLower()) {
    "start" {
        if ($args.Count -eq 0) {
            Write-Host "[ERROR] Error: Please provide session title" -ForegroundColor Red
            Write-Host "   Usage: .\session_tools.ps1 start `"Your session title`"" -ForegroundColor Yellow
            exit 1
        }
        
        $title = $args -join " "
        
        # Interactive prompt for optional fields
        $description = Read-Host "Description (optional)"
        $context = Read-Host "Context (optional)"
        $persona = Read-Host "Persona (optional)"
        $tags = Read-Host "Tags (comma-separated, optional)"
        
        # Build Python command
        $pyArgs = @("$PythonLogger", "start", $title)
        if ($description) { $pyArgs += @("--description", $description) }
        if ($context) { $pyArgs += @("--context", $context) }
        if ($persona) { $pyArgs += @("--persona", $persona) }
        if ($tags) { $pyArgs += @("--tags", $tags) }
        
        Invoke-SessionCommand -Cmd "python" -Args $pyArgs
    }
    
    "task" {
        if ($args.Count -eq 0) {
            Write-Host "[ERROR] Error: Please provide task title" -ForegroundColor Red
            exit 1
        }
        
        $title = $args -join " "
        Invoke-SessionCommand -Cmd $PythonLogger -Args @("task", $title)
    }
    
    "file" {
        if ($args.Count -eq 0) {
            Write-Host "[ERROR] Error: Please provide file path" -ForegroundColor Red
            exit 1
        }
        
        $filePath = $args[0]
        Invoke-SessionCommand -Cmd $PythonLogger -Args @("file", $filePath)
    }
    
    "end" {
        $score = if ($args.Count -gt 0) { $args[0] } else { $null }
        
        $pyArgs = @("$PythonLogger", "end")
        if ($score) { $pyArgs += @("--score", $score) }
        
        Invoke-SessionCommand -Cmd "python" -Args $pyArgs
    }
    
    "pause" {
        Invoke-SessionCommand -Cmd $PythonLogger -Args @("pause")
    }
    
    "resume" {
        if ($args.Count -eq 0) {
            Write-Host "[ERROR] Error: Please provide session ID" -ForegroundColor Red
            exit 1
        }
        
        Invoke-SessionCommand -Cmd $PythonLogger -Args @("resume", $args[0])
    }
    
    "search" {
        if ($args.Count -eq 0) {
            Write-Host "[ERROR] Error: Please provide search query" -ForegroundColor Red
            exit 1
        }
        
        $query = $args -join " "
        Invoke-SessionCommand -Cmd $PythonSearch -Args @("search", $query)
    }
    
    "recent" {
        $limit = if ($args.Count -gt 0) { $args[0] } else { "10" }
        Invoke-SessionCommand -Cmd $PythonSearch -Args @("recent", "--limit", $limit)
    }
    
    "details" {
        if ($args.Count -eq 0) {
            Write-Host "[ERROR] Error: Please provide session ID" -ForegroundColor Red
            exit 1
        }
        
        Invoke-SessionCommand -Cmd $PythonSearch -Args @("details", $args[0])
    }
    
    "active" {
        Invoke-SessionCommand -Cmd $PythonSearch -Args @("active")
    }
    
    "similar" {
        if ($args.Count -eq 0) {
            Write-Host "[ERROR] Error: Please provide session ID" -ForegroundColor Red
            exit 1
        }
        
        Invoke-SessionCommand -Cmd $PythonSearch -Args @("similar", $args[0])
    }
    
    "by-file" {
        if ($args.Count -eq 0) {
            Write-Host "[ERROR] Error: Please provide file pattern" -ForegroundColor Red
            exit 1
        }
        
        Invoke-SessionCommand -Cmd $PythonSearch -Args @("by-file", $args[0])
    }
    
    "export" {
        if ($args.Count -lt 2) {
            Write-Host "[ERROR] Error: Please provide session ID and output path" -ForegroundColor Red
            exit 1
        }
        
        Invoke-SessionCommand -Cmd $PythonSearch -Args @("details", $args[0], "--markdown", $args[1])
    }
    
    "stats" {
        Invoke-SessionCommand -Cmd $PythonSearch -Args @("stats")
    }
    
    "help" {
        Show-Help
    }
    
    default {
        Write-Host "[ERROR] Unknown command: $Command" -ForegroundColor Red
        Show-Help
        exit 1
    }
}
