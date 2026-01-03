#!/usr/bin/env pwsh
<#!
.SYNOPSIS
  Run Lubit review packet builder and Gemini code assist POC in parallel.
.DESCRIPTION
  Prepares review ZIP while concurrently asking Gemini for code assist notes. Outputs paths at the end.
.PARAMETER Issue
  Short description of the coding task/problem for the Gemini POC.
.PARAMETER TargetFile
  Optional path to a target code file for Gemini to consider.
.PARAMETER Model
  Gemini model name. Default: gemini-2.0-flash-exp
.PARAMETER OutDir
  Output base directory for artifacts. Default: $WorkspaceRoot\outputs
#>
param(
    [Parameter(Mandatory = $false)][string]$Issue = "Review Week3 deliverables and propose small refactors to summary pipeline and logging.",
    [string]$TargetFile = $null,
    [string]$Model = "gemini-2.0-flash-exp",
    [string]$OutDir = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs"
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Stop"

function New-DirectoryIfMissing($path) { if (-not (Test-Path -LiteralPath $path)) { New-Item -ItemType Directory -Path $path | Out-Null } }

$root = "$WorkspaceRoot"
New-DirectoryIfMissing $OutDir
$ts = (Get-Date).ToString('yyyyMMdd_HHmmss')

# 1) Start Gemini POC as a background job (if python exists)
$venvPython = "$WorkspaceRoot\LLM_Unified\.venv\Scripts\python.exe"
$geminiOut = Join-Path $OutDir ("gemini_assist_" + $ts + ".md")

$geminiJob = $null
if (Test-Path -LiteralPath $venvPython) {
    $pyArgs = @("tools/gemini_code_assist_poc.py", "--issue", $Issue, "--model", $Model, "--out", $geminiOut)
    if ($TargetFile) { $pyArgs += @("--file", $TargetFile) }
    $geminiJob = Start-Job -ScriptBlock {
        param($py, $wdir, $argv)
        Push-Location $wdir
        & $py $argv 2>&1
        $exit = $LASTEXITCODE
        Pop-Location
        return $exit
    } -ArgumentList $venvPython, $root, $pyArgs
    Write-Host "Started Gemini POC job..." -ForegroundColor Cyan
}
else {
    Write-Host "[WARN] venv python not found: $venvPython" -ForegroundColor Yellow
}

# 2) Prepare Lubit review packet (foreground)
& (Join-Path $root "scripts/prepare_lubit_review_packet.ps1") -OutDir $OutDir

# 3) Wait for Gemini job and capture exit
$geminiExit = $null
if ($geminiJob) {
    Wait-Job $geminiJob | Out-Null
    $geminiExit = Receive-Job $geminiJob
    Remove-Job $geminiJob | Out-Null
}

Write-Host ""; Write-Host "=== Parallel Run Summary ===" -ForegroundColor Green
Write-Host "Gemini output: $geminiOut" -ForegroundColor Cyan
if ($null -ne $geminiExit) { Write-Host "Gemini exit code: $geminiExit" -ForegroundColor Cyan }
Write-Host "Review packet and zip are under: $OutDir" -ForegroundColor Cyan