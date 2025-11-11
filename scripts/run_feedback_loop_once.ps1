# Auto-generated. Do not edit.
param()
$py = "C:\workspace\agi\LLM_Unified\.venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $py)) { $py = "C:\workspace\agi\fdo_agi_repo\.venv\Scripts\python.exe" }
if (-not (Test-Path -LiteralPath $py)) { $py = 'python' }
& $py "C:\workspace\agi\fdo_agi_repo\scripts\rune\feedback_loop_once.py" | Write-Output
