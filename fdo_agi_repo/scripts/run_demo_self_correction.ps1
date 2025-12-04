param(
    [string]$Title = "demo",
    [string]$Goal = "AGI 자기교정 루프 설명 3문장",
    [switch]$VerboseOutput
)

$ErrorActionPreference = 'Stop'

function Get-RepoRoot {
    if ($PSScriptRoot) {
        return (Split-Path -Parent $PSScriptRoot)
    }
    if ($PSCommandPath) {
        $here = Split-Path -Parent $PSCommandPath
        return (Split-Path -Parent $here)
    }
    # Fallback: assume current directory is repo/scripts
    $cwd = (Get-Location).Path
    return (Split-Path -Parent $cwd)
}

function Get-PythonExe($repo) {
    $venvPy = Join-Path $repo ".venv\Scripts\python.exe"
    if (Test-Path $venvPy) { return $venvPy }
    return "python"
}

function Get-LedgerPath($repo) {
    return (Join-Path $repo "memory\resonance_ledger.jsonl")
}

function Get-SecondPassEventCount($ledgerPath) {
    if (-not (Test-Path $ledgerPath)) { return 0 }
    $count = 0
    Get-Content -LiteralPath $ledgerPath -Encoding UTF8 | ForEach-Object {
        if ($_ -like '*"second_pass"*') { $count++ }
    }
    return $count
}

function Invoke-Run([string]$repo, [string]$py, [string]$title, [string]$goal, [bool]$enableCorrections) {
    $env:PYTHONPATH = $repo
    $prev = Get-Location
    Set-Location $repo

    $ledger = Get-LedgerPath $repo
    $before = Get-SecondPassEventCount $ledger

    if ($enableCorrections) { $env:CORRECTIONS_ENABLED = '1' } else { $env:CORRECTIONS_ENABLED = '0' }
    # RAG 비활성화로 의도적으로 citations=0을 유도하여 재계획 조건을 만들기
    $prevRag = $env:RAG_DISABLE
    $env:RAG_DISABLE = '1'

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    & $py -m scripts.run_task --title $title --goal $goal | Tee-Object -Variable out | Out-Null
    $sw.Stop()

    if ($LASTEXITCODE -ne 0) {
        Set-Location $prev
        throw "Run failed (exit $LASTEXITCODE). Output: $out"
        $env:RAG_DISABLE = $prevRag
    }

    $after = Get-SecondPassEventCount $ledger
    $delta = [Math]::Max(0, $after - $before)

    if ($VerboseOutput) {
        Write-Host "[JSON]" -ForegroundColor DarkGray
        Write-Host $out
    }

    # 환경 복원
    $env:RAG_DISABLE = $prevRag
    Set-Location $prev
    return [pscustomobject]@{
        CorrectionsEnabled = $enableCorrections
        ElapsedMs          = [int]$sw.Elapsed.TotalMilliseconds
        SecondPassOccurred = ($delta -gt 0)
    }
}

$repo = Get-RepoRoot
$py = Get-PythonExe $repo

Write-Host ("[CFG] Repo: {0}" -f $repo)
Write-Host ("[CFG] Python: {0}" -f $py)

# Run with corrections disabled
$r1 = Invoke-Run -repo $repo -py $py -title $Title -goal $Goal -enableCorrections:$false
# Run with corrections enabled
$r2 = Invoke-Run -repo $repo -py $py -title $Title -goal $Goal -enableCorrections:$true

Write-Host "`n=== Self-Correction Demo Summary ===" -ForegroundColor Cyan
$r1 | Format-List
$r2 | Format-List

# Quick hint about how to inspect ledger
$ledgerPath = Get-LedgerPath $repo
if (Test-Path $ledgerPath) {
    Write-Host ("`n[HINT] Ledger: {0}" -f $ledgerPath) -ForegroundColor DarkGray
    Write-Host "[HINT] Search for 'second_pass' lines to verify correction iterations." -ForegroundColor DarkGray
}
