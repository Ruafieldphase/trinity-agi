#requires -Version 5.1
# Observe active window/process telemetry and write JSONL for later summarization.
# - Polls foreground window at a fixed interval
# - Captures timestamp (UTC), process name/id, window title
# - Heuristics for VS Code: attempts to guess current file from window title
# - Writes to outputs/telemetry/stream_observer.jsonl (rotates daily)
#
# Params:
#  -IntervalSeconds: polling interval in seconds (default 5)
#  -DurationSeconds: optional total run time; if 0, run indefinitely
#  -OutDir: output directory (default: outputs/telemetry)
# Example:
#  powershell -File scripts/observe_desktop_telemetry.ps1 -IntervalSeconds 2 -DurationSeconds 60
param(
    [int]$IntervalSeconds = 5,
    [int]$DurationSeconds = 0,
    [string]$OutDir = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\telemetry"
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Ensure output directory
$OutDir = [IO.Path]::GetFullPath($OutDir)
if (-not (Test-Path -LiteralPath $OutDir)) {
    try {
        New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
    }
    catch {
        Write-Host "[observer] ERROR: Cannot create output directory: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

# PID file for graceful stop/helpers
$PidFile = Join-Path $OutDir 'observer_telemetry.pid'
try {
    Set-Content -LiteralPath $PidFile -Value $PID -Encoding ascii -Force
}
catch {
    Write-Host "[observer] Warning: failed to write PID file: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Helpers: user32 interop to get active window title and process id
try {
    Add-Type -Namespace Win32 -Name NativeMethods -MemberDefinition @"
  [System.Runtime.InteropServices.DllImport("user32.dll")] public static extern System.IntPtr GetForegroundWindow();
  [System.Runtime.InteropServices.DllImport("user32.dll")] public static extern int GetWindowText(System.IntPtr hWnd, System.Text.StringBuilder text, int count);
  [System.Runtime.InteropServices.DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(System.IntPtr hWnd, out uint lpdwProcessId);
"@ -ErrorAction SilentlyContinue
}
catch {
    # Type already exists - this is fine in repeated runs
    if ($_.Exception.Message -notmatch "already exists") {
        Write-Host "[observer] Warning: Add-Type failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

function Get-ForegroundWindowInfo {
    $h = [Win32.NativeMethods]::GetForegroundWindow()
    if ($h -eq [System.IntPtr]::Zero) { return $null }
    $sb = New-Object System.Text.StringBuilder 1024
    [void][Win32.NativeMethods]::GetWindowText($h, $sb, $sb.Capacity)
    # NOTE: PowerShell is case-insensitive, so using $PID as an out var name collides with the built-in $PID.
    # Use a distinct local variable to avoid "Cannot overwrite variable PID" errors.
    [uint32]$fgProcId = 0
    [void][Win32.NativeMethods]::GetWindowThreadProcessId($h, [ref]$fgProcId)
    if ($fgProcId -eq 0) { return $null }
    try {
        $p = Get-Process -Id $fgProcId -ErrorAction Stop
    }
    catch { return $null }
    [pscustomobject]@{
        Handle      = $h
        ProcessId   = [int]$fgProcId
        ProcessName = $p.ProcessName
        Title       = $sb.ToString()
    }
}

function Get-VSCodeFileGuess([string]$title) {
    if (-not $title) { return $null }
    # Common patterns: "filename – workspace – Visual Studio Code" or "filename (Workspace) - Visual Studio Code"
    $t = $title
    # Split on " - Visual Studio Code" or " — Visual Studio Code"
    if ($t -match "\s[-—]\sVisual Studio Code") {
        $before = $t -replace "\s[-—]\sVisual Studio Code$", ""
        # Further split by dashes/parentheses; pick left-most segment as probable file name
        $parts = $before -split "\s[-—]\s|\s\(|\)"
        if ($parts.Count -gt 0) { return ($parts[0].Trim()) }
    }
    return $null
}

$start = Get-Date
$deadline = if ($DurationSeconds -gt 0) { $start.AddSeconds($DurationSeconds) } else { [datetime]::MaxValue }

function Get-OutputPathForNow([datetime]$ts) {
    $dateStr = $ts.ToString('yyyy-MM-dd')
    return (Join-Path $OutDir "stream_observer_$dateStr.jsonl")
}

$lastPath = $null

Write-Host "[observer] Starting telemetry. Interval=${IntervalSeconds}s Duration=${DurationSeconds}s OutDir=$OutDir" -ForegroundColor Cyan

try {
    while ($true) {
        $now = [datetime]::UtcNow
        if ($now -ge $deadline) { break }

        try {
            $info = Get-ForegroundWindowInfo
            if ($info -ne $null) {
                $isVSCode = ($info.ProcessName -ieq 'Code' -or $info.ProcessName -ieq 'Code - Insiders')
                $guess = if ($isVSCode) { Get-VSCodeFileGuess $info.Title } else { $null }

                $record = [ordered]@{
                    ts_utc            = $now.ToString('o')
                    process_name      = $info.ProcessName
                    process_id        = $info.ProcessId
                    window_title      = $info.Title
                    is_vscode         = [bool]$isVSCode
                    vscode_file_guess = $guess
                }

                $outPath = Get-OutputPathForNow -ts $now
                if ($outPath -ne $lastPath) {
                    # announce rotation
                    Write-Host "[observer] writing -> $outPath" -ForegroundColor DarkGray
                    $lastPath = $outPath
                }
                $json = ($record | ConvertTo-Json -Compress)
                Add-Content -LiteralPath $outPath -Value $json
            }
        }
        catch {
            Write-Host "[observer] Warning: Poll error: $($_.Exception.Message)" -ForegroundColor Yellow
            # Continue polling despite errors
        }

        Start-Sleep -Seconds $IntervalSeconds
    }
}
catch {
    Write-Host "[observer] FATAL: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor Red
    exit 1
}

Write-Host "[observer] Stopped. Duration: $([int]((Get-Date)-$start).TotalSeconds)s" -ForegroundColor Green

# Cleanup PID file if it still points to this process
try {
    if (Test-Path -LiteralPath $PidFile) {
        $pidText = Get-Content -LiteralPath $PidFile -ErrorAction SilentlyContinue | Select-Object -First 1
        [int]$parsed = 0
        $ok = [int]::TryParse($pidText, [ref]$parsed)
        if ($ok -and $parsed -eq $PID) {
            Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue
        }
    }
}
catch {
    # ignore
}

exit 0