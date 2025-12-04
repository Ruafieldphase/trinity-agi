<#!
.SYNOPSIS
    루빛 시각화 이미지를 한 번에 재생성합니다.
.DESCRIPTION
    내부 Python 스크립트(visualize_lubit_data.py)를 호출해 JSON 실험 데이터를 기반으로
    PNG 그래프 3종을 만듭니다. CI나 예약 작업에 바로 연결할 수 있도록 파라미터를 제공합니다.
.PARAMETER Python
    실행할 파이썬 명령. 기본값은 PATH 상의 `python`입니다.
.PARAMETER Data
    입력 JSON 경로(포트폴리오 루트 기준). 기본값은 `lubit_phase_injection_simulation.json`입니다.
.PARAMETER OutputDir
    출력 폴더 경로(포트폴리오 루트 기준). 기본값은 `visualizations`입니다.
.EXAMPLE
    ./update_visualizations.ps1
.EXAMPLE
    ./update_visualizations.ps1 -Python "C:\\venv\\Scripts\\python.exe" -Data data/custom.json
#>
param(
    [string]$Python = "python",
    [string]$Data = "lubit_phase_injection_simulation.json",
    [string]$OutputDir = "visualizations"
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$portfolioRoot = Split-Path -Parent $scriptDir

$visualizeScript = Join-Path $scriptDir 'visualize_lubit_data.py'
if (-not (Test-Path -LiteralPath $visualizeScript)) {
    Write-Error "visualize_lubit_data.py 스크립트를 찾을 수 없습니다: $visualizeScript"
    exit 1
}

function Resolve-PathRelative {
    param([string]$relativePath)
    $combined = Join-Path $portfolioRoot $relativePath
    $resolved = Resolve-Path -LiteralPath $combined -ErrorAction SilentlyContinue
    if ($resolved) {
        return $resolved.Path
    }
    return $combined
}

$dataPath = Resolve-PathRelative $Data
if (-not (Test-Path -LiteralPath $dataPath)) {
    Write-Error "데이터 파일을 찾을 수 없습니다: $dataPath"
    exit 1
}

$outputPath = Resolve-PathRelative $OutputDir
if (-not (Test-Path -LiteralPath $outputPath)) {
    New-Item -ItemType Directory -Path $outputPath -Force | Out-Null
}

$arguments = @(
    $visualizeScript,
    '--data', $dataPath,
    '--output-dir', $outputPath
)

& $Python @arguments
exit $LASTEXITCODE
