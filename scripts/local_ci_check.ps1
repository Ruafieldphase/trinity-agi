#!/usr/bin/env pwsh
# Local CI validation script - Run before pushing
# Usage: .\scripts\local_ci_check.ps1 [-Fast]

param(
    [switch]$Fast = $false,
    [switch]$Parallel = $false,
    [switch]$Coverage = $false,
    [switch]$CoverageHtml = $false,
    [switch]$OpenCoverage = $false
)

$ErrorActionPreference = "Stop"
$startTime = Get-Date

Write-Host "🔍 Local CI Validation Starting..." -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host ""

# Check 1: Git status
Write-Host "1️⃣  Checking git status..." -ForegroundColor Yellow
$gitStatus = git status --porcelain
if ($gitStatus) {
    Write-Host "   ⚠️  Uncommitted changes detected:" -ForegroundColor Yellow
    $gitStatus | ForEach-Object { Write-Host "      $_" -ForegroundColor Gray }
}
else {
    Write-Host "   ✅ Working directory clean" -ForegroundColor Green
}
Write-Host ""

# Check 2: Branch check
Write-Host "2️⃣  Checking current branch..." -ForegroundColor Yellow
$currentBranch = git branch --show-current
Write-Host "   📍 Branch: $currentBranch" -ForegroundColor Cyan
if ($currentBranch -eq "main") {
    Write-Host "   ⚠️  You're on main branch - consider using feature branch" -ForegroundColor Yellow
}
else {
    Write-Host "   ✅ Feature branch in use" -ForegroundColor Green
}
Write-Host ""

# Check 3: Python tests
Write-Host "3️⃣  Running Python tests..." -ForegroundColor Yellow
$testStart = Get-Date
try {
    $pytestArgs = @('-q', '--tb=short', '--basetemp', 'fdo_agi_repo/.pytest_tmp')
    if ($Parallel) { $pytestArgs += @('-n', 'auto') }
    if ($Coverage -or $CoverageHtml) {
        # Ensure cov target added once
        $pytestArgs += @('--cov=fdo_agi_repo')
    }
    if ($Coverage) {
        $pytestArgs += @('--cov-report', 'term-missing:skip-covered')
    }
    if ($CoverageHtml) {
        $covOut = 'outputs/coverage_html'
        if (-not (Test-Path $covOut)) { New-Item -ItemType Directory -Path $covOut -Force | Out-Null }
        $pytestArgs += @('--cov-report', "html:$covOut")
    }

    if ($Fast) {
        Write-Host "   ⚡ Fast mode: Running core tests only" -ForegroundColor Cyan
        $pytestArgs += 'fdo_agi_repo/tests/test_phase3_integration.py'
    }
    else {
        # Constrain discovery to core test suite
        $pytestArgs += 'fdo_agi_repo/tests'
    }

    Write-Host ("   ▶️  pytest {0}" -f ($pytestArgs -join ' ')) -ForegroundColor DarkGray
    python -m pytest @pytestArgs
    
    if ($LASTEXITCODE -eq 0) {
        $testDuration = [math]::Round(((Get-Date) - $testStart).TotalSeconds, 1)
        Write-Host "   ✅ All tests passed ($testDuration seconds)" -ForegroundColor Green
        if ($CoverageHtml -and $OpenCoverage) {
            $indexPath = Join-Path 'outputs/coverage_html' 'index.html'
            if (Test-Path $indexPath) { Start-Process $indexPath }
        }
    }
    else {
        Write-Host "   ❌ Tests failed with exit code $LASTEXITCODE" -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "   ❌ Test execution error: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Check 4: Code formatting (if black is available)
Write-Host "4️⃣  Checking code formatting..." -ForegroundColor Yellow
try {
    python -m black --version 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        python -m black --check --quiet fdo_agi_repo/ 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ Code formatting OK" -ForegroundColor Green
        }
        else {
            Write-Host "   ⚠️  Code formatting issues detected" -ForegroundColor Yellow
            Write-Host "      Run: python -m black fdo_agi_repo/" -ForegroundColor Gray
        }
    }
    else {
        Write-Host "   ℹ️  Black not installed (optional)" -ForegroundColor Gray
    }
}
catch {
    Write-Host "   ℹ️  Skipping formatting check" -ForegroundColor Gray
}
Write-Host ""

# Check 5: File size check
Write-Host "5️⃣  Checking for large files..." -ForegroundColor Yellow
try {
    $largeFiles = git ls-files | ForEach-Object {
        try {
            if (Test-Path $_) {
                $size = (Get-Item -LiteralPath $_).Length / 1MB
                if ($size -gt 1) {
                    [PSCustomObject]@{
                        File   = $_
                        SizeMB = [math]::Round($size, 2)
                    }
                }
            }
        }
        catch {
            # Skip files with invalid paths
        }
    } | Where-Object { $_ -ne $null }

    if ($largeFiles) {
        Write-Host "   ⚠️  Large files detected (>1MB):" -ForegroundColor Yellow
        $largeFiles | ForEach-Object { 
            Write-Host "      $($_.File) - $($_.SizeMB) MB" -ForegroundColor Gray 
        }
    }
    else {
        Write-Host "   ✅ No large files" -ForegroundColor Green
    }
}
catch {
    Write-Host "   ℹ️  Skipping file size check" -ForegroundColor Gray
}
Write-Host ""

# Summary
$totalDuration = [math]::Round(((Get-Date) - $startTime).TotalSeconds, 1)
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host "✨ Local CI check completed in $totalDuration seconds" -ForegroundColor Cyan
Write-Host ""
Write-Host "Ready to push! 🚀" -ForegroundColor Green
Write-Host ""

exit 0