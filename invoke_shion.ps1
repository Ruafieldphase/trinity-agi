param(
    [Parameter(Mandatory = $false)]
    [string]$WorkspaceRoot = $PSScriptRoot,

    [Parameter(Mandatory = $false)]
    [string]$PythonwPath,

    [Parameter(Mandatory = $false)]
    [string]$Reason = "manual",

    [Parameter(Mandatory = $false)]
    [int]$WaitSeconds = 1
)

$ErrorActionPreference = "Stop"

function Resolve-PythonwPath {
    param([string]$Provided)

    if ($Provided -and (Test-Path -LiteralPath $Provided)) {
        return (Resolve-Path -LiteralPath $Provided).Path
    }

    $cmd = Get-Command "pythonw.exe" -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source) {
        return $cmd.Source
    }

    $py = Get-Command "python.exe" -ErrorAction SilentlyContinue
    if ($py -and $py.Source) {
        $candidate = Join-Path (Split-Path -Parent $py.Source) "pythonw.exe"
        if (Test-Path -LiteralPath $candidate) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }

    throw "pythonw.exe not found. Provide -PythonwPath or add it to PATH."
}

function Stop-ShionProcess {
    param([string]$ShionPath)

    $targets = Get-CimInstance Win32_Process | Where-Object {
        $_.CommandLine -and ($_.Name -ieq "pythonw.exe" -or $_.Name -ieq "python.exe") -and ($_.CommandLine -like "*$ShionPath*")
    }

    foreach ($p in $targets) {
        try {
            Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
        }
        catch {
        }
    }
}

$WorkspaceRoot = (Resolve-Path -LiteralPath $WorkspaceRoot).Path
$PythonwPath = Resolve-PythonwPath -Provided $PythonwPath
$ShionPath = Join-Path $WorkspaceRoot "agi\shion.py"

# Stop existing Shion process
Stop-ShionProcess -ShionPath $ShionPath

# Wait for clean shutdown
Start-Sleep -Seconds $WaitSeconds

# Start Silent Heart (Shion)
Start-Process `
    -FilePath $PythonwPath `
    -ArgumentList "`"$ShionPath`" --silent-mode" `
    -WindowStyle Hidden `
    -WorkingDirectory $WorkspaceRoot | Out-Null
