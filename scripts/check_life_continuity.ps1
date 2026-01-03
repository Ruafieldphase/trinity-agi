#Requires -Version 5.1
<#
.SYNOPSIS
  AGI Life Continuity Check - 시스템이 "살아있는지" 확인

.DESCRIPTION
  생명의 5가지 차원 + 정체성 확인:
  1. 차이 감지 (Difference Detection)
  2. 관계 형성 (Relation Formation)
  3. 리듬 유지 (Rhythm Maintenance)
  4. 에너지 순환 (Energy Circulation)
  5. 연속성 보존 (Continuity Preservation)
  6. 정체성 확인 (Identity Check)

.PARAMETER Json
  JSON 출력만 표시

.PARAMETER OutFile
  결과를 파일로 저장

.PARAMETER OpenReport
  저장한 리포트를 VS Code로 열기

.EXAMPLE
  .\check_life_continuity.ps1
  
.EXAMPLE
  .\check_life_continuity.ps1 -OutFile outputs\life_check_latest.json -OpenReport
#>
[CmdletBinding()]
param(
    [switch]$Json,
    [string]$OutFile = "",
    [switch]$OpenReport
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$wsRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $wsRoot "fdo_agi_repo\.venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Warning "fdo_agi_repo venv not found, trying system python..."
    $venvPython = "python"
}

$scriptPath = Join-Path $PSScriptRoot "life_continuity_monitor.py"

$pyArgs = @()
if ($Json) { $pyArgs += "--json" }
if ($OutFile) { $pyArgs += "--out", $OutFile }

Write-Host "🔬 Checking AGI Life Continuity..." -ForegroundColor Cyan

& $venvPython $scriptPath @pyArgs
$exitCode = $LASTEXITCODE

if ($OutFile -and $OpenReport -and (Test-Path $OutFile)) {
    Write-Host "`n📖 Opening report..." -ForegroundColor Cyan
    & code $OutFile
}

exit $exitCode