<#
.SYNOPSIS
Glymphatic 텔레메트리 요약을 갱신하고 확인하는 스크립트.

.DESCRIPTION
`scripts/aggregate_glymphatic_metrics.py`를 호출해 최근 N시간 기준의
Glymphatic 요약 통계를 생성하고, 선택적으로 요약 JSON을 출력합니다.

.PARAMETER Hours
집계할 시간 범위(시간 단위). 기본값은 24시간입니다.

.PARAMETER PythonExe
실행할 파이썬 실행 파일 경로. 기본값은 `python`입니다.

.PARAMETER SummaryPath
요약 JSON이 저장될 경로. 기본값은 `outputs/glymphatic_metrics_latest.json`입니다.

.PARAMETER Json
지정하면 Python 스크립트의 JSON 출력(`--json`)을 활성화합니다.

.PARAMETER OpenSummary
집계 후 요약 JSON 파일 내용을 콘솔에 출력합니다.
#>
param (
    [int]$Hours = 24,
    [string]$PythonExe = "python",
    [string]$SummaryPath = "outputs/glymphatic_metrics_latest.json",
    [switch]$Json,
    [switch]$OpenSummary
)

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot

try {
    $argsList = @(
        "scripts/aggregate_glymphatic_metrics.py",
        "--hours", $Hours,
        "--summary-path", $SummaryPath
    )

    if ($Json) {
        $argsList += "--json"
    }

    Write-Host "▶ Running aggregate_glymphatic_metrics.py (hours=$Hours)..."
    & $PythonExe @argsList
    if ($LASTEXITCODE -ne 0) {
        throw "aggregate_glymphatic_metrics.py exited with code $LASTEXITCODE"
    }

    if ($OpenSummary) {
        if (Test-Path $SummaryPath) {
            Write-Host "`n📄 Summary ($SummaryPath):"
            Get-Content $SummaryPath
        } else {
            Write-Warning "Summary file not found: $SummaryPath"
        }
    }
}
finally {
    Pop-Location
}

