param(
    [string]$Title = 'demo',
    [string]$Goal = 'AGI 자기교정 루프 설명 3문장'
)

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$repo = Split-Path -Parent $repo  # up to fdo_agi_repo

# Pick Python
$venvPy = Join-Path $repo '.venv\Scripts\python.exe'
if (Test-Path $venvPy) {
    $py = $venvPy
}
else {
    $py = 'python'
}

Write-Host "[RUN] Using Python: $py"
Write-Host "[RUN] Repo: $repo"

# Confirm LLM enabled
$appYaml = Join-Path $repo 'configs\app.yaml'
$yamlText = Get-Content -Raw $appYaml
$llmEnabled = $false
if ($yamlText -match '(?ms)llm:\s*\r?\n\s*enabled:\s*true') { $llmEnabled = $true }
Write-Host ("[CFG] LLM enabled: {0}" -f $llmEnabled)

# Ensure module path
$env:PYTHONPATH = $repo

# Run and measure
$old = Get-Location
Set-Location $repo
$sw = [System.Diagnostics.Stopwatch]::StartNew()
& $py -m scripts.run_task --title $Title --goal $Goal
$exit = $LASTEXITCODE
$sw.Stop()
Set-Location $old

Write-Host ("[TIME] ElapsedMs={0}" -f $sw.ElapsedMilliseconds)
Write-Host ("[EXIT] Code={0}" -f $exit)

# Check output file
$outFile = Join-Path $repo 'sandbox\docs\result.md'
if (Test-Path $outFile) {
    Write-Host "[OUT] sandbox/docs/result.md exists"
    Write-Host '----- tail -----'
    Get-Content $outFile -Tail 30
    Write-Host '-----------------'
}
else {
    Write-Warning "Result file not found: $outFile"
}
