# Load Testing Automation Script
# Runs all 4 load test scenarios and saves results

param(
    [string]$ApiServiceUrl = "https://ion-api-x4qvsargwa-uc.a.run.app",
    [string]$OutputDir = "outputs",
    # Accept comma-separated profiles as well as single value
    [string]$ScenarioProfile = 'all',
    [string]$OverrideRunTime = '',
    [switch]$NoSummary,
    [switch]$Strict,
    [switch]$WithHtml,
    [switch]$WithSuccessRate,
    [switch]$Help
)

if ($Help) {
    Write-Host @"
Usage: run_all_load_tests.ps1 [-ApiServiceUrl <url>] [-OutputDir <dir>] [-ScenarioProfile <all|light|medium|heavy|stress|comma-list>]
                              [-OverrideRunTime <e.g., 2m>] [-NoSummary] [-Strict] [-WithHtml] [-WithSuccessRate]

Examples:
  powershell -File scripts/run_all_load_tests.ps1 -ScenarioProfile light -OverrideRunTime 10s -WithSuccessRate -WithHtml
  powershell -File scripts/run_all_load_tests.ps1 -ScenarioProfile light,medium -OverrideRunTime 2m -Strict
"@
    exit 0
}

function Invoke-LocustScenario {
    param(
        [string]$Label,
        [int]$Users,
        [double]$SpawnRate,
        [string]$RunTime,
        [string]$Suffix
    )

    Write-Host $Label -ForegroundColor Yellow
    $csvPrefix = Join-Path $OutputDir ("load_test_{0}_{1}" -f $Suffix, $timestamp)
    $htmlPath = Join-Path $OutputDir ("load_test_{0}_{1}.html" -f $Suffix, $timestamp)
    $arguments = @(
        '-m', 'locust',
        '-f', $Global:LocustFile,
        "--host=$ApiServiceUrl",
        '--users', $Users.ToString(),
        '--spawn-rate', $SpawnRate.ToString(),
        '--run-time', $RunTime,
        '--headless',
        "--csv=$csvPrefix"
    )
    if ($WithHtml) {
        $arguments += @('--html', $htmlPath)
    }

    & $PythonCommand $arguments
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Locust command exited with code $LASTEXITCODE" -ForegroundColor Red
        if ($Strict) { exit $LASTEXITCODE }
    }

    # Track generated stats CSV for summary later
    $statsCsv = "${csvPrefix}_stats.csv"
    if (Test-Path $statsCsv) {
        $Global:GeneratedCsvs += $statsCsv
    }
    else {
        Write-Host "Warning: Expected stats CSV not found: $statsCsv" -ForegroundColor DarkYellow
    }
}

# Allow environment variable override if parameter not explicitly provided
if ($env:ION_API_HOST -and -not $PSBoundParameters.ContainsKey('ApiServiceUrl')) {
    $ApiServiceUrl = $env:ION_API_HOST
}

# Resolve paths
$scriptRoot = $PSScriptRoot
$ionRoot = Resolve-Path (Join-Path $scriptRoot '..')
$repoRoot = Resolve-Path (Join-Path $ionRoot '..')

# Resolve Python: prefer repo venv (LLM_Unified/.venv), then user site, then system
$repoVenvPython = Join-Path $repoRoot '.venv\Scripts\python.exe'
if (Test-Path $repoVenvPython) {
    $PythonCommand = $repoVenvPython
}
else {
    $pythonScripts = Join-Path ([System.Environment]::GetFolderPath('ApplicationData')) 'Python\Python313\Scripts'
    if (-not ($env:PATH -split ';' | Where-Object { $_ -eq $pythonScripts })) {
        $env:PATH += ";$pythonScripts"
    }
    $PythonCommand = 'python'
}
$env:PYTHONUTF8 = '1'

# Locust script absolute path
$Global:LocustFile = Join-Path $ionRoot 'load_test.py'
if (!(Test-Path $Global:LocustFile)) {
    throw "Locust file not found: $Global:LocustFile"
}

# Normalize OutputDir to absolute path under ion-mentoring if relative
if (-not [System.IO.Path]::IsPathRooted($OutputDir)) {
    $OutputDir = Join-Path $ionRoot $OutputDir
}
if (!(Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Global:GeneratedCsvs = @()

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ION Mentoring API - Load Testing Suite" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Configuration" -ForegroundColor White
$displayOverride = $(if ($OverrideRunTime) { $OverrideRunTime } else { '(default per scenario)' })
Write-Host ("  API Host        : {0}" -f $ApiServiceUrl) -ForegroundColor Gray
Write-Host ("  Profile         : {0}" -f $ScenarioProfile) -ForegroundColor Gray
Write-Host ("  Override RunTime: {0}" -f $displayOverride) -ForegroundColor Gray
Write-Host ("  Output Dir      : {0}" -f $OutputDir) -ForegroundColor Gray
Write-Host ("  Python Command  : {0}" -f $PythonCommand) -ForegroundColor Gray
Write-Host ("  Locust File     : {0}" -f $Global:LocustFile) -ForegroundColor Gray
Write-Host ("  Write Summary   : {0}" -f ($(if ($NoSummary) { 'No' }else { 'Yes' }))) -ForegroundColor Gray
Write-Host ("  Strict Fail     : {0}" -f ($(if ($Strict) { 'Yes' } else { 'No' }))) -ForegroundColor Gray
Write-Host ("  With HTML       : {0}" -f ($(if ($WithHtml) { 'Yes' } else { 'No' }))) -ForegroundColor Gray
Write-Host ("  Success Rate Col: {0}" -f ($(if ($WithSuccessRate) { 'Yes' } else { 'No' }))) -ForegroundColor Gray
Write-Host ""

# Default runtimes
$rtLight = if ($OverrideRunTime) { $OverrideRunTime } else { '2m' }
$rtMedium = if ($OverrideRunTime) { $OverrideRunTime } else { '5m' }
$rtHeavy = if ($OverrideRunTime) { $OverrideRunTime } else { '5m' }
$rtStress = if ($OverrideRunTime) { $OverrideRunTime } else { '10m' }

# Build dynamic scenario list (support comma-separated profiles)
$toRun = @()
$profiles = @()
if ($ScenarioProfile -eq 'all') {
    $profiles = @('light', 'medium', 'heavy', 'stress')
}
else {
    $profiles = ($ScenarioProfile -split ',') | ForEach-Object { $_.Trim().ToLower() } | Where-Object { $_ -ne '' }
}
foreach ($p in $profiles) {
    switch ($p) {
        'light' { $toRun += @{ label = "Running Light Load Test (10 users, $rtLight)..."; users = 10; rate = 1; runtime = $rtLight; suffix = 'light'; pause = 30 } }
        'medium' { $toRun += @{ label = "Running Medium Load Test (50 users, $rtMedium)..."; users = 50; rate = 5; runtime = $rtMedium; suffix = 'medium'; pause = 60 } }
        'heavy' { $toRun += @{ label = "Running Heavy Load Test (100 users, $rtHeavy)..."; users = 100; rate = 10; runtime = $rtHeavy; suffix = 'heavy'; pause = 60 } }
        'stress' { $toRun += @{ label = "Running Stress Test (200 users, $rtStress)..."; users = 200; rate = 20; runtime = $rtStress; suffix = 'stress'; pause = 0 } }
        default { Write-Host "Warning: Unknown profile '$p' ignored." -ForegroundColor DarkYellow }
    }
}

if ($toRun.Count -eq 0) {
    Write-Host "No scenarios to run for ScenarioProfile='$ScenarioProfile'" -ForegroundColor Red
    exit 2
}

$total = $toRun.Count
for ($i = 0; $i -lt $total; $i++) {
    $s = $toRun[$i]
    $stepLabel = "[{0}/{1}] {2}" -f ($i + 1), $total, $s.label
    Invoke-LocustScenario $stepLabel $s.users $s.rate $s.runtime $s.suffix
    Write-Host ("[OK] {0} complete." -f ($s.suffix.Substring(0, 1).ToUpper() + $s.suffix.Substring(1))) -ForegroundColor Green
    if ($ScenarioProfile -eq 'all' -and $s.pause -gt 0 -and $i -lt ($total - 1)) { Write-Host ""; Start-Sleep -Seconds $s.pause }
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "All Tests Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Results saved to:" -ForegroundColor White
foreach ($f in $Global:GeneratedCsvs) {
    Write-Host "  - $f" -ForegroundColor Gray
}
Write-Host ""
if (-not $NoSummary) {
    Write-Host "Generating Markdown summary..." -ForegroundColor White
    $summarizer = Join-Path $ionRoot 'scripts\summarize_locust_csv.py'
    if ((Test-Path $summarizer -PathType Leaf) -and ($Global:GeneratedCsvs.Count -gt 0)) {
        # Generate UTF-8 summary file via Python (preserve emojis), then print ASCII preview to console
        $summaryFile = Join-Path $OutputDir ("summary_{0}_{1}.md" -f $ScenarioProfile, $timestamp)
        $displayOverrideForSummary = $(if ($OverrideRunTime) { $OverrideRunTime } else { '(default per scenario)' })
        $configLines = @(
            "API Host        : $ApiServiceUrl",
            "Profile         : $ScenarioProfile",
            "Override RunTime: $displayOverrideForSummary",
            "Output Dir      : $OutputDir",
            "Python Command  : $PythonCommand",
            "Locust File     : $Global:LocustFile"
        )
        if ($Global:GeneratedCsvs.Count -gt 0) {
            $configLines += "Stats CSVs      :"
            foreach ($csv in $Global:GeneratedCsvs) { $configLines += "  - $csv" }
        }
        $configBlock = "~~~text`r`n" + ($configLines -join "`r`n") + "`r`n~~~" + "`r`n`r`n"
        $header = "# Load Test Summary ($ScenarioProfile) - $timestamp`r`n`r`n" + $configBlock
        # Let Python write the table directly to a temp file to preserve UTF-8 emojis
        $summaryTmp = Join-Path $OutputDir ("summary_table_{0}.md" -f $timestamp)
        $sumArgsOut = @('-X', 'utf8', $summarizer, '--out', $summaryTmp)
        if ($ScenarioProfile -eq 'all' -and $Global:GeneratedCsvs.Count -gt 1) {
            $sumArgsOut += @('--with-overall')
        }
        if ($WithSuccessRate) {
            $sumArgsOut += @('--with-success-rate')
        }
        $sumArgsOut += $Global:GeneratedCsvs
        & $PythonCommand $sumArgsOut 2>&1 | Out-Null
        $pyExit = $LASTEXITCODE
        if ($pyExit -ne 0) {
            Write-Host ("Summarizer exited with code {0}." -f $pyExit) -ForegroundColor DarkYellow
            if ($Strict) { exit $pyExit }
        }
        # Verify temp summary file exists before attempting to read it
        if (-not (Test-Path -Path $summaryTmp)) {
            Write-Host ("ERROR: Summarizer did not produce expected temp file: {0}" -f $summaryTmp) -ForegroundColor Red
            Write-Host "This usually indicates a bug in the summarizer script. Check the output above for errors." -ForegroundColor Red
            if ($Strict) { exit 1 }
            return
        }
        # Prepend header + config to the table while keeping UTF-8 intact via .NET APIs
        $tableContent = [System.IO.File]::ReadAllText($summaryTmp, [System.Text.Encoding]::UTF8)
        $combined = $header + $tableContent
        $utf8WithBom = New-Object System.Text.UTF8Encoding($true)
        [System.IO.File]::WriteAllText($summaryFile, $combined, $utf8WithBom)
        Remove-Item -Path $summaryTmp -ErrorAction SilentlyContinue
        # Update a convenient latest pointer file
        $latestSummary = Join-Path $OutputDir "summary_latest.md"
        try {
            Copy-Item -Path $summaryFile -Destination $latestSummary -Force
        }
        catch {
            Write-Host ("Warning: Failed to update latest summary pointer: {0}" -f $_) -ForegroundColor DarkYellow
        }
        # Also print ASCII status table to console for readability
        $sumArgsAscii = @('-X', 'utf8', $summarizer, '--ascii-status')
        if ($ScenarioProfile -eq 'all' -and $Global:GeneratedCsvs.Count -gt 1) {
            $sumArgsAscii += @('--with-overall')
        }
        if ($WithSuccessRate) {
            $sumArgsAscii += @('--with-success-rate')
        }
        $sumArgsAscii += $Global:GeneratedCsvs
        $consoleTable = & $PythonCommand $sumArgsAscii 2>&1
        Write-Host "Summary written to: $summaryFile" -ForegroundColor Green
        Write-Host ""
        Write-Host ($consoleTable -join "`r`n")
    }
    else {
        Write-Host "Skipping summary: summarizer not found or no CSVs generated." -ForegroundColor DarkYellow
        if ($Strict) { exit 1 }
    }
}
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Review CSV files and summary for detailed statistics" -ForegroundColor Gray
Write-Host "  2. Check Cloud Monitoring dashboard for metrics" -ForegroundColor Gray
Write-Host "  3. Update LOAD_TESTING.md with measured benchmarks" -ForegroundColor Gray
Write-Host "  4. Include results in WEEK3_SUMMARY.md" -ForegroundColor Gray
Write-Host ""

exit 0
