# Real-time Event Emitter for PowerShell Scripts
# Python event_emitter.py의 PowerShell 래퍼

param(
    [Parameter(Mandatory = $true)]
    [string]$EventType,
    
    [Parameter(Mandatory = $false)]
    [hashtable]$Payload = @{},
    
    [Parameter(Mandatory = $false)]
    [string]$TaskId,
    
    [Parameter(Mandatory = $false)]
    [string]$SessionId,
    
    [Parameter(Mandatory = $false)]
    [string]$PersonaId
)

$ErrorActionPreference = 'Stop'

# Find Python
$RepoRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $RepoRoot "fdo_agi_repo\.venv\Scripts\python.exe"

if (Test-Path $VenvPython) {
    $Python = $VenvPython
}
elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $Python = "python"
}
else {
    Write-Warning "[EventEmitter] Python not found, skipping event emission"
    exit 0  # Silent failure
}

# Build Python code
$PayloadJson = $Payload | ConvertTo-Json -Compress -Depth 5
$PayloadBase64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($PayloadJson))
$PythonCode = @"
import sys
sys.path.insert(0, r'$RepoRoot\fdo_agi_repo')

from orchestrator.event_emitter import emit_event
import json
import base64

payload = json.loads(base64.b64decode('$PayloadBase64').decode('utf-8'))
kwargs = {}
if '$TaskId': kwargs['task_id'] = '$TaskId'
if '$SessionId': kwargs['session_id'] = '$SessionId'
if '$PersonaId': kwargs['persona_id'] = '$PersonaId'

success = emit_event('$EventType', payload, **kwargs)
sys.exit(0 if success else 1)
"@

# Execute
try {
    & $Python -c $PythonCode
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "[EventEmitter] Failed to emit event: $EventType"
    }
}
catch {
    Write-Warning "[EventEmitter] Exception: $_"
}
