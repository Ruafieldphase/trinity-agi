param(
    [string]$LogDirectory = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\logs",
    [switch]$StopOnError
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot



$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Ensure headless plots for CI/servers
$env:MPLBACKEND = "Agg"

# Prefer workspace .venv
$venvPython = Join-Path "$PSScriptRoot\.." ".venv\Scripts\python.exe"
$pythonExe = if (Test-Path $venvPython) { $venvPython } else { "C:\\Python313\\python.exe" }
if (-not (Test-Path $pythonExe)) { throw "Python executable not found at $pythonExe" }

$root = "$WorkspaceRoot"
$corpus = Join-Path $root "outputs\run_corpus_adapter.py"
$build = Join-Path $root "outputs\build_events.py"
$schema = Join-Path $root "outputs\derive_schema.py"
$runScripts = @(
    (Join-Path $root "outputs\run_autotuner_kpi.py"),
    (Join-Path $root "outputs\run_creative_band.py"),
    (Join-Path $root "outputs\run_dashboard.py"),
    (Join-Path $root "outputs\run_exec_report.py"),
    (Join-Path $root "outputs\run_queue.py")
)

$logDirFull = [System.IO.Path]::GetFullPath($LogDirectory)
if (-not (Test-Path $logDirFull)) { New-Item -ItemType Directory -Path $logDirFull | Out-Null }
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$log = Join-Path $logDirFull "luon_pipeline_$ts.log"

function Invoke-PipelineStep {
    param(
        [string]$Command,
        [string[]]$CommandArgs
    )
    Write-Host "==> $Command $($CommandArgs -join ' ')"
    # Prevent native stderr from being promoted to a terminating error while still capturing it
    $oldEAP = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        Set-Variable -Name LASTEXITCODE -Scope Global -Value 0
        $output = & $Command @CommandArgs 2>&1 | ForEach-Object {
            if ($_ -is [System.Management.Automation.ErrorRecord]) {
                $_.ToString()
            }
            else {
                $_
            }
        }
        if ($null -ne $output) {
            $output | Tee-Object -FilePath $log -Append | ForEach-Object { Write-Host $_ }
        }
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $oldEAP
    }
    if ($exitCode -ne 0) {
        Write-Error "Step failed: $Command"
        if ($StopOnError) { throw "Aborting due to error" }
    }
}

# Pipeline: corpus_adapter -> build_events -> derive_schema -> run_*
if (Test-Path $corpus) { Invoke-PipelineStep -Command $pythonExe -CommandArgs @($corpus) }
Invoke-PipelineStep -Command $pythonExe -CommandArgs @($build)
Invoke-PipelineStep -Command $pythonExe -CommandArgs @($schema)
foreach ($s in $runScripts) { if (Test-Path $s) { Invoke-PipelineStep -Command $pythonExe -CommandArgs @($s) } }

Write-Host "Pipeline completed. Logs: $log"