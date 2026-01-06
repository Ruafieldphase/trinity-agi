# Auto-generated. Do not edit.
param()
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot

$py = "$WorkspaceRoot\LLM_Unified\.venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $py)) { $py = "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe" }
if (-not (Test-Path -LiteralPath $py)) { $py = 'python' }
& $py "$WorkspaceRoot\fdo_agi_repo\scripts\rune\feedback_loop_once.py" | Write-Output