# Extended Load Testing Automation Script
# Runs baseline + additional scenarios (spike, edge, chat-only, optional soak)

param(
    [string]$ApiServiceUrl = "https://ion-api-x4qvsargwa-uc.a.run.app",
    [string]$OutputDir = "outputs",
    [switch]$SkipSoak,
    [switch]$SkipSpike,
    [switch]$SkipEdge,
    [switch]$SkipChatOnly
)

function Invoke-LocustScenario {
    param(
        [string]$Label,
        [int]$Users,
        [double]$SpawnRate,
        [string]$RunTime,
        [string]$Suffix,
        [string[]]$ExtraArgs = @(),
        [string[]]$UserClasses = @()
    )

    Write-Host $Label -ForegroundColor Yellow
    $csvPrefix = Join-Path $OutputDir ("load_test_{0}_{1}" -f $Suffix, $timestamp)

    $arguments = @(
        '-m', 'locust',
        '-f', 'load_test.py',
        "--host=$ApiServiceUrl",
        '--users', $Users.ToString(),
        '--spawn-rate', $SpawnRate.ToString(),
        '--run-time', $RunTime,
        '--headless',
        "--csv=$csvPrefix"
    ) + $ExtraArgs
    if ($UserClasses -and $UserClasses.Count -gt 0) {
        $arguments += $UserClasses
    }

    & $PythonCommand $arguments
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        Write-Host "Locust exited with code $exitCode" -ForegroundColor Red
    }
    else {
        $script:completedResults += "$csvPrefix.csv"
        Write-Host "[OK] Scenario complete. Results: $csvPrefix.csv" -ForegroundColor Green
    }
}

# Resolve Python: prefer repo venv (LLM_Unified/.venv), then user site, then system
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$repoVenvPython = Join-Path $repoRoot '.venv\Scripts\python.exe'
if (Test-Path $repoVenvPython) {
    $PythonCommand = $repoVenvPython
}
else {
    $pythonScripts = Join-Path ([System.Environment]::GetFolderPath('ApplicationData')) "Python\Python313\Scripts"
    if (-not ($env:PATH -split ';' | Where-Object { $_ -eq $pythonScripts })) {
        $env:PATH += ";$pythonScripts"
    }
    $PythonCommand = 'python'
}
$env:PYTHONUTF8 = '1'

# Ensure output directory exists
if (!(Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$completedResults = @()

$scenarios = @(
    @{ Label = "[1] Light Load (10 users, 2 min)"; Users = 10; SpawnRate = 1; RunTime = "2m"; Suffix = "light"; Cooldown = 30 },
    @{ Label = "[2] Medium Load (50 users, 5 min)"; Users = 50; SpawnRate = 5; RunTime = "5m"; Suffix = "medium"; Cooldown = 60 },
    @{ Label = "[3] Heavy Load (100 users, 5 min)"; Users = 100; SpawnRate = 10; RunTime = "5m"; Suffix = "heavy"; Cooldown = 60 },
    @{ Label = "[4] Stress Test (200 users, 10 min)"; Users = 200; SpawnRate = 20; RunTime = "10m"; Suffix = "stress"; Cooldown = 120 },
    @{ Label = "[5] Soak Test (50 users, 8h)"; Users = 50; SpawnRate = 5; RunTime = "8h"; Suffix = "soak"; Cooldown = 60; Skip = $SkipSoak },
    @{ Label = "[6] Spike Test (0→200 users, 6 min)"; Users = 200; SpawnRate = 200; RunTime = "6m"; Suffix = "spike"; Cooldown = 60; Skip = $SkipSpike; UserClasses = @('IonApiUser') },
    @{ Label = "[7] Edge Case Test (abnormal payloads)"; Users = 20; SpawnRate = 2; RunTime = "5m"; Suffix = "edge"; Cooldown = 30; Skip = $SkipEdge; ExtraArgs = @('--tags', 'edge'); UserClasses = @('EdgeCaseUser') },
    @{ Label = "[8] Chat-only Test"; Users = 50; SpawnRate = 5; RunTime = "5m"; Suffix = "chatonly"; Cooldown = 30; Skip = $SkipChatOnly; ExtraArgs = @('--tags', 'chatonly'); UserClasses = @('ChatOnlyUser') }
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ION Mentoring API - Extended Load Testing Suite" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$scenarioCount = ($scenarios | Where-Object { -not $_.Skip }).Count
if ($scenarioCount -eq 0) {
    Write-Host "All scenarios were skipped. Nothing to do." -ForegroundColor Yellow
    return
}

$executedIndex = 0
foreach ($scenario in $scenarios) {
    if ($scenario.Skip) {
        Write-Host "Skipping scenario: $($scenario.Label)" -ForegroundColor DarkGray
        continue
    }

    $executedIndex++
    $label = $scenario.Label.Replace('[', ("[$executedIndex/$scenarioCount] "))
    Invoke-LocustScenario `
        -Label $label `
        -Users $scenario.Users `
        -SpawnRate $scenario.SpawnRate `
        -RunTime $scenario.RunTime `
        -Suffix $scenario.Suffix `
        -ExtraArgs $scenario.ExtraArgs

    if ($scenario.Cooldown -gt 0 -and $executedIndex -lt $scenarioCount) {
        Start-Sleep -Seconds $scenario.Cooldown
    }
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Extended Load Tests Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Results saved to:" -ForegroundColor White
foreach ($path in $completedResults) {
    Write-Host "  - $path" -ForegroundColor Gray
}
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Review CSV files for detailed statistics" -ForegroundColor Gray
Write-Host "  2. Check Cloud Monitoring dashboard for metrics" -ForegroundColor Gray
Write-Host "  3. Update LOAD_TESTING.md with measured benchmarks" -ForegroundColor Gray
Write-Host "  4. Include results in WEEK3_SUMMARY.md" -ForegroundColor Gray
Write-Host ""
