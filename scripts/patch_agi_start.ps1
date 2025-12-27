$Path = "C:\workspace\agi\scripts\agi_session_start.ps1"
$Content = Get-Content -Raw $Path

# Remove the old incorrect placement
$OldPattern = '(?s)# Restore Codex Session.*?Write-Warning "No active Codex session found. A new one will be created."\r?\n\}'
# Actually it's easier to just read the whole file and replace the block.
# I'll use a simpler search.

# Pattern for the insertion point (after Clear-Host)
$TargetPattern = 'Clear-Host'

# The block to move
$RestorationBlock = @"
# Restore Codex Session
Write-Header "Checking Codex Session..."
`$LastSessionId = python (Join-Path `$PSScriptRoot "get_last_codex_session.py")
if (`$LASTEXITCODE -eq 0 -and `$LastSessionId) {
    `$env:CODEX_SESSION_ID = `$LastSessionId.Trim()
    Write-Success "Restored Codex Session: `$env:CODEX_SESSION_ID"
}
else {
    Write-Warning "No active Codex session found. A new one will be created."
}
"@

# Remove the previously added block first (it was after the QuickStart line)
$Content = $Content -replace '(?s)# Restore Codex Session.*?Write-Warning "No active Codex session found. A new one will be created."\r?\n\}', ''

# Inject after Clear-Host
if ($Content -match $TargetPattern) {
    $NewContent = $Content -replace $TargetPattern, "$TargetPattern`r`n$RestorationBlock"
    $NewContent | Set-Content -Path $Path -Encoding UTF8
    Write-Host "Success: Codex session restoration moved after Clear-Host."
}
else {
    # If Clear-Host not found (silent mode?), just put it at start of try block
    $TryPattern = 'try \{'
    if ($Content -match $TryPattern) {
        $NewContent = $Content -replace $TryPattern, "$TryPattern`r`n$RestorationBlock"
        $NewContent | Set-Content -Path $Path -Encoding UTF8
        Write-Host "Success: Codex session restoration added to try block."
    }
    else {
        Write-Error "Error: Could not find insertion point."
        exit 1
    }
}
