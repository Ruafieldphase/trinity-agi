param(
    [string]$Agents = "all",
    [switch]$NoImmediate
)

# Resolve paths
$IonRoot = (Resolve-Path "$PSScriptRoot\..\").Path
$ProjectRoot = (Resolve-Path "$IonRoot\..\").Path
$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Runner = Join-Path $IonRoot "inbox_watcher_runner.py"
$LogDir = Join-Path $IonRoot "logs"
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }
$LogFile = Join-Path $LogDir "inbox_watcher.log"

if (-not (Test-Path $PythonExe)) {
    Write-Error "Python venv not found: $PythonExe"
    exit 1
}
if (-not (Test-Path $Runner)) {
    Write-Error "Runner not found: $Runner"
    exit 1
}

$argsList = @($Runner, "--agents", $Agents)
if ($NoImmediate) { $argsList += "--no-immediate" }

# Start hidden and redirect stdout/stderr to log
Start-Process -FilePath $PythonExe -ArgumentList $argsList -WorkingDirectory $IonRoot -WindowStyle Hidden -RedirectStandardOutput $LogFile -RedirectStandardError $LogFile | Out-Null
Write-Host "Inbox watcher started (agents=$Agents). Log: $LogFile"
