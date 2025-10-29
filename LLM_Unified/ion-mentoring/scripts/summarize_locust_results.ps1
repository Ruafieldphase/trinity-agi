Param(
    [Parameter(Mandatory = $false)]
    [string]$InputGlob = "*.csv",

    [Parameter(Mandatory = $false)]
    [string]$OutputPath = ""
)

$ErrorActionPreference = "Stop"

# Resolve script paths
$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$PythonExe = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$Summarizer = Join-Path $PSScriptRoot "summarize_locust_csv.py"

if (-not (Test-Path $PythonExe)) {
    Write-Error "Python venv not found: $PythonExe"
}
if (-not (Test-Path $Summarizer)) {
    Write-Error "Summarizer not found: $Summarizer"
}

$files = Get-ChildItem -Path $InputGlob -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "*_stats.csv" }
if (-not $files -or $files.Count -eq 0) {
    Write-Warning "No matching *_stats.csv files for glob: $InputGlob"
}

$cmd = @($PythonExe, $Summarizer)
foreach ($f in $files) { $cmd += $f.FullName }
$cmd += @("--ascii-status", "--with-success-rate", "--with-overall")

if ($OutputPath -and $OutputPath.Trim() -ne "") {
    $cmd += @("--out", $OutputPath)
}

Write-Host "Running:" -ForegroundColor Cyan
Write-Host ($cmd -join " ") -ForegroundColor Gray

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $cmd[0]
$psi.Arguments = ($cmd[1..($cmd.Count - 1)] -join " ")
$psi.RedirectStandardOutput = $false
$psi.RedirectStandardError = $false
$psi.UseShellExecute = $true

$proc = [System.Diagnostics.Process]::Start($psi)
$proc.WaitForExit()
exit $proc.ExitCode
