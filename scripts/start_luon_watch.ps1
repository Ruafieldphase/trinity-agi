param(
    [int]$IntervalSeconds = 15,
    [switch]$KillExisting,
    [string]$LogDirectory = "$PSScriptRoot\..\logs"
)

$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf-8"

# Prefer workspace .venv Python, fallback to system path
$venvPython = Join-Path "$PSScriptRoot\.." ".venv\Scripts\python.exe"
$pythonExe = if (Test-Path $venvPython) { $venvPython } else { "C:\\Python313\\python.exe" }
$baseRoot = "C:\workspace\agi\ai_binoche_conversation_origin"
$kpiPath = "C:\workspace\agi\outputs\copilot_kpi.csv"

if (-not (Test-Path $pythonExe)) { throw "Python executable not found at $pythonExe" }
if (-not (Test-Path $baseRoot)) { throw "Base directory not found at $baseRoot" }
if (-not (Test-Path $kpiPath)) { throw "KPI file not found at $kpiPath" }

$lumenPath = Join-Path $baseRoot "lumen"
$toolsRoot = Get-ChildItem -Path $lumenPath -Directory |
Where-Object { Test-Path (Join-Path $_.FullName "luon_watch_loop_auto.py") } |
Select-Object -First 1
if (-not $toolsRoot) { throw "Could not locate luon_watch_loop_auto.py under $lumenPath" }

$watchScript = Join-Path $toolsRoot.FullName "luon_watch_loop_auto.py"
$outdir = Join-Path $baseRoot "luon"
$roots = @(
    (Join-Path $baseRoot "cladeCLI-sena"),
    (Join-Path $baseRoot "lubit"),
    (Join-Path $baseRoot "gemini-sian")
)

if ($KillExisting) {
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
    Where-Object { $_.CommandLine -like "*luon_watch_loop_auto.py*" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
}

$argList = @($watchScript, "--roots") + $roots + @(
    "--outdir", $outdir,
    "--tools", $toolsRoot.FullName,
    "--interval", $IntervalSeconds.ToString(),
    "--dispatch",
    "--report",
    "--kpi", $kpiPath
)

$logDirFull = [System.IO.Path]::GetFullPath($LogDirectory)
if (-not (Test-Path $logDirFull)) { New-Item -ItemType Directory -Path $logDirFull | Out-Null }

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$stdoutLog = Join-Path $logDirFull "luon_watch_$timestamp.out.log"
$stderrLog = Join-Path $logDirFull "luon_watch_$timestamp.err.log"

$process = Start-Process -FilePath $pythonExe -ArgumentList $argList -WindowStyle Hidden -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog -PassThru

Write-Host "Luon watch loop started (PID=$($process.Id), interval=$IntervalSeconds s)."
Write-Host "Logs:"
Write-Host "  stdout -> $stdoutLog"
Write-Host "  stderr -> $stderrLog"
