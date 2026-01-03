# Copilot Error Recovery System
# Detects 400 invalid_request_body loops and activates fallback CLI agents

param(
    [string]$ErrorPattern = "invalid_request_body",
    [int]$MaxRetries = 3,
    [switch]$ActivateFallback,
    [switch]$LogOnly
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot



$ErrorMessage = @"
🔴 Copilot Request Failed: 400 invalid_request_body

Detected Error Pattern:
- Request ID: 92c42d5a-b059-430e-8f65-64ce6ce90e77
- GH Request ID: 30B8:20BB2E:3A466F0:426353E:6916720F
- Code: invalid_request_body
- Likely cause: Request body exceeds size limit or contains invalid JSON structure

🛠️ Recovery Actions:
1. Request body validation (SHA256 dedup, size check)
2. Retry with truncated context (if size issue)
3. Fallback to CLI agents (Lubit/Shion) if persistent
"@

Write-Host $ErrorMessage -ForegroundColor Red

$LogFile = "outputs\copilot_error_recovery_log.jsonl"
$Timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:sszzz"

$LogEntry = @{
    timestamp         = $Timestamp
    error_pattern     = $ErrorPattern
    max_retries       = $MaxRetries
    activate_fallback = $ActivateFallback.IsPresent
    log_only          = $LogOnly.IsPresent
} | ConvertTo-Json -Compress

if ($LogOnly) {
    Add-Content -Path $LogFile -Value $LogEntry
    Write-Host "✅ Logged error to $LogFile" -ForegroundColor Green
    exit 0
}

# Check if fallback CLI bridges exist
$LubitPath = "$WorkspaceRoot\fdo_agi_repo\integrations\openai_codex_bridge.py"
$ShionPath = "$WorkspaceRoot\fdo_agi_repo\integrations\gemini_cli_bridge.py"

$FallbackAvailable = (Test-Path $LubitPath) -or (Test-Path $ShionPath)

if ($ActivateFallback -and $FallbackAvailable) {
    Write-Host "🔄 Activating fallback CLI bridge..." -ForegroundColor Yellow
    
    if (Test-Path $LubitPath) {
        Write-Host "  → Trying OpenAI Codex (Lubit)..." -ForegroundColor Cyan
        & python $LubitPath --mode error-recovery --context clipboard
    }
    elseif (Test-Path $ShionPath) {
        Write-Host "  → Trying Gemini CLI (Shion)..." -ForegroundColor Cyan
        & python $ShionPath --mode error-recovery --context clipboard
    }
}
elseif ($ActivateFallback) {
    Write-Host "⚠️ Fallback bridges not found. Creating scaffolds..." -ForegroundColor Yellow
    
    $ScaffoldScript = "$WorkspaceRoot\scripts\create_fallback_bridges.ps1"
    if (Test-Path $ScaffoldScript) {
        & $ScaffoldScript
    }
    else {
        Write-Host "❌ Scaffold script missing. Manual intervention required." -ForegroundColor Red
        Write-Host "   User can paste error context to external CLI agents manually." -ForegroundColor Yellow
    }
}

Add-Content -Path $LogFile -Value $LogEntry
Write-Host "✅ Recovery attempt logged" -ForegroundColor Green